// SPDX-License-Identifier: MIT
// Verified CCSplitSwin16HQKVAttn layout: 1536x512 QKV, 16 heads,
// 16*64*64 FP16 attention bias, and 16 FP32 temperatures.
#include "video_core/renderer_vulkan/nr_rdna2_split_window_weight_loader.h"
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr std::size_t C=512u;
    std::vector<std::uint8_t> qkv(3u*C*C,0x38u);
    qkv[0]=0x00u; // +0 must re-quantize to -0
    qkv[512u*C]=0x40u; // K head 0, channel 0
    qkv[1024u*C]=0x48u; // V head 0, channel 0
    qkv[32u*C]=0x50u; // Q head 1, channel 0
    std::vector<std::uint8_t> ordered;
    assert(ReorderSplitWindowQkv(qkv,ordered));
    assert(ordered.size()==qkv.size());
    assert(ordered[0]==0x80u);
    assert(ordered[32u*C]==0x40u);
    assert(ordered[64u*C]==0x48u);
    assert(ordered[96u*C]==0x50u);
    assert(!ReorderSplitWindowQkv(
        std::span<const std::uint8_t>{qkv.data(),qkv.size()-1u},ordered));
    assert(ordered.empty());
    qkv[128u*C]=0x7fu;
    assert(!ReorderSplitWindowQkv(qkv,ordered));
    assert(ordered.empty());
    std::array<std::uint8_t,64> raw{};
    for(std::size_t head=0u;head<16u;++head){
        auto bits=std::bit_cast<std::uint32_t>(1.0f+head/16.f);
        for(unsigned j=0;j<4u;++j)
            raw[4u*head+j]=std::uint8_t(bits>>(8u*j));
    }
    std::array<float,16> temperatures{};
    assert(DecodeSplitWindowTemperatures(raw,temperatures));
    assert(temperatures[0]==1.f);
    assert(temperatures[15]==1.f+15.f/16.f);
    assert(!DecodeSplitWindowTemperatures(
        std::span<const std::uint8_t>{raw.data(),63u},temperatures));
    for(float x:temperatures)assert(x==0.f);
    // Reject invalid head temperature, regardless of the other 15 heads.
    raw[0]=0u;raw[1]=0u;raw[2]=0xc0u;raw[3]=0x7fu; // 0x7fc00000 NaN
    assert(!DecodeSplitWindowTemperatures(raw,temperatures));
    std::vector<float> deswizzled;
    std::vector<float> per_head_bias(16u*4096u);
    for(unsigned h=0u;h<16u;++h)
        for(unsigned i=0u;i<4096u;++i)
            per_head_bias[h*4096u+i]=float(h);
    assert(NeuralDeswizzleBias64(per_head_bias,16u,deswizzled));
    assert(deswizzled.size()==per_head_bias.size());
    for(unsigned h=0u;h<16u;++h)
        for(unsigned i=0u;i<4096u;++i)
            assert(deswizzled[h*4096u+i]==float(h));
}
