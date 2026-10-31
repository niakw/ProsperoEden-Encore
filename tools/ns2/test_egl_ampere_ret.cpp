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
            result.instructions.back() != 0xe32000000007000fULL) {
            std::fprintf(stderr,
                "EGL_RET_N49_FAIL link=%u error=%.*s offset=%u consumed=%u expected=%zu last=0x%llx size=%zu\\n",
                link, static_cast<int>(result.error.size()), result.error.data(),
                result.error_offset, result.source_size, sizeof(code),
                static_cast<unsigned long long>(result.instructions.empty()
                    ? 0ULL : result.instructions.back()), result.instructions.size());
            return 1;
        }
    }
    const std::array<Instruction,5> copied{{
        {{0x00007802,0x20,0x00000f00,0}},
        {{0x00007944,0x10,0x03c00000,0}},
        {{0x0000794d,0,0x03800000,0}},
        {{0x00017202,0,0x00000f00,0}},
        {{0x01007950,0xffffffb0,0x03c3ffff,0}},
    }};
    const auto copy_result=LowerToMaxwell(copied);
    if (!copy_result) {
        std::fprintf(stderr, "EGL_RET_N49_COPY_FAIL error=%.*s at=%u\\n",
                     static_cast<int>(copy_result.error.size()), copy_result.error.data(),
                     copy_result.error_offset);
        return 2;
    }
    const std::array<Instruction,5> overwrite{{
        {{0x00007802,0x20,0x00000f00,0}},
        {{0x00007944,0x10,0x03c00000,0}},
        {{0x0000794d,0,0x03800000,0}},
        {{0x00007802,0,0x00000f00,0}},
        {{0x00007950,0xffffffb0,0x03c3ffff,0}},
    }};
    const auto bad=LowerToMaxwell(overwrite);
    if (bad || bad.error != "native callee overwrites link register" ||
        bad.error_offset != 0x30) {
        std::fprintf(stderr, "EGL_RET_N49_OVERWRITE_FAIL status=%d error=%.*s at=%u\\n",
                     static_cast<bool>(bad), static_cast<int>(bad.error.size()),
                     bad.error.data(), bad.error_offset);
        return 3;
    }
    std::puts("N49_EGLANTINE_RET_R0_REGRESSION_PASS host_lowerer=1");
}
