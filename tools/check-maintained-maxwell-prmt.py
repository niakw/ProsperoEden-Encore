#!/usr/bin/env python3
"""Compare the maintained Maxwell PRMT/IMUL shader source to its reviewed single native owner."""
from pathlib import Path
import json
import hashlib
root=Path(__file__).resolve().parents[1]
pristine=(root/"vendor/sources/eden/src/shader_recompiler/frontend/maxwell/translate/impl/not_implemented.cpp").read_text()
actual=(root/"vendor/encore-active/eden-core/src/shader_recompiler/frontend/maxwell/translate/impl/not_implemented.cpp").read_text()
module=(root/"headless/gpu_native_observability.cmake").read_text()
helper,reference,imm_old,imm_new,reg_old,reg_new=json.loads(r'''["\nnamespace {\nunsigned EdenGpuBoundedSample(std::atomic<unsigned>& samples) noexcept {\n    unsigned current = samples.load(std::memory_order_relaxed);\n    while (current < 8u) {\n        if (samples.compare_exchange_weak(current, current + 1u,\n                                          std::memory_order_relaxed))\n            return current;\n    }\n    return 8u;\n}\n}\n","\nnamespace {\nconstexpr unsigned EdenPrmtIndexReference(unsigned a, unsigned b, unsigned selector) {\n    unsigned result = 0;\n    for (unsigned output = 0; output < 4; ++output) {\n        const unsigned nibble = (selector >> (4u * output)) & 15u;\n        const unsigned source = (nibble & 4u) ? b : a;\n        unsigned byte = (source >> (8u * (nibble & 3u))) & 255u;\n        if (nibble & 8u)\n            byte = (byte & 128u) ? 255u : 0u;\n        result |= byte << (8u * output);\n    }\n    return result;\n}\nstatic_assert(EdenPrmtIndexReference(0x11223344u, 0x55667788u, 0x3210u) == 0x11223344u);\nstatic_assert(EdenPrmtIndexReference(0x11223344u, 0x55667788u, 0x7654u) == 0x55667788u);\nstatic_assert(EdenPrmtIndexReference(0x80abcdefu, 0u, 0xbbbbu) == 0xffffffffu);\nstatic_assert(EdenPrmtIndexReference(0x11223344u, 0x55667788u, 0xffffu) == 0u);\n}\n","\nvoid TranslatorVisitor::PRMT_imm(u64) {\n    ThrowNotImplemented(Opcode::PRMT_imm);\n}\n","\nvoid TranslatorVisitor::PRMT_imm(u64 insn) {\n    // Maxwell SASS PRMT immediate (0x36c0) uses:\n    // A = R[8:15], B = R[39:46], selector = bits[20:35],\n    // mode = bits[48:50], D = R[0:7].\n    // Only mode 0 (index byte permutation) is translated here.\n    // Each nibble selects one of eight source bytes and its high bit\n    // requests *sign replication* of that byte, not its raw value.\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned index = EdenGpuBoundedSample(unsupported_samples);\n        if (index < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_IMM raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, index + 1);\n        ThrowNotImplemented(Opcode::PRMT_imm);\n    }\n\n    const unsigned selector = static_cast<unsigned>((insn >> 20) & 0xffffULL);\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetReg39(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned output_byte = 0; output_byte < 4; ++output_byte) {\n        const unsigned nibble = (selector >> (output_byte * 4)) & 15u;\n        const IR::U32 source = (nibble & 4u) ? b : a;\n        const unsigned src_offset = (nibble & 3u) * 8u;\n        // When nibble[3] is set, the NVIDIA byte sign bit\n        // becomes either 0x00 or 0xff in the output.\n        const IR::U32 extracted = (nibble & 8u)\n            ? ir.BitFieldExtract(source, ir.Imm32(src_offset + 7u), ir.Imm32(1), true)\n            : ir.BitFieldExtract(source, ir.Imm32(src_offset), ir.Imm32(8), false);\n        const IR::U32 value = ir.BitwiseAnd(extracted, ir.Imm32(255));\n        const IR::U32 shifted = output_byte == 0 ? value :\n            IR::U32{ir.ShiftLeftLogical(value, ir.Imm32(output_byte * 8u))};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n\n    static std::atomic<unsigned> implemented_samples{0};\n    const unsigned implemented = EdenGpuBoundedSample(implemented_samples);\n    if (implemented < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_IMM_INDEX raw=%016llx selector=%04x sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), selector, implemented + 1);\n}\n","\nvoid TranslatorVisitor::PRMT_reg(u64) {\n    ThrowNotImplemented(Opcode::PRMT_reg);\n}\n","\nvoid TranslatorVisitor::PRMT_reg(u64 insn) {\n    // Maxwell SASS PRMT register selector opcode (0x5bc0).\n    // Dynamic selector is R[20:27]; A=R8, B=R39, mode[48:50].\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned sample = EdenGpuBoundedSample(unsupported_samples);\n        if (sample < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_REG_UNSUPPORTED raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, sample + 1);\n        ThrowNotImplemented(Opcode::PRMT_reg);\n    }\n\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetReg39(insn)};\n    const IR::U32 selector{GetReg20(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned i = 0; i < 4; ++i) {\n        const IR::U32 nibble{ir.BitwiseAnd(\n            ir.ShiftRightLogical(selector, ir.Imm32(i * 4u)), ir.Imm32(15))};\n        const IR::U1 from_b{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(4)), ir.Imm32(0))};\n        const IR::U32 source{ir.Select(from_b, b, a)};\n        const IR::U32 byte_shift{ir.ShiftLeftLogical(\n            ir.BitwiseAnd(nibble, ir.Imm32(3)), ir.Imm32(3))};\n        const IR::U32 selected_byte{ir.BitwiseAnd(\n            ir.ShiftRightLogical(source, byte_shift), ir.Imm32(255))};\n        const IR::U1 signed_replication{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(8)), ir.Imm32(0))};\n        const IR::U1 negative{ir.INotEqual(\n            ir.BitwiseAnd(selected_byte, ir.Imm32(128)), ir.Imm32(0))};\n        const IR::U32 replicated{ir.Select(negative, ir.Imm32(255), ir.Imm32(0))};\n        const IR::U32 byte{ir.Select(signed_replication, replicated, selected_byte)};\n        const IR::U32 shifted{i == 0 ? byte :\n            IR::U32{ir.ShiftLeftLogical(byte, ir.Imm32(i * 8u))}};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n    static std::atomic<unsigned> successes{0};\n    const unsigned sample = EdenGpuBoundedSample(successes);\n    if (sample < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_REG_INDEX raw=%016llx sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), sample + 1);\n}\n"]''')
assert pristine.count(imm_old)==1 and pristine.count(reg_old)==1
expected='#include <atomic>\n#include <cstdio>\n'+helper+"\n"+reference+"\n"+pristine.replace(imm_old,imm_new).replace(reg_old,reg_new)
# PR #199 extends the same maintained source with the two remaining default-mode
# PRMT operand forms. Preserve the exact generated-source oracle rather than
# weakening this check to token presence.
rc_old="void TranslatorVisitor::PRMT_rc(u64) {\n    ThrowNotImplemented(Opcode::PRMT_rc);\n}\n"
rc_new="void TranslatorVisitor::PRMT_rc(u64 insn) {\n    // Upstream Lichii f6a8f513: PRMT R/C form uses a register selector\n    // and a constant-buffer second data source. Keep Encore's bounded\n    // diagnostics and support only the default/index mode, matching reg/imm.\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned sample = EdenGpuBoundedSample(unsupported_samples);\n        if (sample < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_RC_UNSUPPORTED raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, sample + 1);\n        ThrowNotImplemented(Opcode::PRMT_rc);\n    }\n\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetCbuf(insn)};\n    const IR::U32 selector{GetReg39(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned i = 0; i < 4; ++i) {\n        const IR::U32 nibble{ir.BitwiseAnd(\n            ir.ShiftRightLogical(selector, ir.Imm32(i * 4u)), ir.Imm32(15))};\n        const IR::U1 from_b{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(4)), ir.Imm32(0))};\n        const IR::U32 source{ir.Select(from_b, b, a)};\n        const IR::U32 byte_shift{ir.ShiftLeftLogical(\n            ir.BitwiseAnd(nibble, ir.Imm32(3)), ir.Imm32(3))};\n        const IR::U32 selected_byte{ir.BitwiseAnd(\n            ir.ShiftRightLogical(source, byte_shift), ir.Imm32(255))};\n        const IR::U1 signed_replication{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(8)), ir.Imm32(0))};\n        const IR::U1 negative{ir.INotEqual(\n            ir.BitwiseAnd(selected_byte, ir.Imm32(128)), ir.Imm32(0))};\n        const IR::U32 replicated{ir.Select(negative, ir.Imm32(255), ir.Imm32(0))};\n        const IR::U32 byte{ir.Select(signed_replication, replicated, selected_byte)};\n        const IR::U32 shifted{i == 0 ? byte :\n            IR::U32{ir.ShiftLeftLogical(byte, ir.Imm32(i * 8u))}};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n\n    static std::atomic<unsigned> successes{0};\n    const unsigned sample = EdenGpuBoundedSample(successes);\n    if (sample < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_RC_INDEX raw=%016llx sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), sample + 1);\n}\n"
cr_old="void TranslatorVisitor::PRMT_cr(u64) {\n    ThrowNotImplemented(Opcode::PRMT_cr);\n}\n"
cr_new="void TranslatorVisitor::PRMT_cr(u64 insn) {\n    // Upstream Lichii f6a8f513: PRMT C/R form reads its selector from\n    // constant memory and the second data source from the register operand.\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned sample = EdenGpuBoundedSample(unsupported_samples);\n        if (sample < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_CR_UNSUPPORTED raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, sample + 1);\n        ThrowNotImplemented(Opcode::PRMT_cr);\n    }\n\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetReg39(insn)};\n    const IR::U32 selector{GetCbuf(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned i = 0; i < 4; ++i) {\n        const IR::U32 nibble{ir.BitwiseAnd(\n            ir.ShiftRightLogical(selector, ir.Imm32(i * 4u)), ir.Imm32(15))};\n        const IR::U1 from_b{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(4)), ir.Imm32(0))};\n        const IR::U32 source{ir.Select(from_b, b, a)};\n        const IR::U32 byte_shift{ir.ShiftLeftLogical(\n            ir.BitwiseAnd(nibble, ir.Imm32(3)), ir.Imm32(3))};\n        const IR::U32 selected_byte{ir.BitwiseAnd(\n            ir.ShiftRightLogical(source, byte_shift), ir.Imm32(255))};\n        const IR::U1 signed_replication{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(8)), ir.Imm32(0))};\n        const IR::U1 negative{ir.INotEqual(\n            ir.BitwiseAnd(selected_byte, ir.Imm32(128)), ir.Imm32(0))};\n        const IR::U32 replicated{ir.Select(negative, ir.Imm32(255), ir.Imm32(0))};\n        const IR::U32 byte{ir.Select(signed_replication, replicated, selected_byte)};\n        const IR::U32 shifted{i == 0 ? byte :\n            IR::U32{ir.ShiftLeftLogical(byte, ir.Imm32(i * 8u))}};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n\n    static std::atomic<unsigned> successes{0};\n    const unsigned sample = EdenGpuBoundedSample(successes);\n    if (sample < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_CR_INDEX raw=%016llx sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), sample + 1);\n}\n"
assert expected.count(rc_old)==1 and expected.count(cr_old)==1
expected=expected.replace(rc_old,rc_new).replace(cr_old,cr_new)

