// SPDX-License-Identifier: MIT
// Spatial 2x C32 skip fusion before postblock Swin, not RGB presentation.
#pragma once
#include "video_core/renderer_vulkan/nr_rdna2_native_plan_bridge.h"
#include <cstdint>
#include <span>
namespace Eden::Graphics::NeuralRDNA2 {
struct PostblockMixShape {std::uint32_t width{},height{};};
struct PostblockMixCapacity {
    std::uint64_t low_bytes{},skip_bytes{},gains_bytes{},output_bytes{};
};
[[nodiscard]] constexpr bool CanPostblockMix(
    PostblockMixShape s,PostblockMixCapacity c) noexcept {
    if(!s.width||!s.height||(s.width&1u)||(s.height&1u)||
       s.width>8192u||s.height>8192u||c.gains_bytes!=128u)
        return false;
    const std::uint64_t full=std::uint64_t(s.width)*s.height*32u;
    constexpr std::uint64_t limit=256ull<<20;
    return full<=limit&&c.low_bytes>=full/4u&&
           c.low_bytes<=limit&&c.skip_bytes>=full&&
           c.skip_bytes<=limit&&c.output_bytes>=full&&
           c.output_bytes<=limit;
}
[[nodiscard]] inline bool CanNativePostblockMixBoundary(
    std::span<const NativePlanStep> steps,PostblockMixShape s) noexcept {
    if(steps.size()<3u)return false;
    const auto& pre=steps.front();
    const auto& previous=steps[steps.size()-2u];
    const auto& post=steps.back();
    if(pre.block!=0u||pre.layer!=0u||
       pre.type!="CCTinlayoutFusedPreBlockSwin1H"||
       pre.height!=s.width||pre.width!=s.height||
       post.type!="CCTinlayoutFusedPostBlockSwin1H"||
       post.kernel!="cc_tinlayout_fused_post_block_swin_1h_32_fp8"||
       (post.block!=70u&&post.block!=30u)||
       post.layer!=0u||post.div!=2u||
       std::uint64_t(post.width)*2u!=s.height||
       std::uint64_t(post.height)*2u!=s.width||
       post.inputs!=2u||post.input0<0||post.input1!=0||
       previous.block!=static_cast<std::uint32_t>(post.input0)||
       previous.channels!=32u||
       !previous.kernel.ends_with("_outview_fp8")||
       previous.width!=post.width||previous.height!=post.height||
       post.input_channels!=32u||post.output_channels!=3u||
       post.grid_z!=1u||
       post.grid_x!=(s.width+7u)/8u||
       post.grid_y!=(s.height+7u)/8u)return false;
    return CanPostblockMix(s,{
        std::uint64_t(post.width)*post.height*32u,
        std::uint64_t(s.width)*s.height*32u,128u,
        std::uint64_t(s.width)*s.height*32u});
}
} // namespace Eden::Graphics::NeuralRDNA2
