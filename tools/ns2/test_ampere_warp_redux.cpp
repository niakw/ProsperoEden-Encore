// SPDX-License-Identifier: GPL-3.0-or-later
// Execute the maintained native Ampere->Maxwell owner for reviewed REDUX.
// Synthetic source only; no claim of Vulkan execution or PS5 images.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdio>
#include <string_view>

#include "shader_recompiler/frontend/ampere/lower_to_maxwell.h"
#include "shader_recompiler/frontend/ampere/register_pressure.h"
#include "shader_recompiler/frontend/ampere/probe.h"

using namespace Shader::Ampere;
constexpr Instruction Nop{{0x00007918U,0,0,0x000fea00U}};
constexpr Instruction Exit{{0x0000794dU,0,0x03800000U,0x000fea00U}};

static Instruction Redux(u32 mode, u32 source = 32, u32 uniform_dest = 2,
                         u32 pred = 7) {
    return {{{0x3c4U | (pred << 12) | (uniform_dest << 16) | (source << 24),
               0U, mode, 0U}}};
}

static LoweredProgram Lower(Instruction redux, bool spill=true) {
    const std::array shader{Nop, redux, Exit};
    return LowerToMaxwell(shader, {}, spill);
}

int main() {
    // All existing and newly reviewed modes must decode without guessing.
    for (u32 mode : {0xc000U, 0x4000U, 0x8000U, 0x10000U, 0x14000U,
                     0x10200U, 0x14200U}) {
        const auto op=Redux(mode);
        const auto* isa=FindOpcodeRow(0x3c4);
        assert(isa && FirstUnreviewedBit(op,*isa)==-1);
        const auto lowered=Lower(op);
        if (!lowered)
            std::fprintf(stderr, "REDUX=%#x refused: %.*s\n",mode,
                static_cast<int>(lowered.error.size()),lowered.error.data());
        assert(lowered && lowered.source_size == 3 * sizeof(Instruction));
        assert(lowered.source_instruction_offsets.size() == 3);
    }
    // Signed ordering transforms 32 lane operands AND their final result:
    // XOR 0x80000000 converts signed order into unsigned order exactly.
    for (u32 plain : {0x10000U, 0x14000U}) {
        const auto unsigned_code=Lower(Redux(plain));
        const auto signed_code=Lower(Redux(plain | 0x200U));
        assert(unsigned_code && signed_code);
        const u32 ub=unsigned_code.source_instruction_offsets[1];
        const u32 ue=unsigned_code.source_instruction_offsets[2];
        const u32 sb=signed_code.source_instruction_offsets[1];
        const u32 se=signed_code.source_instruction_offsets[2];
        assert(se-sb == ue-ub+33); // 32 per-lane sign XOR + final XOR
        const u64 lane_sign=0x0400000000070000ULL | 251U |
            (u64{251} << 8) | (u64{0x80000000U} << 20) | (u64{2} << 53);
        const u32 count=static_cast<u32>(std::count(
            signed_code.instructions.begin()+sb,
            signed_code.instructions.begin()+se,lane_sign));
        assert(count == 32);
        const u64 final_sign=0x0400000000070000ULL | 218U |
            (u64{218} << 8) | (u64{0x80000000U} << 20) | (u64{2} << 53);
        assert(signed_code.instructions[se-1]==final_sign);
    }
    // REDUX.XOR is not a substitute for OR. Both must emit Maxwell's
    // actual logical reduction mode, with different LOP selector bits.
    const auto logical_or=Lower(Redux(0x4000U));
    const auto logical_xor=Lower(Redux(0x8000U));
    assert(logical_or && logical_xor);
    const u64 low_or=0x5c40000000070000ULL | 218U |
        (u64{218} << 8) | (u64{251} << 20) |
        (u64{1} << 41) | (u64{7} << 48);
    const u64 low_xor=0x5c40000000070000ULL | 218U |
        (u64{218} << 8) | (u64{251} << 20) |
        (u64{2} << 41) | (u64{7} << 48);
    assert(std::count(logical_or.instructions.begin(),
                      logical_or.instructions.end(),low_or)==32);
    assert(std::count(logical_xor.instructions.begin(),
                      logical_xor.instructions.end(),low_xor)==32);
    // An extended uniform bank reserves more scratch. The real REDUX
    // source remains a GPR and must survive spill/restore uncorrupted.
    const Instruction high=Redux(0x14200U,244U,18U);
    const auto pressure=PrepareRegisterPressure(high,168U);
    assert(pressure.valid && !pressure.prefix.empty());
    assert(pressure.instruction.Bits(24,8) < 168);
    const auto lowered_high=Lower(high);
    if (!lowered_high)
        std::fprintf(stderr,"REDUX high refused: %.*s\n",
                     static_cast<int>(lowered_high.error.size()),
                     lowered_high.error.data());
    assert(lowered_high);
    const u32 first=lowered_high.source_instruction_offsets[1];
    const u32 last=lowered_high.source_instruction_offsets[2];
    assert(std::equal(pressure.prefix.begin(),pressure.prefix.end(),
                      lowered_high.instructions.begin()+first));
    assert(std::equal(pressure.suffix.begin(),pressure.suffix.end(),
                      lowered_high.instructions.begin()+last-pressure.suffix.size()));
    assert(!Lower(high,false) &&
           Lower(high,false).error=="native program uses lowering scratch registers");
    // Unknown modes may not silently execute a different reduction.
    for (u32 unsupported : {0x200U,0xc200U,0x4200U,0x8200U,0x18000U,
                            0x16000U,0x10201U,0xffffffffU}) {
        auto rejected=Lower(Redux(unsupported));
        assert(!rejected && rejected.error=="native warp sum mode");
    }
    assert(!Lower(Redux(0x10000U,255U)));
    assert(!Lower(Redux(0x10000U,32U,63U)));
    assert(!Lower(Redux(0x10000U,32U,2U,6U)));
    auto bad_word=Redux(0x10000U);
    bad_word.words[1]=1;
    assert(!Lower(bad_word));
    std::puts("P2_4_REDux_REAL_AMPERE_LOWER_PASS signed_minmax=2 xor=1"
              " high_gpr_shadow=1 spill_restore=1 invalid_modes=8 ns1_unmodified=1");
}