# Generic Maxwell IMUL forms are part of the same exclusively selected native
# translation unit. Reconstruct them from the pristine stubs rather than adding
# a second source path. Bit positions match envytools GM107; .CC remains refused.
imul_include_old="#include \"common/common_types.h\"\n"
imul_include_new="#include \"common/bit_field.h\"\n#include \"common/common_types.h\"\n"
imul_throw_anchor="[[noreturn]] static void ThrowNotImplemented(Opcode opcode) {\n    throw NotImplementedException(\"Instruction {} is not implemented\", opcode);\n}\n"
imul_helper="\nnamespace {\n// Maxwell GM107 IMUL encoding: envytools gm107.c tab5c38_{0,1}/tab1f00_{0,1}.\n// Algorithm adapted from carafe-nx/carafe-lab b1f10cef (GPL-3.0-or-later).\n// Build the high word from 16-bit products so the IR never requires an\n// integer-64 multiply that a host shader backend may not provide.\nIR::U32 MultiplyHigh(TranslatorVisitor& v, const IR::U32& a, const IR::U32& b,\n                     bool is_a_signed, bool is_b_signed) {\n    const IR::U32 mask{v.ir.Imm32(0xffff)};\n    const IR::U32 sixteen{v.ir.Imm32(16)};\n    const IR::U32 a_lo{v.ir.BitwiseAnd(a, mask)};\n    const IR::U32 a_hi{v.ir.ShiftRightLogical(a, sixteen)};\n    const IR::U32 b_lo{v.ir.BitwiseAnd(b, mask)};\n    const IR::U32 b_hi{v.ir.ShiftRightLogical(b, sixteen)};\n    const IR::U32 lo_lo{v.ir.IMul(a_lo, b_lo)};\n    const IR::U32 hi_lo{v.ir.IMul(a_hi, b_lo)};\n    const IR::U32 lo_hi{v.ir.IMul(a_lo, b_hi)};\n    const IR::U32 hi_hi{v.ir.IMul(a_hi, b_hi)};\n    const IR::U32 middle{v.ir.IAdd(v.ir.IAdd(v.ir.ShiftRightLogical(lo_lo, sixteen),\n                                             v.ir.BitwiseAnd(hi_lo, mask)),\n                                   v.ir.BitwiseAnd(lo_hi, mask))};\n    IR::U32 high{v.ir.IAdd(v.ir.IAdd(hi_hi, v.ir.ShiftRightLogical(hi_lo, sixteen)),\n                           v.ir.IAdd(v.ir.ShiftRightLogical(lo_hi, sixteen),\n                                     v.ir.ShiftRightLogical(middle, sixteen)))};\n    if (is_a_signed) {\n        const IR::U1 negative{v.ir.ILessThan(a, v.ir.Imm32(0), true)};\n        high = v.ir.ISub(high, IR::U32{v.ir.Select(negative, b, v.ir.Imm32(0))});\n    }\n    if (is_b_signed) {\n        const IR::U1 negative{v.ir.ILessThan(b, v.ir.Imm32(0), true)};\n        high = v.ir.ISub(high, IR::U32{v.ir.Select(negative, a, v.ir.Imm32(0))});\n    }\n    return high;\n}\n\nvoid TranslateIMul(TranslatorVisitor& v, u64 insn, const IR::U32& src_b,\n                   bool high, bool is_a_signed, bool is_b_signed, bool cc) {\n    union {\n        u64 raw;\n        BitField<0, 8, IR::Reg> dest_reg;\n        BitField<8, 8, IR::Reg> src_reg_a;\n    } const imul{insn};\n\n    // Condition-code publication has separate carry/overflow semantics.\n    // Keep it fail-closed until those flags are implemented and verified.\n    if (cc) {\n        throw NotImplementedException(\"IMUL.CC\");\n    }\n    const IR::U32 src_a{v.X(imul.src_reg_a)};\n    const IR::U32 result{\n        high ? MultiplyHigh(v, src_a, src_b, is_a_signed, is_b_signed)\n             : v.ir.IMul(src_a, src_b)};\n    v.X(imul.dest_reg, result);\n}\n\nvoid TranslateIMul(TranslatorVisitor& v, u64 insn, const IR::U32& src_b) {\n    union {\n        u64 raw;\n        BitField<39, 1, u64> high;\n        BitField<40, 1, u64> is_a_signed;\n        BitField<41, 1, u64> is_b_signed;\n        BitField<47, 1, u64> cc;\n    } const imul{insn};\n    TranslateIMul(v, insn, src_b, imul.high != 0, imul.is_a_signed != 0,\n                  imul.is_b_signed != 0, imul.cc != 0);\n}\n} // namespace\n\n"
imul_rewrites=[
    ("void TranslatorVisitor::IMUL_reg(u64) {\n    ThrowNotImplemented(Opcode::IMUL_reg);\n}\n\n", "void TranslatorVisitor::IMUL_reg(u64 insn) {\n    TranslateIMul(*this, insn, GetReg20(insn));\n}\n\n"),
    ("void TranslatorVisitor::IMUL_cbuf(u64) {\n    ThrowNotImplemented(Opcode::IMUL_cbuf);\n}\n\n", "void TranslatorVisitor::IMUL_cbuf(u64 insn) {\n    TranslateIMul(*this, insn, GetCbuf(insn));\n}\n\n"),
    ("void TranslatorVisitor::IMUL_imm(u64) {\n    ThrowNotImplemented(Opcode::IMUL_imm);\n}\n\n", "void TranslatorVisitor::IMUL_imm(u64 insn) {\n    TranslateIMul(*this, insn, GetImm20(insn));\n}\n\n"),
    ("void TranslatorVisitor::IMUL32I(u64) {\n    ThrowNotImplemented(Opcode::IMUL32I);\n}\n\n", "void TranslatorVisitor::IMUL32I(u64 insn) {\n    union {\n        u64 raw;\n        BitField<52, 1, u64> cc;\n        BitField<53, 1, u64> high;\n        BitField<54, 1, u64> is_a_signed;\n        BitField<55, 1, u64> is_b_signed;\n    } const imul{insn};\n    TranslateIMul(*this, insn, GetImm32(insn), imul.high != 0,\n                  imul.is_a_signed != 0, imul.is_b_signed != 0, imul.cc != 0);\n}\n\n"),
]
assert expected.count(imul_include_old)==1
assert expected.count(imul_throw_anchor)==1
expected=expected.replace(imul_include_old,imul_include_new,1)
expected=expected.replace(imul_throw_anchor,imul_throw_anchor+imul_helper,1)
for old,new in imul_rewrites:
    assert expected.count(old)==1
    expected=expected.replace(old,new,1)
