// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Actual Tegra GMMU-based reader for the isolated NS2 shader capture.
// This is compiled only for opt-in research, not hooked to shipping renderer.
#include "shader_recompiler/frontend/ampere/capture.h"
namespace Tegra { class MemoryManager; }
namespace VideoCommon {
[[nodiscard]] Shader::Ampere::NativeCaptureResult CaptureNs2GraphicsShaderFromGpu(
    Tegra::MemoryManager& memory, u64 gpu_program_address, u32 stage);
} // namespace VideoCommon
