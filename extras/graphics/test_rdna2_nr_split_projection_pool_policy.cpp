// SPDX-License-Identifier: MIT
// Reference for 4x4 tiles per 8x8 window, half-resolution tiled output.
// Does not assume a native capture or certify any Vulkan execution.
#include "rdna2_nr_split_projection_pool_policy.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static std::uint32_t SourceToken(
    std::uint32_t x,std::uint32_t y,std::uint32_t windows_x){
    const std::uint32_t wx=x/8u,wy=y/8u;
    const std::uint32_t quadrant=2u*((y%8u)/4u)+(x%8u)/4u;
    const std::uint32_t slot=4u*(y%4u)+x%4u;
    return ((wy*windows_x+wx)*64u+quadrant*16u+slot);
}
static std::uint32_t DestinationToken(
    std::uint32_t x,std::uint32_t y,std::uint32_t padded_width){
    return ((y/4u)*(padded_width/4u)+x/4u)*16u+
           4u*(y%4u)+(x%4u);
}
int main(){
    constexpr SplitProjectionPool p{60u,33u,8u,5u,0u,0u,0u,0u,768u};
    constexpr auto input=40ull*64u*512u;
    assert(SplitPoolWidth(p)==32u&&SplitPoolHeight(p)==20u);
    assert(SplitPoolLiveTokens(p)==640u);
    assert(SplitPoolOutputTokens(p)==768u);
    assert(CanSplitProjectionPool(p,{input*4u,input,1024u,768ull*512u}));
    assert(!CanSplitProjectionPool(p,{input*4u-1u,input,1024u,768ull*512u}));
    assert(!CanSplitProjectionPool(p,{input*4u,input-1u,1024u,768ull*512u}));
    assert(!CanSplitProjectionPool(p,{input*4u,input,1023u,768ull*512u}));
    assert(!CanSplitProjectionPool(p,{input*4u,input,1024u,768ull*512u-1u}));
    auto bad=p;bad.output_tokens=639u;
    assert(!CanSplitProjectionPool(bad,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=p;bad.windows_x=7u;
    assert(!CanSplitProjectionPool(bad,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=p;bad.width=65u;
    assert(!CanSplitProjectionPool(bad,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=p;bad.pool_base_bytes=1u;
    assert(!CanSplitProjectionPool(bad,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=p;bad.gain_base_halfwords=UINT32_MAX;
    assert(!CanSplitProjectionPool(bad,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    // Every padded source pixel has one distinct window/quadrant/slot.
    std::vector<std::uint8_t> hits(40u*64u,0u);
    for(std::uint32_t y=0u;y<40u;++y)
      for(std::uint32_t x=0u;x<64u;++x)
        ++hits[SourceToken(x,y,8u)];
    for(auto v:hits)assert(v==1u);
    // One unique destination per valid / padded half-res pixel.
    hits.assign(32u*20u,0u);
    for(std::uint32_t y=0u;y<20u;++y)
      for(std::uint32_t x=0u;x<32u;++x)
        ++hits[DestinationToken(x,y,32u)];
    for(auto v:hits)assert(v==1u);
    // 2x2 pooling with 4x4 tile source order, before quantizing.
    std::vector<float> values(40u*64u,0.f),pooled(32u*20u,0.f);
    for(std::uint32_t y=0u;y<33u;++y)
      for(std::uint32_t x=0u;x<60u;++x)
        values[SourceToken(x,y,8u)]=float(y*60u+x);
    for(std::uint32_t y=0u;y<17u;++y)
      for(std::uint32_t x=0u;x<30u;++x){
        float s=0.f;
        for(std::uint32_t dy=0u;dy<2u;++dy)
          for(std::uint32_t dx=0u;dx<2u;++dx){
            const auto sx=2u*x+dx,sy=2u*y+dy;
            if(sx<60u&&sy<33u)
                s+=values[SourceToken(sx,sy,8u)];
          }
        pooled[DestinationToken(x,y,32u)]=s*0.25f;
      }
    assert(pooled[DestinationToken(0u,0u,32u)]==30.5f);
    assert(pooled[DestinationToken(29u,16u,32u)]==
           (1978.f+1979.f)*0.25f);
    assert(pooled[DestinationToken(30u,0u,32u)]==0.f);
    assert(pooled[DestinationToken(0u,17u,32u)]==0.f);
}
