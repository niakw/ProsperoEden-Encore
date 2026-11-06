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
