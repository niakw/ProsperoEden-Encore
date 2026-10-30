// SPDX-License-Identifier: GPL-3.0-or-later
#include "video_core/ns2_shader_spirv_compile.h"
#include <exception>
#include <memory>
#include <utility>
#include "video_core/native_shader_capture.h"
#include "shader_recompiler/frontend/ampere/maxwell_environment.h"
#include "shader_recompiler/frontend/ampere/renderer_spirv_bridge.h"

namespace VideoCommon {
Shader::Ampere::NativeSpirvResult CompileCapturedNs2VertexSpirv(
    Tegra::MemoryManager& memory,
    std::unique_ptr<Shader::Environment> original,
    u64 gpu_program_address,
    const Shader::HostTranslateInfo& host_info,
    const Shader::Profile& profile,
    const Shader::RuntimeInfo& runtime_info,
    Shader::Ampere::NativeTranslationCache* cache,
    bool exits_to_dispatcher) {
    using Shader::Ampere::NativeSpirvStatus;
    // No autodetection, no fallback to Switch 1 shader bytes or cache keys.
    // Reject BEFORE GMMU capture: unmerged VertexA/compute stages cannot
    // silently appear as valid Vulkan VertexB modules.
    if (!original)
        return {NativeSpirvStatus::InvalidImage, {}};
    if (original->ShaderStage() != Shader::Stage::VertexB)
        return {NativeSpirvStatus::UnsupportedStage, {}};
    try {
        auto captured = CaptureNs2GraphicsShaderFromGpu(
            memory, gpu_program_address,
            static_cast<u32>(original->ShaderStage()), cache);
        if (!captured.Ready())
            return {NativeSpirvStatus::InvalidImage, {}};
        auto env = Shader::Ampere::NativeMaxwellEnvironment::CreateOwned(
            std::move(original), std::move(captured.image));
        if (!env)
            return {NativeSpirvStatus::InvalidImage, {}};
        // Only a complete, independently owned module escapes this call.
        // Existing Vulkan pipeline/layout construction is NOT overridden.
        return Shader::Ampere::CompileReviewedNativeVertexSpirv(
            *env, host_info, profile, runtime_info, exits_to_dispatcher);
    } catch (const std::exception&) {
        return {NativeSpirvStatus::CompilationFailed, {}};
    }
}
} // namespace VideoCommon
