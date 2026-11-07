// SPDX-License-Identifier: MIT
// Exhaustive independent CPU mapping for native 512-channel 8x8-window
// -> 4x4-tile/16x16-channel-packed decoder skip, including partial borders.
#include "rdna2_nr_split_decoder_skip_repack_policy.h"
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <utility>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(std::uint32_t W,std::uint32_t H){
    const std::uint32_t wx=(W+7u)/8u,wy=(H+7u)/8u;
    const SplitDecoderSkipRepack p{W,H,wx,wy,512u};
    const auto input_bytes=SplitSkipInputTokens(p)*512u;
    const auto output_bytes=SplitSkipOutputTokens(p)*512u;
    assert(CanSplitDecoderSkipRepack(p,{input_bytes,output_bytes}));
    std::vector<std::uint32_t> source(input_bytes/4u);
    for(std::size_t i=0;i<source.size();++i)
        source[i]=std::uint32_t(31337u*i+101u);
    std::vector<std::uint32_t> destination(output_bytes/4u,0xdeadc0deu);
    std::vector<bool> seen(SplitSkipInputTokens(p),false);
    std::uint32_t live=0u,zeroed=0u;
    const auto cols=(W+3u)/4u;
    for(std::uint32_t t=0u;t<SplitSkipOutputTokens(p);++t){
        const auto tile=t/16u,slot=t%16u;
        const auto x=(tile%cols)*4u+slot%4u;
        const auto y=(tile/cols)*4u+slot/4u;
        const bool valid=x<W&&y<H;
        std::uint32_t source_token=0u;
        if(valid){
            const auto window=(y/8u)*wx+x/8u;
            const auto quadrant=((y%8u)/4u)*2u+(x%8u)/4u;
            source_token=window*64u+quadrant*16u+
                         (y%4u)*4u+x%4u;
            assert(source_token<seen.size());
            assert(!seen[source_token]);
            seen[source_token]=true;
            ++live;
        }else ++zeroed;
        for(std::uint32_t cw=0u;cw<128u;++cw){
            const auto dst=((t/16u)*32u+cw/4u)*64u+
                           (t%16u)*4u+cw%4u;
            assert(dst<destination.size());
            destination[dst]=valid?source[source_token*128u+cw]:0u;
        }
    }
    assert(live==W*H);
    assert(zeroed==SplitSkipOutputTokens(p)-live);
    for(std::uint32_t t=0u;t<SplitSkipOutputTokens(p);++t){
        const auto tile=t/16u,slot=t%16u;
        const auto x=(tile%cols)*4u+slot%4u;
        const auto y=(tile/cols)*4u+slot/4u;
        const auto dst=((t/16u)*32u)*64u+(t%16u)*4u;
        if(x>=W||y>=H)assert(destination[dst]==0u);
        else assert(destination[dst]!=0xdeadc0deu);
    }
    assert(!CanSplitDecoderSkipRepack(p,{
        input_bytes-1u,output_bytes}));
    assert(!CanSplitDecoderSkipRepack(p,{
        input_bytes,output_bytes-1u}));
}
int main(){
    for(const auto dims:{
        std::pair{33u,60u},std::pair{8u,8u},
        std::pair{7u,13u},std::pair{31u,17u},
        std::pair{4u,4u},std::pair{1u,1u}})
        Check(dims.first,dims.second);
    constexpr SplitDecoderSkipRepack native{33u,60u,5u,8u,512u};
    static_assert(SplitSkipInputTokens(native)==2560u);
    static_assert(SplitSkipOutputTokens(native)==2160u);
    static_assert(CanSplitDecoderSkipRepack(native,{
        2560ull*512u,2160ull*512u}));
    assert(!CanSplitDecoderSkipRepack(
        {33u,60u,8u,5u,512u},{
            2560ull*512u,2160ull*512u}));
    assert(!CanSplitDecoderSkipRepack(
        {33u,60u,5u,8u,256u},{
            2560ull*512u,2160ull*512u}));
    assert(!CanSplitDecoderSkipRepack(
        {0u,60u,0u,8u,512u},{UINT64_MAX,UINT64_MAX}));
    assert(!CanSplitDecoderSkipRepack(
        {4096u,4096u,512u,512u,512u},
        {UINT64_MAX,UINT64_MAX}));
    // Native border examples: x=32,y=59 is in window #39, slot 12,
    // but the decoder reads it as tile #134, slot 12.
    const std::uint32_t src=(7u*5u+4u)*64u+12u;
    const std::uint32_t dst=(14u*9u+8u)*16u+12u;
    assert(src==2508u&&dst==2156u);
}
