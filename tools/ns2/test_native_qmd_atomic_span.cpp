// SPDX-License-Identifier: GPL-3.0-or-later
// Host proof: actual native IR instructions -> atomic range -> real
// QMD3 storage-binding metadata. No Vulkan or PS5 GPU dispatch.
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <span>
#include <vector>
#include "shader_recompiler/frontend/ampere/native_atomic_span.h"
#include "shader_recompiler/frontend/ampere/native_qmd_compute_environment.h"
#include "shader_recompiler/object_pool.h"

using namespace Shader::Ampere;
using Shader::IR::Opcode;
using Shader::IR::Value;

static std::optional<std::vector<NativeAtomicSpan>>
MakeIrSpans(Opcode op, u32 slot, u32 offset,
            bool dynamic_offset = false, bool dynamic_slot = false) {
    Shader::ObjectPool<Shader::IR::Inst> pool{12};
    Shader::IR::Block block{pool};
    Shader::IR::Program ir{};
    ir.stage=Shader::Stage::Compute;
    ir.blocks.push_back(&block);
    ir.info.storage_buffers_descriptors.push_back(
        {.cbuf_index=0,.cbuf_offset=0x310,.count=1,.is_written=true});
    ir.info.storage_buffers_descriptors.push_back(
        {.cbuf_index=0,.cbuf_offset=0x320,.count=1,.is_written=true});
    Value binding{slot}, index{offset};
    if(dynamic_slot) {
        block.AppendNewInst(Opcode::IAdd32,{Value{slot},Value{u32{0}}});
        binding=Value{&block.back()};
    }
    if(dynamic_offset) {
        block.AppendNewInst(Opcode::IAdd32,{Value{offset},Value{u32{0}}});
        index=Value{&block.back()};
    }
    if(op >= Opcode::GlobalAtomicIAdd32 && op <= Opcode::GlobalAtomicMaxF32x2) {
        block.AppendNewInst(op,{Value{u64{0x100000}},Value{u32{1}}});
    } else {
        block.AppendNewInst(op,{binding,index,Value{u32{1}}});
    }
    return CollectNativeQmdAtomicSpans(ir);
}

static void Test(Opcode op, u32 slot, u32 offset, bool expected,
                 bool dynamic_offset = false, bool dynamic_slot = false) {
    const auto got=MakeIrSpans(op,slot,offset,dynamic_offset,dynamic_slot);
    if (bool(got)!=expected) std::fprintf(stderr,"atomic=%u slot=%u off=%u dyn=%u/%u expected=%u actual=%u\n", static_cast<unsigned>(op), slot,offset,dynamic_offset,dynamic_slot,expected, bool(got));
    assert(bool(got)==expected);
    if(expected) {
        assert(got->size()==1 && (*got)[0].binding==slot &&
               (*got)[0].offset==offset);
    }
}

