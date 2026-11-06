// SPDX-License-Identifier: MIT
// RDNA2 scalar neural decoder: 512-channel nearest 2x + residual + FP8.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct DecoderUpsample {
    std::uint32_t src_base_bytes, skip_base_bytes, dst_base_bytes, gain_base_bytes;
    std::uint32_t input_width, output_width, output_height;
};
struct DecoderStorage {
    std::uint64_t projected_bytes, activation_bytes, gain_bytes;
};
[[nodiscard]] constexpr bool CanDecoderUpsample(const DecoderUpsample& p,
                                                  const DecoderStorage& s) {
    if(!p.input_width || !p.output_width || !p.output_height) return false;
    if(p.input_width%4u || p.output_width%8u || p.output_height%8u) return false;
    if(std::uint64_t(p.input_width)*2u != p.output_width) return false;
    if((p.src_base_bytes|p.skip_base_bytes|p.dst_base_bytes|p.gain_base_bytes)&3u)
        return false;
    constexpr std::uint64_t kLimit=256ull<<20;
    constexpr std::uint64_t kChannels=512;
    const auto out=std::uint64_t(p.output_width)*p.output_height;
    const auto in=out/4u;
    const auto src_bytes=in*kChannels*2u; // FP16
    const auto act_bytes=out*kChannels; // E4M3FN
    const auto gain_bytes=kChannels*2u; // FP16
    if(src_bytes>kLimit || act_bytes>kLimit) return false;
    const auto src_end=std::uint64_t(p.src_base_bytes)+src_bytes;
    const auto skip_end=std::uint64_t(p.skip_base_bytes)+act_bytes;
    const auto dst_end=std::uint64_t(p.dst_base_bytes)+act_bytes;
    const auto gain_end=std::uint64_t(p.gain_base_bytes)+gain_bytes;
    if(src_end>s.projected_bytes || skip_end>s.activation_bytes ||
       dst_end>s.activation_bytes || gain_end>s.gain_bytes) return false;
    if(src_end>std::numeric_limits<std::uint32_t>::max() ||
       skip_end>std::numeric_limits<std::uint32_t>::max() ||
       dst_end>std::numeric_limits<std::uint32_t>::max() ||
       gain_end>std::numeric_limits<std::uint32_t>::max()) return false;
    // Source skip and destination are distinct spans of one arena. The
    // compute pass does not promise in-place update ordering.
    if(std::uint64_t(p.skip_base_bytes)<dst_end &&
       std::uint64_t(p.dst_base_bytes)<skip_end) return false;
    return (out+63u)/64u<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