assert 'throw NotImplementedException("IMUL.CC")' in expected
assert 'BitField<39, 1, u64> high;' in expected
assert 'BitField<53, 1, u64> high;' in expected

# NVIDIA PTX documents all six specialized PRMT byte modes; envytools GM107
# maps them to mode values 1..6 in the complete four-bit field at 48..51.
# Apply the exact reviewed successor to the already reconstructed PRMT/IMUL
# owner, keeping this a single byte-exact source oracle.
prmt_modes_old_tail="void TranslateIMul(TranslatorVisitor& v, u64 insn, const IR::U32& src_b) {\n    union {\n        u64 raw;\n        BitField<39, 1, u64> high;\n        BitField<40, 1, u64> is_a_signed;\n        BitField<41, 1, u64> is_b_signed;\n        BitField<47, 1, u64> cc;\n    } const imul{insn};\n    TranslateIMul(v, insn, src_b, imul.high != 0, imul.is_a_signed != 0,\n                  imul.is_b_signed != 0, imul.cc != 0);\n}\n} // namespace\n\n"
prmt_modes_new_tail="void TranslateIMul(TranslatorVisitor& v, u64 insn, const IR::U32& src_b) {\n    union {\n        u64 raw;\n        BitField<39, 1, u64> high;\n        BitField<40, 1, u64> is_a_signed;\n        BitField<41, 1, u64> is_b_signed;\n        BitField<47, 1, u64> cc;\n    } const imul{insn};\n    TranslateIMul(v, insn, src_b, imul.high != 0, imul.is_a_signed != 0,\n                  imul.is_b_signed != 0, imul.cc != 0);\n}\n\n// NVIDIA PTX prmt.b32 specialized controls and envytools GM107 tab5bc0_0\n// use mode values 1..6 in bits 48..51. Values 7..15 are reserved.\nenum class PrmtMode : u32 {\n    Index = 0,\n    Forward4Extract = 1,\n    Backward4Extract = 2,\n    Replicate8 = 3,\n    EdgeClampLeft = 4,\n    EdgeClampRight = 5,\n    Replicate16 = 6,\n};\n\nconstexpr u32 PrmtTableIndex(PrmtMode mode, u32 selector, u32 byte) {\n    switch (mode) {\n    case PrmtMode::Forward4Extract:\n        return (selector + byte) & 7;\n    case PrmtMode::Backward4Extract:\n        return (selector - byte) & 7;\n    case PrmtMode::Replicate8:\n        return selector;\n    case PrmtMode::EdgeClampLeft:\n        return selector > byte ? selector : byte;\n    case PrmtMode::EdgeClampRight:\n        return selector < byte ? selector : byte;\n    case PrmtMode::Replicate16:\n        return (byte & 1) + 2 * (selector & 1);\n    case PrmtMode::Index:\n        break;\n    }\n    return 8;\n}\n\nstatic_assert(PrmtTableIndex(PrmtMode::Forward4Extract, 1, 3) == 4);\nstatic_assert(PrmtTableIndex(PrmtMode::Backward4Extract, 0, 3) == 5);\nstatic_assert(PrmtTableIndex(PrmtMode::Replicate8, 2, 3) == 2);\nstatic_assert(PrmtTableIndex(PrmtMode::EdgeClampLeft, 1, 1) == 1);\nstatic_assert(PrmtTableIndex(PrmtMode::EdgeClampRight, 2, 3) == 2);\nstatic_assert(PrmtTableIndex(PrmtMode::Replicate16, 1, 2) == 2);\n\nIR::U32 PickPrmtByte(TranslatorVisitor& v, const IR::U32& a, const IR::U32& b,\n                     const IR::U32& index, const IR::U1& replicate_sign) {\n    const IR::U1 from_b{\n        v.ir.INotEqual(v.ir.BitwiseAnd(index, v.ir.Imm32(4)), v.ir.Imm32(0))};\n    const IR::U32 source{v.ir.Select(from_b, b, a)};\n    const IR::U32 offset{\n        v.ir.ShiftLeftLogical(v.ir.BitwiseAnd(index, v.ir.Imm32(3)), v.ir.Imm32(3))};\n    const IR::U32 value{\n        v.ir.BitFieldExtract(source, offset, v.ir.Imm32(8), false)};\n    const IR::U1 negative{\n        v.ir.INotEqual(v.ir.BitwiseAnd(value, v.ir.Imm32(0x80)), v.ir.Imm32(0))};\n    const IR::U32 sign_byte{\n        v.ir.Select(negative, v.ir.Imm32(0xff), v.ir.Imm32(0))};\n    return IR::U32{v.ir.Select(replicate_sign, sign_byte, value)};\n}\n\nvoid TranslatePrmt(TranslatorVisitor& v, u64 insn, const IR::U32& selector,\n                   const IR::U32& src_b) {\n    union {\n        u64 raw;\n        BitField<0, 8, IR::Reg> dest_reg;\n        BitField<8, 8, IR::Reg> src_reg_a;\n        BitField<48, 4, u64> mode;\n    } const prmt{insn};\n\n    const u32 raw_mode = static_cast<u32>(prmt.mode.Value());\n    if (raw_mode > static_cast<u32>(PrmtMode::Replicate16)) {\n        throw NotImplementedException(\"PRMT reserved mode {}\", raw_mode);\n    }\n    const PrmtMode mode{static_cast<PrmtMode>(raw_mode)};\n    const IR::U32 src_a{v.X(prmt.src_reg_a)};\n    IR::U32 result{v.ir.Imm32(0)};\n    for (u32 byte = 0; byte < 4; ++byte) {\n        IR::U32 index;\n        IR::U1 replicate_sign{v.ir.Imm1(false)};\n        if (mode == PrmtMode::Index) {\n            const IR::U32 nibble{\n                v.ir.BitFieldExtract(selector, v.ir.Imm32(byte * 4), v.ir.Imm32(4), false)};\n            index = v.ir.BitwiseAnd(nibble, v.ir.Imm32(7));\n            replicate_sign =\n                v.ir.INotEqual(v.ir.BitwiseAnd(nibble, v.ir.Imm32(8)), v.ir.Imm32(0));\n        } else {\n            // Specialized PTX modes use only selector c[1:0].\n            const IR::U32 control{v.ir.BitwiseAnd(selector, v.ir.Imm32(3))};\n            index = v.ir.Imm32(PrmtTableIndex(mode, 3, byte));\n            for (u32 value = 0; value < 3; ++value) {\n                index = IR::U32{v.ir.Select(v.ir.IEqual(control, v.ir.Imm32(value)),\n                                            v.ir.Imm32(PrmtTableIndex(mode, value, byte)),\n                                            index)};\n            }\n        }\n        const IR::U32 picked{PickPrmtByte(v, src_a, src_b, index, replicate_sign)};\n        const IR::U32 shifted{\n            byte == 0 ? picked\n                      : IR::U32{v.ir.ShiftLeftLogical(picked, v.ir.Imm32(byte * 8))}};\n        result = v.ir.BitwiseOr(result, shifted);\n    }\n    v.X(prmt.dest_reg, result);\n}\n} // namespace\n\n"
prmt_modes_old_methods="void TranslatorVisitor::PRMT_reg(u64 insn) {\n    // Maxwell SASS PRMT register selector opcode (0x5bc0).\n    // Dynamic selector is R[20:27]; A=R8, B=R39, mode[48:50].\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned sample = EdenGpuBoundedSample(unsupported_samples);\n        if (sample < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_REG_UNSUPPORTED raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, sample + 1);\n        ThrowNotImplemented(Opcode::PRMT_reg);\n    }\n\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetReg39(insn)};\n    const IR::U32 selector{GetReg20(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned i = 0; i < 4; ++i) {\n        const IR::U32 nibble{ir.BitwiseAnd(\n            ir.ShiftRightLogical(selector, ir.Imm32(i * 4u)), ir.Imm32(15))};\n        const IR::U1 from_b{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(4)), ir.Imm32(0))};\n        const IR::U32 source{ir.Select(from_b, b, a)};\n        const IR::U32 byte_shift{ir.ShiftLeftLogical(\n            ir.BitwiseAnd(nibble, ir.Imm32(3)), ir.Imm32(3))};\n        const IR::U32 selected_byte{ir.BitwiseAnd(\n            ir.ShiftRightLogical(source, byte_shift), ir.Imm32(255))};\n        const IR::U1 signed_replication{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(8)), ir.Imm32(0))};\n        const IR::U1 negative{ir.INotEqual(\n            ir.BitwiseAnd(selected_byte, ir.Imm32(128)), ir.Imm32(0))};\n        const IR::U32 replicated{ir.Select(negative, ir.Imm32(255), ir.Imm32(0))};\n        const IR::U32 byte{ir.Select(signed_replication, replicated, selected_byte)};\n        const IR::U32 shifted{i == 0 ? byte :\n            IR::U32{ir.ShiftLeftLogical(byte, ir.Imm32(i * 8u))}};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n    static std::atomic<unsigned> successes{0};\n    const unsigned sample = EdenGpuBoundedSample(successes);\n    if (sample < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_REG_INDEX raw=%016llx sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), sample + 1);\n}\n\nvoid TranslatorVisitor::PRMT_rc(u64 insn) {\n    // Upstream Lichii f6a8f513: PRMT R/C form uses a register selector\n    // and a constant-buffer second data source. Keep Encore's bounded\n    // diagnostics and support only the default/index mode, matching reg/imm.\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned sample = EdenGpuBoundedSample(unsupported_samples);\n        if (sample < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_RC_UNSUPPORTED raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, sample + 1);\n        ThrowNotImplemented(Opcode::PRMT_rc);\n    }\n\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetCbuf(insn)};\n    const IR::U32 selector{GetReg39(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned i = 0; i < 4; ++i) {\n        const IR::U32 nibble{ir.BitwiseAnd(\n            ir.ShiftRightLogical(selector, ir.Imm32(i * 4u)), ir.Imm32(15))};\n        const IR::U1 from_b{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(4)), ir.Imm32(0))};\n        const IR::U32 source{ir.Select(from_b, b, a)};\n        const IR::U32 byte_shift{ir.ShiftLeftLogical(\n            ir.BitwiseAnd(nibble, ir.Imm32(3)), ir.Imm32(3))};\n        const IR::U32 selected_byte{ir.BitwiseAnd(\n            ir.ShiftRightLogical(source, byte_shift), ir.Imm32(255))};\n        const IR::U1 signed_replication{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(8)), ir.Imm32(0))};\n        const IR::U1 negative{ir.INotEqual(\n            ir.BitwiseAnd(selected_byte, ir.Imm32(128)), ir.Imm32(0))};\n        const IR::U32 replicated{ir.Select(negative, ir.Imm32(255), ir.Imm32(0))};\n        const IR::U32 byte{ir.Select(signed_replication, replicated, selected_byte)};\n        const IR::U32 shifted{i == 0 ? byte :\n            IR::U32{ir.ShiftLeftLogical(byte, ir.Imm32(i * 8u))}};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n\n    static std::atomic<unsigned> successes{0};\n    const unsigned sample = EdenGpuBoundedSample(successes);\n    if (sample < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_RC_INDEX raw=%016llx sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), sample + 1);\n}\n\nvoid TranslatorVisitor::PRMT_cr(u64 insn) {\n    // Upstream Lichii f6a8f513: PRMT C/R form reads its selector from\n    // constant memory and the second data source from the register operand.\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned sample = EdenGpuBoundedSample(unsupported_samples);\n        if (sample < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_CR_UNSUPPORTED raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, sample + 1);\n        ThrowNotImplemented(Opcode::PRMT_cr);\n    }\n\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetReg39(insn)};\n    const IR::U32 selector{GetCbuf(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned i = 0; i < 4; ++i) {\n        const IR::U32 nibble{ir.BitwiseAnd(\n            ir.ShiftRightLogical(selector, ir.Imm32(i * 4u)), ir.Imm32(15))};\n        const IR::U1 from_b{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(4)), ir.Imm32(0))};\n        const IR::U32 source{ir.Select(from_b, b, a)};\n        const IR::U32 byte_shift{ir.ShiftLeftLogical(\n            ir.BitwiseAnd(nibble, ir.Imm32(3)), ir.Imm32(3))};\n        const IR::U32 selected_byte{ir.BitwiseAnd(\n            ir.ShiftRightLogical(source, byte_shift), ir.Imm32(255))};\n        const IR::U1 signed_replication{ir.INotEqual(\n            ir.BitwiseAnd(nibble, ir.Imm32(8)), ir.Imm32(0))};\n        const IR::U1 negative{ir.INotEqual(\n            ir.BitwiseAnd(selected_byte, ir.Imm32(128)), ir.Imm32(0))};\n        const IR::U32 replicated{ir.Select(negative, ir.Imm32(255), ir.Imm32(0))};\n        const IR::U32 byte{ir.Select(signed_replication, replicated, selected_byte)};\n        const IR::U32 shifted{i == 0 ? byte :\n            IR::U32{ir.ShiftLeftLogical(byte, ir.Imm32(i * 8u))}};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n\n    static std::atomic<unsigned> successes{0};\n    const unsigned sample = EdenGpuBoundedSample(successes);\n    if (sample < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_CR_INDEX raw=%016llx sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), sample + 1);\n}\n\nvoid TranslatorVisitor::PRMT_imm(u64 insn) {\n    // Maxwell SASS PRMT immediate (0x36c0) uses:\n    // A = R[8:15], B = R[39:46], selector = bits[20:35],\n    // mode = bits[48:50], D = R[0:7].\n    // Only mode 0 (index byte permutation) is translated here.\n    // Each nibble selects one of eight source bytes and its high bit\n    // requests *sign replication* of that byte, not its raw value.\n    const unsigned mode = static_cast<unsigned>((insn >> 48) & 7ULL);\n    if (mode != 0) {\n        static std::atomic<unsigned> unsupported_samples{0};\n        const unsigned index = EdenGpuBoundedSample(unsupported_samples);\n        if (index < 8)\n            std::fprintf(stderr, \"EDEN_GPU_PRMT_IMM raw=%016llx mode=%u sample=%u\\n\",\n                         static_cast<unsigned long long>(insn), mode, index + 1);\n        ThrowNotImplemented(Opcode::PRMT_imm);\n    }\n\n    const unsigned selector = static_cast<unsigned>((insn >> 20) & 0xffffULL);\n    const IR::U32 a{GetReg8(insn)};\n    const IR::U32 b{GetReg39(insn)};\n    IR::U32 result{ir.Imm32(0)};\n    for (unsigned output_byte = 0; output_byte < 4; ++output_byte) {\n        const unsigned nibble = (selector >> (output_byte * 4)) & 15u;\n        const IR::U32 source = (nibble & 4u) ? b : a;\n        const unsigned src_offset = (nibble & 3u) * 8u;\n        // When nibble[3] is set, the NVIDIA byte sign bit\n        // becomes either 0x00 or 0xff in the output.\n        const IR::U32 extracted = (nibble & 8u)\n            ? ir.BitFieldExtract(source, ir.Imm32(src_offset + 7u), ir.Imm32(1), true)\n            : ir.BitFieldExtract(source, ir.Imm32(src_offset), ir.Imm32(8), false);\n        const IR::U32 value = ir.BitwiseAnd(extracted, ir.Imm32(255));\n        const IR::U32 shifted = output_byte == 0 ? value :\n            IR::U32{ir.ShiftLeftLogical(value, ir.Imm32(output_byte * 8u))};\n        result = ir.BitwiseOr(result, shifted);\n    }\n    X(static_cast<IR::Reg>(insn & 255ULL), result);\n\n    static std::atomic<unsigned> implemented_samples{0};\n    const unsigned implemented = EdenGpuBoundedSample(implemented_samples);\n    if (implemented < 8)\n        std::fprintf(stderr, \"EDEN_GPU_PRMT_IMM_INDEX raw=%016llx selector=%04x sample=%u\\n\",\n                     static_cast<unsigned long long>(insn), selector, implemented + 1);\n}\n\n"
prmt_modes_new_methods="void TranslatorVisitor::PRMT_reg(u64 insn) {\n    TranslatePrmt(*this, insn, GetReg20(insn), GetReg39(insn));\n}\n\nvoid TranslatorVisitor::PRMT_rc(u64 insn) {\n    TranslatePrmt(*this, insn, GetReg39(insn), GetCbuf(insn));\n}\n\nvoid TranslatorVisitor::PRMT_cr(u64 insn) {\n    TranslatePrmt(*this, insn, GetCbuf(insn), GetReg39(insn));\n}\n\nvoid TranslatorVisitor::PRMT_imm(u64 insn) {\n    TranslatePrmt(*this, insn, GetImm20(insn), GetReg39(insn));\n}\n\n"
assert expected.count(prmt_modes_old_tail)==1
assert expected.count(prmt_modes_old_methods)==1
expected=expected.replace(prmt_modes_old_tail,prmt_modes_new_tail,1)
expected=expected.replace(prmt_modes_old_methods,prmt_modes_new_methods,1)
assert 'BitField<48, 4, u64> mode;' in expected
assert 'PrmtMode::Forward4Extract' in expected
assert 'PrmtMode::Backward4Extract' in expected
assert 'PrmtMode::Replicate8' in expected
assert 'PrmtMode::EdgeClampLeft' in expected
assert 'PrmtMode::EdgeClampRight' in expected
assert 'PrmtMode::Replicate16' in expected
assert 'throw NotImplementedException("PRMT reserved mode {}", raw_mode)' in expected
# PRMT no longer samples runtime diagnostics: all documented modes are handled,
# while reserved modes fail directly. Remove the now-unused helper/includes
# exactly so native Clang cannot warn on a dormant static function.
retired_prmt_diagnostics='#include <atomic>\n#include <cstdio>\n'+helper+'\n'
assert expected.count(retired_prmt_diagnostics)==1
expected=expected.replace(retired_prmt_diagnostics,'',1)
assert "EdenGpuBoundedSample" not in expected

