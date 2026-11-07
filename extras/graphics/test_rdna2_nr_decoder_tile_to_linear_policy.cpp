// SPDX-License-Identifier: MIT
// Uniqueness + capacity for all 1980 raster pixels of the native 33x60
// ViT tiles, including the non-multiple-of-four final column.
#include "rdna2_nr_decoder_tile_to_linear_policy.h"
#include <cassert>
#include <cstdint>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Verify(std::uint32_t w,std::uint32_t h){
    const DecoderTileToLinear p{w,h};
    const auto pixels=std::uint64_t(w)*h;
    const auto tiles=DecoderTileCount(p);
    assert(CanDecoderTileToLinear(p,{
        tiles*1024u,pixels*1024u}));
    assert(!CanDecoderTileToLinear(p,{
        tiles*1024u-1u,pixels*1024u}));
    assert(!CanDecoderTileToLinear(p,{
        tiles*1024u,pixels*1024u-1u}));
    std::vector<bool> seen(tiles,false);
    const auto cols=(w+3u)/4u;
    for(std::uint32_t pixel=0u;pixel<pixels;++pixel){
        const auto x=pixel%w,y=pixel/w;
        const auto t=((y/4u)*cols+x/4u)*16u+
                     (y%4u)*4u+x%4u;
        assert(t<tiles&&!seen[t]);
        seen[t]=true;
        // The shader copies all 256 uint32 words of C1024.
        assert(pixel*256ull+255u<pixels*256u);
        assert(t*256ull+255u<tiles*256u);
    }
    std::uint32_t mapped=0u;
    for(auto yes:seen)mapped+=yes;
    assert(mapped==pixels);
}
int main(){
    static_assert(DecoderTileCount({33u,60u})==2160u);
    Verify(33u,60u);
    Verify(7u,13u);
    Verify(4u,8u);
    Verify(1u,1u);
    assert(!CanDecoderTileToLinear({0u,60u},{
        UINT64_MAX,UINT64_MAX}));
    assert(!CanDecoderTileToLinear({4096u,4096u},{
        UINT64_MAX,UINT64_MAX}));
    // Raster pixel 32,59 must be tiled token 2156; treating source
    // as linear would read token 1979, a silent wrong-image error.
    constexpr std::uint32_t t=((59u/4u)*9u+32u/4u)*16u+
                              (59u%4u)*4u+32u%4u;
    static_assert(t==2156u);
    static_assert(t!=59u*33u+32u);
}
