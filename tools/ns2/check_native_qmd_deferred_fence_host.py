#!/usr/bin/env python3
"""P4.2: execute the two real deferred Ampere QMD3 fence bodies under faults.

This is a C++20 host fixture, NOT proof of Vulkan or PS5 hardware execution.
Both callbacks come directly from the versioned production puller source.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PULLER = ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp"
source = PULLER.read_text()

def fenced_body(marker):
    assert source.count(marker) == 1, marker
    remaining = source.split(marker, 1)[1]
    start = remaining.index("                try {")
    end = remaining.index("\n            });", start)
    body = remaining[start:end]
    assert body.count("Eden::RecordGpuFailure(std::current_exception());") == 1
    assert body.count("catch (...)") == 1
    assert "#ifdef PS5_NATIVE" in body
    return body

reduction = fenced_body("// The deferred fence may execute after a sparse GMMU unmap.")
release = fenced_body("// A QMD3 dispatch can already be accepted when this")

fixture = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include "gpu_failure.h"
#include "video_core/native_qmd.h"
using u32 = std::uint32_t;
using u64 = std::uint64_t;
namespace Service::Nvidia::Devices {
class NativeGpuChannelRegistry {
    bool active{true};
public:
    void Revoke() {active=false;}
    static NativeGpuChannelRegistry& Instance() {
        static NativeGpuChannelRegistry instance;
        return instance;
    }
    bool IsCurrent(const int* channel, int ticket) const {
        return active && channel && ticket == 7;
    }
};
}
struct Memory {
    bool mapped = true;
    bool fail_map = false;
    bool fail_read = false;
    bool fail_write = false;
    u32 stored = 5;
    unsigned writes = 0;
    bool IsFullyMappedRange(u64, std::size_t) {
        if (fail_map) throw std::runtime_error("mapping race");
        return mapped;
    }
    // The maintained deferred QMD3 release checks the CPU backing
    // pointer in addition to the GMMU span. Keep the test's fail_map
    // exception behavior so a late backing failure is still latched.
    u32* GetPointer(u64) {
        if (fail_map) throw std::runtime_error("mapping race");
        return mapped ? &stored : nullptr;
    }
    template<class T> T Read(u64) {
        if (fail_read) throw std::runtime_error("guest read fault");
        return static_cast<T>(stored);
    }
    template<class T> void Write(u64, T value) {
        if (fail_write) throw std::runtime_error("guest write fault");
        stored = static_cast<u32>(value);
        ++writes;
    }
};
int main() {
    int owner = 42;
    const int* channel = &owner;
    int ticket = 7;
    Memory data;
    auto* memory = &data;
    u64 address = 0x2000;
    u64 addr = address;
    u32 payload = 3;
    u32 reduction = 0;
    u32 flags = 1u << 26;
    const auto reduced = [channel, memory, ticket, address, payload, reduction] {
__REDUCTION__
    };
    const auto released = [channel, memory, ticket, addr, payload, flags] {
__RELEASE__
    };
    Eden::ResetGpuFailureForTitle();
    reduced();
    assert(data.stored == 8 && data.writes == 1 && !Eden::PeekGpuFailure());
    data.mapped = false;
    reduced();
    assert(data.writes == 1 && Eden::PeekGpuFailure());
    Eden::ResetGpuFailureForTitle();
    data.mapped = true;
    data.fail_map = true;
    reduced();
    assert(data.writes == 1 && Eden::PeekGpuFailure());
    Eden::ResetGpuFailureForTitle();
    data.fail_map = false;
    data.fail_read = true;
    reduced();
    assert(data.writes == 1 && Eden::PeekGpuFailure());
    Eden::ResetGpuFailureForTitle();
    data.fail_read = false;
    data.fail_write = true;
    reduced();
    assert(data.stored == 8 && data.writes == 1 && Eden::PeekGpuFailure());
    Eden::ResetGpuFailureForTitle();
    data.fail_write = false;
    released();
    assert(data.stored == 11 && data.writes == 2 && !Eden::PeekGpuFailure());
    data.fail_map = true;
    released();
    assert(data.writes == 2 && Eden::PeekGpuFailure());
    Eden::ResetGpuFailureForTitle();
    data.fail_map = false;
    data.fail_read = true;
    released();
    assert(data.writes == 2 && Eden::PeekGpuFailure());
    Eden::ResetGpuFailureForTitle();
    data.fail_read = false;
    data.fail_write = true;
    released();
    assert(data.writes == 2 && Eden::PeekGpuFailure());
    Eden::ResetGpuFailureForTitle();
    data.fail_write = false;
    released();
    assert(data.writes == 3 && data.stored == 14);
    Eden::ResetGpuFailureForTitle();
    Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance().Revoke();
    // The callback captured the historical ticket, but the registry revoked
    // that epoch. Neither deferred path may publish a stale guest completion.
    reduced();
    released();
    assert(data.writes == 3 && data.stored == 14 && !Eden::PeekGpuFailure());
    std::puts("P4_2_NATIVE_DEFERRED_FENCE_FAULT_HOST_PASS");
}
"""
fixture = fixture.replace("__REDUCTION__", reduction).replace("__RELEASE__", release)
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
env = os.environ.copy()
if sdk.exists():
    env["SDKROOT"] = str(sdk)
compilers = list(dict.fromkeys(filter(None, (
    shutil.which("clang++"), shutil.which("g++")))))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-qmd-fence-fault-") as folder:
    src = Path(folder) / "test.cpp"
    src.write_text(fixture)
    for compiler in compilers:
        for opt in ("-O0", "-O2"):
            out = Path(folder) / (Path(compiler).name.replace("+", "p") + opt)
            args = [compiler, "-std=c++20", opt, "-Wall", "-Wextra",
                    "-Werror", "-Wno-unused-parameter", "-pthread",
                    "-DPS5_NATIVE=1", "-fsanitize=undefined",
                    "-fno-sanitize-recover=all",
                    "-I"+str(ROOT/"headless"),
                    "-I"+str(ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch"),
                    str(src), "-o", str(out)]
            built = subprocess.run(args, env=env, text=True,
                                   capture_output=True, timeout=45)
            assert built.returncode == 0, (compiler, built.stderr[-2700:])
            ran = subprocess.run([str(out)], env=env, text=True,
                                 capture_output=True, timeout=15)
            assert ran.returncode == 0, (compiler, ran.stderr[-2700:])
            assert "P4_2_NATIVE_DEFERRED_FENCE_FAULT_HOST_PASS" in ran.stdout
            print("P4_2_NATIVE_DEFERRED_QMD_FENCE_PASS", Path(compiler).name,
                  opt, "read/write/unmap=latched revoked_channel=no_completion", flush=True)
