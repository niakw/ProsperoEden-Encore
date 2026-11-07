// SPDX-License-Identifier: MIT
// Native Original & Compact decoder projection: 33x60, 2160 input tiles,
// 1980 matrix rows, 512 FP16 output channels. Two safely sequenced batches.
#include "rdna2_nr_decoder_projection_policy.h"
#include <cassert>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    static_assert(DecoderTileTokens(33u,60u)==2160u);
    static_assert(DecoderTileTokens(4u,8u)==32u);
    constexpr DecoderProjectionCapacity native{
        2160ull*1024u,512ull*1024u,1024ull*512u*4u,
        1980ull*512u*2u};
    DecoderProjectionBatches plan{};
    assert(BuildDecoderProjectionBatches(33u,60u,native,plan));
    assert(ValidDecoderProjectionBatches(plan));
    assert(plan.count==2u&&plan.pixels==1980u);
    assert(plan.tokens==2160u);
    assert(plan.slices[0].projection.tokens==1024u);
    assert(plan.slices[1].projection.tokens==956u);
    assert(plan.slices[1].projection.a_base_bytes==1024u*1024u);
    assert(plan.slices[1].convert.output_offset_halfwords==1024u*512u);
    assert(plan.slices[1].convert.elements==956u*512u);
    assert(CanDecoderFp32ToFp16(plan.slices[1].convert,
                               plan.slices[1].conversion_storage));
    auto broken=native;broken.tiled_input--;
    assert(!BuildDecoderProjectionBatches(33u,60u,broken,plan));
    broken=native;broken.weights--;
    assert(!BuildDecoderProjectionBatches(33u,60u,broken,plan));
    broken=native;broken.fp32_scratch=511u*4u;
    assert(!BuildDecoderProjectionBatches(33u,60u,broken,plan));
    broken=native;broken.fp16_projected--;
    assert(!BuildDecoderProjectionBatches(33u,60u,broken,plan));
    assert(!BuildDecoderProjectionBatches(0u,60u,native,plan));
    assert(!BuildDecoderProjectionBatches(33u,4097u,native,plan));
    assert(!CanDecoderFp32ToFp16({512u,0u,1u},{2048u,2048u}));
    assert(!CanDecoderFp32ToFp16({513u,0u,0u},{4096u,4096u}));
    assert(!CanDecoderFp32ToFp16({512u,0u,0u},{2047u,2048u}));
    assert(!CanDecoderFp32ToFp16({512u,0u,0u},{2048u,1023u}));
    assert(BuildDecoderProjectionBatches(33u,60u,native,plan));
    plan.slices[1].projection.a_base_bytes=0u;
    assert(!ValidDecoderProjectionBatches(plan));
    assert(BuildDecoderProjectionBatches(33u,60u,native,plan));
    plan.slices[1].convert.output_offset_halfwords=0u;
    assert(!ValidDecoderProjectionBatches(plan));
    // Earlier legacy test raster 4x8 needs no 33x60 special branch.
    constexpr DecoderProjectionCapacity legacy{
        32ull*1024u,512ull*1024u,32ull*512u*4u,
        32ull*512u*2u};
    assert(BuildDecoderProjectionBatches(4u,8u,legacy,plan));
    assert(ValidDecoderProjectionBatches(plan));
}