# Regular Maxwell IMAD uses the already-reviewed IMUL high-word helper.
# Only LOW/HI reg/rc/cr/imm are admitted; X/SAT/CC remain fail-closed.
imad_helper="// Maxwell GM107 IMAD: low multiplication is sign-independent modulo 2^32;\n// HI uses the same signed/unsigned high-word product as IMUL, then adds C.\n// X/SAT/CC have independent carry/saturation/flag semantics and remain\n// deliberately fail-closed until those contracts are implemented.\nvoid TranslateIMad(TranslatorVisitor& v, u64 insn, const IR::U32& src_b,\n                   const IR::U32& src_c) {\n    union {\n        u64 raw;\n        BitField<0, 8, IR::Reg> dest_reg;\n        BitField<8, 8, IR::Reg> src_reg_a;\n        BitField<47, 1, u64> cc;\n        BitField<48, 1, u64> is_a_signed;\n        BitField<49, 1, u64> extended;\n        BitField<50, 1, u64> saturate;\n        BitField<53, 1, u64> is_b_signed;\n        BitField<54, 1, u64> high;\n    } const imad{insn};\n\n    if (imad.extended != 0 || imad.saturate != 0 || imad.cc != 0) {\n        throw NotImplementedException(\"IMAD X/SAT/CC modifiers\");\n    }\n    const IR::U32 src_a{v.X(imad.src_reg_a)};\n    const IR::U32 product{\n        imad.high != 0\n            ? MultiplyHigh(v, src_a, src_b, imad.is_a_signed != 0, imad.is_b_signed != 0)\n            : v.ir.IMul(src_a, src_b)};\n    v.X(imad.dest_reg, v.ir.IAdd(product, src_c));\n}\n\n"
imad_prmt_anchor="// NVIDIA PTX prmt.b32 specialized controls"
assert expected.count(imad_prmt_anchor)==1
expected=expected.replace(imad_prmt_anchor,imad_helper+imad_prmt_anchor,1)
imad_rewrites=[["void TranslatorVisitor::IMAD_reg(u64) {\n    ThrowNotImplemented(Opcode::IMAD_reg);\n}\n","void TranslatorVisitor::IMAD_reg(u64 insn) {\n    TranslateIMad(*this, insn, GetReg20(insn), GetReg39(insn));\n}\n"],["void TranslatorVisitor::IMAD_rc(u64) {\n    ThrowNotImplemented(Opcode::IMAD_rc);\n}\n","void TranslatorVisitor::IMAD_rc(u64 insn) {\n    TranslateIMad(*this, insn, GetReg39(insn), GetCbuf(insn));\n}\n"],["void TranslatorVisitor::IMAD_cr(u64) {\n    ThrowNotImplemented(Opcode::IMAD_cr);\n}\n","void TranslatorVisitor::IMAD_cr(u64 insn) {\n    TranslateIMad(*this, insn, GetCbuf(insn), GetReg39(insn));\n}\n"],["void TranslatorVisitor::IMAD_imm(u64) {\n    ThrowNotImplemented(Opcode::IMAD_imm);\n}\n","void TranslatorVisitor::IMAD_imm(u64 insn) {\n    TranslateIMad(*this, insn, GetImm20(insn), GetReg39(insn));\n}\n"]]
for old,new in imad_rewrites:
    assert expected.count(old)==1
    expected=expected.replace(old,new,1)
