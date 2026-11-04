// SPDX-License-Identifier: GPL-3.0-or-later
// Native Ampere stage admission must never invent a missing pipeline/QMD.
#include <cassert>
#include "shader_recompiler/frontend/ampere/native_graphics_stage_policy.h"
int main() {
    using Shader::Ampere::IsStandaloneNativeGraphicsStage;
    using Shader::Ampere::RequiresNativeVertexMerge;
    using Shader::Stage;
    assert(IsStandaloneNativeGraphicsStage(Stage::VertexB));
    assert(IsStandaloneNativeGraphicsStage(Stage::Fragment));
    assert(!IsStandaloneNativeGraphicsStage(Stage::VertexA));
    assert(RequiresNativeVertexMerge(Stage::VertexA));
    assert(!RequiresNativeVertexMerge(Stage::Fragment));
    assert(!IsStandaloneNativeGraphicsStage(Stage::TessellationControl));
    assert(!IsStandaloneNativeGraphicsStage(Stage::TessellationEval));
    assert(!IsStandaloneNativeGraphicsStage(Stage::Geometry));
    // Tessellation requires both control + evaluation with the live Vulkan
    // pipeline's state; geometry is also linked, never standalone SPIR-V.
    using Shader::Ampere::NativeGraphicsStageMaskSupported;
    assert(NativeGraphicsStageMaskSupported(0x12));
    assert(NativeGraphicsStageMaskSupported(0x13));
    assert(NativeGraphicsStageMaskSupported(0x32));
    assert(NativeGraphicsStageMaskSupported(0x33));
    assert(NativeGraphicsStageMaskSupported(0x0e));
    assert(NativeGraphicsStageMaskSupported(0x0f));
    assert(NativeGraphicsStageMaskSupported(0x1e));
    assert(NativeGraphicsStageMaskSupported(0x2e));
    assert(NativeGraphicsStageMaskSupported(0x3f));
    assert(!NativeGraphicsStageMaskSupported(0x0a));  // evaluation without control
    assert(!NativeGraphicsStageMaskSupported(0x26));  // control without evaluation
    using Shader::Ampere::NativeGraphicsCbufBank;
    assert(NativeGraphicsCbufBank(Stage::VertexA)==0U);
    assert(NativeGraphicsCbufBank(Stage::VertexB)==0U);
    assert(NativeGraphicsCbufBank(Stage::TessellationControl)==1U);
    assert(NativeGraphicsCbufBank(Stage::TessellationEval)==2U);
    assert(NativeGraphicsCbufBank(Stage::Geometry)==3U);
    assert(NativeGraphicsCbufBank(Stage::Fragment)==4U);
    assert(NativeGraphicsCbufBank(Stage::Compute)==~0U);
    assert(!NativeGraphicsStageMaskSupported(0x10));
    assert(!NativeGraphicsStageMaskSupported(0x30));
    assert(!NativeGraphicsStageMaskSupported(0x06));
    assert(!IsStandaloneNativeGraphicsStage(Stage::Compute));
    assert(!IsStandaloneNativeGraphicsStage(static_cast<Stage>(0xffffffffu)));
}
