// SPDX-License-Identifier: MIT
// GPU FP32 projection output -> packed E4M3FN features; Vulkan 1.1.
// Exactly four independently rounded FP32 source elements per uint word.
#pragma once
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct FloatQuantize {
    std::uint32_t elements{};
    std::uint32_t input_offset_floats{};
    std::uint32_t output_offset_bytes{};
    std::uint32_t flags{}; // must be zero
};
struct FloatQuantizeStorage {
    std::uint64_t input_bytes{},output_bytes{};
};
[[nodiscard]] constexpr bool CanFloatQuantize(
    const FloatQuantize& p,const FloatQuantizeStorage& s) noexcept {
    constexpr std::uint64_t kMaxStorage=256ull<<20;
    constexpr std::uint64_t kMaxGroups=65535u;
    constexpr std::uint64_t kInvocations=64u;
    constexpr std::uint64_t kElementsPerInvocation=4u;
    if(p.elements==0u||(p.elements&3u)!=0u||p.flags!=0u||
       (p.output_offset_bytes&3u)!=0u||s.input_bytes==0u||
       s.output_bytes==0u)return false;
    const std::uint64_t input_end=
        (std::uint64_t(p.input_offset_floats)+p.elements)*4u;
    const std::uint64_t output_end=
        std::uint64_t(p.output_offset_bytes)+p.elements;
    const std::uint64_t words=p.elements/4u;
    const std::uint64_t groups=(words+kInvocations-1u)/kInvocations;
    return groups>0u&&groups<=kMaxGroups&&
           input_end<=kMaxStorage&&output_end<=kMaxStorage&&
           input_end<=s.input_bytes&&output_end<=s.output_bytes;
}
[[nodiscard]] constexpr std::uint32_t FloatQuantizeGroups(
    const FloatQuantize& p) noexcept {
    return (p.elements/4u+63u)/64u;
}
} // namespace Eden::Graphics::NeuralRDNA2
