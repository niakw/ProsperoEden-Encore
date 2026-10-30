// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Actual Tegra GMMU-based reader for the isolated NS2 shader capture.
// This is compiled only for opt-in research, not hooked to shipping renderer.
#include <memory>
#include "shader_recompiler/frontend/ampere/capture.h"
namespace Shader { class Environment; }
namespace Tegra { class MemoryManager; }
namespace VideoCommon {
[[nodiscard]] Shader::Ampere::NativeCaptureResult CaptureNs2GraphicsShaderFromGpu(
    Tegra::MemoryManager& memory, u64 gpu_program_address, u32 stage,
    Shader::Ampere::NativeTranslationCache* cache = nullptr);

// Explicit opt-in bridge from verified guest GMMU bytes into the actual
// Shader::Environment virtual interface used by the existing Maxwell CFG.
// Never auto-detect by title name, GPU address or Switch 1 shader extension.
[[nodiscard]] std::unique_ptr<Shader::Environment> CreateNs2GraphicsShaderEnvironment(
    Tegra::MemoryManager& memory, Shader::Environment& original,
    u64 gpu_program_address, u32 stage,
    Shader::Ampere::NativeTranslationCache* cache = nullptr);
} // namespace VideoCommon
