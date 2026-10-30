// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Explicit session-owned GPU capture -> Vulkan SPIR-V compilation entrypoint.
// Not hooked to normal Switch 1 / Encore PS5 graphics pipeline lookup.
#include <memory>
#include "common/common_types.h"
#include "shader_recompiler/frontend/ampere/renderer_spirv_bridge.h"

namespace Tegra { class MemoryManager; }
namespace Kernel { class KProcess; }
namespace Shader {
class Environment;
struct HostTranslateInfo;
struct Profile;
struct RuntimeInfo;
}
namespace Shader::Ampere { class NativeTranslationCache; }

namespace VideoCommon {
// Caller must provide the actual guest process associated with the NS2 NVDRV
// session and the exact GMMU object for that process. NULL, unrelated or
// destroyed sessions reject BEFORE any GPU memory access.
// Original shader environment, GPU VA, runtime metadata and device profile
// all come from the same active pipeline. NativeTranslationCache is
// caller-owned and must be invalidated on GMMU remaps/session teardown.
[[nodiscard]] Shader::Ampere::NativeSpirvResult CompileCapturedNs2VertexSpirv(
    Tegra::MemoryManager& memory,
    const Kernel::KProcess* process,
    std::unique_ptr<Shader::Environment> original,
    u64 gpu_program_address,
    const Shader::HostTranslateInfo& host_info,
    const Shader::Profile& profile,
    const Shader::RuntimeInfo& runtime_info,
    Shader::Ampere::NativeTranslationCache* cache = nullptr,
    bool exits_to_dispatcher = false);
} // namespace VideoCommon
