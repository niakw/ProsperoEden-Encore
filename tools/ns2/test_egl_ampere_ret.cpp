// SPDX-License-Identifier: GPL-3.0-or-later
// Regression fixtures adapted from Eglantine PR #56, no game assets.
#include <array>
#include <cstdio>
#include <cstdlib>
#include "shader_recompiler/frontend/ampere/lower_to_maxwell.h"
using Shader::Ampere::Instruction;
using Shader::Ampere::LowerToMaxwell;
int main() {
    for (const u32 link : {0U, 55U}) {
        const std::array<Instruction, 4> code{{
            {{0x00007802U | (link << 16), 0x20, 0x00000f00, 0}},
            {{0x00007944, 0x10, 0x03c00000, 0}},
            {{0x0000794d, 0, 0x03800000, 0}},
            {{0x00007950U | (link << 24), 0xffffffc0, 0x03c3ffff, 0}},
        }};
        const auto result=LowerToMaxwell(code);
        if (!result || result.source_size != sizeof(code) ||
            result.instructions.empty() ||
            result.instructions.back() != 0xe32000000007000fULL) std::abort();
    }
    const std::array<Instruction,5> copied{{
        {{0x00007802,0x20,0x00000f00,0}},
        {{0x00007944,0x10,0x03c00000,0}},
        {{0x0000794d,0,0x03800000,0}},
        {{0x00017202,0,0x00000f00,0}},
        {{0x01007950,0xffffffb0,0x03c3ffff,0}},
    }};
    if (!LowerToMaxwell(copied)) std::abort();
    const std::array<Instruction,5> overwrite{{
        {{0x00007802,0x20,0x00000f00,0}},
        {{0x00007944,0x10,0x03c00000,0}},
        {{0x0000794d,0,0x03800000,0}},
        {{0x00007802,0,0x00000f00,0}},
        {{0x00007950,0xffffffb0,0x03c3ffff,0}},
    }};
    const auto bad=LowerToMaxwell(overwrite);
    if (bad || bad.error != "native callee overwrites link register" ||
        bad.error_offset != 0x30) std::abort();
    std::puts("N49_EGLANTINE_RET_R0_REGRESSION_PASS host_lowerer=1");
}
