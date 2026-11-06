// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <limits>
#include "rdna2_nr_fswin_upsample_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u})
        for(std::uint32_t W:{8u,31u,540u})
            for(std::uint32_t H:{8u,17u,960u}){
                FSwinUpsample p{W,H,(W+7u)/8u,(H+7u)/8u,
                               C,0,0,0,0,0};
                const auto low=(std::uint64_t(W+1u)/2u)*
                    ((H+1u)/2u)*2u*C;
                const auto high=std::uint64_t(W)*H*C;
                const auto weight=std::uint64_t(2u)*C*C;
                const FSwinUpsampleStorage s{low,high,weight,4u*C,high};
                assert(CanFSwinUpsample(p,s));
                assert(FSwinUpsampleGridX(p)==C/4u);
                assert(!CanFSwinUpsample(
                    p,{low-1u,high,weight,4u*C,high}));
                assert(!CanFSwinUpsample(
                    p,{low,high-1u,weight,4u*C,high}));
                assert(!CanFSwinUpsample(
                    p,{low,high,weight-1u,4u*C,high}));
                assert(!CanFSwinUpsample(
                    p,{low,high,weight,4u*C-1u,high}));
                assert(!CanFSwinUpsample(
                    p,{low,high,weight,4u*C,high-1u}));
                auto bad=p;bad.windows_y++;assert(!CanFSwinUpsample(bad,s));
                bad=p;bad.low_base_bytes=1u;
                assert(!CanFSwinUpsample(bad,s));
            }
    constexpr FSwinUpsampleStorage ample{
        UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX};
    FSwinUpsample invalid{1920,1080,240,135,256,0,0,0,0,0};
    assert(!CanFSwinUpsample(invalid,ample));
    invalid={8,8,1,1,16,0,0,0,0,0};
    assert(!CanFSwinUpsample(invalid,ample));
    invalid={8,8,1,1,32,0,0,UINT32_MAX-3u,0,0};
    assert(!CanFSwinUpsample(invalid,ample));
}
