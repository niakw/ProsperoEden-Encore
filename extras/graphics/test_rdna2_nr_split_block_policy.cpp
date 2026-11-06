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
    // The half-res side output is 32x20 (640 tokens), plus 128 zero
    // tail tokens for the FinalHead that requests 768.
    auto pooled_caps=caps;
    pooled_caps.pooled=768u*512u;
    const SplitBlockPlan pooled{windows,true,60u,33u,8u,5u,768u};
    assert(CanSplitBlock(pooled,pooled_caps));
    pooled_caps.pooled=768u*512u-1u;
    assert(!CanSplitBlock(pooled,pooled_caps));
    pooled_caps.pooled=768u*512u;
    assert(!CanSplitBlock({windows,true,60u,33u,7u,5u,768u},pooled_caps));
    assert(!CanSplitBlock({windows,true,60u,33u,8u,5u,639u},pooled_caps));
    assert(!CanSplitBlock({windows,true,60u,33u,8u,5u,0u},
                          {fp8,fp8,fp8,fp8,fp8,fp8,fp8,fp8,fp8,
                           fp8*4u,639u*512u}));

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
