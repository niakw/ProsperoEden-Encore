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
static Instruction UniformSel(u32 opcode, u32 dest, u32 source_a, u32 source_b) {
    // The 0xc07 variant encodes a uniform source B (UR0..UR62 or UR63=RZ).
    return Instruction{{(7U << 12) | opcode | (dest << 16) | (source_a << 24),
                        source_b, 7U << 23, 0x000fe200U}};
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
    // P2.4: SEL's uniform-B form (0xc07) is decoded by the same scalar
    // ALU owner as register SEL (0x207), not a shader-wide replacement.
    for (const auto [ureg, expected_gpr] :
         std::array<std::pair<u32,u32>, 3>{{{4,220},{17,201},{63,255}}}) {
        const auto select=UniformSel(0xc07,5,6,ureg);
        Require(Reviewed(select), "uniform SEL must pass the original ISA table");
        const auto bridge=Bridge(select);
        Require(bridge.Ready(), bridge.reason.data());
        const u64 word=bridge.maxwell_instructions[bridge.source_instruction_offsets[0]];
        Require((word>>56)==0x5c && (word&255)==5,
                "Maxwell SEL reused, destination retained");
        Require(((word>>8)&255)==6, "SEL direct source A preserved");
        Require(((word>>20)&255)==expected_gpr,
                "SEL uniform-B operand mapped to the protected register bank");
    }
    const auto bad_ureg=UniformSel(0xc07,5,6,64);
    Require(!Bridge(bad_ureg).Ready(), "out-of-table uniform source must fail closed");
    const auto alias=UniformSel(0xc07,220,6,4);
    Require(!Bridge(alias).Ready(), "uniform bank cannot alias a high output GPR");
    const auto reg_sel=UniformSel(0x207,5,6,8);
    Require(Bridge(reg_sel).Ready(), "normal scalar SEL remains functional");
    // Uniform FSET (0xc0a) uses the same actual bank owner as uniform SEL,
    // but must keep its own float-comparison opcode, operation and predicate.
    for (const auto [ureg, expected_gpr] :
         std::array<std::pair<u32,u32>,3>{{{4,220},{17,201},{63,255}}}) {
        const auto compare=UniformSel(0xc0a,5,6,ureg);
        Require(Reviewed(compare), "uniform FSET fields admitted by reviewed ISA");
        const auto bridge=Bridge(compare);
        Require(bridge.Ready(), bridge.reason.data());
        const u64 word=bridge.maxwell_instructions[bridge.source_instruction_offsets[0]];
        Require((word>>56)==0x58 && (word&255)==5,
                "uniform FSET uses Maxwell floating comparison, destination preserved");
        Require(((word>>8)&255)==6, "FSET direct source A preserved");
        Require(((word>>20)&255)==expected_gpr,
                "FSET uniform B mapped into the protected UR register bank");
    }
    Require(!Bridge(UniformSel(0xc0a,5,6,64)).Ready(),
            "invalid FSET uniform register cannot compile");
    Require(!Bridge(UniformSel(0xc0a,220,6,4)).Ready(),
            "FSET uniform bank must not overwrite high destination");
    auto bad_mode=UniformSel(0xc0a,5,6,4);
    bad_mode.words[2] |= 3U << 10; // invalid floating operation selection
    Require(!Bridge(bad_mode).Ready(), "unreviewed FSET operation refused");
    Require(Bridge(UniformSel(0x20a,5,6,8)).Ready(),
            "ordinary FSET regression guard");
    // Immediate MUFU 0x908 is decoded as operand(1) using the same
    // floating-point operation path as the register and uniform variants.
    // Prove the emitted Maxwell instruction uses a materialized source,
    // rather than treating the 32-bit immediate as an uninitialized GPR.
    const auto immediate_mufu=[](u32 bits, u32 operation=2) {
        return Instruction{{(7U << 12) | 0x908 | (5U << 16), bits,
                            operation << 10, 0x000fe200U}};
    };
    const auto mufu=immediate_mufu(0x3f800000U);
    Require(Reviewed(mufu), "immediate MUFU admitted by native ISA table");
    const auto lowered_mufu=Bridge(mufu);
    Require(lowered_mufu.Ready(), lowered_mufu.reason.data());
    bool has_mufu=false;
    for (const u64 word:lowered_mufu.maxwell_instructions) {
        if ((word>>52)==0x508) {
            Require(((word>>8)&255)==251, "immediate MUFU must use materialized operand R251");
            Require(((word>>20)&255)==2, "MUFU operation selector must survive lowering");
            has_mufu=true;
        }
    }
    Require(has_mufu && lowered_mufu.maxwell_instructions.size()>=3,
            "immediate materialization followed by real Maxwell MUFU");
    const auto other_mufu=Bridge(immediate_mufu(0x40000000U));
    Require(other_mufu.Ready() &&
            other_mufu.maxwell_instructions!=lowered_mufu.maxwell_instructions,
            "MUFU immediate bytes must affect the generated Maxwell program");
    auto bad_mufu=immediate_mufu(0x3f800000U);
    bad_mufu.words[0]|=3U<<24; // illegal source A for immediate form
    Require(!Bridge(bad_mufu).Ready(), "MUFU immediate source A must be empty");
    bad_mufu=immediate_mufu(0x3f800000U);
    bad_mufu.words[2]|=1U<<16; // unknown modifier, forbidden by ISA/mode
    Require(!Bridge(bad_mufu).Ready(), "MUFU immediate modifier rejected");
    bad_mufu=immediate_mufu(0x3f800000U,7); // unsupported hardware function mode
    Require(!Bridge(bad_mufu).Ready(), "MUFU unsupported operation rejected");
    // UPOPC: read a uniform GPR and write the uniform destination, using
    // the real front end, actual ISA masks and Maxwell opcode bits.
    const auto uniform_popc=[](u32 dest, u32 src, bool invert=false) {
        return Instruction{{(7U << 12) | 0x2bf | (dest << 16),
                            src | (invert ? 0x80000000U : 0U),
                            0x08000000U, 0x000fe200U}};
    };
    for (const auto [rd,ra,dst_gpr,src_gpr] :
         std::array<std::array<u32,4>,4>{{{{5,4,221,220}},{{17,18,201,202}},
                                           {{62,63,182,255}},{{8,16,224,200}}}}) {
        const auto insn=uniform_popc(rd,ra);
        Require(Reviewed(insn), "uniform POPC must pass reviewed ISA masks");
        const auto bridge=Bridge(insn);
        Require(bridge.Ready(), bridge.reason.data());
        const u64 word=bridge.maxwell_instructions[bridge.source_instruction_offsets[0]];
        Require((word & 0xff000000000f0000ULL) ==
                (0x5c08000000070000ULL & 0xff000000000f0000ULL),
                "uniform POPC maps to genuine Maxwell population count");
        Require((word & 255)==dst_gpr && ((word>>20)&255)==src_gpr,
                "uniform POPC source and destination use the reserved UR bank");
    }
    const auto inverted=Bridge(uniform_popc(5,4,true));
    Require(inverted.Ready() &&
            ((inverted.maxwell_instructions[inverted.source_instruction_offsets[0]]>>40)&1U)==1,
            "uniform POPC inversion bit preserved");
    Require(!Bridge(uniform_popc(63,4)).Ready(), "UR63 cannot be written");
    Require(!Bridge(uniform_popc(5,64)).Ready(), "out-of-table uniform source rejected");
    auto predicated_popc=uniform_popc(5,4);
    predicated_popc.words[0]=(predicated_popc.words[0]&~0xf000U)|(1U<<12);
    Require(!Bridge(predicated_popc).Ready(), "unrepresentable UPOPC predication rejected");
    auto reserved_popc=uniform_popc(5,4);
    reserved_popc.words[1]|=1U<<30;
    Require(!Bridge(reserved_popc).Ready(), "unreviewed UPOPC source mode rejected");
    std::puts("P2_4_REAL_AMPERE_SCALAR_ALU_SOURCE_PASS");
}
