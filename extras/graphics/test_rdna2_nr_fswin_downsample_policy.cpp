// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <limits>
#include "rdna2_nr_fswin_downsample_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u})
        for(std::uint32_t W:{8u,32u,540u})
            for(std::uint32_t H:{8u,17u,960u}){
                FSwinDownsample p{
                    W,H,(W+7u)/8u,(H+7u)/8u,C,0,-1,0,0,0};
                const auto input=std::uint64_t(p.windows_x)*
                    p.windows_y*64u*C;
                const auto weights=std::uint64_t(2u)*C*C;
                const auto output=(std::uint64_t(W+1u)/2u)*
                    ((H+1u)/2u)*2u*C;
                const FSwinDownsampleStorage s{input,weights,output};
                assert(CanFSwinDownsample(p,s));
                assert(FSwinDownsampleGridX(p)==C/8u);
                assert(!CanFSwinDownsample(
                    p,{input-1u,weights,output}));
                assert(!CanFSwinDownsample(
                    p,{input,weights-1u,output}));
                assert(!CanFSwinDownsample(
                    p,{input,weights,output-1u}));
                p.shift_y=-2;
                assert(!CanFSwinDownsample(p,s));
                p.shift_y=-1;
                p.windows_x++;
                assert(!CanFSwinDownsample(p,s));
            }
    const FSwinDownsampleStorage unlimited{
        UINT64_MAX,UINT64_MAX,UINT64_MAX};
    FSwinDownsample bad{1920,1080,240,135,256,0,-1,0,0,0};
    assert(!CanFSwinDownsample(bad,unlimited));
    bad={8,8,1,1,32,0,0,1,0,0};
    assert(!CanFSwinDownsample(bad,unlimited));
    bad={8,8,1,1,32,0,0,UINT32_MAX-3u,0,0};
    assert(!CanFSwinDownsample(bad,unlimited));
}