// The backend's REAL emitted address is (R12 & mask), not a guessed
// host-side offset. An aligned constant AND mask bounds every possible
// byte index regardless of the runtime register value. No other dynamic
// arithmetic is accepted without a runtime SPIR-V conditional.
static std::optional<std::vector<NativeAtomicSpan>>
MakeMaskedIrSpans(Opcode op, u32 slot, u32 mask, bool swap_constant = false,
                  bool wrap_identity = false, bool add_after_mask = false,
                  u32 addend = 4, bool swap_addition = false,
                  bool unbounded_second_addition = false,
                  bool shift_after_mask = false, u32 shift_by = 2,
                  bool dynamic_shift = false) {
    Shader::ObjectPool<Shader::IR::Inst> pool{14};
    Shader::IR::Block block{pool};
    Shader::IR::Program ir{};
    ir.stage=Shader::Stage::Compute;
    ir.blocks.push_back(&block);
    ir.info.storage_buffers_descriptors.push_back(
        {.cbuf_index=0,.cbuf_offset=0x310,.count=1,.is_written=true});
    ir.info.storage_buffers_descriptors.push_back(
        {.cbuf_index=0,.cbuf_offset=0x320,.count=1,.is_written=true});
    block.AppendNewInst(Opcode::GetRegister,{Value{Shader::IR::Reg::R12}});
    const Value register_value{&block.back()};
    block.AppendNewInst(Opcode::BitwiseAnd32,
        swap_constant ? std::initializer_list<Value>{Value{mask},register_value}
                      : std::initializer_list<Value>{register_value,Value{mask}});
    Value index{&block.back()};
    if (wrap_identity) {
        block.AppendNewInst(Opcode::Identity,{index});
        index=Value{&block.back()};
    }
    if (shift_after_mask) {
        block.AppendNewInst(Opcode::ShiftLeftLogical32,
            {index,dynamic_shift ? register_value : Value{shift_by}});
        index=Value{&block.back()};
    }
    if (add_after_mask) {
        block.AppendNewInst(Opcode::IAdd32,
            swap_addition ? std::initializer_list<Value>{Value{addend},index}
                          : std::initializer_list<Value>{index,Value{addend}});
        index=Value{&block.back()};
    }
    if (unbounded_second_addition) {
        block.AppendNewInst(Opcode::IAdd32,{index,register_value});
        index=Value{&block.back()};
    }
    block.AppendNewInst(op,{Value{slot},index,Value{u32{1}}});
    return CollectNativeQmdAtomicSpans(ir);
}

static void CheckMaskedAtomic(Opcode op, u32 slot, u32 mask, bool expected,
                              bool swap_constant = false,
                              bool wrap_identity = false,
                              bool add_after_mask = false,
                              u32 addend = 4, bool swap_addition = false,
                              bool unbounded_second_addition = false,
                              bool shift_after_mask = false, u32 shift_by = 2,
                              bool dynamic_shift = false) {
    const auto spans=MakeMaskedIrSpans(
        op,slot,mask,swap_constant,wrap_identity,add_after_mask,
        addend,swap_addition,unbounded_second_addition,
        shift_after_mask,shift_by,dynamic_shift);
    if (bool(spans)!=expected)
        std::fprintf(stderr,"masked atomic op=%u slot=%u mask=%#x "
                             "swap=%u identity=%u plus=%u delta=%#x "
                             "swap_plus=%u dynamic_second=%u shift=%u "
                             "shift_by=%u dynamic_shift=%u expected=%u got=%u\n",
            static_cast<u32>(op),slot,mask,swap_constant,wrap_identity,
            add_after_mask,addend,swap_addition,unbounded_second_addition,
            shift_after_mask,shift_by,dynamic_shift,expected,bool(spans));
    assert(bool(spans)==expected);
    if (expected) {
        const u32 bound = shift_after_mask ? mask << shift_by : mask;
        assert(spans->size()==1 && spans->front().binding==slot &&
               spans->front().offset==
                  (add_after_mask ? bound + addend : bound));
    }
}

// Actual SPIR-V OpBitFieldUExtract uses U32 input, literal bit offset and
// count: a count of N has range [0,2^N-1] independent of the input.
// The only admitted byte address applies a checked constant shift, then
// optionally an aligned, non-wrapping base.
static std::optional<std::vector<NativeAtomicSpan>>
MakeExtractIrSpans(Opcode op, u32 slot, u32 bit_offset, u32 bit_count,
                   u32 shift = 2, u32 base = 0,
                   bool variable_offset = false,
                   bool variable_count = false,
                   bool variable_shift = false,
                   bool extra_dynamic_add = false) {
    Shader::ObjectPool<Shader::IR::Inst> pool{16};
    Shader::IR::Block block{pool};
    Shader::IR::Program ir{};
    ir.stage=Shader::Stage::Compute;
    ir.blocks.push_back(&block);
    ir.info.storage_buffers_descriptors.push_back(
        {.cbuf_index=0,.cbuf_offset=0x310,.count=1,.is_written=true});
    block.AppendNewInst(Opcode::GetRegister,{Value{Shader::IR::Reg::R12}});
    const Value reg{&block.back()};
    block.AppendNewInst(Opcode::BitFieldUExtract,
        {reg,
         variable_offset ? reg : Value{bit_offset},
         variable_count ? reg : Value{bit_count}});
    Value offset{&block.back()};
    block.AppendNewInst(Opcode::ShiftLeftLogical32,
        {offset,variable_shift ? reg : Value{shift}});
    offset=Value{&block.back()};
    if (base) {
        block.AppendNewInst(Opcode::IAdd32,{offset,Value{base}});
        offset=Value{&block.back()};
    }
    if (extra_dynamic_add) {
        block.AppendNewInst(Opcode::IAdd32,{offset,reg});
        offset=Value{&block.back()};
    }
    block.AppendNewInst(op,{Value{slot},offset,Value{u32{1}}});
    return CollectNativeQmdAtomicSpans(ir);
}

