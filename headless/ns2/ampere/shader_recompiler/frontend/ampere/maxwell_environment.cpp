// SPDX-License-Identifier: GPL-3.0-or-later
#include "shader_recompiler/frontend/ampere/maxwell_environment.h"
#include <stdexcept>
#include <utility>

namespace Shader::Ampere {

NativeMaxwellEnvironment::NativeMaxwellEnvironment(
    Shader::Environment& source, MaxwellShaderImage translated)
    : original{source}, image{std::move(translated)} {
    // Feed the existing Maxwell CFG its expected SPH, stage, passthrough
    // mask and first real 64-bit instruction address (after 0x50 SPH).
    sph = source.SPH();
    stage = source.ShaderStage();
    gp_passthrough_mask = source.GpPassthroughMask();
    start_address = image.first_instruction_address;
    is_proprietary_driver = source.IsProprietaryDriver();
}
std::unique_ptr<NativeMaxwellEnvironment> NativeMaxwellEnvironment::Create(
    Shader::Environment& source, MaxwellShaderImage image) {
    if (!image.Ready() || image.code.empty() ||
        image.first_instruction_address != 0x50 ||
        !image.ReadMaxwellInstruction(0x50))
        return {};
    return std::unique_ptr<NativeMaxwellEnvironment>(
        new NativeMaxwellEnvironment(source, std::move(image)));
}
u64 NativeMaxwellEnvironment::ReadInstruction(u32 address) {
    // Fail closed instead of falling back to *native* GMMU bytes interpreted
    // as Maxwell instructions. Bounds and schedule slots are enforced by
    // MaxwellShaderImage::ReadMaxwellInstruction.
    auto instruction = image.ReadMaxwellInstruction(address);
    if (!instruction)
        throw std::out_of_range{"NS2 Maxwell environment: invalid shader instruction address"};
    return *instruction;
}
u32 NativeMaxwellEnvironment::ReadCbufValue(u32 index, u32 offset) {
    return original.ReadCbufValue(index, offset);
}
Shader::TextureType NativeMaxwellEnvironment::ReadTextureType(u32 handle) {
    return original.ReadTextureType(handle);
}
Shader::TexturePixelFormat NativeMaxwellEnvironment::ReadTexturePixelFormat(u32 handle) {
    return original.ReadTexturePixelFormat(handle);
}
bool NativeMaxwellEnvironment::IsTexturePixelFormatInteger(u32 handle) {
    return original.IsTexturePixelFormatInteger(handle);
}
u32 NativeMaxwellEnvironment::ReadViewportTransformState() {
    return original.ReadViewportTransformState();
}
u32 NativeMaxwellEnvironment::TextureBoundBuffer() const {
    return original.TextureBoundBuffer();
}
u32 NativeMaxwellEnvironment::LocalMemorySize() const {
    return original.LocalMemorySize();
}
u32 NativeMaxwellEnvironment::SharedMemorySize() const {
    return original.SharedMemorySize();
}
std::array<u32, 3> NativeMaxwellEnvironment::WorkgroupSize() const {
    return original.WorkgroupSize();
}
bool NativeMaxwellEnvironment::HasHLEMacroState() const {
    return original.HasHLEMacroState();
}
std::optional<Shader::ReplaceConstant> NativeMaxwellEnvironment::GetReplaceConstBuffer(
    u32 bank, u32 offset) {
    return original.GetReplaceConstBuffer(bank, offset);
}
void NativeMaxwellEnvironment::Dump(u64, u64) {
    // Explicitly disabled: forwarding would incorrectly dump native guest
    // bytes or assign a Switch 1 cache identity to an NS2 shader.
}
} // namespace Shader::Ampere
