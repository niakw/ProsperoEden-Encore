// SPDX-License-Identifier: GPL-3.0-or-later
#include "video_core/native_shader_capture.h"
#include <limits>
#include "video_core/memory_manager.h"

namespace VideoCommon {
namespace {
bool ReadNs2GpuShader(void* context, u64 address, void* dest, std::size_t size) {
    auto* const memory = static_cast<Tegra::MemoryManager*>(context);
    if (!memory || !dest || !size ||
        address > std::numeric_limits<u64>::max() - size ||
        !memory->IsFullyMappedRange(address, size))
        return false;
    memory->ReadBlock(address, dest, size);
    return true;
}
} // namespace

Shader::Ampere::NativeCaptureResult CaptureNs2GraphicsShaderFromGpu(
    Tegra::MemoryManager& memory, u64 gpu_program_address, u32 stage) {
    // The GMMU mapping check is repeated for EVERY individual native
    // instruction. A fault aborts capture without populating a shader image.
    return Shader::Ampere::CaptureNativeGraphicsShader(
        gpu_program_address, stage, ReadNs2GpuShader, &memory);
}
} // namespace VideoCommon
