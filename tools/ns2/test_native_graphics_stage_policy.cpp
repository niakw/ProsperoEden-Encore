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
    // Geometry is compiled only with its real VertexB linker and CBUF bank.
    // Standalone SPIR-V helpers do not fabricate pipeline topology.
    using Shader::Ampere::NativeGraphicsStageMaskSupported;
    assert(NativeGraphicsStageMaskSupported(0x12));
    assert(NativeGraphicsStageMaskSupported(0x13));
    assert(NativeGraphicsStageMaskSupported(0x32));
    assert(NativeGraphicsStageMaskSupported(0x33));
    assert(!NativeGraphicsStageMaskSupported(0x10));
    assert(!NativeGraphicsStageMaskSupported(0x30));
    assert(!NativeGraphicsStageMaskSupported(0x06));
    assert(!IsStandaloneNativeGraphicsStage(Stage::Compute));
    assert(!IsStandaloneNativeGraphicsStage(static_cast<Stage>(0xffffffffu)));
}
