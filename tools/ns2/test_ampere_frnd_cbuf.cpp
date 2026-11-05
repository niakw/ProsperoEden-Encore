// SPDX-License-Identifier: GPL-3.0-or-later
// P2.4: actual Ampere -> Maxwell lowering, without a game or fake renderer.
#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include "shader_recompiler/frontend/ampere/lower_to_maxwell.h"
#include "shader_recompiler/frontend/ampere/probe.h"
#include "shader_recompiler/frontend/ampere/lower_bridge.h"

using namespace Shader::Ampere;
constexpr Instruction Exit{{0x0000794dU, 0, 0x03800000U, 0x000fea00U}};

static Instruction Frnd(u32 op, u32 dest, u32 src, u32 bank = 0) {
    return Instruction{{(7U << 12) | op | (dest << 16),
                        op == 0xb07 ? (src << 6) | (bank << 22) : src,
                        (2U << 11) | (2U << 20), 0x000fe200U}};
}
static LoweredProgram Lower(const Instruction& inst) {
    const std::array code{inst, Exit};
    return LowerToMaxwell(code);
}
static bool Reviewed(const Instruction& inst) {
    const auto* row = FindOpcodeRow(inst.Bits(0,12));
    return row && FirstUnreviewedBit(inst,*row) < 0;
}
static std::array<u8, 2 * sizeof(Instruction)> Encode(const Instruction& inst) {
    std::array<u8, 2 * sizeof(Instruction)> bytes{};
    const std::array code{inst, Exit};
    for (u32 i = 0; i < code.size(); ++i)
        for (u32 word = 0; word < 4; ++word)
            for (u32 byte = 0; byte < 4; ++byte)
                bytes[i * sizeof(Instruction) + word * 4 + byte] =
                    static_cast<u8>(code[i].words[word] >> (byte * 8));
    return bytes;
}
static LowerBridgeResult Bridge(const Instruction& inst) {
    const auto bytes=Encode(inst);
    return LowerReviewedToMaxwell(bytes);
}
static void Require(bool pass, const char* why) {
    if (!pass) {
        std::fprintf(stderr,"NS2 native FRND CBUF FAIL: %s\n", why);
        std::exit(1);
    }
}
int main() {
    for (const auto [bank, offset] : std::array<std::pair<u32,u32>, 3>{
            {{0,4},{7,508},{17,65532}}}) {
        const auto inst=Frnd(0xb07,5,offset,bank);
        Require(Reviewed(inst), "CBUF source must be admitted by actual ISA field table");
        const auto lowered=Lower(inst);
        Require(bool(lowered), lowered.error.data());
        Require(lowered.source_instruction_offsets.size()==2, "two input offsets");
        const u64 word=lowered.instructions[lowered.source_instruction_offsets[0]];
        Require((word >> 56)==0x4c, "Maxwell FRND CBUF opcode");
        Require((word & 255)==5, "destination register retained");
        Require(((word>>20)&0x3fff)==offset/4, "constant byte offset converted to words");
        Require(((word>>34)&0x1f)==bank, "constant buffer bank retained");
        const auto reviewed=Bridge(inst);
        Require(reviewed.Ready(), reviewed.reason.data());
        Require(reviewed.preflight.recognized==2 &&
                reviewed.consumed_native_bytes==2*sizeof(Instruction) &&
                reviewed.maxwell_instructions[reviewed.source_instruction_offsets[0]]==word,
                "renderer bridge accepts the reviewed CBUF semantics, no private lowerer path");
    }
    const auto register_form=Frnd(0x307,5,22);
    Require(Reviewed(register_form), "GPR source still accepted by ISA table");
    const auto original=Lower(register_form);
    Require(bool(original), original.error.data());
    const u64 gpr_word=original.instructions[original.source_instruction_offsets[0]];
    Require((gpr_word>>56)==0x5c, "native register FRND unchanged");
    Require(((gpr_word>>20)&255)==22, "native register source unchanged");
    Require(Bridge(register_form).Ready(), "normal FRND remains accepted in the full bridge");

    for (const auto invalid : {Frnd(0xb07,5,1,7), // unaligned offset
                              Frnd(0xb07,5,4,18), // descriptor beyond supported stage slots
                              Frnd(0xb07,5,4,31)}) {
        Require(!Lower(invalid), "invalid CBUF rejected, not reinterpreted as a GPR");
        Require(Bridge(invalid).status==LowerBridgeStatus::UnsupportedSemantics,
                "bridge rejects invalid CBUF with explicit unsupported semantics");
    }
    auto bad_round=Frnd(0xb07,5,4,7);
    bad_round.words[2] ^= 1U << 11;
    Require(!Lower(bad_round), "unreviewed floating mode still refused");
    Require(!Bridge(bad_round).Ready(), "real bridge rejects invalid FRND mode");
    std::puts("P2_4_REAL_FRND_CBUF_LOWER_PASS");
}
