// SPDX-License-Identifier: MIT
// Preflight one full four-step NON-POOLED native Split-Swin16H block.
// FFWD3 -> FFWDProj(residual from input) -> QKV/attention ->
// transpose head->token -> Proj(residual from FFWDProj).
// Native ProjPool has a second output: fail closed until it is wired.
#pragma once
#include "rdna2_nr_ffwd3_policy.h"
#include "rdna2_nr_projection_policy.h"
#include "rdna2_nr_vit_epilogue_policy.h"
#include "rdna2_nr_split_context_repack_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_split_window_link_policy.h"
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct SplitBlockPlan {
    std::uint32_t windows{};
    bool has_pooled_projection{};
};
struct SplitBlockCapacity {
    std::uint64_t input{},ffwd{},ffwd_projected{},context_heads{};
    std::uint64_t context_tokens{},projected{};
    std::uint64_t query{},key{},value{},fp32_scratch{};
};
[[nodiscard]] constexpr bool CanSplitBlock(
    const SplitBlockPlan& p,const SplitBlockCapacity& c) noexcept {
    if(!p.windows||p.windows>1023u||p.has_pooled_projection)
        return false;
    const std::uint32_t tokens=p.windows*64u;
    const auto rowbytes=std::uint64_t(tokens)*512u;
    const FFWD3 ffwd{0u,0u,0u,0u,0u,tokens};
    const FFWD3Storage ffwd_storage{
        c.input,262144u,131072u,131072u,c.ffwd};
    if(!CanFFWD3(ffwd,ffwd_storage))return false;
    const Projection proj{tokens,512u,512u,512u,512u,0u,0u};
    const Storage fwd_storage{
        c.ffwd,512u*512u,c.fp32_scratch,c.fp32_scratch};
    if(!CanDispatch(proj,fwd_storage))return false;
    const VitResidual residual{tokens,512u,0u,0u,0u,0u};
    if(!CanVitResidual(residual,{
        c.fp32_scratch,c.input,1024u,c.ffwd_projected}))return false;
    const SplitWindowLink window{
        {0u,0u,0u,0u,0u,0u,p.windows,16u},
        {0u,0u,0u,0u,0u,p.windows,16u}};
    const SplitWindowLinkStorage storage{
        {c.ffwd_projected,786432u,64u,c.query,c.key,c.value},
        {c.query,c.key,c.value,c.context_heads,262144u}};
    if(!CanSplitWindowLink(window,storage))return false;
    const SplitContextRepack repack{p.windows,16u,0u,0u};
    if(!CanSplitContextRepack(repack,{
        c.context_heads,c.context_tokens}))return false;
    const Storage proj_storage{
        c.context_tokens,512u*512u,
        c.fp32_scratch,c.fp32_scratch};
    if(!CanDispatch(proj,proj_storage))return false;
    if(!CanVitResidual(residual,{
        c.fp32_scratch,c.ffwd_projected,1024u,c.projected}))
        return false;
    // All intermediate windows must have a complete, contiguous row-major
    // tensor. The GPU buffer identity and nonaliasing checks are in Vulkan.
    return c.input>=rowbytes&&c.ffwd>=rowbytes&&
           c.ffwd_projected>=rowbytes&&c.context_heads>=rowbytes&&
           c.context_tokens>=rowbytes&&c.projected>=rowbytes;
}
} // namespace Eden::Graphics::NeuralRDNA2
