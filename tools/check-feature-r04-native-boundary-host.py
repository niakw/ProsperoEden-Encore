#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile the shipping R04 C++ bodies with small source-extracted host shims.

This proves the exact native AudioIn stream's sample lengths and the exact
maintained RomFS destructor's nonrecursive ownership release. It does not
replace eden-devices-check/eden-romfs-check or a full PS5 native link.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "headless/audio.cpp"
MAIN = ROOT / "headless/main.cpp"
ROMFS = ROOT / "vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp"
DEVICES_CHECK = ROOT / "headless/devices_check.cpp"
ROMFS_CHECK = ROOT / "headless/romfs_check.cpp"


def extract(source: str, start: str, end: str) -> str:
    if source.count(start) != 1:
        raise AssertionError(f"expected one source anchor {start!r}")
    first = source.index(start)
    stop = source.index(end, first + len(start))
    return source[first:stop]


def run_cpp(name: str, cpp: str, optimization: str) -> None:
    with tempfile.TemporaryDirectory(prefix=f"encore-r04-{name}-") as folder:
        source = Path(folder) / "check.cpp"
        binary = Path(folder) / "check"
        source.write_text(cpp, encoding="utf-8")
        subprocess.run(
            [os.environ.get("CXX", "g++"), "-std=c++20", optimization,
             "-Wall", "-Wextra", "-Werror", "-pthread",
             "-fsanitize=undefined", "-fno-sanitize-recover=all",
             str(source), "-o", str(binary)],
            check=True,
        )
        subprocess.run([str(binary)], check=True)
        print(f"R04_{name}_EXTRACTED_NATIVE_PASS {optimization}", flush=True)


def main() -> None:
    audio = AUDIO.read_text(encoding="utf-8")
    romfs = ROMFS.read_text(encoding="utf-8")
    main_cpp = MAIN.read_text(encoding="utf-8")
    native_audio_class = extract(audio, "class SilentInputStream final : public SinkStream {", "\n} // namespace")
    if "std::make_unique<SilentInputStream>(system)" not in audio:
        raise AssertionError("shipping guest AudioIn must select silent stream")
    if 'Settings::values.audio_input_device_id = "ps5";' not in main_cpp:
        raise AssertionError("native session must select the PS5 input sink")
    if "const auto released = input->ReleaseBuffer(0xf00 / sizeof(s16))" not in DEVICES_CHECK.read_text():
        raise AssertionError("whole-device AudioIn regression fixture absent")
    audio_cpp = r"""
#include <cassert>
#include <cstdint>
#include <span>
#include <vector>
using s16 = int16_t;
using u64 = uint64_t;
namespace Core { struct System {}; }
enum class StreamType { In, Out };
struct SinkBuffer {};
struct SinkStream {
    explicit SinkStream(Core::System&, StreamType) {}
    virtual ~SinkStream() = default;
    virtual void AppendBuffer(SinkBuffer&, std::span<s16>) = 0;
    virtual std::vector<s16> ReleaseBuffer(u64) = 0;
};
""" + native_audio_class + r"""
int main() {
    Core::System system;
    SilentInputStream input(system);
    SinkBuffer empty{};
    std::vector<s16> samples(7, 24);
    input.AppendBuffer(empty, samples);
    for (unsigned n : {0u, 1u, 0x780u, 48000u}) {
        auto block = input.ReleaseBuffer(n);
        assert(block.size() == n);
        for (auto sample : block) assert(sample == 0);
    }
}
"""
    destructor = extract(romfs, "RomFSBuildContext::~RomFSBuildContext() {", "\n}\n") + "\n}"
    if "for (auto& file : files)" not in destructor or "dir->child.reset();" not in destructor:
        raise AssertionError("wide-tree safe destructor is not present")
    fixture = ROMFS_CHECK.read_text(encoding="utf-8")
    if "pthread_attr_setstacksize(&attributes, 256 * 1024)" not in fixture or "32768" not in fixture:
        raise AssertionError("real builder 32K-entry/256KiB stack fixture missing")
    romfs_cpp = r"""
#include <atomic>
#include <cassert>
#include <memory>
#include <pthread.h>
#include <vector>
#include <utility>
static std::atomic<int> alive = 0;
struct RomFSBuildFileContext {
    RomFSBuildFileContext() { ++alive; }
    ~RomFSBuildFileContext() { --alive; }
    std::shared_ptr<RomFSBuildFileContext> sibling;
};
struct RomFSBuildDirectoryContext {
    RomFSBuildDirectoryContext() { ++alive; }
    ~RomFSBuildDirectoryContext() { --alive; }
    std::shared_ptr<RomFSBuildDirectoryContext> child;
    std::shared_ptr<RomFSBuildDirectoryContext> sibling;
    std::shared_ptr<RomFSBuildFileContext> file;
};
struct RomFSBuildContext {
    std::vector<std::shared_ptr<RomFSBuildDirectoryContext>> directories;
    std::vector<std::shared_ptr<RomFSBuildFileContext>> files;
    ~RomFSBuildContext();
};
""" + destructor + r"""
static void* wide(void*) {
    for (bool directory_case : {false, true}) {
        {
            RomFSBuildContext ctx;
            if (directory_case) {
                ctx.directories.reserve(32768);
                for (int i=0; i<32768; ++i) {
                    auto node = std::make_shared<RomFSBuildDirectoryContext>();
                    if (!ctx.directories.empty()) ctx.directories.back()->sibling = node;
                    ctx.directories.push_back(std::move(node));
                }
                ctx.directories.front()->child = ctx.directories[100];
            } else {
                ctx.files.reserve(32768);
                for (int i=0; i<32768; ++i) {
                    auto node = std::make_shared<RomFSBuildFileContext>();
                    if (!ctx.files.empty()) ctx.files.back()->sibling = node;
                    ctx.files.push_back(std::move(node));
                }
            }
        }
        assert(alive.load() == 0);
    }
    return nullptr;
}
int main() {
    pthread_attr_t attrs{};
    assert(pthread_attr_init(&attrs) == 0);
    assert(pthread_attr_setstacksize(&attrs, 256 * 1024) == 0);
    pthread_t thread{};
    assert(pthread_create(&thread, &attrs, wide, nullptr) == 0);
    assert(pthread_attr_destroy(&attrs) == 0);
    assert(pthread_join(thread, nullptr) == 0);
    assert(alive.load() == 0);
}
"""
    for opt in ("-O0", "-O2"):
        run_cpp("AUDIOIN", audio_cpp, opt)
        run_cpp("ROMFS_WIDE_TREE", romfs_cpp, opt)


if __name__ == "__main__":
    main()