assert 'throw NotImplementedException("IMAD X/SAT/CC modifiers")' in expected
assert 'BitField<48, 1, u64> is_a_signed;' in expected
assert 'BitField<49, 1, u64> extended;' in expected
assert 'BitField<50, 1, u64> saturate;' in expected
assert 'BitField<53, 1, u64> is_b_signed;' in expected
assert 'BitField<54, 1, u64> high;' in expected
assert 'ThrowNotImplemented(Opcode::IMAD32I);' in expected
assert 'ThrowNotImplemented(Opcode::IMADSP_reg);' in expected

# IMAD32I is a separate encoding. Admit only LOW/HI with no CC or operand
# negations; its addend is the pre-instruction destination register.
imad32_old="void TranslatorVisitor::IMAD32I(u64) {\n    ThrowNotImplemented(Opcode::IMAD32I);\n}\n"
imad32_new="void TranslatorVisitor::IMAD32I(u64 insn) {\n    // GM107 IMAD32I: D = A * imm32 + old(D). The low word is independent\n    // of signedness; HI uses bits 54/57 as the A/B signed-type selectors.\n    // Negating A or the addend and publishing condition codes remain\n    // fail-closed until their exact arithmetic flag contracts are covered.\n    union {\n        u64 raw;\n        BitField<0, 8, IR::Reg> dest_reg;\n        BitField<8, 8, IR::Reg> src_reg_a;\n        BitField<52, 1, u64> cc;\n        BitField<53, 1, u64> high;\n        BitField<54, 1, u64> is_a_signed;\n        BitField<55, 1, u64> negate_addend;\n        BitField<56, 1, u64> negate_a;\n        BitField<57, 1, u64> is_b_signed;\n    } const imad{insn};\n\n    if (imad.cc != 0 || imad.negate_addend != 0 || imad.negate_a != 0) {\n        throw NotImplementedException(\"IMAD32I CC/NEG modifiers\");\n    }\n    const IR::U32 src_a{X(imad.src_reg_a)};\n    const IR::U32 src_b{GetImm32(insn)};\n    const IR::U32 product{\n        imad.high != 0\n            ? MultiplyHigh(*this, src_a, src_b, imad.is_a_signed != 0, imad.is_b_signed != 0)\n            : ir.IMul(src_a, src_b)};\n    X(imad.dest_reg, ir.IAdd(product, X(imad.dest_reg)));\n}\n"
assert expected.count(imad32_old)==1
expected=expected.replace(imad32_old,imad32_new,1)
assert 'BitField<52, 1, u64> cc;' in expected
assert 'BitField<53, 1, u64> high;' in expected
assert 'BitField<54, 1, u64> is_a_signed;' in expected
assert 'BitField<55, 1, u64> negate_addend;' in expected
assert 'BitField<56, 1, u64> negate_a;' in expected
assert 'BitField<57, 1, u64> is_b_signed;' in expected
assert 'throw NotImplementedException("IMAD32I CC/NEG modifiers")' in expected
assert 'ThrowNotImplemented(Opcode::IMADSP_reg);' in expected
# CFG-owned Maxwell control instructions: the CFG consumes all actual
# branch/reconvergence semantics. The visitor sees only statically false
# branches or stack markers with no remaining data-path IR side effect.
control_flow_rewrites=[["void TranslatorVisitor::BRA(u64) {\n    ThrowNotImplemented(Opcode::BRA);\n}\n","void TranslatorVisitor::BRA(u64) {\n    // CFG owns the branch. This visitor is reached only when the predicate is statically false.\n}\n"],["void TranslatorVisitor::BRK(u64) {\n    ThrowNotImplemented(Opcode::BRK);\n}\n","void TranslatorVisitor::BRK(u64) {\n    // CFG owns the break token/branch. A statically false branch is a no-op here.\n}\n"],["void TranslatorVisitor::CONT(u64) {\n    ThrowNotImplemented(Opcode::CONT);\n}\n","void TranslatorVisitor::CONT(u64) {\n    // CFG owns the continue token/branch. A statically false branch is a no-op here.\n}\n"],["void TranslatorVisitor::JMP(u64) {\n    ThrowNotImplemented(Opcode::JMP);\n}\n","void TranslatorVisitor::JMP(u64) {\n    // CFG owns the jump. This visitor is reached only when the predicate is statically false.\n}\n"],["void TranslatorVisitor::LONGJMP(u64) {\n    ThrowNotImplemented(Opcode::LONGJMP);\n}\n","void TranslatorVisitor::LONGJMP(u64) {\n    // CFG owns the token pop/branch. A statically false branch is a no-op here.\n}\n"],["void TranslatorVisitor::RET(u64) {\n    ThrowNotImplemented(Opcode::RET);\n}\n","void TranslatorVisitor::RET(u64) {\n    // CFG owns function return. A statically false return is a no-op here.\n}\n"],["void TranslatorVisitor::SYNC(u64) {\n    ThrowNotImplemented(Opcode::SYNC);\n}\n","void TranslatorVisitor::SYNC(u64) {\n    // CFG owns the SSY token pop/branch. A statically false sync is a no-op here.\n}\n"],["void TranslatorVisitor::PEXIT(u64) {\n    ThrowNotImplemented(Opcode::PEXIT);\n}\n","void TranslatorVisitor::PEXIT(u64) {\n    // CFG records the PEXIT reconvergence token; there is no data-path IR side effect.\n}\n"],["void TranslatorVisitor::PLONGJMP(u64) {\n    ThrowNotImplemented(Opcode::PLONGJMP);\n}\n","void TranslatorVisitor::PLONGJMP(u64) {\n    // CFG records the PLONGJMP reconvergence token; there is no data-path IR side effect.\n}\n"]]
for old_method,new_method in control_flow_rewrites:
    assert expected.count(old_method)==1
    expected=expected.replace(old_method,new_method,1)
