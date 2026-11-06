// SPDX-License-Identifier: MIT
// Host verification of a true RDNA2 Split-Swin QKV -> attention handoff.
#include "video_core/renderer_vulkan/nr_rdna2_split_window_link_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;

int main() {
    constexpr std::uint32_t windows=64u, heads=8u;
    constexpr std::uint64_t activation=std::uint64_t(windows)*64u*512u;
    constexpr std::uint64_t weights=std::uint64_t(heads)*96u*512u;
    constexpr std::uint64_t tensor=std::uint64_t(windows)*heads*64u*32u;
    constexpr std::uint64_t bias=std::uint64_t(heads)*64u*64u*4u;
    const SplitWindowLink shape{
        {0u,0u,0u,0u,0u,0u,windows,heads},
        {0u,0u,0u,0u,0u,windows,heads}};
    const SplitWindowLinkStorage capacity{
        {activation,weights,heads*4u,tensor,tensor,tensor},
        {tensor,tensor,tensor,tensor,bias}};
    assert(CanSplitWindowLink(shape,capacity));

    // Tests all three producer/consumer offsets independently.
    auto bad=shape;
    bad.attention.q_base_bytes=4u;
    assert(!CanSplitWindowLink(bad,capacity));
    bad=shape;bad.attention.k_base_bytes=4u;
    assert(!CanSplitWindowLink(bad,capacity));
    bad=shape;bad.attention.v_base_bytes=4u;
    assert(!CanSplitWindowLink(bad,capacity));
    bad=shape;bad.attention.windows=windows/2u;
    assert(!CanSplitWindowLink(bad,capacity));
    bad=shape;bad.attention.heads=heads/2u;
    assert(!CanSplitWindowLink(bad,capacity));

    auto smaller=capacity;
    smaller.qkv.q_bytes=tensor-4u;
    assert(!CanSplitWindowLink(shape,smaller));
    smaller=capacity;smaller.attention.context_bytes=0u;
    assert(!CanSplitWindowLink(shape,smaller));
    smaller=capacity;smaller.attention.bias_bytes=bias-1u;
    assert(!CanSplitWindowLink(shape,smaller));
    smaller=capacity;smaller.attention.v_bytes=tensor+4u;
    assert(!CanSplitWindowLink(shape,smaller));

    // Matching nonzero, byte-aligned offsets are allowed when both stages
    // target the same live descriptor ranges.
    auto shifted=shape;
    shifted.qkv.q_base_bytes=shifted.attention.q_base_bytes=4u;
    shifted.qkv.k_base_bytes=shifted.attention.k_base_bytes=4u;
    shifted.qkv.v_base_bytes=shifted.attention.v_base_bytes=4u;
    auto padded=capacity;
    padded.qkv.q_bytes=padded.attention.q_bytes=tensor+4u;
    padded.qkv.k_bytes=padded.attention.k_bytes=tensor+4u;
    padded.qkv.v_bytes=padded.attention.v_bytes=tensor+4u;
    assert(CanSplitWindowLink(shifted,padded));
    shifted.attention.v_base_bytes=0u;
    assert(!CanSplitWindowLink(shifted,padded));
}
