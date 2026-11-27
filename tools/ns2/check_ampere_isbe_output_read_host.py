#!/usr/bin/env python3
"""Host regression for Lichii 31f1378 / #2074 adapted to Encore.

Proves the reviewed Ampere ISBERD.ATTR.32.O form is admitted by the native
stage-buffer decoder, routed to a distinct IR opcode, and emitted by the
selected Vulkan SPIR-V backend. No game data or PS5 execution is used.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
AMPERE = VENDOR / "encore-active/eden/srcpere"
SHADER = VENDOR / "encore-active/eden-shader/src"

decoder = (AMPERE / "shader_recompiler/frontend/ampere/native_stage_buffer.h").read_text()
lowerer = (AMPERE / "shader_recompiler/frontend/ampere/lower_to_maxwell.h").read_text()
ir_h = (SHADER / "shader_recompiler/frontend/ir/ir_emitter.h").read_text()
ir_cpp = (SHADER / "shader_recompiler/frontend/ir/ir_emitter.cpp").read_text()
opcodes = (SHADER / "shader_recompiler/frontend/ir/opcodes.inc").read_text()
translator = (
    SHADER / "shader_recompiler/frontend/maxwell/translate/impl/internal_stage_buffer_entry_read.cpp"
).read_text()
spirv_h = (SHADER / "shader_recompiler/backend/spirv/emit_spirv_instructions.h").read_text()
spirv_mesh = (SHADER / "shader_recompiler/backend/spirv/emit_spirv_mesh.cpp").read_text()
glsl_h = (SHADER / "shader_recompiler/backend/glsl/emit_glsl_instructions.h").read_text()
glsl_ni = (SHADER / "shader_recompiler/backend/glsl/emit_glsl_not_implemented.cpp").read_text()
glasm_h = (SHADER / "shader_recompiler/backend/glasm/emit_glasm_instructions.h").read_text()
glasm_ni = (SHADER / "shader_recompiler/backend/glasm/emit_glasm_not_implemented.cpp").read_text()

for needle in (
    "const bool output_read = !write && output && is_32 && !skew;",
    "(write != output && !output_read)",
):
    assert needle in decoder, needle

assert "(u64{access->output} << 47)" in lowerer
assert "[[nodiscard]] U32 IsbeReadOutput(const U32& address);" in ir_h
assert "U32 IREmitter::IsbeReadOutput(const U32& address)" in ir_cpp
assert "Opcode::IsbeReadOutput" in ir_cpp
assert "OPCODE(IsbeReadOutput" in opcodes
assert "BitField<47, 1, u64> output;" in translator
assert "isbe.output != 0 ? ir.IsbeReadOutput(address) : ir.IsbeRead(address)" in translator
assert "Id EmitIsbeReadOutput(EmitContext& ctx, Id address);" in spirv_h
assert "Id EmitIsbeReadOutput(EmitContext& ctx, Id address)" in spirv_mesh
assert "PayloadWord(ctx, index)" in spirv_mesh
assert "ctx.mesh_attributes" in spirv_mesh
assert "void EmitIsbeReadOutput(EmitContext& ctx);" in glsl_h
assert "void EmitIsbeReadOutput(EmitContext& ctx)" in glsl_ni
assert "void EmitIsbeReadOutput(EmitContext& ctx);" in glasm_h
assert "void EmitIsbeReadOutput(EmitContext& ctx)" in glasm_ni

fixture = r"""
#include <cassert>
#include "shader_recompiler/frontend/ampere/native_stage_buffer.h"

using Shader::Ampere::DecodeNativeStageBufferAccess;
using Shader::Ampere::Instruction;

int main() {
    // Lichii #2074 / Switch Sports Resort: ISBERD.ATTR.32.O R35, [R30 + 0x24].
    const Instruction output_read{{0x1e237923, 0x00002400, 0x0000b800, 0x000e2400}};
    const auto decoded = DecodeNativeStageBufferAccess(output_read);
    assert(decoded.has_value());
    assert(!decoded->write);
    assert(decoded->output);
    assert(decoded->attribute);
    assert(decoded->width_32);
    assert(!decoded->skew);
    assert(decoded->address_register == 30);
    assert(decoded->value_register == 35);
    assert(decoded->byte_offset == 0x24);

    auto skew = output_read;
    skew.words[2] |= 1U << 14;
    assert(!DecodeNativeStageBufferAccess(skew));

    auto byte = output_read;
    byte.words[2] &= ~(1U << 11);
    assert(!DecodeNativeStageBufferAccess(byte));

    auto map = output_read;
    map.words[2] &= ~(3U << 12);
    assert(!DecodeNativeStageBufferAccess(map));

    auto ordinary_read = output_read;
    ordinary_read.words[2] &= ~(1U << 15);
    const auto ordinary = DecodeNativeStageBufferAccess(ordinary_read);
    assert(ordinary.has_value());
    assert(!ordinary->output);
    return 0;
}
"""

compilers = [c for c in (shutil.which("clang++"), shutil.which("g++")) if c]
assert compilers, "no C++ compiler available"
with tempfile.TemporaryDirectory(prefix="encore-isbe-output-") as td:
    source = Path(td) / "isbe_output.cpp"
    source.write_text(fixture)
    for compiler in dict.fromkeys(compilers):
        for opt in ("0", "2"):
            binary = Path(td) / (Path(compiler).name.replace("+", "p") + "-O" + opt)
            cmd = [
                compiler,
                "-std=c++20",
                "-O" + opt,
                "-Wall",
                "-Wextra",
                "-Werror",
                "-fsanitize=undefined",
                "-fno-sanitize-recover=all",
                "-I",
                str(AMPERE),
                "-I",
                str(VENDOR / "sources/eden/src"),
                str(source),
                "-o",
                str(binary),
            ]
            subprocess.run(cmd, check=True)
            subprocess.run([str(binary)], check=True)

print(
    "NS2_ISBE_OUTPUT_READ_HOST_PASS",
    "upstream=31f1378",
    "decoder=1",
    "ir=1",
    "spirv=1",
    "glsl_fail_closed=1",
    "glasm_fail_closed=1",
)
