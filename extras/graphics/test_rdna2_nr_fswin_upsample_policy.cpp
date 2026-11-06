// SPDX-License-Identifier: MIT
#include <array>
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
                const auto low=(std::uint64_t(W/2u)?W/2u:1u)*
                    (H/2u?H/2u:1u)*2u*C;
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
    // Exact U-Net native shapes for both 152-step and 76-step plans.
    // The first levels have odd dimensions: never read an absent row.
    for(const auto [W,H,C] : {
        std::array<std::uint32_t,3>{120u,67u,256u},
        {240u,135u,128u},
        {480u,270u,64u},
        {960u,540u,32u}}) {
        const FSwinUpsample p{W,H,(W+7u)/8u,(H+7u)/8u,
                             C,0,0,0,0,0};
        const std::uint64_t low=std::uint64_t(W/2u)* (H/2u)*2u*C;
        const std::uint64_t high=std::uint64_t(W)*H*C;
        const std::uint64_t weight=std::uint64_t(2u)*C*C;
        assert(CanFSwinUpsample(
            p,{low,high,weight,4u*C,high}));
        assert(!CanFSwinUpsample(
            p,{low-1u,high,weight,4u*C,high}));
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
