#!/usr/bin/env python3
"""Compile the *actual extracted* SilentAudioInputStream with a minimal fake sink.

This is host timing/stop/resize evidence, NOT a real Core::System, guest
DeviceSession, Vulkan, compiled PS5 binary, or microphone device test.
No files in the repository/vendor are written or modified.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "headless/audio.cpp"
START = "class SilentAudioInputStream final : public SinkStream {"
END = "\nAudioStream::AudioStream"

def main() -> None:
    source = SRC.read_text()
    if source.count(START) != 1 or source.count(END) != 1:
        raise AssertionError("native silent input class signature drift")
    body = source.split(START, 1)[1].split(END, 1)[0]
    cls = START + body
    if "ProcessAudioIn(silent_frames, frames_per_tick)" not in cls:
        raise AssertionError("silent input worker no longer advances actual SinkStream counters")
    if "wait_for(" not in cls or "worker.request_stop()" not in cls:
        raise AssertionError("capture pacing or controlled worker retirement missing")
    fixture = r"""
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <mutex>
#include <span>
#include <stdexcept>
#include <stop_token>
#include <thread>
#include <vector>
#include "audio_in_silence.h"

using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s16 = std::int16_t;
using namespace std::chrono_literals;
namespace Core { struct System {}; }
namespace AudioCore::Sink {
enum class StreamType { Render, Out, In };
struct SinkBuffer {};
class SinkStream {
public:
    explicit SinkStream(Core::System&, StreamType) {}
    virtual ~SinkStream() = default;
    virtual void Start(bool = false) {}
    virtual void Stop() {}
    virtual void Finalize() {}
    virtual void AppendBuffer(SinkBuffer&, std::span<s16>) {}
    virtual std::vector<s16> ReleaseBuffer(u64) { return {}; }
    void SetSystemChannels(u32 c) { channels = c; }
    u32 GetSystemChannels() const { return channels; }
    u64 GetExpectedPlayedSampleCount() const { return sample_count.load(); }
    void ProcessAudioIn(std::span<const s16> data, std::size_t frames) {
        assert(frames == 480);
        assert(data.size() == frames * 2);
        assert(std::all_of(data.begin(), data.end(), [](s16 v) { return v == 0; }));
        if (!paused.load()) sample_count.fetch_add(frames);
    }
protected:
    std::atomic<bool> paused{true};
private:
    u32 channels{2};
    std::atomic<u64> sample_count{0};
};
}
namespace Eden {
using namespace AudioCore::Sink;
""" + cls + r"""
}
int main() {
    Core::System system;
    for (u32 channels : {1u, 2u, 6u}) {
        Eden::SilentAudioInputStream stream(system, channels);
        assert(stream.GetSystemChannels() == channels);
        assert(stream.GetExpectedPlayedSampleCount() == 0);
        assert(stream.ReleaseBuffer(0).empty());
        auto silent = stream.ReleaseBuffer(256);
        assert(silent.size() == 256);
        assert(std::all_of(silent.begin(), silent.end(), [](s16 v){return v == 0;}));
        stream.Start();
        const auto deadline = std::chrono::steady_clock::now() + 800ms;
        while (stream.GetExpectedPlayedSampleCount() < 3 * 480 &&
               std::chrono::steady_clock::now() < deadline) {
            std::this_thread::sleep_for(5ms);
        }
        const u64 progressed = stream.GetExpectedPlayedSampleCount();
        assert(progressed >= 1440 && "capture timeline did not advance");
        stream.Stop();
        const u64 paused = stream.GetExpectedPlayedSampleCount();
        std::this_thread::sleep_for(35ms);
        assert(stream.GetExpectedPlayedSampleCount() == paused &&
               "capture clock advanced after Stop");
        stream.Start(true);
        const auto resume_deadline = std::chrono::steady_clock::now() + 800ms;
        while (stream.GetExpectedPlayedSampleCount() < paused + 480 &&
               std::chrono::steady_clock::now() < resume_deadline) {
            std::this_thread::sleep_for(5ms);
        }
        assert(stream.GetExpectedPlayedSampleCount() >= paused + 480 &&
               "capture clock did not resume");
        stream.Finalize();
        const u64 finished = stream.GetExpectedPlayedSampleCount();
        std::this_thread::sleep_for(35ms);
        assert(stream.GetExpectedPlayedSampleCount() == finished &&
               "capture worker survived Finalize");
        stream.Finalize();
    }
}
"""
    with tempfile.TemporaryDirectory(prefix="ab-ns1-audioin-") as folder:
        sourcefile = Path(folder) / "capture.cpp"
        program = Path(folder) / "capture"
        sourcefile.write_text(fixture)
        command = [
            "clang++", "-std=c++20", "-O1", "-g", "-Wall", "-Wextra",
            "-Werror", "-pthread", "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer", "-I", str(ROOT / "headless"),
            str(sourcefile), "-o", str(program),
        ]
        subprocess.run(command, cwd=ROOT, check=True, timeout=120)
        subprocess.run([str(program)], cwd=ROOT, check=True, timeout=15,
                       env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"})
    print("AB_NS1_ACTUAL_CAPTURE_CLASS_EXTRACTED_HOST_ASAN_UBSAN_PASS",
          "channels=1,2,6", "stop_resume_and_join=1",
          "guest_DeviceSession_untested=1")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AssertionError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as e:
        print("AB_NS1_ACTUAL_CAPTURE_CLASS_EXTRACTED_HOST_FAIL", str(e), file=sys.stderr)
        sys.exit(1)
