// SPDX-License-Identifier: GPL-3.0-or-later
// Host proof over the production Ampere high-GPR spill/rewrite owner.
// Only register descriptors differ; no per-title exception or GPU mock.
#include <array>
#include <cassert>
#include <cstdio>
#include <vector>
#include "shader_recompiler/frontend/ampere/register_pressure.h"
#include "shader_recompiler/frontend/ampere/lower_to_maxwell.h"

using namespace Shader::Ampere;
struct Fixture {
    u32 opcode;
    std::vector<u32> operands;
};
int main() {
    const std::vector<Fixture> fixtures{
        {0x919,{16}},             // S2R high destination
        {0x80b,{24}},            // predicate compare source
        {0x20b,{24,32}},         // register predicate compare
        {0x820,{16,24}},         // FMUL high destination/source
        {0x220,{16,24,32}},      // FMUL register multiplier (Lichii #56)
        {0x421,{16,24}},         // FADD with constant operand
        {0x208,{16,24,32}},      // bitwise/floating SEL
        {0x221,{16,24,32}},      // FADD register
        {0x817,{16,24}},         // IMNMX immediate, not word1 as GPR
        {0x223,{16,24,32,64}},   // FFMA has a third source
        {0x245,{16,32}},         // I2FP register input
        {0x823,{16,24,64}},      // FFMA other source mode
        {0x381,{16,24}},         // LDG.E register address pair
        {0x386,{24,32}},         // STG.E register data and address pair
        {0x981,{16,24}},         // uniform-address LDG
        {0x986,{24,32}},         // uniform-address STG
        {0x3a8,{16,24,32}},     // GPR-address ATOMG old value, address pair
        {0x9a8,{16,32}},        // uniform-pointer ATOMG high data/output
    };
    for (const auto& fixture : fixtures) {
        Instruction original{{fixture.opcode | (252U<<16) | (248U<<24),
                              252U, 248U, 0U}};
        const auto translated = PrepareRegisterPressure(original, 216);
        assert(translated.valid);
        assert(!translated.prefix.empty());
        assert(translated.prefix.size() == translated.suffix.size());
        assert(translated.prefix.size() % 8U == 0);
        std::array<u32,4> masks{};
        for (const u32 field : fixture.operands) {
            masks[field / 32] |= 255U << (field % 32);
            const u32 before = original.Bits(field,8);
            const u32 after = translated.instruction.Bits(field,8);
            assert(before >= 216 && before < 255);
            assert(after < 216);
            assert((after & 3U) == (before & 3U));
        }
        for (u32 i=0;i<4;++i)
            assert((translated.instruction.words[i] & ~masks[i]) ==
                   (original.words[i] & ~masks[i]));
        // A non-high GPR instruction must not create any scratch traffic.
        Instruction low=original;
        for (const u32 field:fixture.operands)
            low.words[field/32] = (low.words[field/32] &
                   ~(255U << (field%32))) | (u32{32} << (field%32));
        const auto untouched=PrepareRegisterPressure(low,216);
        assert(untouched.valid && untouched.prefix.empty() &&
               untouched.suffix.empty());
    }
    // Test an actual captured Ampere load with high GPRs under the
    // native Maxwell scratch limit (the default no-uniform limit is 250).
    constexpr Instruction UniformMarker{{0x00007918,0,0,0x000fea00}};
    constexpr Instruction Exit{{0x0000794d,0,0x03800000,0x000fea00}};
    const std::array captured{
        UniformMarker,
        Instruction{{0x46fa7381,0x00003000,0x001e8900,0x00013400}},
        Exit
    };
    const auto lowered=LowerToMaxwell(captured,{},true);
    if (!lowered) std::fprintf(stderr,"Captured LDG lowerer refused: %.*s\n",
                                static_cast<int>(lowered.error.size()), lowered.error.data());
    assert(lowered && !lowered.instructions.empty() &&
           lowered.source_instruction_offsets.size()==captured.size());
    assert(lowered.source_instruction_offsets[2] >= 17); // prefix + LDG + suffix
    // An aligned high-register quartet can be borrowed safely.
    Instruction aligned{{0x381U | (220U<<16) | (32U<<24),
                         0U,6U<<9,0U}};
    const auto aligned_result = PrepareRegisterPressure(aligned,216);
    assert(aligned_result.valid && !aligned_result.prefix.empty());
    assert(aligned_result.instruction.Bits(16,8) < 216);
    // A vector encoded by one base register must not span from a low
    // register into a borrowed high quartet. Nor can two non-contiguous
    // high scratch quartets masquerade as one contiguous register vector.
    Instruction straddles_reserved{{0x381U | (215U<<16) | (32U<<24),
                                   0U,5U<<9,0U}};
    Instruction straddles_borrowed{{0x381U | (219U<<16) | (32U<<24),
                                   0U,5U<<9,0U}};
    assert(NativeVectorCrossesScratch(straddles_reserved,216));
    assert(!PrepareRegisterPressure(straddles_reserved,216).valid);
    assert(!PrepareRegisterPressure(straddles_borrowed,216).valid);
    // Exercise the real lowerer, whose default no-uniform scratch boundary
    // is 248, not the synthetic 216 used by the standalone spill fixture.
    // A low vector base must never escape the scalar pre-check.
    Instruction straddles_runtime{{0x381U | (247U<<16) | (32U<<24),
                                   0U,5U<<9,0U}};
    assert(NativeVectorCrossesScratch(straddles_runtime,248));
    const std::array crossing_program{UniformMarker,straddles_runtime,Exit};
    const auto crossing_lowered=LowerToMaxwell(crossing_program,{},true);
    assert(!crossing_lowered &&
           crossing_lowered.error == "native register shadowing mode");
    // Vector loads must reject an overflowing high-register quartet.
    Instruction overflowing{{0x381U | (252U<<16) | (248U<<24),
                             0U,6U<<9,0U}};
    assert(!PrepareRegisterPressure(overflowing,216).valid);
    // A native global atomic must never read the synthetic Maxwell
    // uniform-bank scratch register as its GPR source. An atomically
    // shadowed 32-bit data value and destination are borrowed to low
    // aligned quartets, with the original registers restored afterward.
    // Covers both the true register address pair and uniform pointer
    // forms. No per-game or per-shader exception is used.
    constexpr Instruction AtomGpr{{
        0x3a8U | (7U << 12) | (244U << 16) | (250U << 24),
        252U,
        0x001ee100U,
        0U
    }};
    constexpr Instruction AtomUniform{{
        0x9a8U | (7U << 12) | (244U << 16) | (255U << 24),
        240U,
        0x081ee140U | 2U,
        0U
    }};
    for (const auto atom : {AtomGpr, AtomUniform}) {
        const bool uniform_pointer = atom.Bits(0,12) == 0x9a8;
        const u32 boundary = uniform_pointer ? 216U : 248U;
        const auto pressure = PrepareRegisterPressure(atom, boundary);
        assert(pressure.valid && !pressure.prefix.empty() &&
               pressure.prefix.size() == pressure.suffix.size());
        assert(pressure.instruction.Bits(16,8) < boundary);
        assert(pressure.instruction.Bits(32,8) < boundary);
        if (uniform_pointer) {
            assert(pressure.instruction.Bits(64,6) == 2);
        } else {
            assert(pressure.instruction.Bits(24,8) < boundary);
            assert((pressure.instruction.Bits(24,8) & 1U) == 0);
            assert(!NativeVectorCrossesScratch(pressure.instruction,boundary));
        }
        const std::array program{UniformMarker,atom,Exit};
        const auto lowered=LowerToMaxwell(program,{},true);
        if (!lowered)
            std::fprintf(stderr,"Atomic lowering refused: %.*s at %#x\n",
                static_cast<int>(lowered.error.size()),lowered.error.data(),
                lowered.error_offset);
        assert(lowered && lowered.source_size == sizeof(program));
        const auto begin=lowered.source_instruction_offsets[1];
        const auto end=lowered.source_instruction_offsets[2];
        assert(end > begin+pressure.prefix.size() &&
               end >= begin+pressure.prefix.size()+pressure.suffix.size()+1);
        assert(std::equal(pressure.prefix.begin(), pressure.prefix.end(),
                          lowered.instructions.begin()+begin));
        const u64 actual_atom=lowered.instructions[begin+pressure.prefix.size()];
        assert((actual_atom & 0xff00000000000000ULL)==0xed00000000000000ULL);
        assert((actual_atom & 0xffU)==pressure.instruction.Bits(16,8));
        assert(((actual_atom>>20)&0xffU)==pressure.instruction.Bits(32,8));
        assert(std::equal(pressure.suffix.begin(), pressure.suffix.end(),
                          lowered.instructions.begin()+end-pressure.suffix.size()));
        const auto refusal=LowerToMaxwell(program,{},false);
        assert(!refusal && refusal.error=="native program uses lowering scratch registers");
    }
    // GPR-address atomic pointer must be genuinely even/aligned, not
    // misrepresented as a register pair crossing an unsupported operand.
    auto odd_address=AtomGpr;
    odd_address.words[0] = (odd_address.words[0] & 0x00ffffffU) | (249U << 24);
    const auto odd=LowerToMaxwell(std::array{UniformMarker,odd_address,Exit},{},true);
    assert(!odd);
    assert(odd.error == "native global register atomic mode" ||
           odd.error == "native register shadowing mode");
    // U62 is the final real uniform word; U63 represents zero, not its
    // adjacent high pointer half. Never use U47's physical GPR as U63.
    auto last_uniform=AtomUniform;
    last_uniform.words[2] = (last_uniform.words[2] & ~0x3fU) | 62U;
    const auto rejected_last=LowerToMaxwell(std::array{UniformMarker,last_uniform,Exit},{},true);
    assert(!rejected_last && rejected_last.error=="native global atomic mode");
    // An odd uniform pointer is equally unrepresentable as an aligned
    // 64-bit guest pointer for a native Maxwell atom.
    last_uniform.words[2] = (last_uniform.words[2] & ~0x3fU) | 61U;
    const auto rejected_odd=LowerToMaxwell(std::array{UniformMarker,last_uniform,Exit},{},true);
    assert(!rejected_odd && rejected_odd.error=="native global atomic mode");
    // The two words of a low register address may straddle an aligned
    // scratch limit in a synthetic case. Detect before rewriting the
    // base register without guaranteeing contiguous physical operands.
    Instruction straddles_atomic{{0x3a8U | (4U<<16) | (248U<<24),240U,0x001ee100U,0U}};
    assert(NativeVectorCrossesScratch(straddles_atomic,249));
    std::puts("P2_4_AMPERE_REGISTER_PRESSURE_PASS high_gpr=18 opcode_families "
              "atomic_global_gpr=1 atomic_uniform_pointer=1 uniform_u62_refused=1 ns1_unchanged=1");
}
