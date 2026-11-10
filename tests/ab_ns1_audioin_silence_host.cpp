// SPDX-License-Identifier: GPL-3.0-or-later
#include "headless/audio_in_silence.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <limits>
#include <stdexcept>

int main() {
    constexpr std::array<std::uint64_t, 7> sample_counts{
        0, 1, 2, 16, 128, 8192, 65536
    };
    for (const auto count : sample_counts) {
        const auto samples = Eden::MakeSilentAudioInSamples(count);
        assert(samples.size() == count);
        assert(std::all_of(samples.begin(), samples.end(),
                           [](std::int16_t sample) { return sample == 0; }));
    }

    bool rejected = false;
    try {
        (void)Eden::MakeSilentAudioInSamples(
            std::numeric_limits<std::uint64_t>::max());
    } catch (const std::length_error&) {
        rejected = true;
    }
    assert(rejected && "oversize sample request must be rejected before allocating");
}