static void CheckExtractAtomic(Opcode op, u32 bit_offset, u32 bit_count,
                               u32 shift, u32 base, bool expected) {
    const auto got=MakeExtractIrSpans(op,0,bit_offset,bit_count,shift,base);
    if (bool(got)!=expected)
        std::fprintf(stderr,"UExtract atomic=%u offset=%u count=%u "
                            "shift=%u base=%u expected=%u got=%u\n",
            static_cast<u32>(op),bit_offset,bit_count,shift,base,
            expected,bool(got));
    assert(bool(got)==expected);
    if (expected) {
        const u32 bound=(bit_count==32 ? 0xffffffffU
                                     : (u32{1}<<bit_count)-1U);
        assert(got->size()==1 && got->front().binding==0 &&
               got->front().offset==(bound<<shift)+base);
    }
}

int main() {
    static_assert(NativeAtomicSpan{1,4,4} == NativeAtomicSpan{1,4,4});
    Test(Opcode::StorageAtomicIAdd32,0,0,true);
    Test(Opcode::StorageAtomicExchange32,1,4,true);
    Test(Opcode::StorageAtomicIAdd32,1,12,true);
    Test(Opcode::StorageAtomicIAdd64,0,0,true);
    Test(Opcode::StorageAtomicExchange64,1,8,true);
    Test(Opcode::StorageAtomicAddF32,0,8,true);
    Test(Opcode::StorageAtomicAddF16x2,0,8,true);
    Test(Opcode::StorageAtomicMaxF32x2,0,8,true);
    Test(Opcode::StorageAtomicIAdd32x2,0,0,false);
    Test(Opcode::StorageAtomicExchange32x2,0,0,false);
    Test(Opcode::GlobalAtomicIAdd32,0,0,false);
    Test(Opcode::GlobalAtomicExchange64,0,0,false);
    Test(Opcode::StorageAtomicIAdd32,2,0,false);
    Test(Opcode::StorageAtomicIAdd32,0,1,false);
    Test(Opcode::StorageAtomicIAdd32,0,6,false);
    Test(Opcode::StorageAtomicIAdd64,0,4,false);
    Test(Opcode::StorageAtomicIAdd32,0,0,false,true);
    Test(Opcode::StorageAtomicIAdd64,0,0,false,true);
    Test(Opcode::StorageAtomicIAdd32,0,0,false,false,true);
    Test(Opcode::StorageAtomicIAdd64,0,0,false,false,true);
    Test(Opcode::StorageAtomicIAdd64,0,0xfffffff0U,true);
    Test(Opcode::StorageAtomicIAdd64,0,0xfffffff8U,false);
    Test(Opcode::StorageAtomicIAdd64,0,0xfffffff9U,false);
    Test(Opcode::StorageAtomicIAdd64,0,0xfffffffcU,false);
    Test(Opcode::StorageAtomicIAdd32,0,0xfffffff8U,true);
    Test(Opcode::StorageAtomicIAdd32,0,0xfffffffcU,false);

    // 32-bit atomic: R12&0x3c yields [0,60] in 4-byte units, which
    // fits a 64-byte QMD3 SSBO exactly. 64-bit works with mask 0x38.
    // Both constant operand orders and IR identity wrappers are valid.
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x3c,true);
    CheckMaskedAtomic(Opcode::StorageAtomicExchange32,0,0x3c,true,true);
    CheckMaskedAtomic(Opcode::StorageAtomicSMin32,0,0x3c,true,false,true);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0x38,true);
    CheckMaskedAtomic(Opcode::StorageAtomicExchange64,1,0x0,true);
    CheckMaskedAtomic(Opcode::StorageAtomicAddF32,0,0x3c,true);
    // Exactly one aligned constant base after AND is also bounded,
    // independent of runtime R12, even through IR identity wrappers.
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x3c,true,
                      false,false,true,4);
    CheckMaskedAtomic(Opcode::StorageAtomicExchange32,0,0x3c,true,
                      false,true,true,0x20,true);
    CheckMaskedAtomic(Opcode::StorageAtomicSMin32,0,0x3c,true,
                      true,true,true,0x40);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0x38,true,
                      false,false,true,8);
    CheckMaskedAtomic(Opcode::StorageAtomicExchange64,0,0x0,true,
                      true,false,true,8,true);
    // Dynamic guest array indices in element units are commonly masked
    // and left-shifted to atomically addressed BYTE offsets. The shift
    // and optional constant base must be literal, alignment-preserving
    // and non-overflowing for EVERY possible register value.
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x0f,true,
                      false,false,false,4,false,false,true,2);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0x07,true,
                      true,true,false,4,false,false,true,3);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x0f,true,
                      false,true,true,4,false,false,true,2);
    CheckMaskedAtomic(Opcode::StorageAtomicExchange64,0,0x07,true,
                      true,false,true,8,true,false,true,3);
    // Native 32-bit unsigned bitfield extraction also proves a range
    // when offset/count are real U32 literals. The same shift and base
    // owners require exact, non-wrapping 4/8-byte address alignment.
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,3,4,2,0,true);
    CheckExtractAtomic(Opcode::StorageAtomicExchange64,0,3,3,0,true);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,28,4,2,4,true);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd64,0,3,3,8,true);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,0,4,1,0,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd64,0,3,2,0,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,31,2,2,0,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,32,1,2,0,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,0,0,2,0,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,0,32,2,0,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,0,4,32,0,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,0,4,2,2,false);
    CheckExtractAtomic(Opcode::StorageAtomicIAdd32,0,4,2,0xffffffc0U,false);
    assert(!MakeExtractIrSpans(Opcode::StorageAtomicIAdd32,0,3,4,
                               2,0,true));
    assert(!MakeExtractIrSpans(Opcode::StorageAtomicIAdd32,0,3,4,
                               2,0,false,true));
    assert(!MakeExtractIrSpans(Opcode::StorageAtomicIAdd32,0,3,4,
                               2,0,false,false,true));
    assert(!MakeExtractIrSpans(Opcode::StorageAtomicIAdd32,0,3,4,
                               2,0,false,false,false,true));

    // Low alignment bits, oversized mask, non-integral constant base,
    // overflow, a second dynamic addition, and non-atomic 32x2 fail closed.
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x3e,false);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0x3c,false);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0xfffffffcU,false);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0xfffffff8U,false);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x3c,false,
                      false,false,true,2);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0x38,false,
                      false,false,true,4);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x3c,false,
                      false,false,true,0xffffffc0U);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0x38,false,
                      false,false,true,0xffffffc0U);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x3c,false,
                      false,false,true,4,false,true);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x03,false,
                      false,false,false,4,false,false,true,1);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x0f,false,
                      false,false,false,4,false,false,true,0);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd64,0,0x07,false,
                      false,false,false,4,false,false,true,2);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x80000000U,false,
                      false,false,false,4,false,false,true,2);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x0f,false,
                      false,false,false,4,false,false,true,32);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x0f,false,
                      false,false,false,4,false,false,true,2,true);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,0,0x0f,false,
                      false,false,true,0xffffffc0U,false,false,true,2);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32x2,0,0x38,false);
    CheckMaskedAtomic(Opcode::StorageAtomicIAdd32,2,0x3c,false);

    const std::vector<NativeQmdStorageBinding> real_bindings{
        {0x100000,64,true,true}, {0x200000,8,true,true}};
    const auto prove=[&](std::initializer_list<NativeAtomicSpan> accesses,
                         bool expected) {
        assert(NativeQmdAtomicSpansFitBindings(
            std::span<const NativeAtomicSpan>{accesses.begin(),accesses.size()},
            real_bindings)==expected);
    };
    prove({},true);
    prove({{0,0,4},{0,60,4},{1,0,8}},true);
    prove({{0,56,8},{1,4,4}},true);
    // These are conservatively proven UPPER bounds of dynamic masked IR,
    // not arbitrary snapshot offsets. Actual live resource lengths decide.
    const auto masked32 = MakeMaskedIrSpans(Opcode::StorageAtomicIAdd32,0,0x3c);
    const auto masked64 = MakeMaskedIrSpans(Opcode::StorageAtomicIAdd64,0,0x38);
    assert(masked32 && masked64);
    assert(NativeQmdAtomicSpansFitBindings(*masked32,real_bindings));
    assert(NativeQmdAtomicSpansFitBindings(*masked64,real_bindings));
    const auto base_shifted32=MakeMaskedIrSpans(
        Opcode::StorageAtomicIAdd32,0,0x3c,false,false,true,4);
    const auto base_shifted64=MakeMaskedIrSpans(
        Opcode::StorageAtomicIAdd64,0,0x38,true,true,true,8,true);
    assert(base_shifted32 && base_shifted64);
    assert(base_shifted32->front().offset == 64 &&
           base_shifted64->front().offset == 64);
    auto region68=real_bindings;
    region68[0].bytes=68;
    assert(NativeQmdAtomicSpansFitBindings(*base_shifted32,region68));
    assert(!NativeQmdAtomicSpansFitBindings(*base_shifted64,region68));
    region68[0].bytes=72;
    assert(NativeQmdAtomicSpansFitBindings(*base_shifted32,region68));
    assert(NativeQmdAtomicSpansFitBindings(*base_shifted64,region68));
    const auto shifted32 = MakeMaskedIrSpans(
        Opcode::StorageAtomicIAdd32,0,0x0f,false,false,false,
        4,false,false,true,2);
    const auto shifted64 = MakeMaskedIrSpans(
        Opcode::StorageAtomicIAdd64,0,0x07,false,false,false,
        4,false,false,true,3);
    const auto shifted_with_base = MakeMaskedIrSpans(
        Opcode::StorageAtomicIAdd32,0,0x0f,true,true,true,
        4,true,false,true,2);
    assert(shifted32 && shifted64 && shifted_with_base);
    assert(shifted32->front().offset==60 &&
           shifted64->front().offset==56 &&
           shifted_with_base->front().offset==64);
    assert(NativeQmdAtomicSpansFitBindings(*shifted32,real_bindings));
    assert(NativeQmdAtomicSpansFitBindings(*shifted64,real_bindings));
    auto shifted_buffer=real_bindings;
    shifted_buffer[0].bytes=67;
    assert(!NativeQmdAtomicSpansFitBindings(*shifted_with_base,shifted_buffer));
    shifted_buffer[0].bytes=68;
    assert(NativeQmdAtomicSpansFitBindings(*shifted_with_base,shifted_buffer));
    const auto extracted32=MakeExtractIrSpans(
        Opcode::StorageAtomicIAdd32,0,3,4,2);
    const auto extracted64=MakeExtractIrSpans(
        Opcode::StorageAtomicIAdd64,0,0,3,3);
    const auto extracted_with_base=MakeExtractIrSpans(
        Opcode::StorageAtomicIAdd32,0,3,4,2,4);
    assert(extracted32 && extracted64 && extracted_with_base);
    assert(extracted32->front().offset==60 &&
           extracted64->front().offset==56 &&
           extracted_with_base->front().offset==64);
    assert(NativeQmdAtomicSpansFitBindings(*extracted32,real_bindings));
    assert(NativeQmdAtomicSpansFitBindings(*extracted64,real_bindings));
    assert(!NativeQmdAtomicSpansFitBindings(*extracted_with_base,real_bindings));
    auto extracted_buffer=real_bindings;
    extracted_buffer[0].bytes=68;
    assert(NativeQmdAtomicSpansFitBindings(*extracted_with_base,extracted_buffer));
    extracted_buffer[0].bytes=63;
    assert(!NativeQmdAtomicSpansFitBindings(*extracted32,extracted_buffer));

    auto short_resource=real_bindings;
    short_resource[0].bytes=63;
    assert(!NativeQmdAtomicSpansFitBindings(*masked32,short_resource));
    short_resource[0].bytes=60;
    assert(!NativeQmdAtomicSpansFitBindings(*masked64,short_resource));
    prove({{0,60,8}},false); // last word leaves buffer
    prove({{1,4,8}},false);  // last word leaves small binding
    prove({{0,2,4}},false);  // alignment cannot silently floor index
    prove({{1,4,8}},false);
    prove({{2,0,4}},false);
    prove({{0,0,0}},false);
    prove({{0,0,16}},false);
    prove({{0,0xfffffffcU,4}},false);
    prove({{0,0xfffffff8U,8}},false);
    // Validate the physical GMMU range as well as the byte offset.
    // A perfectly aligned masked offset cannot repair a misaligned base.
    auto misaligned_base=real_bindings;
    misaligned_base[0].gpu_address=0x100002U;
    assert(!NativeQmdAtomicSpansFitBindings(*masked32,misaligned_base));
    assert(!NativeQmdAtomicSpansFitBindings(*base_shifted32,misaligned_base));
    misaligned_base[0].gpu_address=0x100004U;
    assert(NativeQmdAtomicSpansFitBindings(*masked32,misaligned_base));
    assert(!NativeQmdAtomicSpansFitBindings(*masked64,misaligned_base));
    const auto beyond_gpu_limit=real_bindings;
    auto invalid_gpu=beyond_gpu_limit;
    invalid_gpu[0].gpu_address=u64{1} << 49;
    assert(!NativeQmdAtomicSpansFitBindings(*masked32,invalid_gpu));
    invalid_gpu[0].gpu_address=(u64{1} << 49) - 32U;
    assert(!NativeQmdAtomicSpansFitBindings(*masked32,invalid_gpu));
    invalid_gpu[0].gpu_address=(u64{1} << 49) - 64U;
    assert(NativeQmdAtomicSpansFitBindings(*masked32,invalid_gpu));
    const std::array bad_bindings{
        NativeQmdStorageBinding{0,64,true,true},
        NativeQmdStorageBinding{0x200000,8,false,true}};
    assert(!NativeQmdAtomicSpansFitBindings(
        std::array{NativeAtomicSpan{0,0,4}},bad_bindings));
    assert(!NativeQmdAtomicSpansFitBindings(
        std::array{NativeAtomicSpan{1,0,4}},bad_bindings));
    const std::array unknown_bindings{
        NativeQmdStorageBinding{0x100000,64,true,false}};
    assert(!NativeQmdAtomicSpansFitBindings(
        std::array{NativeAtomicSpan{0,0,4}},unknown_bindings));
    const std::array empty_bindings{
        NativeQmdStorageBinding{0x100000,0,true,true}};
    assert(!NativeQmdAtomicSpansFitBindings(
        std::array{NativeAtomicSpan{0,0,4}},empty_bindings));
    // Real QMD descriptor mutation means a recheck against a NEW
    // binding can refuse an atomic previously valid at compile time.
    auto mutated = real_bindings;
    mutated[0].bytes=60;
    assert(!NativeQmdAtomicSpansFitBindings(
        std::array{NativeAtomicSpan{0,60,4}},mutated));
    std::puts("P2_3_NATIVE_ATOMIC_SPAN_REAL_IR_PASS static=1 "
              "dynamic_unbounded_rejected=1 aligned_and_max_admitted=1 "
              "aligned_base_plus_and=1 shifted_mask_index=1 "
              "shifted_mask_plus_base=1 bitfield_unsigned_extract=1 "
              "extract_invalid_ranges_refused=1 checked_u32_no_wrap=1 "
              "atomic_gmmu_base_alignment=1 guest_va_49=1 "
              "dynamic_live_size_proved=1 stale_size_refused=1");
}
