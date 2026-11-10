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

inline std::vector<std::int16_t> MakeSilentAudioInSamples(std::uint64_t count) {
    const auto limit = std::vector<std::int16_t>{}.max_size();
    if (count > static_cast<std::uint64_t>(limit))
        throw std::length_error("AudioIn sample count exceeds vector capacity");
    return std::vector<std::int16_t>(static_cast<std::size_t>(count), 0);
}

} // namespace Eden
