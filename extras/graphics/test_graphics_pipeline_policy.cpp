// SPDX-License-Identifier: GPL-3.0-or-later
#include "graphics_pipeline_policy.h"
#include <cassert>
using namespace Eden::FeatureLab;
int main() {
    constexpr auto off=ResolveGraphicsPipeline({}, {});
    static_assert(off.resolution == ResolutionStage::Native);
    static_assert(off.frame_generation == FrameGeneration::Off);
    static_assert(off.neural == NeuralStage::Off);
    static_assert(off.textures == TextureStage::Original);
    static_assert(off.display_hz == 60 && !off.runtime_qualified);
    RequestedPipeline request{};
    request.resolution=ResolutionStage::TemporalFsr3;
    request.frame_generation=FrameGeneration::MihawkGen;
    request.neural=NeuralStage::AMDCompute;
    request.textures=TextureStage::VerifiedHdPack;
    request.display_hz=120;
    auto p=ResolveGraphicsPipeline(request, {});
    assert(p.resolution==ResolutionStage::Native);
    assert(p.frame_generation==FrameGeneration::Off);
    assert(p.neural==NeuralStage::Off);
    assert(p.textures==TextureStage::Original);
    assert(p.display_hz==60);
    auto caps=PipelineCapabilities{};
    caps.framegen.native_vulkan=true;
    caps.framegen.game_fps=30;
    caps.framegen.mihawk_compute=true;
    caps.framegen.model_weights_verified_and_licensed=true;
    caps.fsr_temporal_backend_ready=true;
    caps.neural_vulkan_spirv_ready=true;
    caps.neural_weights_redistributable=true;
    p=ResolveGraphicsPipeline(request,caps);
    assert(p.generation_reason==Rejection::HudUnsafe);
    assert(p.resolution_reason==Rejection::MissingSceneData);
    assert(p.neural_reason==Rejection::HudUnsafe);
    caps.framegen.guest_motion_vectors=true;
    caps.framegen.guest_depth=true;
    caps.temporal_jitter_valid=true;
    caps.hud_separated=true;
    caps.neural_hdr_and_colorspace_checked=true;
    caps.neural_ui_exclusion_mask=true;
    caps.verified_hd_texture_pack=true;
    caps.output_120hz_negotiated=true;
    p=ResolveGraphicsPipeline(request,caps);
    assert(p.resolution==ResolutionStage::TemporalFsr3);
    assert(p.frame_generation==FrameGeneration::MihawkGen);
    assert(p.neural==NeuralStage::AMDCompute);
    assert(p.textures==TextureStage::VerifiedHdPack);
    assert(p.display_hz==120);
    assert(!p.runtime_qualified); // policy != actual shader/presenter integration
    caps.neural_weights_redistributable=false;
    p=ResolveGraphicsPipeline(request,caps);
    assert(p.neural==NeuralStage::Off);
    assert(p.neural_reason==Rejection::UnlicensedModel);
    request.frame_generation=FrameGeneration::DlssPcOnlyUnsupported;
    p=ResolveGraphicsPipeline(request,caps);
    assert(p.frame_generation==FrameGeneration::Off);
    assert(p.generation_reason==Rejection::Unsupported);
    request.resolution=ResolutionStage::SpatialFsr;
    caps.fsr_spatial_backend_ready=true;
    p=ResolveGraphicsPipeline(request,caps);
    assert(p.resolution==ResolutionStage::SpatialFsr);
    request.display_hz=360;
    p=ResolveGraphicsPipeline(request,caps);
    assert(p.display_hz==60);
    assert(p.display_reason==Rejection::UnverifiedOutput);
    assert(p.resolution_reason==Rejection::None);
}
