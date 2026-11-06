// SPDX-License-Identifier: MIT
// Exhaustively check the 256-value upstream E4M3FN requantizer mapping.
#include <array>
#include <cassert>
#include <cstdint>
#include "video_core/renderer_vulkan/nr_rdna2_e4m3_requantize.h"
using namespace Eden::Graphics::NeuralRDNA2;
static_assert(RequantizedE4M3(0x00u)==0x80u);
static_assert(RequantizedE4M3(0xffu)==0x7fu);
static_assert(RequantizedE4M3(0x38u)==0x38u);
int main(){
    std::array<std::uint8_t,256> codes{};
    for(unsigned i=0u;i<256u;++i)
        codes[i]=static_cast<std::uint8_t>(i);
    RequantizeE4M3(codes);
    for(unsigned i=0u;i<256u;++i)
        assert(codes[i]==(i==0u?0x80u:i==255u?0x7fu:i));
}
