// SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <limits>

namespace Eden::Graphics::NeuralRDNA2 {
struct TokenRepack {
    std::uint32_t src_base_bytes, dst_base_bytes;
    std::uint32_t width, height, channels;
    std::uint32_t inverse;
};
constexpr std::uint64_t kMaxTokenRepack = 256ull << 20;
[[nodiscard]] constexpr bool CanRepack(const TokenRepack& p, std::uint64_t arena_bytes) {
    if (!p.width || !p.height || !p.channels || p.inverse > 1) return false;
    if (p.width % 4u || p.height % 4u || p.channels % 16u) return false;
    if ((p.src_base_bytes & 15u) || (p.dst_base_bytes & 15u)) return false;
    const auto w=std::uint64_t(p.width), h=std::uint64_t(p.height);
    const auto c=std::uint64_t(p.channels);
    const auto tokens=w*h;
    const auto copy=tokens*c;
    if (copy > kMaxTokenRepack || !copy) return false;
    const auto src_end=std::uint64_t(p.src_base_bytes)+copy;
    const auto dst_end=std::uint64_t(p.dst_base_bytes)+copy;
    if (src_end>arena_bytes || dst_end>arena_bytes) return false;
    if (src_end>std::numeric_limits<std::uint32_t>::max() ||
        dst_end>std::numeric_limits<std::uint32_t>::max()) return false;
    // Both regions share one VkBuffer; no read/write overlap across invocations.
    if (p.src_base_bytes < dst_end && p.dst_base_bytes < src_end) return false;
    const auto invocations=tokens*(c/16u);
    return (invocations+63u)/64u <= 65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
