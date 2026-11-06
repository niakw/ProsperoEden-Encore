// SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinWindowRepack {
    std::uint32_t windows_x,windows_y,channels;
    std::int32_t src_shift_x,src_shift_y,dst_shift_x,dst_shift_y;
};
struct FSwinWindowRepackStorage {
    std::uint64_t input_bytes,output_bytes;
};
[[nodiscard]] constexpr bool CanFSwinWindowRepack(
    const FSwinWindowRepack& p,const FSwinWindowRepackStorage& s) noexcept {
    const auto valid=[](std::int32_t v){return v>=-1&&v<=1;};
    if(!p.windows_x||!p.windows_y||
       std::uint64_t(p.windows_x)*p.windows_y>65535u||
       (p.channels!=32u&&p.channels!=64u&&
        p.channels!=128u&&p.channels!=256u&&
        p.channels!=512u)||
       !valid(p.src_shift_x)||!valid(p.src_shift_y)||
       !valid(p.dst_shift_x)||!valid(p.dst_shift_y))return false;
    const auto bytes=std::uint64_t(p.windows_x)*p.windows_y*64u*p.channels;
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    return bytes<=max&&bytes<=(256ull<<20)&&
           bytes<=s.input_bytes&&bytes<=s.output_bytes;
}
[[nodiscard]] constexpr std::uint32_t FSwinWindowRepackGridX(
    const FSwinWindowRepack& p) noexcept {
    return p.channels/4u;
}
} // namespace Eden::Graphics::NeuralRDNA2
