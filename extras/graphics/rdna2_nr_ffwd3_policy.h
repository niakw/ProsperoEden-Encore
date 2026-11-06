// SPDX-License-Identifier: MIT
// RDNA2 grouped 3-projection FFWD: 8 groups, 64/256/64 hidden channels.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct FFWD3 {
    std::uint32_t x_base_bytes,w1_base_bytes,w2_base_bytes;
    std::uint32_t w3_base_bytes,out_base_bytes,tokens;
};
struct FFWD3Storage {
    std::uint64_t input_bytes,w1_bytes,w2_bytes,w3_bytes,output_bytes;
};
[[nodiscard]] constexpr bool CanFFWD3(const FFWD3& p,const FFWD3Storage& s) {
    if(!p.tokens||p.tokens>65535u) return false;
    if((p.x_base_bytes|p.w1_base_bytes|p.w2_base_bytes|
        p.w3_base_bytes|p.out_base_bytes)&3u)return false;
    constexpr std::uint64_t kMaxBytes=256ull<<20;
    const auto bytes=std::uint64_t(p.tokens)*512u;
    constexpr std::uint64_t w1_bytes=8u*64u*512u;
    constexpr std::uint64_t w2_bytes=8u*256u*64u;
    constexpr std::uint64_t w3_bytes=8u*64u*256u;
    if(bytes>kMaxBytes) return false;
    const auto end_x=std::uint64_t(p.x_base_bytes)+bytes;
    const auto end_1=std::uint64_t(p.w1_base_bytes)+w1_bytes;
    const auto end_2=std::uint64_t(p.w2_base_bytes)+w2_bytes;
    const auto end_3=std::uint64_t(p.w3_base_bytes)+w3_bytes;
    const auto end_out=std::uint64_t(p.out_base_bytes)+bytes;
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    if(end_x>max||end_1>max||end_2>max||end_3>max||end_out>max)return false;
    if(end_x>s.input_bytes||end_1>s.w1_bytes||end_2>s.w2_bytes||
       end_3>s.w3_bytes||end_out>s.output_bytes)return false;
    // All five bindings must refer to live nonaliasing storage ranges.
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
