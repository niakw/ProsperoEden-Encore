// SPDX-License-Identifier: MIT
// Numerical unit tests for learned-model half scalars and Swin bias layout.
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_weight_decode.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    assert(NeuralHalfToFloat(0x3c00u)==1.0f);
    assert(NeuralHalfToFloat(0xbc00u)==-1.0f);
    assert(NeuralHalfToFloat(0x4000u)==2.0f);
    assert(NeuralHalfToFloat(0x0001u)==std::ldexp(1.0f,-24));
    assert(NeuralHalfToFloat(0x0400u)==std::ldexp(1.0f,-14));
    assert(NeuralHalfToFloat(0x7bffu)==65504.0f);
    assert(std::isinf(NeuralHalfToFloat(0x7c00u)));
    assert(std::isnan(NeuralHalfToFloat(0x7e00u)));
    std::vector<float> decoded;
    const std::vector<std::uint8_t> halfs{0x00,0x3c,0x00,0xc0};
    assert(NeuralDecodeF16(halfs,decoded));
    assert(decoded.size()==2u&&decoded[0]==1.0f&&decoded[1]==-2.0f);
    assert(!NeuralDecodeF16(std::vector<std::uint8_t>{0x00},decoded));
    assert(decoded.empty());
    assert(!NeuralDecodeF16(std::vector<std::uint8_t>{0x00,0x7c},decoded));
    assert(decoded.empty());

    std::vector<float> packed(8192u);
    for(std::size_t i=0;i<packed.size();++i)packed[i]=float(i);
    std::vector<float> bias;
    assert(NeuralDeswizzleBias64(packed,2u,bias));
    assert(bias.size()==8192u);
    for(std::uint32_t h=0;h<2u;++h)
        for(std::uint32_t i=0;i<64u;++i)
            for(std::uint32_t j=0;j<64u;++j){
                const auto lane=4u*((i%16u)%8u)+((j%16u)%8u)/2u;
                const auto sl=(j%2u)|(((i%16u)/8u)<<1u)|
                    (((j%16u)/8u)<<2u);
                const auto src=(4u*(i/16u)+(j/16u))*256u+lane*8u+sl;
                assert(bias[h*4096u+i*64u+j]==packed[h*4096u+src]);
            }
    std::sort(bias.begin(),bias.begin()+4096u);
    for(unsigned i=0;i<4096u;++i)assert(bias[i]==float(i));
    assert(!NeuralDeswizzleBias64(packed,3u,bias));
    assert(bias.empty());

    std::vector<float> residual(48u,0.f);
    for(unsigned i=0;i<32u;++i)residual[8u+i]=float(i+1u);
    std::vector<float> out;
    assert(NeuralResidualScale(residual,32u,false,out));
    assert(out.size()==32u&&out[0]==1.f&&out[31]==32.f);
    residual.assign(80u,3.f);
    for(unsigned i=0;i<80u;++i)residual[i]=float(i+1u);
    assert(NeuralResidualScale(residual,64u,false,out));
    assert(out.front()==1.f&&out.back()==64.f);
    assert(NeuralResidualScale(residual,64u,true,out));
    assert(out.front()==17.f&&out.back()==80.f);
    assert(!NeuralResidualScale(residual,256u,false,out));
    assert(out.empty());
}
