// SPDX-License-Identifier: MIT
// Host-side validation for the RDNA2 neural noise-field pass.
// Output: 2 uint32 per padded pixel, containing 3 FP16 noise features and 0.
#pragma once
#include <cstdint>
#include <limits>

namespace Eden::Graphics::NeuralRDNA2 {
struct NoiseField {
    std::uint32_t base_words, width, height, seed;
    float gain;
};
[[nodiscard]] constexpr bool CanNoiseField(const NoiseField& p,
                                            std::uint64_t arena_bytes) {
    // Network working dimensions are padded to whole 8x8 blocks.
    if (!p.width || !p.height || p.width % 8u || p.height % 8u)
        return false;
    if (!(p.gain >= -64.f && p.gain <= 64.f)) return false; // reject NaN/Inf
    constexpr std::uint64_t kMaxOutputBytes = 256ull << 20;
    const std::uint64_t pixels = std::uint64_t(p.width)*p.height;
    const std::uint64_t words = pixels*2ull;
    if (words*4ull > kMaxOutputBytes) return false;
    const std::uint64_t end_words = std::uint64_t(p.base_words)+words;
    // Shader address arithmetic is 32-bit, prohibit offset wrap.
    if (end_words > std::numeric_limits<std::uint32_t>::max()) return false;
    if (end_words*4ull > arena_bytes) return false;
    return p.width/8u <= 65535u && p.height/8u <= 65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
