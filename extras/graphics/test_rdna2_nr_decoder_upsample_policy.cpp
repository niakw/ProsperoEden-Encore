// SPDX-License-Identifier: MIT
// Decoder upsample bounds, 512-channel tiled address, and FP8 reference values.
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
#include "rdna2_nr_decoder_upsample_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
static std::uint32_t token(std::uint32_t x,std::uint32_t y,std::uint32_t w){
    return ((y/4)*((w+3)/4)+x/4)*16+(y%4)*4+x%4;
}
static std::uint32_t at(std::uint32_t t,std::uint32_t c){
    return ((t/16)*32+c/16)*256+(t%16)*16+c%16;
}
static std::uint32_t quant(float v) {
    unsigned sign=(std::signbit(v)?128u:0u);
    if(std::isnan(v))return sign|127u;
    float a=std::fmin(std::fabs(v),448.f);
    if(a<0.015625f) {
        auto q=static_cast<unsigned>(std::nearbyint(a*512.f));
        return sign|(q>=8u?8u:q);
    }
    int e=static_cast<int>(std::floor(std::log2(a)));
    auto m=static_cast<unsigned>(std::nearbyint((a/std::exp2(float(e))-1.f)*8.f));
    if(m==8u){++e;m=0;}
    unsigned ex=static_cast<unsigned>(e+7);
    if(ex>15u || (ex==15u && m>6u))return sign|126u;
    return sign|(ex<<3u)|m;
}
int main(){
    DecoderUpsample p{0,32768,65536,0,4,8,8};
    DecoderStorage s{16384,98304,131072,1024};
    assert(CanDecoderUpsample(p,s));
    assert(!CanDecoderUpsample(p,{16383,98304,131072,1024}));
    assert(!CanDecoderUpsample(p,{16384,65535,131072,1024}));
    assert(!CanDecoderUpsample(p,{16384,98304,98303,1024}));
    assert(!CanDecoderUpsample(p,{16384,98304,131072,1023}));
    p.dst_base_bytes=131072;
    assert(!CanDecoderUpsample(p,s));
    p={0,32768,65536,0,4,8,8};
    p.output_width=12;
    assert(!CanDecoderUpsample(p,s));
    p={0,32768,65536,0,4,8,8};
    p.input_width=3;
    assert(!CanDecoderUpsample(p,s));
    p={0,32768,65536,0,4,8,8};
    p.src_base_bytes=2;
    assert(!CanDecoderUpsample(p,s));
    p={0,32768,65536,0,4,8,8};
    p.gain_base_bytes=UINT32_MAX-3;
    assert(!CanDecoderUpsample(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,1024,2048,2048};
    assert(!CanDecoderUpsample(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    // Native 1080p decoder: upstream PushDecoderUps uses
    // IW=prev.H=33, OW=s.H=33, OH=s.W=60 (NOT OW=2*IW).
    // Both Original b39 and Compact b19 use this same shape.
    constexpr DecoderUpsample native{0u,0u,0u,0u,
                                     33u,33u,60u};
    constexpr std::uint64_t native_source=1152ull*512u*2u;
    constexpr std::uint64_t native_tile=2160ull*512u;
    static_assert(DecoderOutputTileTokens(native)==2160u);
    static_assert(DecoderInputTileTokens(native)==1152u);
    static_assert(CanDecoderUpsample(native,{
        native_source,native_tile,native_tile,1024u}));
    assert(CanDecoderUpsample(native,{
        native_source,native_tile,native_tile,1024u}));
    assert(!CanDecoderUpsample(native,{
        native_source-1u,native_tile,native_tile,1024u}));
    assert(!CanDecoderUpsample(native,{
        native_source,native_tile-1u,native_tile,1024u}));
    assert(!CanDecoderUpsample(native,{
        native_source,native_tile,native_tile-1u,1024u}));
    assert(!CanDecoderUpsample(
        {0u,0u,0u,0u,16u,33u,60u},
        {native_source,native_tile,native_tile,1024u}));
    // Exhaustively check that every live raster pixel occupies one unique
    // padded 4x4 token and its nearest source token is inside the budget.
    std::uint32_t live=0u,padded=0u;
    for(std::uint32_t t=0u;t<2160u;++t) {
        const auto tile=t/16u,local=t%16u;
        const auto x=(tile%9u)*4u+local%4u;
        const auto y=(tile/9u)*4u+local/4u;
        if(x>=33u||y>=60u){++padded;continue;}
        assert(token(x,y,33u)==t);
        assert(token(x/2u,y/2u,33u)<1152u);
        ++live;
    }
    assert(live==33u*60u&&padded==2160u-33u*60u);
    assert(token(32u,59u,33u)==2156u);
    // Four output pixels map to one 2x source pixel, never cross a 4x4 tile.
    assert(token(0,0,8)==0u);
    assert(token(1,0,8)==1u);
    assert(token(4,0,8)==16u);
    assert(token(0,4,8)==32u);
    assert(token(0,0,4)==0u);
    assert(token(1/2,1/2,4)==token(0,0,4));
    assert(at(0,0)==0u);
    assert(at(0,4)==4u);
    assert(at(0,16)==256u);
    assert(at(1,0)==16u);
    // E4M3FN nearest-even and saturation reference: zeros, normals,
    // subnormals, negative values and the largest finite number.
    assert(quant(0.f)==0x00u);
    assert(quant(-0.f)==0x80u);
    assert(quant(1.f)==0x38u);
    assert(quant(0.5f)==0x30u);
    assert(quant(-2.f)==0xc0u);
    assert(quant(448.f)==0x7eu);
    assert(quant(500.f)==0x7eu);
    assert(quant(1.f/512.f)==0x01u);
    assert(quant(1.f/1024.f)==0x00u); // tie to even
    assert(quant(3.f/1024.f)==0x02u); // tie to even
}
