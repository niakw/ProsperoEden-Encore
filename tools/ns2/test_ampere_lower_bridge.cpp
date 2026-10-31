// SPDX-License-Identifier: GPL-3.0-or-later
// Compile against the REAL upstream Ampere->Maxwell lowerer. This does not
// execute shaders, games, Vulkan commands, or PS5 native code.
#include <array>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "shader_recompiler/frontend/ampere/lower_bridge.h"

using namespace Shader::Ampere;
static void check(bool value, const char* why) {
    if (!value) {
        std::fprintf(stderr, "NS2 Ampere lowering FAIL: %s\n", why);
        std::exit(1);
    }
}
static void Emit(std::vector<u8>& dst, u32 word0, u32 word1 = 0,
                 u32 word2 = 0, u32 word3 = 0) {
    for (const u32 word : {word0, word1, word2, word3}) {
        for (unsigned b=0; b<4; ++b)
            dst.push_back(static_cast<u8>(word >> (b * 8)));
    }
}
int main() {
    constexpr u32 PredTrue = 7U << 12;
    constexpr u32 ExitCondTrue = 7U << 23;
    std::vector<u8> code;
    Emit(code, PredTrue | 0x918);                    // NOP
    Emit(code, PredTrue | 0x94d, 0, ExitCondTrue);   // EXIT
    const auto ok = LowerReviewedToMaxwell(code);
    check(ok.Ready() && ok.preflight.instructions == 2 &&
          ok.preflight.recognized == 2 && ok.preflight.control_flow == 1,
          "recognized NOP+EXIT really lowered through native Maxwell frontend");
    check(ok.consumed_native_bytes == code.size() &&
          ok.source_instruction_offsets.size() == 2 &&
          ok.maxwell_instructions.size() >= 2 &&
          ok.source_instruction_offsets[0] <= ok.source_instruction_offsets[1],
          "source offsets and complete input consumption survived lowering");
    check((ok.maxwell_instructions.back() & 0xff0000000000000fULL) ==
          (0xe30000000000000fULL & 0xff0000000000000fULL),
          "an actual Maxwell EXIT opcode was emitted");

    code.clear();
    Emit(code, PredTrue | 0x202 | (1U << 16), 2, 15U << 8); // MOV R1, R2
    Emit(code, PredTrue | 0x94d, 0, ExitCondTrue);
    const auto mov = LowerReviewedToMaxwell(code);
    check(mov.Ready() && mov.source_instruction_offsets.size() == 2 &&
          mov.maxwell_instructions.front() != 0 &&
          mov.maxwell_instructions.front() != ok.maxwell_instructions.front(),
          "real native MOV lowered into a non-NOP Maxwell move");

    code.resize(1);
    check(LowerReviewedToMaxwell(code).status == LowerBridgeStatus::InvalidInput,
          "partial native instruction rejected before parsing");
    code.clear();
    check(LowerReviewedToMaxwell(code).status == LowerBridgeStatus::InvalidInput,
          "empty shader rejected before lowering");
    code.resize((4096U + 1) * 16U);
    check(LowerReviewedToMaxwell(code).status == LowerBridgeStatus::InvalidInput,
          "hard 4096-instruction analysis bound enforced");

    code.clear();
    Emit(code, PredTrue | 0x202 | (1U << 16) | (1U << 24), 2, 15U << 8);
    Emit(code, PredTrue | 0x94d, 0, ExitCondTrue);
    const auto unknown_bits = LowerReviewedToMaxwell(code);
    check(unknown_bits.status == LowerBridgeStatus::UnreviewedFields &&
          unknown_bits.failed_native_byte_offset == 0 &&
          unknown_bits.maxwell_instructions.empty(),
          "unknown ISA fields must fail closed without fabricated output");

    u32 unknown_opcode = 0;
    while (unknown_opcode != 4096 && FindOpcodeRow(unknown_opcode))
        ++unknown_opcode;
    check(unknown_opcode != 4096, "ISA has deliberately unsupported opcodes");
    code.clear();
    Emit(code, PredTrue | unknown_opcode);
    Emit(code, PredTrue | 0x94d, 0, ExitCondTrue);
    const auto missing = LowerReviewedToMaxwell(code);
    check(missing.status == LowerBridgeStatus::UnrecognizedOpcode &&
          missing.maxwell_instructions.empty(),
          "unrecognized Ampere instruction never lowers via unknown fallback");

    code.clear();
    Emit(code, PredTrue | 0x918);
    const auto no_exit = LowerReviewedToMaxwell(code);
    check(no_exit.status == LowerBridgeStatus::UnsupportedSemantics &&
          no_exit.maxwell_instructions.empty() &&
          !no_exit.reason.empty(),
          "recognizable NOP is not a full executable without an EXIT");

    // An unknown NOP field is rejected before the lowerer sees it.
    code.clear();
    Emit(code, PredTrue | 0x918, 1);
    check(LowerReviewedToMaxwell(code).status == LowerBridgeStatus::UnreviewedFields,
          "extra unreviewed words cannot slip through translation");

    std::puts("NS2 Ampere->Maxwell lowering: PASS (host translation only)");
}
