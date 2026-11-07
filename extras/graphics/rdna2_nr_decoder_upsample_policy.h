// SPDX-License-Identifier: MIT
// RDNA2 native neural decoder: 512-channel FP16->FP8 nearest + skip/gain.
// Native W/H are often 33x60 (partial 4x4 tiles), NOT 8-padded sizes.
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
[[nodiscard]] constexpr std::uint64_t DecoderOutputTileTokens(
    const DecoderUpsample& p) noexcept {
    return ((std::uint64_t(p.output_width)+3u)/4u)*
           ((std::uint64_t(p.output_height)+3u)/4u)*16u;
}
[[nodiscard]] constexpr std::uint64_t DecoderInputTileTokens(
    const DecoderUpsample& p) noexcept {
    // The decoder reads nearest x/2,y/2 in a 4x4 tile-major FP16 source.
    // The source row stride is input_width; only ceil(output_height/2)
    // source rows are sampled, irrespective of the higher-level plan.
    const auto sampled_height=(std::uint64_t(p.output_height)+1u)/2u;
    return ((std::uint64_t(p.input_width)+3u)/4u)*
           ((sampled_height+3u)/4u)*16u;
}
[[nodiscard]] constexpr bool CanDecoderUpsample(
    const DecoderUpsample& p,const DecoderStorage& s) noexcept {
    if(!p.input_width||!p.output_width||!p.output_height||
       p.input_width>4096u||p.output_width>4096u||
       p.output_height>4096u)return false;
    // Older padded shapes can use a 2x wide output; the native
    // FinalHead/ViT plan at 1080p uses IW=OW=33 and OH=60.
    if(p.output_width!=p.input_width&&
       std::uint64_t(p.input_width)*2u!=p.output_width)return false;
    if((p.src_base_bytes|p.skip_base_bytes|
        p.dst_base_bytes|p.gain_base_bytes)&3u)return false;
    constexpr std::uint64_t kLimit=256ull<<20;
    constexpr std::uint64_t kChannels=512u;
    const auto source_tiles=DecoderInputTileTokens(p);
    const auto output_tiles=DecoderOutputTileTokens(p);
    if(!source_tiles||!output_tiles)return false;
    const auto src_bytes=source_tiles*kChannels*2u; // FP16
    const auto act_bytes=output_tiles*kChannels; // E4M3FN, incl. border
    const auto gain_bytes=kChannels*2u; // FP16
    if(src_bytes>kLimit||act_bytes>kLimit)return false;
    const auto src_end=std::uint64_t(p.src_base_bytes)+src_bytes;
    const auto skip_end=std::uint64_t(p.skip_base_bytes)+act_bytes;
    const auto dst_end=std::uint64_t(p.dst_base_bytes)+act_bytes;
    const auto gain_end=std::uint64_t(p.gain_base_bytes)+gain_bytes;
    if(src_end>s.projected_bytes||skip_end>s.activation_bytes||
       dst_end>s.activation_bytes||gain_end>s.gain_bytes)return false;
    if(src_end>kLimit||skip_end>kLimit||dst_end>kLimit||
       gain_end>kLimit)return false;
    // Source skip and destination are two disjoint spans in the
    // same activation arena. Do not permit a racy in-place GPU update.
    if(std::uint64_t(p.skip_base_bytes)<dst_end &&
       std::uint64_t(p.dst_base_bytes)<skip_end)return false;
    return (output_tiles+63u)/64u<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
