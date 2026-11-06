// SPDX-License-Identifier: MIT
// Validated arena access contract for the RDNA2 upsample-view permutation.
#pragma once
#include <cstdint>
#include <limits>

namespace Eden::Graphics::NeuralRDNA2 {
struct UpsampleView {
    std::uint32_t src_base_bytes,dst_base_bytes,tokens,channels;
    std::uint32_t width,height,resized_width,resized_height;
};
[[nodiscard]] constexpr bool CanUpsampleView(const UpsampleView& p,
                                              std::uint64_t arena_bytes) {
    if (!p.width || !p.height || !p.resized_width || !p.resized_height ||
        !p.channels || !p.tokens) return false;
    if (p.width%4u || p.height%4u ||
        p.resized_width%4u || p.resized_height%4u ||
        p.channels%16u) return false;
    if ((p.src_base_bytes&15u) || (p.dst_base_bytes&15u)) return false;
    // Protect the workgroup->token coordinate mapping. In the generic
    // upstream kernel tokens may be a subrange; this first port supports
    // a complete padded view only, keeping all source/dest bounds provable.
    const auto r=std::uint64_t(p.resized_width)*p.resized_height;
    if (p.tokens!=r || p.resized_width<p.width || p.resized_height<p.height)
        return false;
    const auto src=std::uint64_t(p.width)*p.height*p.channels;
    const auto dst=r*p.channels;
    constexpr std::uint64_t kMaxBytes=256ull<<20;
    if (src>kMaxBytes || dst>kMaxBytes) return false;
    const auto se=std::uint64_t(p.src_base_bytes)+src;
    const auto de=std::uint64_t(p.dst_base_bytes)+dst;
    if (se>arena_bytes || de>arena_bytes) return false;
    if (se>std::numeric_limits<std::uint32_t>::max() ||
        de>std::numeric_limits<std::uint32_t>::max()) return false;
    if (p.src_base_bytes<de && p.dst_base_bytes<se) return false;
    const auto invocations=r*(p.channels/16u);
    return (invocations+63u)/64u<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