for name in ("BRA","BRK","CONT","JMP","LONGJMP","RET","SYNC","PEXIT","PLONGJMP"):
    assert f"ThrowNotImplemented(Opcode::{name});" not in expected
pret_visitor_old="void TranslatorVisitor::PRET(u64) {\n    ThrowNotImplemented(Opcode::PRET);\n}\n"
pret_visitor_new="void TranslatorVisitor::PRET(u64) {\n    // CFG already records the supported direct PRET return token.\n}\n"
assert expected.count(pret_visitor_old)==1
expected=expected.replace(pret_visitor_old,pret_visitor_new,1)
assert "ThrowNotImplemented(Opcode::PRET);" not in expected
assert "ThrowNotImplemented(Opcode::JCAL);" in expected
def git_blob(text):
    data=text.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()

# The historical reconstruction above checks every reviewed semantic successor,
# while exact Git blobs seal the two complete sources actually compared. This
# avoids coupling byte identity to obsolete intermediate whitespace/order.
assert git_blob(pristine)=="02553558a826d31e76c20eb53bf729af8de4a6b7"
assert git_blob(actual)=="a22e8c635831d970fced9a5b2afaf9c6851b7460"
# IMAD/IMAD32I AvgMode is a 2-bit field, not two independent booleans.
# Modes 1/2 are reviewed negate-addend/negate-multiplier operations; mode 3
# remains fail-closed. CC/X/SAT are deliberately still unsupported.
assert "enum class ImadNegation : u32" in actual
assert "BitField<51, 2, u64> negation;" in actual
assert "BitField<55, 2, u64> negation;" in actual
assert 'throw NotImplementedException("IMAD reserved PlusOne mode")' in actual
assert 'throw NotImplementedException("IMAD32I reserved PlusOne mode")' in actual
assert 'throw NotImplementedException("IMAD X/SAT/CC modifiers")' in actual
assert 'throw NotImplementedException("IMAD32I CC modifier")' in actual
assert "negate_addend" not in actual and "negate_a" not in actual
assert actual.count("ImadNegation::Multiplier") >= 2
assert actual.count("ImadNegation::Addend") >= 2
# IMADSP is intentionally bounded to the qualified Maxwell forms. The .CC
# flag contract and C width 3 remain fail-closed.
assert "enum class ImadSpType : u32" in actual
for imadsp_type in ("U32", "S32", "U24", "S24", "U16Lo", "S16Lo", "U16Hi", "S16Hi"):
    assert imadsp_type in actual
