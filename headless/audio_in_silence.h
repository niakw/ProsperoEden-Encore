// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Silent capture for the native PS5 AudioIn adapter.
// The guest AudioIn path copies exactly the requested PCM byte count.
// Returning an empty vector for a nonzero request is not safe.
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace Eden {

// A single guest capture request must not allocate arbitrary host RAM.
// 2 MiB of PCM16 holds over 21 seconds of mono audio at 48 kHz.
inline constexpr std::uint64_t kMaxSilentAudioInSamples = 1ull << 20;
inline constexpr std::uint64_t kMaxSilentAudioInBytes =
    kMaxSilentAudioInSamples * sizeof(std::int16_t);

// Checked before entering the original AudioIn device session's raw guest
// copy. Reject fractional PCM16 frames and unbounded capture requests.
// The device-session owner separately validates the guest address range.
inline constexpr bool IsValidAudioInBufferShape(std::uint64_t bytes,
                                                 std::uint32_t channels) noexcept {
    return (channels == 1 || channels == 2 || channels == 6) &&
           bytes <= kMaxSilentAudioInBytes &&
           bytes % (std::uint64_t{channels} * sizeof(std::int16_t)) == 0;
}

inline std::vector<std::int16_t> MakeSilentAudioInSamples(std::uint64_t count) {
    if (count > kMaxSilentAudioInSamples ||
        count > static_cast<std::uint64_t>(std::vector<std::int16_t>{}.max_size()))
        throw std::length_error("AudioIn sample count exceeds bounded capture capacity");
    return std::vector<std::int16_t>(static_cast<std::size_t>(count), 0);
}

} // namespace Eden
