// SPDX-License-Identifier: GPL-3.0-or-later
// Source-owner-backed host dimensions for the R09 720p ViT/decoder Vulkan path.
// Computes the launch math used by native owners; no VkCommandBuffer is issued.
#include "dlss_nr_min_720_route_trial.h"
#include "rdna2_nr_vit_attention_policy.h"
#include "rdna2_nr_vit_qkv_norm_policy.h"
#include "rdna2_nr_vit_epilogue_policy.h"
#include "rdna2_nr_decoder_upsample_policy.h"
#include "rdna2_nr_vit_boundary_repack_policy.h"
#include "r09_native_plans.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string_view>
#include <vector>

namespace NR = Eden::Graphics::NeuralRDNA2;
using namespace Eden::Graphics::DlssNrMin;

struct Dispatch {std::uint32_t x{},y{},z{};};
[[nodiscard]] constexpr bool FitsVulkanCore(Dispatch d) noexcept {
    return d.x>0u&&d.y>0u&&d.z>0u&&
           d.x<=65535u&&d.y<=65535u&&d.z<=65535u;
}

static void CheckVariant(std::string_view plan,bool original) {
    Route720Trial trial{};
    assert(BuildR09Min720Routes(plan,trial));
    assert(trial.rows.size()==(original?152u:76u));
    assert(trial.vit.tokens==960u);
    assert(trial.vit.raster_width==22u&&trial.vit.raster_height==40u);
    assert(trial.logical_vit_tokens==880u);
    constexpr std::uint32_t tokens=960u;
    constexpr std::uint64_t plane=std::uint64_t(tokens)*1024u;

    // Actual NrRdna2VitRun::InitializeWithModel() constructs these two
    // boundary requests from native route dimensions, not plan grid_x/y.
    const NR::VitBoundaryRepack in{22u,40u,1024u,tokens,0u,0u,0u};
    const NR::VitBoundaryRepack out{22u,40u,1024u,tokens,1u,0u,0u};
    assert(NR::CanVitBoundaryRepack(in,{plane,plane}));
    assert(NR::CanVitBoundaryRepack(out,{plane,plane}));
    assert(NR::VitBoundaryGrid(in)==tokens);
    assert(NR::VitBoundaryGrid(out)==tokens);
    assert(FitsVulkanCore({NR::VitBoundaryGrid(in),1u,1u}));
    assert(!NR::CanVitBoundaryRepack(in,{plane-1u,plane}));
    assert(!NR::CanVitBoundaryRepack(out,{plane,plane-1u}));

    // Actual NrRdna2VitAttention::Record(): ceil(tokens/32), 32, 1.
    const NR::VitAttention attention{0u,0u,0u,0u,tokens};
    const NR::VitAttentionStorage attention_storage{
        plane,plane,plane,plane};
    assert(NR::CanVitAttention(attention,attention_storage));
    const Dispatch attention_groups{(tokens+31u)/32u,32u,1u};
    assert(attention_groups.x==30u&&FitsVulkanCore(attention_groups));
    assert(!NR::CanVitAttention(attention,{plane-1u,plane,plane,plane}));
    assert(!NR::CanVitAttention(attention,{plane,plane,plane,plane-1u}));

    // Actual NrRdna2VitQkvNorm::Record(): tokens, 32, 1.
    const NR::VitQkvNorm norm{tokens,0u,0u,0u,0u,0u};
    const NR::VitQkvNormStorage norm_storage{
        std::uint64_t(tokens)*3072u*4u,128u,plane,plane,plane};
    assert(NR::CanVitQkvNorm(norm,norm_storage));
    assert(FitsVulkanCore({tokens,32u,1u}));
    assert(!NR::CanVitQkvNorm(norm,{
        norm_storage.input_bytes,128u,plane,plane-1u,plane}));
    assert(!NR::CanVitQkvNorm(norm,{
        norm_storage.input_bytes-1u,128u,plane,plane,plane}));

    // Actual NrRdna2VitEpilogue::Record{Activation,Residual}:
    // ceil(tokens*channels / 512), 1, 1, with per-batch tokens.
    assert(NR::VitEpilogueGroups(tokens,1024u)==1920u);
    assert(NR::VitEpilogueGroups(tokens,4096u)==7680u);
    assert(FitsVulkanCore({NR::VitEpilogueGroups(tokens,1024u),1u,1u}));
    assert(FitsVulkanCore({NR::VitEpilogueGroups(tokens,4096u),1u,1u}));
    const NR::VitActivation activation{
        tokens,1024u,0u,0u};
    assert(NR::CanVitActivation(activation,{
        plane*4u,0u,0u,plane}));
    assert(!NR::CanVitActivation(activation,{
        plane*4u-1u,0u,0u,plane}));

    // Actual NrRdna2NativeDecoderLink::InitializeWithModel()
    // constructs {0,0,0,0,width,width,height}; the decoder launch is
    // ceil(output_padded_tile_tokens/64),128,1, not inherited grid_x/y.
    const NR::DecoderUpsample decoder{0u,0u,0u,0u,22u,22u,40u};
    assert(NR::DecoderOutputTileTokens(decoder)==tokens);
    assert(NR::DecoderInputTileTokens(decoder)==480u);
    const NR::DecoderStorage decoder_storage{
        NR::DecoderInputTileTokens(decoder)*512u*2u,
        std::uint64_t(tokens)*512u,
        std::uint64_t(tokens)*512u,1024u};
    assert(NR::CanDecoderUpsample(decoder,decoder_storage));
    const Dispatch decoder_groups{
        static_cast<std::uint32_t>(
            (NR::DecoderOutputTileTokens(decoder)+63u)/64u),128u,1u};
    assert(decoder_groups.x==15u&&FitsVulkanCore(decoder_groups));
    assert(!NR::CanDecoderUpsample(decoder,{
        decoder_storage.projected_bytes,
        decoder_storage.skip_bytes-1u,
        decoder_storage.output_bytes,decoder_storage.gain_bytes}));

    std::vector<NR::NativePlanStep> original_rows{};
    assert(NR::ParseNativePlan(plan,original_rows)==NR::NativePlanError::Ok);
    assert(original_rows.size()==trial.rows.size());
    std::uint32_t inherited{},vit{},decoder_rows{};
    for(std::size_t i=0u;i<trial.rows.size();++i) {
        const auto op=NR::ClassifyNativeNrOp(trial.rows[i]);
        const bool v=NR::IsNativeNrVitOp(op);
        const bool d=op==NR::NativeNrOp::DecoderUpsample;
        if(!v&&!d)continue;
        inherited+=trial.rows[i].grid_x==original_rows[i].grid_x&&
                   trial.rows[i].grid_y==original_rows[i].grid_y&&
                   trial.rows[i].grid_z==original_rows[i].grid_z?1u:0u;
        vit+=v?1u:0u;
        decoder_rows+=d?1u:0u;
    }
    assert(vit==40u&&decoder_rows==1u&&inherited==41u);
    // Inherited model metadata != the native owner dispatch dimensions.
    // These host checks do NOT qualify model weights, resource descriptors,
    // synchronization, full 152-stage GPU execution or PS5 performance.
    assert(!trial.gpu_dispatch_qualified&&!trial.ready_to_enable_720p);
    std::cout<<"R09_MIN_720P_NATIVE_OWNER_LAUNCH_MATH_PASS "
             <<(original?"Original":"Compact")
             <<" inherited_plan_grids="<<inherited
             <<" attention_groups=30x32"
             <<" normalize_groups=960x32"
             <<" decoder_groups=15x128"
             <<" vit_boundary_groups=960"
             <<" GPU_DISABLED\n";
}
int main() {
    CheckVariant(Eden::NeuralPlans::Original,true);
    CheckVariant(Eden::NeuralPlans::Compact,false);
}
