// SPDX-License-Identifier: MIT
// Reference retile from source 2x2 tiles/window to shifted window layout.
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <vector>
#include "rdna2_nr_fswin_window_repack_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
static std::vector<std::uint32_t> Repack(
    const FSwinWindowRepack& p,const std::vector<std::uint32_t>& source){
    const std::uint32_t wp=p.channels/4u;
    const std::size_t total=std::size_t(p.windows_x)*p.windows_y*64u*wp;
    assert(source.size()==total);
    std::vector<std::uint32_t> out(total,0u);
    for(std::size_t idx=0;idx<total;++idx){
        const auto cw=std::uint32_t(idx%wp);
        const auto t=std::uint32_t((idx/wp)%64u);
        const auto win=std::uint32_t(idx/(wp*64u));
        const auto wx=win%p.windows_x,wy=win/p.windows_x;
        const auto quadrant=t/16u,slot=t%16u;
        const int tx=2*int(wx)+p.dst_shift_x+int(quadrant%2u);
        const int ty=2*int(wy)+p.dst_shift_y+int(quadrant/2u);
        const int sx=tx-p.src_shift_x,sy=ty-p.src_shift_y;
        if(tx<0||ty<0||tx>=2*int(p.windows_x)||ty>=2*int(p.windows_y)||
           sx<0||sy<0||sx>=2*int(p.windows_x)||sy>=2*int(p.windows_y))
            continue;
        const auto swx=std::uint32_t(sx/2),swy=std::uint32_t(sy/2);
        const auto sq=std::uint32_t((sy%2)*2+sx%2);
        const auto src_index=(
            (swy*p.windows_x+swx)*64u+sq*16u+slot)*wp+cw;
        assert(src_index<total);
        out[idx]=source[src_index];
    }
    return out;
}
int main(){
    for(std::uint32_t W:{1u,2u,4u})
      for(std::uint32_t H:{1u,2u,4u})
       for(std::uint32_t C:{32u,64u,128u,256u}){
        const auto size=std::size_t(W)*H*64u*C;
        FSwinWindowRepack p{W,H,C,0,0,0,0};
        assert(CanFSwinWindowRepack(p,{size,size}));
        assert(FSwinWindowRepackGridX(p)==C/4u);
        std::vector<std::uint32_t> original(size/4u);
        for(std::size_t i=0;i<original.size();++i)
            original[i]=std::uint32_t(i+1u);
        assert(Repack(p,original)==original);
        p.dst_shift_x=1;p.dst_shift_y=1;
        auto shifted=Repack(p,original);
        assert(shifted.size()==original.size());
        p.src_shift_x=1;p.src_shift_y=1;
        p.dst_shift_x=0;p.dst_shift_y=0;
        auto restored=Repack(p,shifted);
        // The out-of-grid boundary is lost by design; all interior 4x4 tiles
        // survive the permutation exactly.
        for(std::uint32_t y=1;y<2u*H;++y)
         for(std::uint32_t x=1;x<2u*W;++x){
            std::uint32_t w=(y/2u)*W+x/2u;
            std::uint32_t q=(y%2u)*2u+x%2u;
            for(std::uint32_t slot=0;slot<16u;++slot)
             for(std::uint32_t c=0;c<C/4u;++c){
                const auto off=((w*64u+q*16u+slot)*C/4u)+c;
                assert(restored[off]==original[off]);
            }
         }
        p={W,H,C,2,0,0,0};
        assert(!CanFSwinWindowRepack(p,{size,size}));
        p={W,H,C,0,0,0,0};
        assert(!CanFSwinWindowRepack(p,{size-1,size}));
       }
    FSwinWindowRepack bad{65536,1,64,0,0,0,0};
    assert(!CanFSwinWindowRepack(bad,{UINT64_MAX,UINT64_MAX}));
    FSwinWindowRepack fullhd{120,68,32,0,0,-1,-1};
    const auto fullhd_bytes=std::uint64_t{120}*68u*64u*32u;
    assert(CanFSwinWindowRepack(fullhd,{fullhd_bytes,fullhd_bytes}));
    assert(FSwinWindowRepackGridX(fullhd)==8u);
}
