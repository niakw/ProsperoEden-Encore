// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "rdna2_nr_fswin_level_link_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u}){
        const std::uint32_t w=C==32u?540u:C==64u?270u:135u;
        const std::uint32_t h=C==32u?960u:C==64u?480u:240u;
        const FSwinLevelLink p{
            w,h,C,2u*C,{(w+7u)/8u,(h+7u)/8u,0,-1},
            {(w/2u+7u)/8u,(h/2u+7u)/8u,0,0}};
        const auto bytes=std::uint64_t(w/2u)*(h/2u)*2u*C;
        const auto target=std::uint64_t(p.destination_grid.windows_x)*
            p.destination_grid.windows_y*64u*2u*C;
        assert(CanFSwinLevelLink(p,bytes,target));
        assert(!CanFSwinLevelLink(p,bytes-1u,target));
        assert(!CanFSwinLevelLink(p,bytes,target-1u));
        auto bad=p;bad.destination_channels=C;
        assert(!CanFSwinLevelLink(bad,bytes,target));
        bad=p;bad.destination_grid.shift_x=-1;
        assert(!CanFSwinLevelLink(bad,bytes,target));
        bad=p;bad.destination_grid.windows_y++;
        assert(!CanFSwinLevelLink(bad,bytes,target));
        bad=p;bad.source_grid.windows_x++;
        assert(!CanFSwinLevelLink(bad,bytes,target));
        bad=p;bad.source_grid.shift_y=2;
        assert(!CanFSwinLevelLink(bad,bytes,target));
    }
    // W=135 is odd: exact native 135x240 -> 67x120.
    {
        const FSwinLevelLink p{
            135u,240u,128u,256u,
            {17u,30u,0,-1},{9u,15u,0,0}};
        const std::uint64_t exact=67ull*120u*256u;
        const std::uint64_t padded=9ull*15u*64u*256u;
        assert(CanFSwinLevelLink(p,exact,padded));
        assert(!CanFSwinLevelLink(p,exact-1u,padded));
    }
    // 256->512 is a Split-Swin transition, NOT a same-family FSwin link.
    const FSwinLevelLink split{120u,67u,256u,512u,
                              {15u,9u,0,-1},{8u,5u,0,0}};
    assert(!CanFSwinLevelLink(split,UINT64_MAX,UINT64_MAX));
    const FSwinLevelLink huge{16384u,16384u,32u,64u,
                             {2048u,2048u,0,0},{1024u,1024u,0,0}};
    assert(!CanFSwinLevelLink(huge,UINT64_MAX,UINT64_MAX));
}
