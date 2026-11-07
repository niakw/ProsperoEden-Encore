// SPDX-License-Identifier: MIT
// Native Original/Compact decoder learned GEMM: 33x60 live pixels,
 // ViT 2160 padded FP8 tokens -> linear 1980 GEMM rows -> 2160 FP16 tiles.
#include "rdna2_nr_decoder_projection_policy.h"
#include <cassert>
#include <cstdint>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    static_assert(DecoderTileTokens(33u,60u)==2160u);
    static_assert(DecoderTileTokens(4u,8u)==32u);
    constexpr DecoderProjectionCapacity native{
        1980ull*1024u,512ull*1024u,1024ull*512u*4u,
        2160ull*512u*2u};
    DecoderProjectionBatches plan{};
    assert(BuildDecoderProjectionBatches(33u,60u,native,plan));
    assert(ValidDecoderProjectionBatches(plan));
    assert(plan.count==2u&&plan.pixels==1980u&&plan.tokens==2160u);
    assert(plan.slices[0].projection.tokens==1024u);
    assert(plan.slices[1].projection.tokens==956u);
    assert(plan.slices[1].projection.a_base_bytes==1024u*1024u);
    assert(plan.slices[1].convert.output_offset_halfwords==1024u*512u);
    assert(plan.slices[1].convert.elements==956u*512u);
    assert(plan.slices[1].convert.width==33u&&plan.slices[1].convert.height==60u);
    assert(CanDecoderFp32ToFp16(plan.slices[1].convert,
                               plan.slices[1].conversion_storage));
    auto invalid=native;invalid.linear_input--;
    assert(!BuildDecoderProjectionBatches(33u,60u,invalid,plan));
    invalid=native;invalid.weights--;
    assert(!BuildDecoderProjectionBatches(33u,60u,invalid,plan));
    invalid=native;invalid.fp32_scratch=511u*4u;
    assert(!BuildDecoderProjectionBatches(33u,60u,invalid,plan));
    invalid=native;invalid.fp16_projected--;
    assert(!BuildDecoderProjectionBatches(33u,60u,invalid,plan));
    assert(!BuildDecoderProjectionBatches(0u,60u,native,plan));
    assert(!BuildDecoderProjectionBatches(33u,4097u,native,plan));
    constexpr DecoderFp32ToFp16Storage cap{
        1024ull*512u*4u,2160ull*512u*2u};
    assert(!CanDecoderFp32ToFp16({512u,0u,1u,33u,60u},cap));
    assert(!CanDecoderFp32ToFp16({513u,0u,0u,33u,60u},cap));
    assert(!CanDecoderFp32ToFp16({512u,0u,0u,33u,60u},
                                 {2047u,cap.output_bytes}));
    assert(!CanDecoderFp32ToFp16({512u,0u,0u,33u,60u},
                                 {cap.input_bytes,cap.output_bytes-1u}));
    assert(!CanDecoderFp32ToFp16(
        {512u,0u,1980u*512u,33u,60u},cap));
    assert(BuildDecoderProjectionBatches(33u,60u,native,plan));
    plan.slices[1].projection.a_base_bytes=0u;
    assert(!ValidDecoderProjectionBatches(plan));
    assert(BuildDecoderProjectionBatches(33u,60u,native,plan));
    plan.slices[1].convert.output_offset_halfwords=0u;
    assert(!ValidDecoderProjectionBatches(plan));
    assert(BuildDecoderProjectionBatches(33u,60u,native,plan));
    plan.slices[1].convert.width=60u;
    assert(!ValidDecoderProjectionBatches(plan));
    // Every valid 33x60 raster pixel is written to one unique padded
    // 4x4 tile (plus its 256 independent FP16 pairs).
    std::vector<bool> occupied(2160u,false);
    for(std::uint32_t pixel=0u;pixel<1980u;++pixel){
        const auto x=pixel%33u,y=pixel/33u;
        const auto t=((y/4u)*9u+x/4u)*16u+
                     (y%4u)*4u+x%4u;
        assert(t<occupied.size()&&!occupied[t]);
        occupied[t]=true;
        assert(t*256ull+255u<cap.output_bytes/4u);
    }
    std::uint32_t live=0;
    for(bool filled:occupied)live+=filled;
    assert(live==1980u);
    constexpr DecoderProjectionCapacity legacy{
        32ull*1024u,512ull*1024u,32ull*512u*4u,
        32ull*512u*2u};
    assert(BuildDecoderProjectionBatches(4u,8u,legacy,plan));
    assert(ValidDecoderProjectionBatches(plan));
}
