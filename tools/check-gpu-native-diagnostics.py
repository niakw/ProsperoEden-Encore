#!/usr/bin/env python3
"""Check Maxwell PRMT/IMUL translation and bounded Fermi2D software slice support.

Reserved PRMT encodings and unsupported block-linear layers remain unimplemented.
This is a source contract, not a native graphics correctness test.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cmake = (ROOT / "headless/gpu_native_observability.cmake").read_text()
launcher = (ROOT / "headless/CMakeLists.txt").read_text()
assert 'include("${CMAKE_CURRENT_LIST_DIR}/gpu_native_observability.cmake")' in launcher
assert cmake.count('if(NOT PS5_NATIVE)') == 1
# FC27 hardware regression: unqualified 3D/pitch software blits can skip
# texture writes and stall the GPU frame. They must not be compiled by default.
assert 'EDEN_UNQUALIFIED_FERMI2D_COPY' not in cmake
assert cmake.count('"${EDEN_MAINTAINED_FERMI_ROOT}/fermi_2d_observed.cpp"') == 1
assert 'fermi_2d_experimental.cpp' not in cmake
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_FERMI_FILE}")' in cmake
assert 'target_sources(shader_recompiler PRIVATE "${EDEN_MAINTAINED_NATIVE_PRMT}")' in cmake
assert 'target_sources(shader_recompiler PRIVATE "${EDEN_MAINTAINED_MAXWELL_CONTROL_FLOW}")' in cmake
assert 'list(FILTER shader_cfg_sources EXCLUDE REGEX "frontend/maxwell/control_flow[.]cpp$")' in cmake
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_NATIVE_BLITTER}")' in cmake
assert 'write_derived(' not in cmake and 'string(REPLACE' not in cmake
# PRMT is now compiled from a full maintained shader unit, while Fermi
# below still carries one isolated CMake generator.
prmt = (ROOT / "vendor/encore-active/eden/src/shader_recompiler/frontend/maxwell/translate/impl/not_implemented.cpp").read_text()
pinned_prmt = (ROOT / "vendor/sources/eden/src/shader_recompiler/frontend/maxwell/translate/impl/not_implemented.cpp").read_text()
def extract_method(text: str, sig: str) -> str:
    match = re.search(r"^void TranslatorVisitor::" + sig + r"\([^\n]*\) \{\n.*?^\}\n", text, re.S | re.M)
    assert match, sig
    return match.group(0)
prmt_old = extract_method(pinned_prmt, "PRMT_imm")
prmt_reg_old = extract_method(pinned_prmt, "PRMT_reg")
prmt_new = extract_method(prmt, "PRMT_imm")
prmt_reg_new = extract_method(prmt, "PRMT_reg")
# The same complete native source now owns generic Maxwell IMUL forms.
# Verify all four decoded forms are translated while condition-code variants
# remain deliberately fail-closed until their flag semantics are implemented.
for imul_name in ("IMUL_reg", "IMUL_cbuf", "IMUL_imm", "IMUL32I"):
    old = extract_method(pinned_prmt, imul_name)
    new = extract_method(prmt, imul_name)
    assert "ThrowNotImplemented(Opcode::" + imul_name + ");" in old
    assert "TranslateIMul(*this, insn" in new
assert "IR::U32 MultiplyHigh(" in prmt
assert "BitField<39, 1, u64> high;" in prmt
assert "BitField<40, 1, u64> is_a_signed;" in prmt
assert "BitField<41, 1, u64> is_b_signed;" in prmt
assert "BitField<47, 1, u64> cc;" in prmt
assert "BitField<52, 1, u64> cc;" in prmt
assert "BitField<53, 1, u64> high;" in prmt
assert "BitField<54, 1, u64> is_a_signed;" in prmt
assert "BitField<55, 1, u64> is_b_signed;" in prmt
assert 'throw NotImplementedException("IMUL.CC")' in prmt
# Bounded regular IMAD: all four ordinary operand forms translate LOW/HI,
# while extended carry, saturation and condition-code publication remain refused.
for imad_name in ("IMAD_reg", "IMAD_rc", "IMAD_cr", "IMAD_imm"):
    old = extract_method(pinned_prmt, imad_name)
    new = extract_method(prmt, imad_name)
    assert "ThrowNotImplemented(Opcode::" + imad_name + ");" in old
    assert "TranslateIMad(*this, insn" in new
assert "void TranslateIMad(" in prmt
assert "BitField<48, 1, u64> is_a_signed;" in prmt
assert "BitField<49, 1, u64> extended;" in prmt
assert "BitField<50, 1, u64> saturate;" in prmt
assert "BitField<51, 2, u64> negation;" in prmt
assert "BitField<53, 1, u64> is_b_signed;" in prmt
assert "BitField<54, 1, u64> high;" in prmt
assert "enum class ImadNegation : u32" in prmt
assert "ImadNegation::Addend" in prmt and "ImadNegation::Multiplier" in prmt
assert 'throw NotImplementedException("IMAD reserved PlusOne mode")' in prmt
assert 'throw NotImplementedException("IMAD X/SAT/CC modifiers")' in prmt
imad32_old = extract_method(pinned_prmt, "IMAD32I")
imad32_new = extract_method(prmt, "IMAD32I")
assert "ThrowNotImplemented(Opcode::IMAD32I);" in imad32_old
assert "BitField<52, 1, u64> cc;" in imad32_new
assert "BitField<53, 1, u64> high;" in imad32_new
assert "BitField<54, 1, u64> is_a_signed;" in imad32_new
assert "BitField<55, 2, u64> negation;" in imad32_new
assert "BitField<57, 1, u64> is_b_signed;" in imad32_new
assert 'throw NotImplementedException("IMAD32I CC modifier")' in imad32_new
assert 'throw NotImplementedException("IMAD32I reserved PlusOne mode")' in imad32_new
assert "IR::U32 addend{X(imad.dest_reg)};" in imad32_new
assert "X(imad.dest_reg, ir.IAdd(product, addend));" in imad32_new
for imadsp_name in ("IMADSP_reg", "IMADSP_rc", "IMADSP_cr", "IMADSP_imm"):
    imadsp_old = extract_method(pinned_prmt, imadsp_name)
    imadsp_new = extract_method(prmt, imadsp_name)
    assert "ThrowNotImplemented(Opcode::" + imadsp_name + ");" in imadsp_old
    assert "TranslateIMadSp(*this, insn" in imadsp_new
assert "enum class ImadSpType : u32" in prmt
assert "IR::U32 ExtractImadSp(" in prmt
assert "void TranslateIMadSp(" in prmt
assert 'throw NotImplementedException("IMADSP CC modifier")' in prmt
assert 'throw NotImplementedException("IMADSP reserved C width")' in prmt

# CFG-owned control instructions have no remaining data-path work in the
# visitor. For ordinary branches, Translate() sees them only when the CFG
# proved the branch statically false; PEXIT/PLONGJMP are reconvergence tokens
# already pushed by CFG::AnalyzeInst before translation continues.
control_noops=("BRA","BRK","CONT","JMP","LONGJMP","RET","SYNC","PEXIT","PLONGJMP")
for name in control_noops:
    old = extract_method(pinned_prmt, name)
    new = extract_method(prmt, name)
    assert "ThrowNotImplemented(Opcode::" + name + ");" in old
    assert "ThrowNotImplemented" not in new
assert "ThrowNotImplemented(Opcode::PRET);" in pinned_prmt
assert "ThrowNotImplemented(Opcode::PRET);" not in prmt
assert "ThrowNotImplemented(Opcode::JCAL);" in prmt

pinned_control=(ROOT / "vendor/sources/eden/src/shader_recompiler/frontend/maxwell/control_flow.cpp").read_text()
native_control=(ROOT / "vendor/encore-active/eden/src/shader_recompiler/frontend/maxwell/control_flow.cpp").read_text()
for control in (pinned_control,native_control):
    assert "if (pred == Predicate{false}) {\n        return false;\n    }" in control
    assert "case Opcode::BRA:\n    case Opcode::JMP:\n    case Opcode::RET:" in control
    assert "case Opcode::BRK:\n    case Opcode::CONT:\n    case Opcode::LONGJMP:\n    case Opcode::SYNC:" in control
    assert "case Opcode::PEXIT:\n    case Opcode::PLONGJMP:\n    case Opcode::SSY:" in control
    assert "block->stack.Push(OpcodeToken(opcode), BranchOffset(pc, inst));" in control
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
assert pinned_control.count(pret_flow_old)==1
assert native_control.count(pret_flow_new)==1
assert native_control.replace(pret_flow_new,pret_flow_old,1)==pinned_control
pret_old=extract_method(pinned_prmt,"PRET")
pret_new=extract_method(prmt,"PRET")
assert "ThrowNotImplemented(Opcode::PRET);" in pret_old
assert "ThrowNotImplemented" not in pret_new
assert "ThrowNotImplemented(Opcode::JCAL);" in prmt
prmt_reference = prmt
fermi_pinned = (ROOT / "vendor/sources/eden/src/video_core/engines/fermi_2d.cpp").read_text()
fermi_default = (ROOT / "vendor/encore-active/eden/src/video_core/engines/fermi_2d_observed.cpp").read_text()

# GPU-31: preserve exact shipping/retired Fermi provenance. Only the
# reviewed nonzero pitch-layer guards and the software-copy tail are
# reversed on this temporary historical verification COPY.
import hashlib as _fermi_hashlib
def _fermi_blob(data: str) -> str:
    raw = data.encode("utf-8")
    return _fermi_hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
assert _fermi_blob(fermi_default) == "4be53f7b3ec2daf06b54dacc4d77dc4b75e9db05", "GPU-44 active Fermi source drift"
# NV50 DST_LAYER successor: authenticate the shipping source, then reverse
# only the reviewed destination-volume delta on this in-memory receipt copy.
_dst_layer_guard_new = "    // Pitch-linear arrays select a layer by advancing the base address.\n    // NV50 depth-tiled 3D destinations instead use DST_LAYER. Support only\n    // that hardware-defined destination case; source depth-tiling remains\n    // fail-closed because Nouveau cannot feed it through this 2D path.\n    const bool has_layer = regs.src.layer != 0 || regs.dst.layer != 0;\n    const bool pitch_layer_copy =\n        has_layer && regs.src.linear == MemoryLayout::Pitch &&\n        regs.dst.linear == MemoryLayout::Pitch;\n    const bool dst_volume_layer_copy =\n        regs.src.layer == 0 && regs.dst.layer != 0 &&\n        regs.dst.linear == MemoryLayout::BlockLinear && regs.dst.block_depth > 0 &&\n        regs.dst.depth > 1 && regs.dst.layer < regs.dst.depth &&\n        (regs.src.linear == MemoryLayout::Pitch || regs.src.block_depth == 0 ||\n         regs.src.depth == 1) &&\n        regs.src.depth >= 1 && regs.clip_enable == 0;\n    if (pitch_layer_copy) {\n        const auto valid_pitch_layers = [](const Surface& surface) {\n            constexpr u64 MAX_PLANE_BYTES = 256ULL << 20;\n            const u64 bpp = BytesPerBlock(\n                PixelFormatFromRenderTargetFormat(surface.format));\n            if (surface.linear != MemoryLayout::Pitch || surface.depth == 0 ||\n                surface.layer >= surface.depth || surface.width == 0 ||\n                surface.height == 0 || surface.pitch == 0 || bpp == 0 ||\n                bpp > 16 || static_cast<u64>(surface.width) * bpp > surface.pitch) {\n                return false;\n            }\n            const u64 plane = static_cast<u64>(surface.pitch) * surface.height;\n            return plane != 0 && plane <= MAX_PLANE_BYTES;\n        };\n        if (!valid_pitch_layers(regs.src) || !valid_pitch_layers(regs.dst) ||\n            regs.src.format != regs.dst.format || regs.clip_enable != 0) {\n            UNIMPLEMENTED_MSG(\"Unsupported layered Fermi2D surface or operation\");\n            return;\n        }\n    } else if (has_layer && !dst_volume_layer_copy) {\n        UNIMPLEMENTED_MSG(\"Unsupported layered Fermi2D surface or operation\");\n        return;\n    } else if (regs.src.depth == 0 || regs.dst.depth == 0) {\n        UNIMPLEMENTED_MSG(\"Invalid zero-depth Fermi2D surface\");\n        return;\n    }\n"
_dst_layer_guard_old = "    // NVIDIA 2D pitch surfaces have contiguous, pitch*height-sized slices.\n    // Support only explicitly addressed layers of two pitch-linear images.\n    // Block-linear layers require a separate verified origin_z decoder.\n    const bool pitch_layer_copy = regs.src.layer != 0 || regs.dst.layer != 0;\n    if (pitch_layer_copy) {\n        const auto valid_pitch_layers = [](const Surface& surface) {\n            constexpr u64 MAX_PLANE_BYTES = 256ULL << 20;\n            const u64 bpp = BytesPerBlock(\n                PixelFormatFromRenderTargetFormat(surface.format));\n            if (surface.linear != MemoryLayout::Pitch || surface.depth == 0 ||\n                surface.layer >= surface.depth || surface.width == 0 ||\n                surface.height == 0 || surface.pitch == 0 || bpp == 0 ||\n                bpp > 16 || static_cast<u64>(surface.width) * bpp > surface.pitch) {\n                return false;\n            }\n            const u64 plane = static_cast<u64>(surface.pitch) * surface.height;\n            return plane != 0 && plane <= MAX_PLANE_BYTES;\n        };\n        if (!valid_pitch_layers(regs.src) || !valid_pitch_layers(regs.dst) ||\n            regs.src.format != regs.dst.format || regs.clip_enable != 0) {\n            UNIMPLEMENTED_MSG(\"Unsupported layered Fermi2D surface or operation\");\n            return;\n        }\n    } else if (regs.src.depth == 0 || regs.dst.depth == 0) {\n        UNIMPLEMENTED_MSG(\"Invalid zero-depth Fermi2D surface\");\n        return;\n    }\n"
_dst_layer_tail_new = "    if (dst_volume_layer_copy) {\n        // NV50/Nouveau programs DST_LAYER for a depth-tiled 3D destination.\n        // Keep the complete destination backing mapped; the maintained\n        // software writer consumes dst.layer as its explicit GOB origin Z.\n        Surface dst = regs.dst;\n        src.depth = 1;\n        if (!sw_blitter->Blit(src, dst, config)) {\n            UNIMPLEMENTED_MSG(\"Rejected Fermi2D destination volume slice\");\n        }\n        return;\n    }\n"
assert fermi_default.count(_dst_layer_guard_new) == fermi_default.count(_dst_layer_tail_new) == 1
fermi_default = fermi_default.replace(_dst_layer_guard_new, _dst_layer_guard_old, 1).replace(_dst_layer_tail_new, "", 1)
assert _fermi_blob(fermi_default) == "2319fa5c787f5b772a7af3fe0e9801cc99c1479e", "GPU-44 DST_LAYER predecessor drift"
_new_guard = "    // Never treat an unsupported 2D operation as a SrcCopy: soft\n    // assertions return in release and would silently overwrite guest RAM.\n    if (regs.operation != Operation::SrcCopy) {\n        UNIMPLEMENTED_MSG(\"Operation is not copy\");\n        return;\n    }\n    // RenderTargetFormat::NONE is an unbound/disabled surface, not RGBA8.\n    // PixelFormatFromRenderTargetFormat historically falls back to RGBA8 for\n    // unknown values, which would turn format 0 into a real copy and corrupt\n    // guest pixels. Reject it before any bytes-per-block or converter lookup.\n    if (regs.src.format == RenderTargetFormat::NONE ||\n        regs.dst.format == RenderTargetFormat::NONE) {\n        UNIMPLEMENTED_MSG(\"Fermi2D copy with unbound render-target format\");\n        return;\n    }\n    // NVIDIA 2D pitch surfaces have contiguous, pitch*height-sized slices.\n    // Support only explicitly addressed layers of two pitch-linear images.\n    // Block-linear layers require a separate verified origin_z decoder.\n    const bool pitch_layer_copy = regs.src.layer != 0 || regs.dst.layer != 0;\n    if (pitch_layer_copy) {\n        const auto valid_pitch_layers = [](const Surface& surface) {\n            constexpr u64 MAX_PLANE_BYTES = 256ULL << 20;\n            const u64 bpp = BytesPerBlock(\n                PixelFormatFromRenderTargetFormat(surface.format));\n            if (surface.linear != MemoryLayout::Pitch || surface.depth == 0 ||\n                surface.layer >= surface.depth || surface.width == 0 ||\n                surface.height == 0 || surface.pitch == 0 || bpp == 0 ||\n                bpp > 16 || static_cast<u64>(surface.width) * bpp > surface.pitch) {\n                return false;\n            }\n            const u64 plane = static_cast<u64>(surface.pitch) * surface.height;\n            return plane != 0 && plane <= MAX_PLANE_BYTES;\n        };\n        if (!valid_pitch_layers(regs.src) || !valid_pitch_layers(regs.dst) ||\n            regs.src.format != regs.dst.format || regs.clip_enable != 0) {\n            UNIMPLEMENTED_MSG(\"Unsupported layered Fermi2D surface or operation\");\n            return;\n        }\n    } else if (regs.src.depth == 0 || regs.dst.depth == 0) {\n        UNIMPLEMENTED_MSG(\"Invalid zero-depth Fermi2D surface\");\n        return;\n    }\n\n"
_old_guard = "    // A soft UNIMPLEMENTED_IF_MSG reports a failure but continues execution.\n    // Never turn unsupported Fermi2D operations or nonzero layers into a\n    // normal SrcCopy of layer zero: that silently overwrites guest pixels.\n    if (regs.operation != Operation::SrcCopy) {\n        UNIMPLEMENTED_MSG(\"Operation is not copy\");\n        return;\n    }\n    if (regs.src.layer != 0) {\n        UNIMPLEMENTED_MSG(\"Source layer is not zero\");\n        return;\n    }\n    if (regs.dst.layer != 0) {\n        UNIMPLEMENTED_MSG(\"Destination layer is not zero\");\n        return;\n    }\n    if (regs.src.depth != 1) {\n        UNIMPLEMENTED_MSG(\"Source depth is not one\");\n        return;\n    }\n\n"
_new_tail = "    memory_manager.FlushCaching();\n    if (pitch_layer_copy) {\n        // Copy ONLY the selected pitch-linear slice. The software blitter\n        // snapshots the source before constructing the destination writer,\n        // preserving overlapping guest surfaces. Do not route a layered\n        // operation to TextureCache's layer-zero Vulkan acceleration.\n        Surface dst = regs.dst;\n        const auto select_pitch_layer = [this](Surface& surface) {\n            constexpr u64 MAX_PLANE_BYTES = 256ULL << 20;\n            const u64 plane = static_cast<u64>(surface.pitch) * surface.height;\n            if (plane == 0 || plane > MAX_PLANE_BYTES ||\n                surface.depth == 0 || surface.layer >= surface.depth ||\n                (surface.layer != 0 && plane > ~u64{0} / surface.layer)) {\n                return false;\n            }\n            const u64 offset = plane * surface.layer;\n            const GPUVAddr base = surface.Address();\n            if (base > ~u64{0} - offset ||\n                base + offset > ~u64{0} - plane ||\n                !memory_manager.IsFullyMappedRange(base + offset,\n                                                   static_cast<size_t>(plane))) {\n                return false;\n            }\n            const GPUVAddr selected = base + offset;\n            surface.addr_upper = static_cast<u32>(selected >> 32);\n            surface.addr_lower = static_cast<u32>(selected);\n            surface.layer = 0;\n            surface.depth = 1;\n            return true;\n        };\n        if (!select_pitch_layer(src) || !select_pitch_layer(dst)) {\n            AssertFailSoftImpl();\n            return; // Reject without writing a partial destination layer.\n        }\n        sw_blitter->Blit(src, dst, config);\n        return;\n    }\n    if (!rasterizer->AccelerateSurfaceCopy(src, regs.dst, config)) {\n        // The software swizzler can decode the z=0 subrectangle of a 3D\n        // surface when both guest layer selectors are zero. Preserve the\n        // unresolved non-zero slice case: origin_z is still hard-coded to 0.\n        if (src.depth != 1 || regs.dst.depth != 1) {\n            const bool base_layer_3d_copy =\n                src.depth >= 1 && regs.dst.depth >= 1 &&\n                src.layer == 0 && regs.dst.layer == 0 &&\n                regs.clip_enable == 0;\n            if (!base_layer_3d_copy) {\n                UNIMPLEMENTED_MSG(\"Unresolved Fermi2D volume-slice copy\");\n                return;\n            }\n            Surface dst = regs.dst;\n            src.depth = 1;\n            dst.depth = 1;\n            sw_blitter->Blit(src, dst, config);\n            return;\n        }\n        sw_blitter->Blit(src, regs.dst, config);\n    }"
_old_tail = "    memory_manager.FlushCaching();\n    if (!rasterizer->AccelerateSurfaceCopy(src, regs.dst, config)) {\n        sw_blitter->Blit(src, regs.dst, config);\n    }"
assert fermi_default.count(_new_guard) == fermi_default.count(_new_tail) == 1
fermi_default = fermi_default.replace(_new_guard, _old_guard, 1).replace(_new_tail, _old_tail, 1)
assert _fermi_blob(fermi_default) == "ab64638f45d3ca2e15f8204a2ed22a611fe5cd78", "GPU-31 predecessor Fermi source drift"


# Native register method bounds were hardened after the pinned Eden source.
# Reverse the two exact hunks only while proving historical source parity.
fermi_direct_new = """    // Assertions can be soft in release. Reject the guest method before
    // indexing the register file; an out-of-range write corrupts emulator state.
    if (method >= Regs::NUM_REGS) {
        ASSERT_MSG(false, "Invalid Fermi2D register, increase the size of the Regs structure");
        return;
    }
    regs.reg_array[method] = method_argument;"""
fermi_direct_old = """    ASSERT_MSG(method < Regs::NUM_REGS, "Invalid Fermi2D register, increase the size of the Regs structure");
    regs.reg_array[method] = method_argument;"""
fermi_sink_new = """    for (auto [method, value] : method_sink) {
        if (method >= Regs::NUM_REGS) {
            ASSERT_MSG(false, "Invalid deferred Fermi2D register");
            continue;
        }
        regs.reg_array[method] = value;
    }"""
fermi_sink_old = """    for (auto [method, value] in method_sink) {
        regs.reg_array[method] = value;
    }""".replace(" in method_sink)", " : method_sink)")
for reviewed, original in ((fermi_direct_new, fermi_direct_old),
                           (fermi_sink_new, fermi_sink_old)):
    assert fermi_default.count(reviewed) == 1, "Native Fermi register bounds source drift"
    fermi_default = fermi_default.replace(reviewed, original, 1)
# A soft assertion alone does not prevent the unsupported blit from
# changing guest memory. Reverse only the exact reviewed fail-closed hunk
# in this in-memory historical-source proof, never in the compiled owner.
fail_closed_fermi_guard = "    // A soft UNIMPLEMENTED_IF_MSG reports a failure but continues execution.\n    // Never turn unsupported Fermi2D operations or nonzero layers into a\n    // normal SrcCopy of layer zero: that silently overwrites guest pixels.\n    if (regs.operation != Operation::SrcCopy) {\n        UNIMPLEMENTED_MSG(\"Operation is not copy\");\n        return;\n    }\n    if (regs.src.layer != 0) {\n        UNIMPLEMENTED_MSG(\"Source layer is not zero\");\n        return;\n    }\n    if (regs.dst.layer != 0) {\n        UNIMPLEMENTED_MSG(\"Destination layer is not zero\");\n        return;\n    }\n    if (regs.src.depth != 1) {\n        UNIMPLEMENTED_MSG(\"Source depth is not one\");\n        return;\n    }\n"
legacy_soft_fermi_guard = "    UNIMPLEMENTED_IF_MSG(regs.operation != Operation::SrcCopy, \"Operation is not copy\");\n    UNIMPLEMENTED_IF_MSG(regs.src.layer != 0, \"Source layer is not zero\");\n    UNIMPLEMENTED_IF_MSG(regs.dst.layer != 0, \"Destination layer is not zero\");\n    UNIMPLEMENTED_IF_MSG(regs.src.depth != 1, \"Source depth is not one\");\n"
assert fermi_default.count(fail_closed_fermi_guard) == 1
fermi_default = fermi_default.replace(fail_closed_fermi_guard, legacy_soft_fermi_guard, 1)
# Verify the current native clipping implementation, then rewind that ONE
# feature in-memory for the old pinned/experimental parity contract below.
assert "NVIDIA 2D CLIP_X/Y/W/H is a destination scissor" in fermi_default
assert "__builtin_mul_overflow" in fermi_default
assert "left - args.dst_x0, config.src_x0" in fermi_default
assert "right - args.dst_x0, config.src_x1" in fermi_default
assert "top - args.dst_y0, config.src_y0" in fermi_default
assert "bottom - args.dst_y0, config.src_y1" in fermi_default
assert 'UNIMPLEMENTED_IF_MSG(regs.clip_enable != 0, "Clipped blit enabled");' not in fermi_default
fermi_default = fermi_default.replace("#include <algorithm>\n#include <limits>\n\n", "", 1)
clip_start = "    // NVIDIA 2D CLIP_X/Y/W/H is a destination scissor"
clip_end = "\n    const auto need_align_to_pitch ="
assert fermi_default.count(clip_start) == 1
clip_start_pos = fermi_default.index(clip_start)
clip_end_pos = fermi_default.index(clip_end, clip_start_pos)
fermi_default = fermi_default[:clip_start_pos] + fermi_default[clip_end_pos + 1:]
depth_line = '    UNIMPLEMENTED_IF_MSG(regs.src.depth != 1, "Source depth is not one");\n'
assert fermi_default.count(depth_line + "\n") == 1
fermi_default = fermi_default.replace(depth_line + "\n", depth_line +
    '    UNIMPLEMENTED_IF_MSG(regs.clip_enable != 0, "Clipped blit enabled");\n\n', 1)
# Rewind the signed corner offset + safe clipped initialization on the COPY
# to preserve the historical pinned-translation-unit comparison.
assert "__builtin_sub_overflow(srcX" not in fermi_pinned
origin_start = "    if (args.sample_mode.origin == Origin::Corner) {"
origin_end = "    const auto need_align_to_pitch ="
assert fermi_default.count(origin_start) == fermi_pinned.count(origin_start) == 1
a = fermi_default.index(origin_start)
z = fermi_default.index(origin_end, a)
p = fermi_pinned.index(origin_start)
q = fermi_pinned.index(origin_end, p)
fermi_default = fermi_default[:a] + fermi_pinned[p:q] + fermi_default[z:]
fermi_experimental = (ROOT / "vendor/encore-active/eden/src/video_core/engines/fermi_2d_experimental.cpp").read_text()
# The shipping variant adds an audited CodeQL #55 security-only
# replacement of the pitch-alignment address block. Reverse that one
# replacement before comparing to the immutable pinned baseline.
# check-maintained-fermi2d-variants.py separately enforces full parity.
pitch_anchor = "    const auto need_align_to_pitch ="
pitch_end = "\n    memory_manager.FlushCaching();"
def alignment_block(text: str) -> str:
    begin = text.index(pitch_anchor)
    end = text.index(pitch_end, begin)
    return text[begin:end]
secure_pitch = alignment_block(fermi_default)
pinned_pitch = alignment_block(fermi_pinned)
assert secure_pitch == alignment_block(fermi_experimental)
assert "static_cast<u64>(config.src_x0) *" in secure_pitch
assert "static_cast<u64>(bytes_per_pixel)" in secure_pitch
assert "x_offset > ~u64{0} - base_address" in secure_pitch
assert "bytes_per_pixel != 0 &&" in secure_pitch
assert fermi_default.count(secure_pitch) == 1
assert fermi_pinned in fermi_default.replace(secure_pitch, pinned_pitch, 1)
def extract_range(src: str, beginning: str, ending: str) -> str:
    start = src.index(beginning)
    finish = src.index(ending, start)
    return src[start:finish]
fermi_old = fermi_pinned
fermi_layer_old = fermi_pinned
fermi_copy_old = fermi_pinned
fermi_layer_new = extract_range(fermi_experimental,
    "    // For pitch-linear images, one layer starts exactly pitch*height",
    "    // The software swizzler already handles the z=0 subrectangle")
fermi_new = extract_range(fermi_experimental,
    "    // The software swizzler already handles the z=0 subrectangle",
    '    UNIMPLEMENTED_IF_MSG(regs.clip_enable != 0, "Clipped blit enabled");')
fermi_copy_new = extract_range(fermi_experimental,
    "    if (base_layer_3d_copy || pitch_layer_copy) {",
    "\n}\n\n} // namespace")
# Pristine Eden rejects all four PRMT operand forms; the native owner routes
# each decoded form through one implementation covering index + NVIDIA modes 1..6.
for name in ("PRMT_reg", "PRMT_rc", "PRMT_cr", "PRMT_imm"):
    old_method = extract_method(pinned_prmt, name)
    new_method = extract_method(prmt, name)
    assert "ThrowNotImplemented(Opcode::" + name + ");" in old_method
    assert "TranslatePrmt(*this, insn" in new_method
assert "enum class PrmtMode : u32" in prmt
for token in (
    "Forward4Extract = 1", "Backward4Extract = 2", "Replicate8 = 3",
    "EdgeClampLeft = 4", "EdgeClampRight = 5", "Replicate16 = 6",
):
    assert token in prmt, token
# GM107 uses the complete four-bit mode field. Values above RC16 are reserved
# and must never alias a documented operation.
assert "BitField<48, 4, u64> mode;" in prmt
assert 'if (raw_mode > static_cast<u32>(PrmtMode::Replicate16))' in prmt
assert 'throw NotImplementedException("PRMT reserved mode {}", raw_mode)' in prmt
assert "BitField<48, 3, u64> mode;" not in prmt

# Independent NVIDIA PTX table model. output byte numbering is little-endian:
# byte 0 is d.b0; source bytes 0..3 are A and 4..7 are B.
def prmt_table_index(mode: int, selector: int, byte: int) -> int:
    if mode == 1:  # f4e
        return (selector + byte) & 7
    if mode == 2:  # b4e
        return (selector - byte) & 7
    if mode == 3:  # rc8
        return selector
    if mode == 4:  # ecl
        return max(byte, selector)
    if mode == 5:  # ecr
        return min(byte, selector)
    if mode == 6:  # rc16
        return (byte & 1) + 2 * (selector & 1)
    raise ValueError(mode)

expected_tables = {
    1: ((0,1,2,3),(1,2,3,4),(2,3,4,5),(3,4,5,6)),
    2: ((0,7,6,5),(1,0,7,6),(2,1,0,7),(3,2,1,0)),
    3: ((0,0,0,0),(1,1,1,1),(2,2,2,2),(3,3,3,3)),
    4: ((0,1,2,3),(1,1,2,3),(2,2,2,3),(3,3,3,3)),
    5: ((0,0,0,0),(0,1,1,1),(0,1,2,2),(0,1,2,3)),
    6: ((0,1,0,1),(2,3,2,3),(0,1,0,1),(2,3,2,3)),
}
for mode, rows in expected_tables.items():
    for selector, row in enumerate(rows):
        assert tuple(prmt_table_index(mode, selector, byte) for byte in range(4)) == row

def prmt_index(a: int, b: int, selector: int) -> int:
    result = 0
    for out in range(4):
        nibble = (selector >> (out * 4)) & 0xf
        source = b if nibble & 4 else a
        value = (source >> ((nibble & 3) * 8)) & 0xff
        if nibble & 8:
            value = 0xff if value & 0x80 else 0
        result |= value << (out * 8)
    return result

def prmt_special(a: int, b: int, selector: int, mode: int) -> int:
    source64 = (b << 32) | a
    n = selector & 3
    result = 0
    for out in range(4):
        index = prmt_table_index(mode, n, out)
        result |= ((source64 >> (index * 8)) & 0xff) << (out * 8)
    return result

assert prmt_index(0x11223344, 0x55667788, 0x3210) == 0x11223344
assert prmt_index(0x11223344, 0x55667788, 0x7654) == 0x55667788
assert prmt_index(0x80abcdef, 0, 0xbbbb) == 0xffffffff
assert prmt_index(0x11223344, 0x55667788, 0xffff) == 0
for mode in range(1, 7):
    for selector in range(4):
        value = prmt_special(0x11223344, 0x55667788, selector, mode)
        assert 0 <= value <= 0xffffffff

assert "constexpr u32 PrmtTableIndex(" in prmt
assert prmt.count("static_assert(PrmtTableIndex(") >= 6
assert "constexpr unsigned EdenPrmtIndexReference(" in prmt_reference
assert prmt_reference.count("static_assert(EdenPrmtIndexReference(") >= 4
assert 'target_sources(shader_recompiler PRIVATE "${EDEN_MAINTAINED_NATIVE_PRMT}")' in cmake
assert 'write_derived("${PORT_BUILD_DIR}/maxwell_prmt_observed.cpp"' not in cmake

# All documented PRMT modes now execute without runtime sampling. The helper
# would otherwise be an unused static function in native Clang. Fermi's
# optional experiment retains its own bounded helper; shipping Fermi does not.
assert "EdenGpuBoundedSample" not in prmt
assert "EdenGpuBoundedSample" not in fermi_default
assert "unsigned EdenGpuBoundedSample(std::atomic<unsigned>& samples) noexcept" in fermi_experimental
assert "compare_exchange_weak(current, current + 1u," in fermi_experimental
assert "while (current < 8u)" in fermi_experimental
assert "return 8u;" in fermi_experimental
assert "${gpu_bounded_sample_helper}" not in cmake
for part in (prmt_new, prmt_reg_new, fermi_new, fermi_layer_new, fermi_copy_new):
    assert ".fetch_add(1, std::memory_order_relaxed)" not in part
assert "EdenGpuBoundedSample(" not in prmt_new
assert "EdenGpuBoundedSample(" not in prmt_reg_new
assert fermi_new.count("EdenGpuBoundedSample(") == 1
assert fermi_layer_new.count("EdenGpuBoundedSample(") == 1
assert fermi_copy_new.count("EdenGpuBoundedSample(") == 2
assert 'UNIMPLEMENTED_IF_MSG(regs.src.depth != 1, "Source depth is not one")' in fermi_old
assert "regs.src.depth != 1" in fermi_new
assert "EDEN_GPU_FERMI2D_UNSUPPORTED" in fermi_new
assert "if (count < 8)" in fermi_new
for field in ("regs.src.depth", "regs.dst.depth", "regs.src.layer",
              "regs.dst.layer", "regs.src.block_depth", "regs.dst.block_depth",
              "regs.src.Address()", "regs.dst.Address()"):
    assert field in fermi_new, field
assert "regs.src.depth = 1" not in fermi_new
assert "regs.dst.depth = 1" not in fermi_new
assert "src.size.depth = 1" not in fermi_new
assert "LOG_CRITICAL(Debug" in fermi_new
assert fermi_new.count("AssertFailSoftImpl();") == 1
assert fermi_new.index("AssertFailSoftImpl();") > fermi_new.index("if (count < 8)")
# Only layer-0, source depth>1 SrcCopy can use the software blitter.
# Existing decoding routines preserve block-depth layout and hardcode z=0;
# all other cases retain the original soft-assert semantics.
assert "(regs.src.depth > 1 || regs.dst.depth > 1)" in fermi_new
assert "regs.src.depth >= 1 && regs.dst.depth >= 1" in fermi_new
assert "regs.src.layer == 0 && regs.dst.layer == 0" in fermi_new
assert "regs.operation == Operation::SrcCopy" in fermi_new
assert "regs.clip_enable == 0" in fermi_new
assert "regs.src.depth != 1 && !base_layer_3d_copy && !pitch_layer_copy" in fermi_new
assert "if (!rasterizer->AccelerateSurfaceCopy(src, regs.dst, config))" in fermi_copy_old
assert "if (base_layer_3d_copy || pitch_layer_copy)" in fermi_copy_new
# New software layer paths reject negative/overflowed subrects without
# modifying the historical GPU-accelerated normal-depth path.
assert "const bool rect_valid =" in fermi_copy_new
assert "config.src_x0 >= 0 && config.src_y0 >= 0" in fermi_copy_new
assert "config.dst_x0 >= 0 && config.dst_y0 >= 0" in fermi_copy_new
assert "config.src_x1 > config.src_x0" in fermi_copy_new
assert "config.dst_y1 > config.dst_y0" in fermi_copy_new
assert "static_cast<u64>(config.src_x1) <= src.width" in fermi_copy_new
assert "static_cast<u64>(config.src_y1) <= src.height" in fermi_copy_new
assert "static_cast<u64>(config.dst_x1) <= regs.dst.width" in fermi_copy_new
assert "static_cast<u64>(config.dst_y1) <= regs.dst.height" in fermi_copy_new
assert "EDEN_GPU_FERMI2D_SOFTWARE_BOUNDS_INVALID" in fermi_copy_new
assert "const bool copy_storage_valid =" in fermi_copy_new
assert "src_bpp != 0 && dst_bpp != 0" in fermi_copy_new
assert "static_cast<u64>(surface.pitch) * surface.height <= 0xffffffffULL" in fermi_copy_new
assert "const bool copy_sizes_valid = rect_valid && copy_storage_valid" in fermi_copy_new
assert "const auto valid_byte_count =" in fermi_copy_new
assert "bpp == 0 || bpp > 0xffffffffULL" in fermi_copy_new
assert "width <= max / bpp" in fermi_copy_new
assert "height <= max / (width * bpp)" in fermi_copy_new
assert "valid_byte_count(config.src_x0, config.src_x1," in fermi_copy_new
assert "valid_byte_count(config.dst_x0, config.dst_x1," in fermi_copy_new

# The admissible decoded byte count is bounded without first evaluating
# width*height*bpp. This matters even for intentionally malformed guest regs.
def valid_byte_count(width: int, height: int, bpp: int) -> bool:
    cap = (1 << 32) - 1
    return (width > 0 and height > 0 and 0 < bpp <= cap
            and width <= cap // bpp and height <= cap // (width * bpp))
assert valid_byte_count(1920, 1080, 4)
assert valid_byte_count(65535, 65535, 1)
assert not valid_byte_count(65536, 65536, 1)
assert not valid_byte_count((1 << 31) - 1, (1 << 31) - 1, 16)
assert not valid_byte_count(1920, 1080, 0)
assert not valid_byte_count(1, 1, (1 << 32))
assert fermi_copy_new.index("if (!copy_sizes_valid)") < fermi_copy_new.index("sw_blitter->Blit(src, dst, config);")

# Nonzero layers are only copied using simple pitch-linear planes.
# The layer stride is pitch*height; 3D swizzled z>0 remains unsupported.
assert "regs.src.layer != 0" in fermi_layer_old
assert "regs.dst.layer != 0" in fermi_layer_old
assert "const bool pitch_layer_copy =" in fermi_layer_new
assert "regs.src.linear == MemoryLayout::Pitch" in fermi_layer_new
assert "regs.dst.linear == MemoryLayout::Pitch" in fermi_layer_new
assert "regs.src.layer < regs.src.depth && regs.dst.layer < regs.dst.depth" in fermi_layer_new
assert "regs.src.format == regs.dst.format" in fermi_layer_new
assert "BytesPerBlock(PixelFormatFromRenderTargetFormat(regs.src.format))" in fermi_layer_new
assert "BytesPerBlock(PixelFormatFromRenderTargetFormat(regs.dst.format))" in fermi_layer_new
assert "if ((regs.src.layer != 0 || regs.dst.layer != 0) && !pitch_layer_copy)" in fermi_layer_new
assert "EDEN_GPU_FERMI2D_UNSUPPORTED_LAYER" in fermi_layer_new
assert "if (count < 8)" in fermi_layer_new
assert fermi_layer_new.count("AssertFailSoftImpl();") == 1
assert fermi_layer_new.index("AssertFailSoftImpl();") < fermi_layer_new.index("return;")
assert fermi_new.count("AssertFailSoftImpl();") == 1
assert fermi_new.index("AssertFailSoftImpl();") < fermi_new.index("return;")
assert "const u64 plane_bytes = static_cast<u64>(surface.pitch) * surface.height;" in fermi_copy_new
assert "const u64 offset = plane_bytes * surface.layer;" in fermi_copy_new
assert "offset / surface.layer != plane_bytes" in fermi_copy_new
assert "offset > last - surface.Address()" in fermi_copy_new
assert "surface.layer = 0;" in fermi_copy_new
assert "if (!select_pitch_layer(src) || !select_pitch_layer(dst))" in fermi_copy_new
assert "EDEN_GPU_FERMI2D_PITCH_LAYER_INVALID" in fermi_copy_new
# Independent arithmetic model of the linear image-layer address.
def pitch_layer_address(base: int, pitch: int, height: int, layer: int,
                        depth: int) -> int | None:
    max_u64 = (1 << 64) - 1
    if pitch <= 0 or height <= 0 or layer < 0 or layer >= depth:
        return None
    plane_bytes = pitch * height
    offset = plane_bytes * layer
    if offset > max_u64 or base > max_u64 - offset:
        return None
    return base + offset

assert pitch_layer_address(0x1000, 2048, 1080, 0, 4) == 0x1000
assert pitch_layer_address(0x1000, 2048, 1080, 2, 4) == 0x1000 + 2 * 2048 * 1080
assert pitch_layer_address(0x1000, 2048, 1080, 4, 4) is None
assert pitch_layer_address((1 << 64) - 2, 2048, 1080, 1, 2) is None
assert pitch_layer_address(0x1000, 0, 1080, 1, 2) is None

assert "return;" in fermi_copy_new
assert (ROOT / "tools/check-maintained-fermi2d-variants.py").is_file()
assert 'EDEN_UNQUALIFIED_FERMI2D_COPY' not in cmake
assert "src.depth = 1;" in fermi_copy_new
assert "Surface dst = regs.dst;" in fermi_copy_new
assert "dst.depth = 1;" in fermi_copy_new
assert "EDEN_GPU_FERMI2D_SOFTWARE" in fermi_copy_new
assert "sw_blitter->Blit(src, dst, config);" in fermi_copy_new
assert "else if (!rasterizer->AccelerateSurfaceCopy(src, regs.dst, config))" in fermi_copy_new
assert "regs.src.depth = 1;" not in fermi_copy_new
assert "regs.dst.depth = 1;" not in fermi_copy_new
# The widened software blitter is a tracked source built from the shipping
# backport, not a CMake-generated translation unit.
blitter = (ROOT / "vendor/encore-active/eden/src/video_core/engines/sw_blitter/blitter.cpp").read_text()
for token in (
    "src.depth, config.src_x0", "dst.depth, config.dst_x0",
    # The selected Fermi2D blitter now admits the entire GOB extent in u64,
    # including the simpler pitch case, before any guest-memory read/write.
    "const u64 bytes = static_cast<u64>(surface.pitch) * surface.height;",
    "const auto src_size = checked_surface_size(src, src_bytes_per_pixel);",
    "const auto dst_size = checked_surface_size(dst, dst_bytes_per_pixel);",
    "const size_t src_copy_size = static_cast<size_t>(src_extent_x) * src_extent_y * src_bytes_per_pixel;",
    "const size_t dst_copy_size = static_cast<size_t>(dst_extent_x) * dst_extent_y * dst_bytes_per_pixel;",
):
    assert token in blitter, token
assert 'write_derived("${PORT_BUILD_DIR}/sw_blitter_sized.cpp"' not in cmake
assert 'list(FILTER sw_blitter_sources EXCLUDE REGEX "engines/sw_blitter/blitter[.]cpp$")' in cmake
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_NATIVE_BLITTER}")' in cmake

# Regressions that were once silent truncation in the pinned software blitter.
# The widened intermediate must match arbitrary-precision math for these cases.
def safe_product(*values):
    result = 1
    for value in values:
        result *= value
    return result
assert safe_product(65536, 65536) == 1 << 32  # pitch x height
assert safe_product(8192, 8192, 16) == 1 << 30  # source/destination rect
assert safe_product(65536, 65536, 4) == 1 << 34  # not 32-bit-wrapped
assert safe_product(65536, 65536, 4) != (safe_product(65536, 65536, 4) & 0xffffffff)


# All three native GPU units compile from full Encore-maintained sources.
# The last diagnostic module has no CMake source rewriting left.
assert "write_derived(" not in cmake
assert 'target_sources(shader_recompiler PRIVATE "${EDEN_MAINTAINED_NATIVE_PRMT}")' in cmake
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_NATIVE_BLITTER}")' in cmake
assert 'target_sources(video_core PRIVATE "${EDEN_MAINTAINED_FERMI_FILE}")' in cmake
shared_atomic=(ROOT/"vendor/encore-active/eden/src/shader_recompiler/frontend/maxwell/translate/impl/atomic_operations_shared_memory.cpp").read_text()
assert "void TranslatorVisitor::ATOMS_cas(u64 insn)" in shared_atomic
assert "SharedAtomicCompareExchange" in shared_atomic
assert "BitField<28, 2, AtomsCasBcRz> bc_rz;" in shared_atomic
assert "BitField<52, 4, u64> operation;" in shared_atomic
assert "void TranslatorVisitor::ATOMS_cas" not in prmt
print("GPU SOURCE CONTRACT: PRMT modes 0-6, IMUL, IMAD/IMAD32I negate modes, bounded IMADSP, ATOMS.CAS.B32 and CFG-owned control/PRET translated; unsupported forms fail closed; one fixed observed Fermi2D owner")
print("NOTE graphics correctness and PS5 native CMake build remain to be qualified")
