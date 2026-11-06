// SPDX-License-Identifier: MIT
// CPU reference for public MIT model's padded view / channel spill mapping.
#include <cassert>
#include <algorithm>
#include <cstdint>
#include <vector>
#include "rdna2_nr_upsample_view_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
static uint32_t at(uint32_t t,uint32_t c,uint32_t C){
    return ((t/16u)*(C/16u)+c/16u)*256u+(t%16u)*16u;
}
static void convert(std::vector<uint8_t>& mem,const UpsampleView& p){
    assert(CanUpsampleView(p,mem.size()));
    auto runs=p.channels/16u;
    for(uint32_t i=0;i<p.tokens*runs;++i){
        uint32_t t=i/runs,c=(i%runs)*16u;
        uint32_t tw=p.resized_width/4u;
        uint32_t x=(t/16u%tw)*4u+t%4u;
        uint32_t y=(t/16u/tw)*4u+(t%16u)/4u;
        uint32_t pos=(c/16u)*p.resized_width*p.resized_height+
            y*p.resized_width+x;
        uint32_t sc=(pos/(p.width*p.height))*16u;
        uint32_t pixel=pos%(p.width*p.height);
        uint32_t sx=pixel%p.width,sy=pixel/p.width;
        uint32_t st=((sy/4u)*(p.width/4u)+sx/4u)*16u+(sy%4u)*4u+sx%4u;
        auto dst=p.dst_base_bytes+at(t,c,p.channels);
        if(y<p.resized_height && sc<p.channels)
            std::copy_n(mem.begin()+p.src_base_bytes+at(st,sc,p.channels),
                        16,mem.begin()+dst);
        else std::fill_n(mem.begin()+dst,16,0u);
    }
}
int main(){
    // No padding: exact bitwise copy at every token/channel.
    UpsampleView p{0,2048,64,32,8,8,8,8};
    std::vector<uint8_t> mem(15000,0);
    for(uint32_t i=0;i<2048;++i)mem[i]=uint8_t((i*73u+31u)&255u);
    assert(CanUpsampleView(p,mem.size()));
    convert(mem,p);
    assert(std::equal(mem.begin(),mem.begin()+2048,mem.begin()+2048));
    // Padded grid: view crosses channel-plane boundaries; out of
    // range of all source channels produces zero.
    p={0,4096,144,32,8,8,12,12};
    assert(CanUpsampleView(p,mem.size()));
    convert(mem,p);
    assert(std::equal(mem.begin(),mem.begin()+16,mem.begin()+4096));
    auto invalid=p;
    invalid.width=7;assert(!CanUpsampleView(invalid,mem.size()));
    invalid=p;invalid.tokens=143;assert(!CanUpsampleView(invalid,mem.size()));
    invalid=p;invalid.dst_base_bytes=16;assert(!CanUpsampleView(invalid,mem.size()));
    invalid=p;invalid.channels=31;assert(!CanUpsampleView(invalid,mem.size()));
    invalid=p;invalid.resized_width=4;assert(!CanUpsampleView(invalid,mem.size()));
    invalid=p;invalid.src_base_bytes=1;assert(!CanUpsampleView(invalid,mem.size()));
    invalid=p;invalid.dst_base_bytes=UINT32_MAX-15u;
    assert(!CanUpsampleView(invalid,UINT64_MAX));
    return 0;
}
