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
    prove({{0,60,8}},false); // last word leaves buffer
    prove({{1,4,8}},false);  // last word leaves small binding
    prove({{0,2,4}},false);  // alignment cannot silently floor index
    prove({{1,4,8}},false);
    prove({{2,0,4}},false);
    prove({{0,0,0}},false);
    prove({{0,0,16}},false);
    prove({{0,0xfffffffcU,4}},false);
    prove({{0,0xfffffff8U,8}},false);
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
              "dynamic_rejected=1 actual_bound=1 stale_size_refused=1");
}
