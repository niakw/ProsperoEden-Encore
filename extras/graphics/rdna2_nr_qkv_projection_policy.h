// SPDX-License-Identifier: MIT
// RDNA2 QKV 512->(3*32*heads) projection: strict row-major buffer ABI.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct QkvProjection {
    std::uint32_t a_base_bytes,w_base_bytes,scale_base_floats;
    std::uint32_t q_base_bytes,k_base_bytes,v_base_bytes;
    std::uint32_t windows,heads;
};
struct QkvStorage {
    std::uint64_t activation_bytes,weight_bytes,scale_bytes;
    std::uint64_t q_bytes,k_bytes,v_bytes;
};
[[nodiscard]] constexpr bool CanQkvProjection(
    const QkvProjection& p,const QkvStorage& s){
    if(!p.windows || p.windows>65535u ||
        (p.heads!=1u && p.heads!=2u && p.heads!=4u &&
         p.heads!=8u && p.heads!=16u))return false;
    if((p.a_base_bytes|p.w_base_bytes|p.q_base_bytes|
        p.k_base_bytes|p.v_base_bytes)&3u)return false;
    constexpr std::uint64_t kMaxBytes=256ull<<20;
    const auto a=std::uint64_t(p.windows)*64u*512u;
    const auto w=std::uint64_t(p.heads)*96u*512u;
    const auto o=std::uint64_t(p.windows)*p.heads*64u*32u;
    if(a>kMaxBytes||w>kMaxBytes||o>kMaxBytes)return false;
    const auto ae=std::uint64_t(p.a_base_bytes)+a;
    const auto we=std::uint64_t(p.w_base_bytes)+w;
    const auto qe=std::uint64_t(p.q_base_bytes)+o;
    const auto ke=std::uint64_t(p.k_base_bytes)+o;
    const auto ve=std::uint64_t(p.v_base_bytes)+o;
    const auto se=std::uint64_t(p.scale_base_floats)+p.heads;
    if(ae>std::numeric_limits<std::uint32_t>::max()||
       we>std::numeric_limits<std::uint32_t>::max()||
       qe>std::numeric_limits<std::uint32_t>::max()||
       ke>std::numeric_limits<std::uint32_t>::max()||
       ve>std::numeric_limits<std::uint32_t>::max()||
       se>std::numeric_limits<std::uint32_t>::max())return false;
    if(ae>s.activation_bytes||we>s.weight_bytes||
       qe>s.q_bytes||ke>s.k_bytes||ve>s.v_bytes||
       se*4u>s.scale_bytes)return false;
    // Caller must verify distinct nonaliasing descriptor ranges, finite
    // scales and finite/valid E4M3FN model tensors before recording.
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
