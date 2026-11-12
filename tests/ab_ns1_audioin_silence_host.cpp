// SPDX-License-Identifier: GPL-3.0-or-later
#include "headless/audio_in_silence.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <vector>
#include <limits>
#include <stdexcept>

int main() {
    constexpr std::array<std::uint64_t, 8> sample_counts{
        0, 1, 2, 16, 128, 8192, 65536, Eden::kMaxSilentAudioInSamples
    };
    for (const auto count : sample_counts) {
        const auto samples = Eden::MakeSilentAudioInSamples(count);
        assert(samples.size() == count);
        assert(std::all_of(samples.begin(), samples.end(),
                           [](std::int16_t sample) { return sample == 0; }));
        // DeviceSession's actual fast path copies buffer.size bytes. Exercise
        // that copy boundary under ASan/UBSan for every VALID even-size request.
        const auto bytes = static_cast<std::size_t>(count * sizeof(std::int16_t));
        std::vector<std::uint8_t> guest(bytes + 2, 0xa5);
        if (bytes != 0) {
            std::memcpy(guest.data() + 1, samples.data(), bytes);
        }
        assert(guest.front() == 0xa5 && guest.back() == 0xa5);
        assert(std::all_of(guest.begin() + 1, guest.end() - 1,
                           [](std::uint8_t byte) { return byte == 0; }));
    }

    bool rejected = false;
    try {
        (void)Eden::MakeSilentAudioInSamples(
            std::numeric_limits<std::uint64_t>::max());
    } catch (const std::length_error&) {
        rejected = true;
    }
    assert(rejected && "oversize sample request must be rejected before allocating");
    rejected = false;
    try {
        (void)Eden::MakeSilentAudioInSamples(Eden::kMaxSilentAudioInSamples + 1);
    } catch (const std::length_error&) {
        rejected = true;
    }
    assert(rejected && "untrusted AudioIn requests must be bounded to 2 MiB");
    for (const std::uint32_t channels : {1u, 2u, 6u}) {
        const std::uint64_t frame_bytes = channels * sizeof(std::int16_t);
        const std::uint64_t max_good =
            (Eden::kMaxSilentAudioInBytes / frame_bytes) * frame_bytes;
        assert(Eden::IsValidAudioInBufferShape(0, channels));
        assert(Eden::IsValidAudioInBufferShape(frame_bytes, channels));
        assert(Eden::IsValidAudioInBufferShape(max_good, channels));
        assert(!Eden::IsValidAudioInBufferShape(frame_bytes - 1, channels));
        assert(!Eden::IsValidAudioInBufferShape(max_good + frame_bytes, channels));
        assert(!Eden::IsValidAudioInBufferShape(
            std::numeric_limits<std::uint64_t>::max(), channels));
    }
    assert(!Eden::IsValidAudioInBufferShape(2, 0));
    assert(!Eden::IsValidAudioInBufferShape(2, 3));
    assert(!Eden::IsValidAudioInBufferShape(2, 7));
    assert(!Eden::IsValidAudioInBufferShape(1, 1));
}
