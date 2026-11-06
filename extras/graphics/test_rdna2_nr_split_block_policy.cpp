// SPDX-License-Identifier: MIT
#include "rdna2_nr_split_block_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr auto windows=40u;
    constexpr std::uint64_t fp8=40ull*64u*512u;
    constexpr SplitBlockCapacity caps{
        fp8,fp8,fp8,fp8,fp8,fp8,fp8,fp8,fp8,fp8*4u};
    const SplitBlockPlan p{windows,false};
    assert(CanSplitBlock(p,caps));
    // A ProjPool output cannot be omitted by treating it as a plain Proj.
    // Native 1080p ProjPool: width 60, height 33, windows 8x5.
    // The half-res side output is 32x20 (640 tokens), plus 1280 zero
    // tail tokens for the native default 1920-token FinalHead.
    auto pooled_caps=caps;
    pooled_caps.pooled=1920u*512u;
    const SplitBlockPlan pooled{windows,true,60u,33u,8u,5u,1920u};
    assert(CanSplitBlock(pooled,pooled_caps));
    // The last NRMODEL1 layer (FinalHead, 512->1024) can be linked,
    // provided distinct FP32 scratch and output buffers are allocated.
    pooled_caps.final_fp32=1920ull*1024u*4u;
    pooled_caps.final_fp8=1920ull*1024u;
    const SplitBlockPlan with_final{
        windows,true,60u,33u,8u,5u,1920u,1920u};
    assert(CanSplitBlock(with_final,pooled_caps));
    auto insufficient_final=pooled_caps;
    insufficient_final.final_fp8--;
    assert(!CanSplitBlock(with_final,insufficient_final));
    insufficient_final=pooled_caps;
    insufficient_final.final_fp32--;
    assert(!CanSplitBlock(with_final,insufficient_final));
    assert(!CanSplitBlock({
        windows,false,0u,0u,0u,0u,0u,1920u},pooled_caps));
    assert(!CanSplitBlock({
        windows,true,60u,33u,8u,5u,1920u,2560u},pooled_caps));
    pooled_caps.pooled=1920u*512u-1u;
    assert(!CanSplitBlock(pooled,pooled_caps));
    pooled_caps.pooled=1920u*512u;
    assert(!CanSplitBlock({windows,true,60u,33u,7u,5u,1920u},pooled_caps));
    assert(!CanSplitBlock({windows,true,60u,33u,8u,5u,639u},pooled_caps));
    assert(!CanSplitBlock({windows,true,60u,33u,8u,5u,0u},
                          {fp8,fp8,fp8,fp8,fp8,fp8,fp8,fp8,fp8,
                           fp8*4u,639u*512u}));

    // Attention shift -1/-1 lives on its own input and output tensors.
    // Without both GPU repacks the QKV/Proj descriptors would be wrong.
    auto shift_caps=caps;
    shift_caps.shifted_input=fp8;
    shift_caps.unshifted_context=fp8;
    SplitBlockPlan shifted{windows,false};
    shifted.window_grid_x=8u;shifted.window_grid_y=5u;
    shifted.attention_shift_x=-1;
    shifted.attention_shift_y=-1;
    assert(CanSplitBlock(shifted,shift_caps));
    auto missing=shift_caps;missing.shifted_input=fp8-1u;
    assert(!CanSplitBlock(shifted,missing));
    missing=shift_caps;missing.unshifted_context=fp8-1u;
    assert(!CanSplitBlock(shifted,missing));
    shifted.attention_shift_x=2;
    assert(!CanSplitBlock(shifted,shift_caps));
    shifted.attention_shift_x=1;
    assert(CanSplitBlock(shifted,shift_caps));
    shifted.window_grid_y=4u;
    assert(!CanSplitBlock(shifted,shift_caps));
    assert(!CanSplitBlock({windows,true},caps));
    assert(!CanSplitBlock({0u,false},caps));
    assert(!CanSplitBlock({1024u,false},caps));
    assert(CanSplitBlock({1u,false},{
        32768u,32768u,32768u,32768u,32768u,32768u,
        32768u,32768u,32768u,32768u*4u}));
    auto broken=caps;broken.input=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.ffwd=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.ffwd_projected=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.context_heads=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.context_tokens=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.projected=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.query=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.key=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.value=fp8-1u;
    assert(!CanSplitBlock(p,broken));
    broken=caps;broken.fp32_scratch=fp8*4u-1u;
    assert(!CanSplitBlock(p,broken));
}
