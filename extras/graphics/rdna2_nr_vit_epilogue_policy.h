// SPDX-License-Identifier: MIT
// Shared portable Vulkan FP32->E4M3FN activation and half residual policies.
// Width 512 supports Split-Swin residual projections, 1024/4096 ViT.
// No opaque model state, output buffers must be caller-owned/nonaliasing.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct VitActivation {
    std::uint32_t tokens{},channels{},input_offset_floats{},output_offset_bytes{};
};
struct VitResidual {
    std::uint32_t tokens{},channels{},input_offset_floats{};
    std::uint32_t output_offset_bytes{},residual_offset_bytes{};
    std::uint32_t gain_offset_halfwords{};
};
struct VitEpilogueStorage {
    std::uint64_t source_bytes{},residual_bytes{},gain_bytes{},output_bytes{};
};
[[nodiscard]] constexpr bool VitValidExtent(
    std::uint32_t tokens,std::uint32_t channels) noexcept {
    return tokens>0u&&tokens<=4096u&&
       (channels==512u||channels==1024u||channels==4096u);
}
[[nodiscard]] constexpr std::uint32_t VitEpilogueGroups(
    std::uint32_t tokens,std::uint32_t channels) noexcept {
    return static_cast<std::uint32_t>(
        (std::uint64_t(tokens)*channels+511u)/512u);
}
[[nodiscard]] constexpr bool CanVitActivation(
    const VitActivation& p,const VitEpilogueStorage& s) noexcept {
    if(!VitValidExtent(p.tokens,p.channels)||
       (p.output_offset_bytes&3u)!=0u)return false;
    const std::uint64_t n=std::uint64_t(p.tokens)*p.channels;
    const std::uint64_t source_end=
        (std::uint64_t(p.input_offset_floats)+n)*4u;
    const std::uint64_t output_end=
        std::uint64_t(p.output_offset_bytes)+n;
    constexpr std::uint64_t max=256ull<<20;
    if(source_end>max||output_end>max||
       source_end>std::numeric_limits<std::uint32_t>::max()||
       output_end>std::numeric_limits<std::uint32_t>::max())
        return false;
    return source_end<=s.source_bytes&&output_end<=s.output_bytes&&
           VitEpilogueGroups(p.tokens,p.channels)<=65535u;
}
[[nodiscard]] constexpr bool CanVitResidual(
    const VitResidual& p,const VitEpilogueStorage& s) noexcept {
    if(!VitValidExtent(p.tokens,p.channels)||
       ((p.output_offset_bytes|p.residual_offset_bytes)&3u)!=0u)
        return false;
    const std::uint64_t n=std::uint64_t(p.tokens)*p.channels;
    const std::uint64_t source_end=
        (std::uint64_t(p.input_offset_floats)+n)*4u;
    const std::uint64_t residual_end=
        std::uint64_t(p.residual_offset_bytes)+n;
    const std::uint64_t output_end=
        std::uint64_t(p.output_offset_bytes)+n;
    const std::uint64_t gain_halfwords=
        std::uint64_t(p.gain_offset_halfwords)+p.channels;
    const std::uint64_t gains_end=((gain_halfwords+1u)/2u)*4u;
    constexpr std::uint64_t max=256ull<<20;
    constexpr auto u32=std::numeric_limits<std::uint32_t>::max();
    if(source_end>max||residual_end>max||output_end>max||
       gains_end>max||source_end>u32||residual_end>u32||
       output_end>u32||gain_halfwords>u32)return false;
    return source_end<=s.source_bytes&&
           residual_end<=s.residual_bytes&&
           gains_end<=s.gain_bytes&&
           output_end<=s.output_bytes&&
           VitEpilogueGroups(p.tokens,p.channels)<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
