// SPDX-License-Identifier: MIT
// FSwin QKV 64-token projected FP8, supports 32/64/128/256 channels.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinQkv {
    std::uint32_t a_base_bytes,w_base_bytes,scale_base_floats;
    std::uint32_t q_base_bytes,k_base_bytes,v_base_bytes;
    std::uint32_t windows,channels,heads;
};
struct FSwinQkvStorage {
    std::uint64_t activation_bytes,weight_bytes,scale_bytes;
    std::uint64_t q_bytes,k_bytes,v_bytes;
};
[[nodiscard]] constexpr bool CanFSwinQkv(
    const FSwinQkv& p,const FSwinQkvStorage& s) noexcept {
    if(!p.windows || p.windows>65535u ||
       (p.channels!=32u && p.channels!=64u &&
        p.channels!=128u && p.channels!=256u) ||
       p.heads!=p.channels/32u)return false;
    if((p.a_base_bytes|p.w_base_bytes|p.q_base_bytes|
        p.k_base_bytes|p.v_base_bytes)&3u)return false;
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    const auto C=std::uint64_t(p.channels);
    const auto a=std::uint64_t(p.windows)*64u*C;
    const auto w=std::uint64_t(p.heads)*96u*C;
    const auto out=std::uint64_t(p.windows)*p.heads*64u*32u;
    if(a>(256ull<<20)||w>(256ull<<20)||out>(256ull<<20))return false;
    const auto ae=std::uint64_t(p.a_base_bytes)+a;
    const auto we=std::uint64_t(p.w_base_bytes)+w;
    const auto qe=std::uint64_t(p.q_base_bytes)+out;
    const auto ke=std::uint64_t(p.k_base_bytes)+out;
    const auto ve=std::uint64_t(p.v_base_bytes)+out;
    const auto se=std::uint64_t(p.scale_base_floats)+p.heads;
    if(ae>max||we>max||qe>max||ke>max||ve>max||se>max)return false;
    return ae<=s.activation_bytes&&we<=s.weight_bytes&&
        qe<=s.q_bytes&&ke<=s.k_bytes&&ve<=s.v_bytes&&
        se*4u<=s.scale_bytes;
    // Caller verifies distinct, nonaliasing descriptors and finite weights.
}
} // namespace Eden::Graphics::NeuralRDNA2
