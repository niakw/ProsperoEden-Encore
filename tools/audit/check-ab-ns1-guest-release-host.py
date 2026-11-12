#!/usr/bin/env python3
"""Compile the actual native DeviceSession::ReleaseBuffer body with fake guest memory.

Checks whole-frame PCM16, bounded sizes, valid guest spans, zero-byte requests,
short mic vectors, successful copies and guard bytes under ASan/UBSan. Still
NOT a compiled original Eden audio_core module or PS5 console runtime proof.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vendor/encore-active/eden-core/src/audio_core/device/device_session.cpp"
START = "void DeviceSession::ReleaseBuffer(const AudioBuffer& buffer) const {"
END = "\nbool DeviceSession::IsBufferConsumed"

def main() -> None:
    original = SOURCE.read_text()
    if original.count(START) != 1 or original.count(END) != 1:
        raise AssertionError("AudioIn release source signature drift")
    method = START + original.split(START, 1)[1].split(END, 1)[0]
    for expected in (
        "IsValidAudioInBufferShape(buffer.size, channel_count)",
        "memory.ReadyForAudioRead()",
        "IsValidVirtualAddressRange(Common::ProcessAddress{buffer.samples}",
        "samples.size() != buffer.size / sizeof(s16)",
        "WriteBlockUnsafe(buffer.samples, samples.data(), buffer.size)",
    ):
        if expected not in method:
            raise AssertionError("required guest memory safety check missing: " + expected)
    test = r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>
#include "audio_in_silence.h"

using u16 = std::uint16_t;
using u64 = std::uint64_t;
using s16 = std::int16_t;
namespace Common { struct ProcessAddress { u64 value; }; }
struct Memory {
    bool ReadyForAudioRead() const noexcept { return true; }
    std::vector<std::uint8_t> bytes;
    mutable unsigned checks{};
    unsigned writes{};
    Memory() : bytes(Eden::kMaxSilentAudioInBytes + 32, 0xa5) {}
    bool IsValidVirtualAddressRange(Common::ProcessAddress addr, u64 size) const {
        ++checks;
        return addr.value <= bytes.size() && size <= bytes.size() - addr.value;
    }
    bool WriteBlockUnsafe(u64 addr, const void* src, std::size_t size) {
        assert(IsValidVirtualAddressRange({addr}, size));
        assert(size != 0 && src != nullptr);
        std::memcpy(bytes.data() + addr, src, size);
        ++writes;
        return true;
    }
};
struct Process {
    Memory memory;
    Memory& GetMemory() { return memory; }
};
namespace AudioCore {
namespace Sink {
enum class StreamType { Render, Out, In };
struct SinkStream {
    bool shortened{};
    std::vector<s16> ReleaseBuffer(u64 samples) {
        auto count = static_cast<std::size_t>(samples);
        if (shortened && count > 0) --count;
        return std::vector<s16>(count, 0);
    }
};
}
struct AudioBuffer { u64 size; u64 samples; };
struct DeviceSession {
    Sink::StreamType type{Sink::StreamType::In};
    u16 channel_count{2};
    Process* handle{};
    Sink::SinkStream* stream{};
    void ReleaseBuffer(const AudioBuffer&) const;
};
""" + method + r"""
}
int main() {
    Process proc;
    AudioCore::Sink::SinkStream stream;
    AudioCore::DeviceSession session;
    session.handle = &proc;
    session.stream = &stream;
    auto& mem = proc.memory;
    // A valid capture writes exactly its requested PCM16 bytes.
    session.ReleaseBuffer({4, 1});
    assert(mem.writes == 1);
    assert(mem.bytes.front() == 0xa5 && mem.bytes[1] == 0 &&
           mem.bytes[4] == 0 && mem.bytes[5] == 0xa5);
    for (u64 bad : std::array<u64, 6>{0, 1, 3, 5,
                     Eden::kMaxSilentAudioInBytes + 2,
                     UINT64_MAX}) {
        session.ReleaseBuffer({bad, 1});
        assert(mem.writes == 1);
    }
    // On 2-channel input 6 bytes is not a whole PCM frame.
    session.ReleaseBuffer({6, 1});
    assert(mem.writes == 1);
    // Reject invalid guest spans BEFORE dereferencing/copying host memory.
    session.ReleaseBuffer({4, mem.bytes.size() - 1});
    session.ReleaseBuffer({4, UINT64_MAX});
    assert(mem.writes == 1);
    // Even a vector returned too short by a different sink must not overread.
    stream.shortened = true;
    session.ReleaseBuffer({4, 1});
    assert(mem.writes == 1);
    stream.shortened = false;
    session.channel_count = 6;
    session.ReleaseBuffer({12, 10});
    assert(mem.writes == 2);
    session.channel_count = 0;
    session.ReleaseBuffer({4, 1});
    assert(mem.writes == 2);
    session.channel_count = 2;
    session.type = AudioCore::Sink::StreamType::Out;
    session.ReleaseBuffer({4, 1});
    assert(mem.writes == 2);
    session.type = AudioCore::Sink::StreamType::In;
    session.handle = nullptr;
    session.ReleaseBuffer({4, 1});
    assert(mem.writes == 2);
}
"""
    with tempfile.TemporaryDirectory(prefix="ab-ns1-guest-buffer-") as directory:
        path = Path(directory)
        src = path / "guest_release.cpp"
        executable = path / "guest_release"
        src.write_text(test)
        subprocess.run([
            "clang++", "-std=c++20", "-O1", "-g",
            "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer", "-I", str(ROOT / "headless"),
            str(src), "-o", str(executable),
        ], check=True, cwd=ROOT, timeout=90)
        subprocess.run([str(executable)], check=True, cwd=ROOT, timeout=15,
                       env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"})
    print("AB_NS1_EXTRACTED_AUDIOIN_GUEST_RELEASE_ASAN_UBSAN_PASS",
          "odd,channel,oversize,guest-span,short-sink,zero,output-noop")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        print("AB_NS1_EXTRACTED_AUDIOIN_GUEST_RELEASE_FAIL", exc, file=sys.stderr)
        sys.exit(1)