assert "BitField<47, 1, u64> cc;" in actual
assert "BitField<48, 3, u64> a_type;" in actual
assert "BitField<51, 2, u64> c_width;" in actual
assert "BitField<53, 2, u64> b_type;" in actual
assert 'throw NotImplementedException("IMADSP CC modifier")' in actual
assert 'throw NotImplementedException("IMADSP reserved C width")' in actual
for imadsp_method in ("IMADSP_reg", "IMADSP_rc", "IMADSP_cr", "IMADSP_imm"):
    assert f"void TranslatorVisitor::{imadsp_method}(u64 insn)" in actual
    assert f"ThrowNotImplemented(Opcode::{imadsp_method});" not in actual
# The reviewed shared CAS translator now owns ATOM_cas. Retaining its
# retired stub in the active native PRMT owner produces duplicate symbols
# and silently diverges from the actual source-generation oracle.
cas_owner=(root/"vendor/sources/eden/src/shader_recompiler/frontend/maxwell/translate/impl/atomic_operations_global_memory.cpp").read_text()
assert "void TranslatorVisitor::ATOM_cas(u64 insn)" in cas_owner
assert "void TranslatorVisitor::ATOM_cas(u64)" not in actual
assert "EdenGpuBoundedSample" not in actual and "EdenPrmtIndexReference" in actual
assert "static_assert(EdenPrmtIndexReference" in actual
assert 'target_sources(shader_recompiler PRIVATE "${EDEN_MAINTAINED_NATIVE_PRMT}")' in module
assert 'target_sources(shader_recompiler PRIVATE "${EDEN_MAINTAINED_MAXWELL_CONTROL_FLOW}")' in module
assert 'list(FILTER shader_cfg_sources EXCLUDE REGEX "frontend/maxwell/control_flow[.]cpp$")' in module
assert 'write_derived("${PORT_BUILD_DIR}/maxwell_prmt_observed.cpp"' not in module

