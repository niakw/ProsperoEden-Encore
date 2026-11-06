#!/usr/bin/env python3
"""P2.4: compile and execute the real native Ampere ISBE/CSM operand guards.

No emulator, ROM, PS5 or Vulkan hardware is required. This test never
pretends to validate Task/Mesh rendering or shading-mode predicate results.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
AMPERE = ROOT / "vendor/encore-active/ns2-runtime/ampere"
EDEN = ROOT / "vendor/sources/eden/src"
PROBE = AMPERE / "shader_recompiler/frontend/ampere/probe.cpp"
DECODER = AMPERE / "shader_recompiler/frontend/ampere/native_stage_buffer.h"
assert DECODER.is_file(), f"Missing maintained stage-buffer decoder: {DECODER}"

CODE = r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <span>
#include "shader_recompiler/frontend/ampere/probe.h"
#include "shader_recompiler/frontend/ampere/ampere_isa_table.h"
#include "shader_recompiler/frontend/ampere/native_stage_buffer.h"

using namespace Shader::Ampere;

Instruction Stage(u32 op, u32 ra, u32 value, u32 byte_offset, u32 flags) {
    Instruction inst{};
    inst.words[0] = op | (op == 0x923 ? (value << 16) : 0U) | (ra << 24);
    inst.words[1] = (byte_offset << 8) | (op == 0x927 ? value : 0U);
    inst.words[2] = flags;
    return inst;
}

int main() {
    // Output Task stage buffer: 32-bit attribute, U8/U32 primitive map.
    const auto attr = Stage(0x927, 17, 37, 0x123456, 0xb800);
    const auto attr_info = DecodeNativeStageBufferAccess(attr);
    assert(attr_info && attr_info->write && attr_info->attribute);
    assert(attr_info->address_register == 17 && attr_info->value_register == 37);
    assert(attr_info->byte_offset == 0x123456 && attr_info->width_32);
    assert(attr_info->output && !attr_info->skew);
    const auto* write_row = FindOpcodeRow(0x927);
    assert(write_row && FirstUnreviewedBit(attr, *write_row) == -1);

    const auto map_u8 = Stage(0x927, 255, 0, 4, 0x8000);
    const auto map_info = DecodeNativeStageBufferAccess(map_u8);
    assert(map_info && map_info->write && !map_info->attribute && !map_info->width_32);
    const auto map_u32 = Stage(0x927, 6, 2, 3, 0x8800);
    assert(DecodeNativeStageBufferAccess(map_u32)->width_32);

    // Task input: 32-bit attribute, unmodified linear byte offset.
    const auto read = Stage(0x923, 4, 8, 0xabcde, 0x3800);
    const auto read_info = DecodeNativeStageBufferAccess(read);
    assert(read_info && !read_info->write && read_info->attribute);
    assert(read_info->byte_offset == 0xabcde);
    assert(FirstUnreviewedBit(read, *FindOpcodeRow(0x923)) == -1);

    // Refuse undefined stage-buffer regions and observable-looking false success.
    assert(!DecodeNativeStageBufferAccess(Stage(0x927, 1, 2, 0, 0x3800))); // output off
    assert(!DecodeNativeStageBufferAccess(Stage(0x927, 1, 2, 0, 0xb000))); // ATTR U8
    assert(!DecodeNativeStageBufferAccess(Stage(0x923, 1, 2, 0, 0x8000))); // output read
    assert(!DecodeNativeStageBufferAccess(Stage(0x923, 1, 2, 0, 0x0000))); // map read
    assert(!DecodeNativeStageBufferAccess(Stage(0x923, 1, 255, 0, 0x3000))); // PT/RZ sink read
    assert(!DecodeNativeStageBufferAccess(Stage(0x923, 1, 2, 0, 0x3000))); // U8 input read unimplemented
    assert(!DecodeNativeStageBufferAccess(Stage(0x923, 1, 2, 0, 0x7800))); // skew read not silently flattened
    assert(!DecodeNativeStageBufferAccess(Stage(0x927, 1, 2, 0, 0xf800))); // skew write not silently flattened
    assert(!DecodeNativeStageBufferAccess(Stage(0x927, 1, 2, 0, 0x9000))); // region 1
    assert(!DecodeNativeStageBufferAccess(Stage(0x927, 1, 2, 0, 0xb400))); // reserved bit
    assert(!DecodeNativeStageBufferAccess(Stage(0x999, 1, 2, 0, 0xb800)));

    // CSMTEST is structurally reviewed. Only the semantic lowerer may drop
    // both PT outputs; merely recognizing it in a probe is not a true result.
    Instruction csm{{0x80d, 0, 0x03fe0000U, 0}};
    const auto* csm_row = FindOpcodeRow(0x80d);
    assert(csm_row && FirstUnreviewedBit(csm, *csm_row) == -1);
    auto wrong_mode = csm;
    wrong_mode.words[2] |= (1U << 16);
    assert(FirstUnreviewedBit(wrong_mode, *csm_row) == 80);

    std::array<Instruction, 3> program{read, attr, csm};
    const auto* bytes = reinterpret_cast<const std::uint8_t*>(program.data());
    const auto probe = ProbeProgram(std::span<const std::uint8_t>(bytes, sizeof(program)));
    assert(probe.status == ProbeStatus::Recognized);
    assert(probe.recognized == program.size());
}
"""

compilers = [c for c in ("clang++", "g++") if shutil.which(c)]
if not compilers:
    raise SystemExit("No Clang/GCC C++ compiler found")
with tempfile.TemporaryDirectory(prefix="native-stage-buffer-") as d:
    source = Path(d, "test.cpp")
    source.write_text(CODE)
    for compiler in compilers:
        for optimization in ("-O0", "-O2"):
            binary = Path(d, "test")
            cmd = [
                compiler, "-std=c++20", optimization, "-Wall", "-Wextra",
                "-I" + str(AMPERE), "-I" + str(EDEN),
                str(source), str(PROBE), "-o", str(binary),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, timeout=90)
            subprocess.run([str(binary)], check=True, timeout=15)
            print(f"NS2_STAGE_BUFFER_PASS compiler={compiler} optimization={optimization}")
