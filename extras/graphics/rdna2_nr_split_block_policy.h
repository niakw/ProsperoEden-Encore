// SPDX-License-Identifier: MIT
// Preflight native Split-Swin16H, optionally ProjPool + FinalHead.
// FFWD3 -> FFWDProj(residual from input) -> QKV/attention ->
// transpose head->token -> Proj(residual from FFWDProj).
// ProjPool's second output and FinalHead are explicit, never skipped.
#pragma once
#include "rdna2_nr_ffwd3_policy.h"
#include "rdna2_nr_projection_policy.h"
#include "rdna2_nr_projection_quantized_policy.h"
#include "rdna2_nr_vit_epilogue_policy.h"
#include "rdna2_nr_split_context_repack_policy.h"
#include "rdna2_nr_fswin_window_repack_policy.h"
#include "rdna2_nr_split_projection_pool_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_split_window_link_policy.h"
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct SplitBlockPlan {
    std::uint32_t windows{};
    bool has_pooled_projection{};
    std::uint32_t pool_width{},pool_height{};
    std::uint32_t pool_windows_x{},pool_windows_y{};
    std::uint32_t pool_output_tokens{};
    std::uint32_t final_head_tokens{}; // optional 512->1024 projection
    // Native QKV 4x4-tile shift in a 2x2-tile window grid.
    std::uint32_t window_grid_x{},window_grid_y{};
    std::int32_t attention_shift_x{},attention_shift_y{};
};
struct SplitBlockCapacity {
    std::uint64_t input{},ffwd{},ffwd_projected{},context_heads{};
    std::uint64_t context_tokens{},projected{};
    std::uint64_t query{},key{},value{},fp32_scratch{};
    std::uint64_t pooled{};
    std::uint64_t final_fp32{},final_fp8{};
    std::uint64_t shifted_input{},unshifted_context{};
};
[[nodiscard]] constexpr bool CanSplitBlock(
    const SplitBlockPlan& p,const SplitBlockCapacity& c) noexcept {
    if(!p.windows||p.windows>1023u||
       p.attention_shift_x<-1||p.attention_shift_x>1||
       p.attention_shift_y<-1||p.attention_shift_y>1)
        return false;
    const bool needs_shift=
        p.attention_shift_x!=0||p.attention_shift_y!=0;
    if((p.window_grid_x||p.window_grid_y||needs_shift)&&
       (!p.window_grid_x||!p.window_grid_y||
        std::uint64_t(p.window_grid_x)*p.window_grid_y!=p.windows))
        return false;
    if(needs_shift){
        const FSwinWindowRepack forward{
            p.window_grid_x,p.window_grid_y,512u,0,0,
            p.attention_shift_x,p.attention_shift_y};
        const FSwinWindowRepack reverse{
            p.window_grid_x,p.window_grid_y,512u,
            p.attention_shift_x,p.attention_shift_y,0,0};
        if(!CanFSwinWindowRepack(forward,{
              c.ffwd_projected,c.shifted_input})||
           !CanFSwinWindowRepack(reverse,{
              c.context_tokens,c.unshifted_context}))
            return false;
    }
    if(p.has_pooled_projection){
        if(!p.pool_windows_x||!p.pool_windows_y||
           std::uint64_t(p.pool_windows_x)*p.pool_windows_y!=p.windows)
            return false;
        const SplitProjectionPool secondary{
            p.pool_width,p.pool_height,p.pool_windows_x,p.pool_windows_y,
            0u,0u,0u,0u,p.pool_output_tokens};
        // The same GEMM scratch + learned skip gain must produce the
        // secondary half-res output, including padded zero tail.
        if(!CanSplitProjectionPool(secondary,{
              c.fp32_scratch,c.ffwd_projected,1024u,c.pooled}))
            return false;
    }
    if(p.final_head_tokens){
        if(!p.has_pooled_projection||
           p.final_head_tokens>SplitPoolOutputTokens({
               p.pool_width,p.pool_height,p.pool_windows_x,p.pool_windows_y,
               0u,0u,0u,0u,p.pool_output_tokens}))return false;
        const Projection final{p.final_head_tokens,1024u,512u,
                               512u,512u,0u,0u};
        const Storage final_storage{
            c.pooled,1024u*512u,c.final_fp32,c.final_fp32};
        QuantizedProjectionPlan final_plan{};
        if(!PrepareQuantizedProjection(
              final,final_storage,c.final_fp8,final_plan))return false;
    }
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
        {needs_shift?c.shifted_input:c.ffwd_projected,
         786432u,64u,c.query,c.key,c.value},
        {c.query,c.key,c.value,c.context_heads,262144u}};
    if(!CanSplitWindowLink(window,storage))return false;
    const SplitContextRepack repack{p.windows,16u,0u,0u};
    if(!CanSplitContextRepack(repack,{
        c.context_heads,c.context_tokens}))return false;
    const Storage proj_storage{
        needs_shift?c.unshifted_context:c.context_tokens,
        512u*512u,
        c.fp32_scratch,c.fp32_scratch};
    if(!CanDispatch(proj,proj_storage))return false;
    if(!CanVitResidual(residual,{
        c.fp32_scratch,c.ffwd_projected,1024u,c.projected}))
        return false;
    // All intermediate windows must have a complete, contiguous row-major
    // tensor. The GPU buffer identity and nonaliasing checks are in Vulkan.
    return c.input>=rowbytes&&c.ffwd>=rowbytes&&
           c.ffwd_projected>=rowbytes&&c.context_heads>=rowbytes&&
           c.context_tokens>=rowbytes&&c.projected>=rowbytes&&
           (!needs_shift||(c.shifted_input>=rowbytes&&
                            c.unshifted_context>=rowbytes));
}
} // namespace Eden::Graphics::NeuralRDNA2
