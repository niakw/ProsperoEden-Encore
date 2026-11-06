#!/usr/bin/env python3
"""P1.3/P4.2 host witness: concurrent Gather on the REAL shared GPU dirty owner.

A host1x video decoder may call Gather while the GPU worker is gathering.
The callback runs outside the producer guard, but it must not race another
consumer's front_buffer.swap / clear. This test compiles the pinned header.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = Path(os.environ.get(
    "EDEN_GPU_DIRTY_HEADER_SOURCE",
    str(ROOT / "vendor/encore-active/eden-core/overrides/core/gpu_dirty_memory_manager.h")))
body = OWNER.read_text()
assert body.count("std::scoped_lock gather_lock(gather_guard);") == 1
assert body.count("std::mutex gather_guard;") == 1
assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")' in (
    ROOT/"headless/CMakeLists.txt").read_text()
# The pinned Eden source now carries the same concurrency fix. Verify both
# independent implementations guard the entire front-buffer iteration; a
# stale "upstream must have no lock" assumption is not a safety property.
pinned = (ROOT/"vendor/sources/eden/src/core/gpu_dirty_memory_manager.h").read_text()
assert pinned.count("std::mutex gather_guard;") == 1
assert pinned.count("std::scoped_lock gather_lock{gather_guard};") == 1
assert pinned.index("std::scoped_lock gather_lock{gather_guard};") < pinned.index(
    "front_buffer.swap(back_buffer)")
assert pinned.index("front_buffer.swap(back_buffer)") < pinned.index(
    "front_buffer.clear();")
assert body.index("std::scoped_lock gather_lock(gather_guard);") < body.index(
    "front_buffer.swap(back_buffer)")
assert body.index("front_buffer.clear();") < body.index("private:")

fixture = r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <functional>
#include <thread>
#include "core/gpu_dirty_memory_manager.h"

int main() {
    Core::GPUDirtyMemoryManager dirty;
    constexpr PAddr first_address = 0x10000;
    constexpr PAddr second_address = 0x30000;
    dirty.Collect(first_address, 64);
    std::atomic<bool> first_entered{false};
    std::atomic<bool> release_first{false};
    std::atomic<bool> second_started{false};
    std::atomic<unsigned> first_calls{0};
    std::atomic<unsigned> second_calls{0};

    std::function<void(PAddr, size_t)> first = [&](PAddr addr, size_t bytes) {
        assert(addr == first_address && bytes == 64);
        first_calls.fetch_add(1, std::memory_order_relaxed);
        first_entered.store(true, std::memory_order_release);
        while (!release_first.load(std::memory_order_acquire))
            std::this_thread::yield();
    };
    std::function<void(PAddr, size_t)> second = [&](PAddr addr, size_t bytes) {
        assert(addr == second_address && bytes == 64);
        second_calls.fetch_add(1, std::memory_order_relaxed);
    };

    std::thread consumer_a([&] { dirty.Gather(first); });
    while (!first_entered.load(std::memory_order_acquire))
        std::this_thread::yield();
    // The guest GPU producer is free to Collect during a Gather callback.
    dirty.Collect(second_address, 64);
    std::thread consumer_b([&] {
        second_started.store(true, std::memory_order_release);
        dirty.Gather(second);
    });
    while (!second_started.load(std::memory_order_acquire))
        std::this_thread::yield();
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    // Without the gather lock, consumer B swaps/reuses A's front_buffer.
    assert(second_calls.load(std::memory_order_relaxed) == 0);
    release_first.store(true, std::memory_order_release);
    consumer_a.join();
    consumer_b.join();
    assert(first_calls.load(std::memory_order_relaxed) == 1);
    assert(second_calls.load(std::memory_order_relaxed) == 1);
    // Both batches must be drained, not accidentally replayed later.
    unsigned leftovers{};
    std::function<void(PAddr, size_t)> empty = [&](PAddr, size_t) {
        ++leftovers;
    };
    dirty.Gather(empty);
    assert(leftovers == 0);
    std::puts("P1_3_SHARED_GPU_DIRTY_GATHER_RACE_PASS");
}
"""
# The pinned active header is copied byte-for-byte to a temporary overlay
# before compilation; dependencies resolve from the real vendor source tree.
# The override is only for isolated local worktree validation.
with tempfile.TemporaryDirectory(prefix="eden-gpu-dirty-gather-") as temp:
    temp = Path(temp)
    overlay = temp/"include"/"core"
    overlay.mkdir(parents=True)
    (overlay/"gpu_dirty_memory_manager.h").write_text(body)
    cpp = temp/"test.cpp"
    cpp.write_text("#include <cstdio>\n" + fixture)
    roots = [temp/"include", ROOT/"vendor/sources/eden/src",
             ROOT/"vendor/sources/fmt/include"]
    boost = ROOT/"vendor/sources/eden-cpm/boost/boost-1.90.0/libs"
    roots += list(boost.glob("*/include"))
    includes = ["-I"+str(p) for p in roots if p.is_dir()]
    sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    env = os.environ.copy()
    if sdk.exists():
        env["SDKROOT"] = str(sdk)
    compilers = list(dict.fromkeys(filter(None, (
        shutil.which("clang++"), shutil.which("g++")))))
    assert compilers
    for cxx in compilers:
        for opt in ("-O0", "-O2"):
            exe = temp/(Path(cxx).name.replace("+", "p")+opt)
            cmd = [cxx, "-std=c++20", opt, "-Wall", "-Wextra",
                   "-Werror", "-Wno-unused-parameter", "-pthread",
                   "-fsanitize=undefined", "-fno-sanitize-recover=all",
                   *includes, str(cpp), "-o", str(exe)]
            built = subprocess.run(cmd, env=env, capture_output=True,
                                   text=True, timeout=65)
            assert built.returncode == 0, (cxx, built.stderr[-3500:])
            run = subprocess.run([str(exe)], env=env, capture_output=True,
                                 text=True, timeout=15)
            assert run.returncode == 0, (cxx, run.stderr[-3500:])
            assert "P1_3_SHARED_GPU_DIRTY_GATHER_RACE_PASS" in run.stdout
            print("P1_3_SHARED_GPU_DIRTY_GATHER_PASS",
                  Path(cxx).name, opt, flush=True)
