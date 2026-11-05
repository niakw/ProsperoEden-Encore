// SPDX-License-Identifier: GPL-3.0-or-later
// Source-level cross-repo regressions: Ampere 128-bit ISA -> shared Maxwell
// lowerer. No game-specific title or fake framebuffer, no PS5 GPU assertions.
#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <tuple>
#include <vector>
#include "shader_recompiler/frontend/ampere/lower_to_maxwell.h"
#include "shader_recompiler/frontend/ampere/lower_bridge.h"
#include "shader_recompiler/frontend/ampere/probe.h"

using namespace Shader::Ampere;
static constexpr Instruction Exit{{0x0000794d, 0, 0x03800000, 0x000fea00}};
static constexpr Instruction UniformClamp{{0x3f057499, 0xffffffff, 0x08010604, 0x000fe200}};
static constexpr Instruction UniformWrap{{0x3f057499, 1, 0x08010e04, 0x000fc800}};
static constexpr Instruction SurfaceReduction{{0x0500759f, 0x20c00206, 0x0010e000, 0x000fe200}};
static constexpr Instruction BindlessLoad{{0x10007998, 0x60000000, 0x001e0f1d, 0x010f6600}};
static constexpr Instruction BindlessStore{{0x0200799c, 0x60000004, 0x00100f00, 0x004fe200}};
static constexpr Instruction FullIntegerMinMax{{0x0b037817, 0x1fffffff, 0x03800000, 0x001fc800}};