control_pristine=(root/"vendor/sources/eden/src/shader_recompiler/frontend/maxwell/control_flow.cpp").read_text()
control_actual=(root/"vendor/encore-active/eden/src/shader_recompiler/frontend/maxwell/control_flow.cpp").read_text()
pret_flow_old='    case Opcode::PRET:\n        throw NotImplementedException("PRET flow analysis");\n'
pret_flow_new='''    case Opcode::PRET:
        // GM107 PRET stores a return target in the PRET stack. Support the
        // ordinary direct form used by Nouveau; cbuf targets and NOINC have
        // separate semantics and remain fail-closed until explicitly modeled.
        if (inst.branch.is_cbuf) {
            throw NotImplementedException("PRET with constant buffer target");
        }
        if ((inst.raw & (u64{1} << 6)) != 0) {
            throw NotImplementedException("PRET noinc");
        }
        block->stack.Push(Token::PRET, BranchOffset(pc, inst));
        return AnalysisState::Continue;
'''
assert control_pristine.count(pret_flow_old)==1
assert control_actual.count(pret_flow_new)==1
assert control_actual.replace(pret_flow_new,pret_flow_old,1)==control_pristine
# The shipping Fermi2D owner never samples diagnostics. Reintroducing
# the helper there produces -Wunused-function on native Clang; only the
# optional experiment needs the bounded logging helper.
fermi_default = (root / "vendor/encore-active/eden-core/src/video_core/engines/fermi_2d_observed.cpp").read_text()
fermi_experiment = (root / "vendor/encore-active/eden-core/src/video_core/engines/fermi_2d_experimental.cpp").read_text()
assert "EdenGpuBoundedSample" not in fermi_default, "shipping Fermi2D has unused sampling helper"
assert helper.strip() in fermi_experiment, "experimental Fermi2D lost its bounded sample helper"
assert "set(gpu_bounded_sample_helper [=[" not in module
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_FERMI_FILE}")' in module
# PIXLD.CovMask is a cross-file IR/backend contract. Keep the production
# SPIR-V chain and its fail-closed GLASM sibling together in the existing
# maintained-Maxwell gate instead of adding another standalone checker.
sample_pixel=(root/"vendor/encore-active/eden/src/shader_recompiler/frontend/maxwell/translate/impl/pixel_load.cpp").read_text()
sample_ir=(root/"vendor/encore-active/eden/src/shader_recompiler/frontend/ir/ir_emitter.cpp").read_text()
sample_opcodes=(root/"vendor/encore-active/eden/src/shader_recompiler/frontend/ir/opcodes.inc").read_text()
sample_info=(root/"vendor/encore-active/eden/src/shader_recompiler/shader_info.h").read_text()
sample_collect=(root/"vendor/encore-active/eden/src/shader_recompiler/ir_opt/collect_shader_info_pass.cpp").read_text()
sample_spirv=(root/"vendor/encore-active/eden/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp").read_text()
sample_spirv_ctx=(root/"vendor/encore-active/eden/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp").read_text()
sample_glsl=(root/"vendor/encore-active/eden/src/shader_recompiler/backend/glsl/emit_glsl_context_get_set.cpp").read_text()
sample_glasm=(root/"vendor/encore-active/eden/src/shader_recompiler/backend/glasm/emit_glasm_context_get_set.cpp").read_text()
sample_cmake=(root/"headless/CMakeLists.txt").read_text()
assert "case Mode::CovMask:" in sample_pixel and "ir.SampleMask()" in sample_pixel
assert "U32 IREmitter::SampleMask()" in sample_ir
assert "OPCODE(SampleMask," in sample_opcodes
assert "bool uses_sample_mask{};" in sample_info
assert "case IR::Opcode::SampleMask:" in sample_collect
assert "ctx.input_sample_mask" in sample_spirv
assert "spv::BuiltIn::SampleMask" in sample_spirv_ctx
assert "gl_SampleMaskIn[0]" in sample_glsl
assert "// not implemented yet on Encore" in sample_glasm
for sample_unit in (
    "backend/spirv/emit_spirv_context_get_set.cpp",
    "backend/spirv/spirv_emit_context.cpp",
    "frontend/maxwell/translate/impl/pixel_load.cpp",
):
    assert sample_unit in sample_cmake
image_atomic=(root/"vendor/encore-active/eden/src/shader_recompiler/backend/spirv/emit_spirv_image_atomic.cpp").read_text()
assert "Id ImageAtomicCasU32(" in image_atomic
assert "OpAtomicLoad(ctx.U32[1], pointer, scope, semantics)" in image_atomic
assert "OpAtomicCompareExchange(ctx.U32[1], pointer, scope, semantics" in image_atomic
assert "ImageCasOperation::Increment" in image_atomic
assert "ImageCasOperation::Decrement" in image_atomic
assert "old >= limit ? 0 : old + 1" in image_atomic
assert "old == 0 || old > limit ? limit : old - 1" in image_atomic
assert 'throw NotImplementedException("Image indexing")' in image_atomic
assert "backend/spirv/emit_spirv_image_atomic.cpp" in sample_cmake

image_descriptor=(root/"vendor/encore-active/eden/src/shader_recompiler/backend/spirv/emit_spirv_image.cpp").read_text()
assert 'DescType(*this, image_type, pointer_type, desc.count)' in sample_spirv_ctx
assert sample_spirv_ctx.count('DescType(*this, image_type, pointer_type, desc.count)') >= 2
assert 'CheckedTextureArrayIndex(EmitContext& ctx' in image_descriptor
assert 'Image descriptor array index out of range' in image_descriptor
assert 'Dynamic image descriptor requires non-uniform indexing support' in image_descriptor
assert 'CheckedAtomicImageIndex(EmitContext& ctx' in image_atomic
assert 'Atomic image descriptor array index out of range' in image_atomic
assert 'Dynamic atomic image descriptor requires non-uniform indexing support' in image_atomic
assert 'ctx.OpAccessChain(def.pointer_type, def.id, idx)' in image_atomic
assert 'ctx.uses_nonuniform_storage_image = true' in image_atomic
assert 'ctx.uses_nonuniform_storage_texel_buffer = true' in image_atomic
assert "backend/spirv/emit_spirv_image.cpp" in sample_cmake
shared_cas=(root/"vendor/encore-active/eden/src/shader_recompiler/frontend/maxwell/translate/impl/atomic_operations_shared_memory.cpp").read_text()
assert "void TranslatorVisitor::ATOMS_cas(u64 insn)" in shared_cas
assert "AtomsCasBcRz::Pair" in shared_cas
assert "AtomsCasBcRz::ReplacementRz" in shared_cas
assert "AtomsCasBcRz::CompareRz" in shared_cas
assert 'throw NotImplementedException("ATOMS.CAS reserved BcRz mode")' in shared_cas
assert 'throw NotImplementedException("ATOMS.CAS sub-operation {}"' in shared_cas
assert "ir.SharedAtomicCompareExchange(offset, comparator, replacement)" in shared_cas
assert "void TranslatorVisitor::ATOMS_cas" not in actual
print("VENDOR_MAINTAINED_MAXWELL_SHADER_PARITY_PASS: PRMT modes 0-6 + IMUL + IMAD/IMAD32I NEG + bounded IMADSP + ATOMS.CAS.B32 + CFG control/PRET + PIXLD.CovMask SampleMask + bounded storage image arrays + image atomic Inc32/Dec32 CAS, unsupported forms fail-closed")