static LoweredProgram Lower(const Instruction& insn) {
    return LowerToMaxwell(std::array{insn, Exit});
}
static std::array<u8, 2 * sizeof(Instruction)> Bytes(const Instruction& insn) {
    std::array<u8, 2 * sizeof(Instruction)> bytes{};
    for (unsigned i = 0; i < 4; ++i) {
        for (unsigned j = 0; j < 4; ++j) {
            bytes[i * 4 + j] = static_cast<u8>(insn.words[i] >> (j * 8));
            bytes[16 + i * 4 + j] = static_cast<u8>(Exit.words[i] >> (j * 8));
        }
    }
    return bytes;
}
static ProgramProbe Probe(const Instruction& insn) { return ProbeProgram(Bytes(insn)); }
int main() {
    // Shader probe and actual lowerer must agree. A private opcode accepted
    // only by LowerToMaxwell would never enter the actual renderer pipeline.
    assert(FindOpcodeRow(0x499) != nullptr);
    assert(FindOpcodeRow(0x59f) != nullptr);
    for (const Instruction insn : {UniformClamp, UniformWrap}) {
        const auto probe = Probe(insn);
        assert(probe.status == ProbeStatus::Recognized);
        const auto result = Lower(insn);
        assert(result && result.source_size == 32 && result.instructions.size() == 3);
        assert(result.instructions[0] ==
            (insn.words[1] == 1 ? 0x010000000017f0faULL : 0x010ffffffff7f0faULL));
        assert(result.instructions[1] ==
            (insn.words[1] == 1 ? 0x5c4800800dc7faddULL : 0x5c4800000dc7faddULL));
        const u64 shift_word = result.instructions[1];
        assert((shift_word & 255U) == 221U); // UR5 maps to GPR221
        assert(((shift_word >> 8) & 255U) == 250U);
        assert(((shift_word >> 20) & 255U) == 220U); // UR4
        assert(((shift_word >> 39) & 1U) == (insn.Bits(75, 1)));
    }
    // Execute the actual encoded operands against the two observed ISA
    // modes. An instruction with a wrongly mapped GPR/mode is caught even if
    // its textual source describes the right operation.
    for (const Instruction insn : {UniformClamp, UniformWrap}) {
        const auto lowered = Lower(insn);
        const u64 op = lowered.instructions[1];
        const u32 dest_reg = op & 255U;
        const u32 immediate_reg = (op >> 8) & 255U;
        const u32 shift_reg = (op >> 20) & 255U;
        const bool wraps = (op >> 39) & 1U;
        for (const u32 amount : {0U,1U,31U,32U,33U,63U,64U,0xffffffffU}) {
            std::array<u32,256> regs{};
            regs[immediate_reg] = insn.words[1];
            regs[shift_reg] = amount;
            regs[dest_reg] = wraps
                ? (regs[immediate_reg] << (regs[shift_reg] & 31))
                : (regs[shift_reg] < 32
                    ? (regs[immediate_reg] << regs[shift_reg]) : 0U);
            const u32 expected = wraps || amount < 32
                ? static_cast<u32>(u64{insn.words[1]} << (amount & 31))
                : 0U;
            assert(regs[dest_reg] == expected);
        }
    }
    for (const Instruction original : {UniformClamp, UniformWrap}) {
        for (const auto& [word, bit] : std::array{
            std::pair{0U, 24U}, std::pair{2U, 8U}, std::pair{2U, 9U},
            std::pair{2U, 12U}, std::pair{2U, 16U}, std::pair{2U, 27U},
            std::pair{3U, 0U}, std::pair{3U, 30U}}) {
            auto invalid = original;
            invalid.words[word] ^= 1U << bit;
            assert(!Lower(invalid));
        }
        auto bad_uniform = original;
        bad_uniform.words[2] = (bad_uniform.words[2] & ~255U) | 64U;
        assert(!Lower(bad_uniform));
        auto discard = original;
        discard.words[0] = (discard.words[0] & ~0xff0000U) | (63U << 16);
        assert(!Lower(discard));
    }
    // Native register-handle images may use any valid 2D/array/3D
    // dimension; never bind a synthetic direct CBUF/TIC descriptor.
    struct SurfaceCase { Instruction instruction; u64 expected; };
    for (const auto& test : std::array{
            SurfaceCase{BindlessLoad, 0xeb000e8600f71000ULL},
            SurfaceCase{BindlessStore, 0xeb20000600f70204ULL},
            SurfaceCase{Instruction{{0x00037998, 0xa0000000, 0x001e0119, 0x010f6200}},
                        0xeb000c8a00170003ULL},
            SurfaceCase{Instruction{{0x0000799c, 0xa0000004, 0x00100f03, 0x0101e200}},
                        0xeb20018a00f70004ULL},
            SurfaceCase{Instruction{{0x0000799c, 0x8000000c, 0x00100f07, 0x0041e200}},
                        0xeb20038800f7000cULL}
         }) {
        assert(Probe(test.instruction).status == ProbeStatus::Recognized);
        const auto result = Lower(test.instruction);
        assert(result && result.instructions.size() == 2);
        assert(result.instructions.front() == test.expected);
        assert(result.required_texture_buffer == ~0U);
    }
    for (const Instruction original : {BindlessLoad, BindlessStore}) {
        auto guarded = original;
        guarded.words[0] = (guarded.words[0] & ~0xf000U) | 0x9000U;
        const auto plain = Lower(original);
        const auto predicated = Lower(guarded);
        assert(plain && predicated);
        assert(predicated.instructions.front() ==
               ((plain.instructions.front() & ~(u64{0xf} << 16)) | (u64{9} << 16)));
        for (const auto& [word, bit] : std::array{
                std::pair{1U, 8U}, std::pair{1U, 28U}, std::pair{2U, 12U},
                std::pair{2U, 13U}, std::pair{2U, 20U}, std::pair{2U, 31U},
                std::pair{3U, 0U}, std::pair{3U, 30U}}) {
            auto invalid = original;
            invalid.words[word] ^= 1U << bit;
            assert(!Lower(invalid));
        }
        auto no_channels = original;
        no_channels.words[2] &= ~0xf00U;
        assert(!Lower(no_channels));
        auto invalid_handle = original;
        invalid_handle.words[2] = (invalid_handle.words[2] & ~255U) | 250U;
        assert(!Lower(invalid_handle));
    }
    // SURED accepts only direct, fully validated 1D buffer / 2D targets.
    for (const u32 dimension : {1U, 3U}) {
        for (const u32 guard : {0U, 7U, 9U}) {
            auto insn = SurfaceReduction;
            insn.words[0] = (insn.words[0] & ~0xf000U) | (guard << 12);
            insn.words[1] = (insn.words[1] & 0x1fffffffU) | (dimension << 29);
            assert(Probe(insn).status == ProbeStatus::Recognized);
            const auto result = Lower(insn);
            assert(result && result.source_size == 32 && result.instructions.size() == 2);
            assert(result.required_texture_buffer == 3);
            assert(result.instructions[0] ==
                (0xeb48002000000506ULL | (u64{guard} << 16) | (u64{dimension} << 33)));
        }
    }
    for (const u32 dimension : {0U, 2U, 4U, 5U, 6U, 7U}) {
        auto invalid = SurfaceReduction;
        invalid.words[1] = (invalid.words[1] & 0x1fffffffU) | (dimension << 29);
        assert(!Lower(invalid));
    }
    auto invalid_reduction = SurfaceReduction;
    invalid_reduction.words[2] ^= 0x200U;
    assert(!Lower(invalid_reduction));
    auto unreviewed_reduction = SurfaceReduction;
    unreviewed_reduction.words[0] |= 1U << 16;
    assert(Probe(unreviewed_reduction).status == ProbeStatus::UnreviewedFields);
    auto unreviewed_uniform_shift = UniformClamp;
    unreviewed_uniform_shift.words[3] |= 1U;
    assert(Probe(unreviewed_uniform_shift).status == ProbeStatus::UnreviewedFields);
    auto invalid_binding = SurfaceReduction;
    invalid_binding.words[1] = (invalid_binding.words[1] & ~(0x1fU << 22)) | (18U << 22);
    assert(!Lower(invalid_binding));
    auto invalid_offset = SurfaceReduction;
    invalid_offset.words[1] |= (0x2000U << 8);
    assert(!Lower(invalid_offset));
    auto scratch_data = SurfaceReduction;
    scratch_data.words[1] = (scratch_data.words[1] & ~0xffU) | 250U;
    assert(!Lower(scratch_data));
    auto scratch_coordinate = SurfaceReduction;
    scratch_coordinate.words[0] = (scratch_coordinate.words[0] & 0x00ffffffU) |
                                  (248U << 24);
    assert(!Lower(scratch_coordinate));

    // IMNMX signed 20-bit immediate must not consume a scratch register.
    for (u32 value : {0U, 0x7ffffU, 0xfff80000U, 0xffffffffU}) {
        auto insn = FullIntegerMinMax;
        insn.words[1] = value;
        const auto result = Lower(insn);
        assert(result && result.instructions.size() == 2);
        assert((result.instructions.front() >> 56 & 1U) == (value >> 31));
        assert(((result.instructions.front() >> 20) & 0x7ffffU) == (value & 0x7ffffU));
    }
    for (u32 value : {0x80000U, 0x1fffffffU, 0x7fffffffU, 0x80000000U, 0xfff7ffffU}) {
        auto insn = FullIntegerMinMax;
        insn.words[1] = value;
        const auto result = Lower(insn);
        assert(result && result.instructions.size() == 3);
        assert((result.instructions.front() & 0xffU) == 251U); // materialized immediate
        assert(((result.instructions.front() >> 20) & 0xffffffffULL) == value);
    }
    // The exact renderer-facing bridge must pass the same captured cases
    // through classification, checked ISA fields, lowerer, and image output.
    for (const Instruction insn : {UniformClamp, UniformWrap, SurfaceReduction,
                                    FullIntegerMinMax, BindlessLoad, BindlessStore}) {
        const auto bridge = LowerReviewedToMaxwell(Bytes(insn));
        assert(bridge.Ready());
        assert(bridge.consumed_native_bytes == 32);
        assert(!bridge.maxwell_instructions.empty());
    }
    // BRA.U's low address bits are convergence flags. Verify the real
    // branch relocation and a signed backward jump, never merely masking
    // the bits in a separate non-production model.
    constexpr Instruction Nop{{0x00007918, 0, 0, 0x000fea00}};
    {
        std::array<Instruction, 133> program{};
        program.fill(Nop);
        program[91] = Instruction{{0x00008947, 0x00000281, 0x03800000, 0x000fea00}};
        program.back() = Exit;
        const auto linked = LowerToMaxwell(program);
        assert(linked && linked.source_size == sizeof(program));
        assert(linked.source_instruction_offsets.size() == program.size());
        assert(linked.instructions[linked.source_instruction_offsets[91]] ==
               0xe24000001b08000fULL);
        // A lowerer-only PASS is not useful if the actual source-checked
        // renderer bridge rejects the captured BRA.U opcode or mode.
        std::vector<u8> encoded;
        encoded.reserve(sizeof(program));
        for (const auto& instruction : program)
            for (u32 word : instruction.words)
                for (unsigned shift = 0; shift != 32; shift += 8)
                    encoded.push_back(static_cast<u8>(word >> shift));
        const auto bridge = LowerReviewedToMaxwell(encoded);
        assert(bridge.Ready() && bridge.consumed_native_bytes == encoded.size());
    }
    {
        const std::array program{
            Nop,
            Instruction{{0x00008947, 0xffffffe1, 0x0383ffff, 0x000fea00}},
            Exit,
        };
        const auto backward = LowerToMaxwell(program);
        assert(backward && backward.source_size == sizeof(program));
        assert(backward.instructions[backward.source_instruction_offsets[1]] ==
               0xe2400fffff08000fULL);
    }
    {
        const std::array program{
            Instruction{{0x00008947, 0x11, 0x04800000, 0x000fea00}},
            Nop,
            Exit,
        };
        const auto guarded = LowerToMaxwell(program);
        assert(guarded && guarded.source_size == sizeof(program));
        assert(guarded.instructions.size() >= 4);
    }
    for (const u32 bit : {82U,83U,84U,85U,86U,91U,92U,93U,94U,
                          95U,96U,97U,98U,99U,100U,101U,102U,103U,104U}) {
        auto branch = Instruction{{0x00008947, 1, 0x03800000, 0x000fea00}};
        branch.words[bit / 32] |= 1U << (bit % 32);
        const auto rejected = LowerToMaxwell(std::array{branch, Exit});
        assert(!rejected && rejected.instructions.empty());
    }
    for (const u32 offset : {5U,0x11U,0xffffffe1U}) {
        auto branch = Instruction{{0x00008947, offset, 0x03800000, 0x000fea00}};
        if (offset == 0xffffffe1U) branch.words[2] |= 0x3ffffU;
        const auto rejected = LowerToMaxwell(std::array{branch, Exit});
        assert(!rejected && rejected.instructions.empty());
    }
    // P2.3: native QMD CBUF reads use the actual Ampere opcode/byte
    // offset and the reviewed shared Maxwell indexed load, never a
    // special-case title path or guessed aligned word read.
    for (const auto& [instruction, bank, byte_offset, width, dst, index] :
         std::array<std::tuple<Instruction,u32,u32,u32,u32,u32>, 3>{{
             {Instruction{{0x11047abb,0x01400000,0x08000400,0x000fe400}}, 5, 0, 2, 220, 201},
             {Instruction{{0x06077abb,0x01002080,0x08000000,0x000fe400}}, 4, 0x82, 0, 223, 222},
             {Instruction{{0x0d047abb,0x014000c0,0x08000000,0x000fe400}}, 5, 3, 0, 220, 229},
         }}) {
        const auto probe = Probe(instruction);
        assert(probe.status == ProbeStatus::Recognized);
        const auto lowered = Lower(instruction);
        assert(lowered && lowered.source_instruction_offsets.size() == 2);
        const u64 word = lowered.instructions[lowered.source_instruction_offsets[0]];
        assert((word & 0xff00000000000000ULL) == 0xef00000000000000ULL);
        assert((word & 255U) == dst);
        assert(((word >> 8) & 255U) == index);
        assert(((word >> 20) & 0xffffU) == byte_offset);
        assert(((word >> 36) & 31U) == bank);
        assert(((word >> 48) & 7U) == width);
        const auto bridge = LowerReviewedToMaxwell(Bytes(instruction));
        assert(bridge.Ready() && bridge.source_instruction_offsets.size() == 2);
        assert(bridge.maxwell_instructions[bridge.source_instruction_offsets[0]] == word);
    }
    for (const u32 invalid_width : {6U,7U}) {
        auto invalid = Instruction{{0x06077abb,0x01002080,0x08000000,0x000fe400}};
        invalid.words[2] |= invalid_width << 9;
        assert(!Lower(invalid));
    }
    // Direct byte/halfword ULDC is also legal when the immediate is
    // naturally aligned and below Maxwell's subword displacement limit.
    for (const auto& [instruction, byte_offset, width] :
         std::array<std::tuple<Instruction,u32,u32>,2>{{
             {Instruction{{0x06077ab9,0x01002080,0x00000000,0x000fe400}}, 0x82, 0},
             {Instruction{{0x06077ab9,0x01000080,0x00000400,0x000fe400}}, 2, 2}
         }}) {
        const auto lowered = Lower(instruction);
        assert(lowered && lowered.source_instruction_offsets.size() == 2);
        const u64 word = lowered.instructions[lowered.source_instruction_offsets[0]];
        assert((word & 255U) == 223U);
        assert(((word >> 8) & 255U) == 255U); // direct, no UR offset
        assert(((word >> 20) & 0xffffU) == byte_offset);
        assert(((word >> 48) & 7U) == width);
        const auto bridge = LowerReviewedToMaxwell(Bytes(instruction));
        assert(bridge.Ready());
        assert(bridge.maxwell_instructions[bridge.source_instruction_offsets[0]] == word);
    }
    // Signed native subword reads use Maxwell's signed 8/16-bit widths,
    // both with a direct displacement and a dynamic uniform index.
    for (const bool indexed : {false, true}) {
        for (const u32 width : {1U, 3U}) {
            auto instruction = indexed
                ? Instruction{{0x06077abb,0x01002080,0x08000000,0x000fe400}}
                : Instruction{{0x06077ab9,0x01002080,0x00000000,0x000fe400}};
            instruction.words[2] |= width << 9;
            assert(Probe(instruction).status == ProbeStatus::Recognized);
            const auto lowered = Lower(instruction);
            assert(lowered && lowered.source_instruction_offsets.size() == 2);
            const u64 word = lowered.instructions[lowered.source_instruction_offsets[0]];
            assert((word & 0xff00000000000000ULL) == 0xef00000000000000ULL);
            assert(((word >> 8) & 255U) == (indexed ? 222U : 255U));
            assert(((word >> 20) & 0xffffU) == 0x82U);
            assert(((word >> 48) & 7U) == width);
            const auto bridge = LowerReviewedToMaxwell(Bytes(instruction));
            assert(bridge.Ready());
            assert(bridge.maxwell_instructions[bridge.source_instruction_offsets[0]] == word);
        }
    }
    auto direct_signed_byte_odd = Instruction{{0x06077ab9,0x010000c0,0x00000200,0x000fe400}};
    assert(Lower(direct_signed_byte_odd));
    auto direct_signed_half_odd = Instruction{{0x06077ab9,0x010000c0,0x00000600,0x000fe400}};
    assert(!Lower(direct_signed_half_odd));
    auto direct_signed_half_range = Instruction{{0x06077ab9,0x01200000,0x00000600,0x000fe400}};
    assert(!Lower(direct_signed_half_range));
    auto direct_bad_alignment = Instruction{{0x06077ab9,0x010000c0,0x00000400,0x000fe400}};
    assert(!Lower(direct_bad_alignment)); // U16 at odd byte address
    auto direct_bad_range = Instruction{{0x06077ab9,0x01200000,0x00000000,0x000fe400}};
    assert(!Lower(direct_bad_range)); // direct short displacement sign bit set
    auto bad_index = Instruction{{0x3f077abb,0x01002080,0x08000000,0x000fe400}};
    assert(!Lower(bad_index)); // no UR63 as a dynamic index
    std::puts("P2_4_LICHII_NX2_GENERIC_AMPERE_LOWERING_PASS 0x499 0x59f 0x817 0x998 0x99c BRA.U renderer_bridge=ready");
}
