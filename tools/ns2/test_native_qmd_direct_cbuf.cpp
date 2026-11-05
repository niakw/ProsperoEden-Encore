// SPDX-License-Identifier: GPL-3.0-or-later
// Real IR opcode/block and QMD3 CBUF admission. Host-only, no guest keys.
#include <array>
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include "shader_recompiler/frontend/ampere/native_indirect_cbuf.h"
#include "shader_recompiler/object_pool.h"

using Shader::IR::Opcode;
using Shader::IR::Value;

static void Check(Opcode op, u32 bank, u32 offset, u32 reflected,
                  u32 enabled, bool dynamic_bank, bool dynamic_offset,
                  bool accepted, u32 required) {
    Shader::ObjectPool<Shader::IR::Inst> pool{16};
    Shader::IR::Block block{pool};
    Shader::IR::Program program{};
    program.stage=Shader::Stage::Compute;
    program.blocks.push_back(&block);
    program.info.constant_buffer_mask=reflected;
    for (u32 i=0;i<8;++i)
        if (reflected & (1U<<i))
            program.info.constant_buffer_descriptors.push_back({i,1});
    Value source{bank}, byte_offset{offset};
    if (dynamic_bank) {
        block.AppendNewInst(Opcode::IAdd32,{Value{u32{0}},Value{u32{1}}});
        source=Value{&block.back()};
    }
    if (dynamic_offset) {
        block.AppendNewInst(Opcode::IAdd32,{Value{u32{0}},Value{u32{4}}});
        byte_offset=Value{&block.back()};
    }
    block.AppendNewInst(op,{source,byte_offset});
    const bool ok=Shader::Ampere::NormalizeNativeQmdIndirectCbufIR(program,enabled);
    if (ok!=accepted || (ok && program.info.constant_buffer_used_sizes[bank]!=required)) {
        std::fprintf(stderr,"QMD3 direct CBUF bank=%u offset=%u op=%u ok=%u required=%u actual=%u\n",
                     bank,offset,static_cast<unsigned>(op),ok,required,
                     program.info.constant_buffer_used_sizes[bank]);
        std::abort();
    }
}
static void CheckNativeAtomic(
    Opcode opcode, bool expected,
    bool writable = true, bool declared = true, bool used = true,
    bool aliases = true, bool int64_atomics = true,
    bool dynamic_binding = false, u32 cbuf_offset = 0x310,
    u32 atomic_offset = 0, bool int64 = true,
    bool declared_record = true, bool sized_record = true,
    u32 nvn_base = 0x310, u32 reflected_size = 0x10000) {
    Shader::ObjectPool<Shader::IR::Inst> pool{16};
    Shader::IR::Block block{pool};
    Shader::IR::Program program{};
    program.stage = Shader::Stage::Compute;
    program.blocks.push_back(&block);
    if (declared) {
        program.info.constant_buffer_mask = 1;
        if (declared_record)
            program.info.constant_buffer_descriptors.push_back({0, 1});
        if (sized_record)
            program.info.constant_buffer_used_sizes[0] = reflected_size;
    }
    program.info.nvn_buffer_base = nvn_base;
    program.info.storage_buffers_descriptors.push_back(
        {.cbuf_index = 0, .cbuf_offset = cbuf_offset,
         .count = 1, .is_written = writable});
    if (used) program.info.nvn_buffer_used.set(0);
    Shader::Profile profile{};
    profile.support_descriptor_aliasing = aliases;
    profile.support_int64 = int64;
    profile.support_int64_atomics = int64_atomics;
    Value binding{u32{0}};
    if (dynamic_binding) {
        block.AppendNewInst(Opcode::IAdd32, {Value{u32{0}}, Value{u32{1}}});
        binding = Value{&block.back()};
    }
    // Storage atomics use flattened SSBO slot; unresolved GlobalAtomic
    // instead carries a raw 64-bit guest address (unprovable here).
    if (opcode >= Opcode::GlobalAtomicIAdd32 &&
        opcode <= Opcode::GlobalAtomicMaxF32x2)
        block.AppendNewInst(opcode, {Value{u64{0x100000}}, Value{u32{1}}});
    else
        block.AppendNewInst(opcode,
                            {binding, Value{atomic_offset}, Value{u32{1}}});
    const bool actual=Shader::Ampere::NativeQmdAtomicStorageIRAdmissible(
        program,profile);
    if (actual!=expected) {
        std::fprintf(stderr,
            "Native QMD3 atomic opcode=%u expected=%u got=%u\n",
            static_cast<unsigned>(opcode), expected, actual);
        std::abort();
    }
}
// Real flattened NVN descriptors may contain several SSBOs. The
// reflected slot 1 must refer to NVN base+16, not be accepted merely
// because both CBUF records happen to be writable and in bounds.
static void CheckNativeAtomicSlotOrder(bool swapped, bool accepted) {
    Shader::ObjectPool<Shader::IR::Inst> pool{16};
    Shader::IR::Block block{pool};
    Shader::IR::Program program{};
    program.stage = Shader::Stage::Compute;
    program.blocks.push_back(&block);
    program.info.constant_buffer_mask = 1;
    program.info.constant_buffer_descriptors.push_back({0,1});
    program.info.constant_buffer_used_sizes[0] = 0x330;
    program.info.nvn_buffer_base = 0x310;
    program.info.nvn_buffer_used.set(0);
    program.info.nvn_buffer_used.set(1);
    program.info.storage_buffers_descriptors.push_back({
        .cbuf_index = 0, .cbuf_offset = swapped ? 0x320U : 0x310U,
        .count = 1, .is_written = true});
    program.info.storage_buffers_descriptors.push_back({
        .cbuf_index = 0, .cbuf_offset = swapped ? 0x310U : 0x320U,
        .count = 1, .is_written = true});
    block.AppendNewInst(Opcode::StorageAtomicIAdd32,
        {Value{u32{1}}, Value{u32{0}}, Value{u32{7}}});
    const bool actual = Shader::Ampere::NativeQmdAtomicStorageIRAdmissible(
        program, Shader::Profile{});
    assert(actual == accepted);
}
int main() {
    // P2.3: actual native global memory OpAccessChain must never start
    // inside a valid SSBO if the last byte falls outside it. The old
    // SPIR-V check accepted such 8/16-byte accesses and silently floored
    // misaligned addresses to the preceding word.
    using Shader::Ampere::NativeQmdGlobalAccessWithinStorage;
    for (const u32 width : {4U,8U,16U}) {
        for (const u32 bytes : {1U,3U,4U,7U,8U,15U,16U,17U,31U,32U,33U,64U}) {
            for (u32 offset = 0; offset < 80; ++offset) {
                const bool expected = bytes >= width &&
                    offset % width == 0 &&
                    offset <= bytes - (std::min)(bytes, width);
                assert(NativeQmdGlobalAccessWithinStorage(
                    0x100000, bytes, 0x100000 + offset, width) == expected);
            }
        }
    }
    assert(!NativeQmdGlobalAccessWithinStorage(0, 4096, 4, 4));
    assert(!NativeQmdGlobalAccessWithinStorage(0x1000, 8, 0xfff, 4));
    assert(!NativeQmdGlobalAccessWithinStorage(0x1000, 8, ~u64{0}, 4));
    assert(!NativeQmdGlobalAccessWithinStorage(0x1000, 8, 0x1000, 1));
    assert(!NativeQmdGlobalAccessWithinStorage(0x1000, 8, 0x1000, 32));
    assert(!NativeQmdGlobalAccessWithinStorage((u64{1} << 49) - 4, 8,
                                                (u64{1} << 49) - 4, 4));
    assert(!NativeQmdGlobalAccessWithinStorage(u64{1} << 49, 4,
                                                u64{1} << 49, 4));
    assert(NativeQmdGlobalAccessWithinStorage((u64{1} << 49) - 16, 16,
                                               (u64{1} << 49) - 16, 16));
    // P2.3: write-only Ampere NVN global memory must reach the SAME CBUF0
    // descriptor bridge as read+write programs, never a detached SSBO.
    {
        using Shader::Ampere::NormalizeNativeQmdGlobalStoreOnlyInfo;
        Shader::Info stores{};
        stores.stores_global_memory = true;
        stores.constant_buffer_mask = 1;
        stores.constant_buffer_descriptors.push_back({0, 1});
        stores.nvn_buffer_used.set(0);
        assert(NormalizeNativeQmdGlobalStoreOnlyInfo(stores, 1));
        assert(stores.uses_global_memory && stores.stores_global_memory);
        assert(stores.storage_buffers_descriptors.size() == 1);
        const auto& storage = stores.storage_buffers_descriptors[0];
        assert(storage.cbuf_index == 0 && storage.cbuf_offset == 0x310U &&
               storage.count == 1 && storage.is_written);
        assert(stores.constant_buffer_used_sizes[0] == 0x320U);
        // Already normalized: no duplicate descriptors or changed ordering.
        assert(NormalizeNativeQmdGlobalStoreOnlyInfo(stores, 1));
        assert(stores.storage_buffers_descriptors.size() == 1);

        Shader::Info many{};
        many.stores_global_memory = true;
        many.constant_buffer_mask = 1;
        many.constant_buffer_descriptors.push_back({0, 1});
        for (u32 i = 0; i < 16; ++i) many.nvn_buffer_used.set(i);
        assert(NormalizeNativeQmdGlobalStoreOnlyInfo(many, 1));
        assert(many.storage_buffers_descriptors.size() == 16);
        assert(many.constant_buffer_used_sizes[0] == 0x410U);
        for (u32 i = 0; i < 16; ++i) {
            const auto& desc = many.storage_buffers_descriptors[i];
            assert(desc.cbuf_index == 0 && desc.cbuf_offset == 0x310U + i * 16U &&
                   desc.count == 1 && desc.is_written);
        }

        // Rejection must NOT partially mutate an IR or invent missing banks.
        auto missing_cbuf = stores;
        missing_cbuf.uses_global_memory = false;
        missing_cbuf.storage_buffers_descriptors.clear();
        missing_cbuf.constant_buffer_mask = 0;
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(missing_cbuf, 1));
        assert(!missing_cbuf.uses_global_memory &&
               missing_cbuf.storage_buffers_descriptors.empty());
        missing_cbuf = stores;
        missing_cbuf.uses_global_memory = false;
        missing_cbuf.storage_buffers_descriptors.clear();
        missing_cbuf.constant_buffer_descriptors.clear();
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(missing_cbuf, 1));
        assert(missing_cbuf.storage_buffers_descriptors.empty());
        auto missing_pin = stores;
        missing_pin.uses_global_memory = false;
        missing_pin.storage_buffers_descriptors.clear();
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(missing_pin, 0));
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(missing_pin, 0x101U));
        assert(missing_pin.storage_buffers_descriptors.empty());
        auto gaps = missing_pin;
        gaps.nvn_buffer_used.reset();
        gaps.nvn_buffer_used.set(1);
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(gaps, 1));
        assert(gaps.storage_buffers_descriptors.empty());
        gaps.nvn_buffer_used.set(0);
        gaps.nvn_buffer_used.set(3); // Deliberate hole at slot 2.
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(gaps, 1));
        assert(gaps.storage_buffers_descriptors.empty());
        gaps.nvn_buffer_used.reset();
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(gaps, 1));
        auto collision = missing_pin;
        collision.storage_buffers_descriptors.push_back({0, 0x310, 1, true});
        assert(!NormalizeNativeQmdGlobalStoreOnlyInfo(collision, 1));
        assert(collision.storage_buffers_descriptors.size() == 1);
        auto no_global = missing_pin;
        no_global.stores_global_memory = false;
        assert(NormalizeNativeQmdGlobalStoreOnlyInfo(no_global, 0));
        assert(no_global.storage_buffers_descriptors.empty());
    }
    Check(Opcode::GetCbufU32,0,0,1,1,false,false,true,16);
    Check(Opcode::GetCbufU32,0,0xfffc,1,1,false,false,true,0x10000);
    Check(Opcode::GetCbufU32,0,0xffff,1,1,false,false,false,0);
    Check(Opcode::GetCbufU8,0,0xffff,1,1,false,false,true,0x10000);
    Check(Opcode::GetCbufS16,0,0xffff,1,1,false,false,false,0);
    Check(Opcode::GetCbufU32x2,0,0,1,1,false,false,true,16);
    Check(Opcode::GetCbufU32x2,0,8,1,1,false,false,true,16);
    Check(Opcode::GetCbufU32x2,0,4,1,1,false,false,true,16);
    Check(Opcode::GetCbufU32x2,0,12,1,1,false,false,true,32);
    Check(Opcode::GetCbufU32x2,0,6,1,1,false,false,false,0);
    Check(Opcode::GetCbufU32x2,0,0xfff0,1,1,false,false,true,0x10000);
    Check(Opcode::GetCbufU32x2,0,0xfff4,1,1,false,false,true,0x10000);
    Check(Opcode::GetCbufU32x2,0,0xfff6,1,1,false,false,false,0);
    Check(Opcode::GetCbufU32x2,0,0xfff8,1,1,false,false,true,0x10000);
    Check(Opcode::GetCbufU32x2,0,0xfffc,1,1,false,false,false,0);
    // Real dynamic QMD offsets still require 64-KiB residency. SPIR-V
    // assembles the two guest words across 8-/16-byte uniform vectors;
    // non-word-aligned and out-of-window offsets are zeroed safely.
    Check(Opcode::GetCbufU32x2,0,0,1,1,false,true,true,0x10000);
    Check(Opcode::GetCbufU32,0,0,1,1,false,true,true,0x10000);
    Check(Opcode::GetCbufU32,1,0,1,3,false,false,false,0);
    Check(Opcode::GetCbufU32,0,0,1,1,true,false,false,0);
    Check(Opcode::GetCbufU32,0,0,1,0,false,false,false,0);
    // P2.3: execute the REAL post-translation QMD3 atomic admission.
    // The shared SPIR-V emitter fails on unresolved GlobalAtomic, and
    // silently substitutes non-atomic loads/stores for U32x2 or unsupported
    // U64 atomics. Only reflected, writable native storage slots are safe.
    CheckNativeAtomicSlotOrder(false, true);
    CheckNativeAtomicSlotOrder(true, false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,true);
    // The old guard trusted only the CBUF mask bit. These negative
    // inputs look allocated, but lack the actual CBUF descriptor or
    // the reflected 16-byte NVN record. No atomic must reach SPIR-V.
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,
                      true,false,0x310,0,true,false,true);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,
                      true,false,0x310,0,true,true,false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,
                      true,false,0x310,0,true,true,true,0x320);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,true,true,true,true,true,
                      true,false,0x310,0,true,true,true,0x310,0x320);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,
                      true,false,0x310,0,true,true,true,0x310,0x31f);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,
                      true,false,0x318,0,true,true,true,0x318);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,
                      true,false,0x320,0,true,true,true,0x310);
    CheckNativeAtomic(Opcode::StorageAtomicExchange32,true);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd64,true);
    CheckNativeAtomic(Opcode::StorageAtomicExchange64,true);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd64,false,true,true,true,true,false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd64,false,true,true,true,false,true);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd64,false,true,true,true,true,true,
                      false,0x310,0,false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,true,
                      false,0x310,2);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd64,false,true,true,true,true,true,
                      false,0x310,4);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,true,true,true,true,true,true,
                      false,0x310,4);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd64,true,true,true,true,true,true,
                      false,0x310,8);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32x2,false);
    CheckNativeAtomic(Opcode::StorageAtomicExchange32x2,false);
    CheckNativeAtomic(Opcode::GlobalAtomicIAdd32,false);
    CheckNativeAtomic(Opcode::GlobalAtomicExchange64,false);
    CheckNativeAtomic(Opcode::GlobalAtomicMaxF32x2,false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,false);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,true,true);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,true,false,0x314);
    CheckNativeAtomic(Opcode::StorageAtomicIAdd32,false,true,true,true,true,true,false,0xfff8);
    // No atomic instructions is valid even when there are no SSBOs.
    {
        Shader::ObjectPool<Shader::IR::Inst> pool{4};
        Shader::IR::Block block{pool};
        Shader::IR::Program program{};
        program.stage=Shader::Stage::Compute;
        program.blocks.push_back(&block);
        block.AppendNewInst(Opcode::IAdd32,{Value{u32{0}},Value{u32{1}}});
        assert(Shader::Ampere::NativeQmdAtomicStorageIRAdmissible(
            program,Shader::Profile{}));
    }
    std::puts("P2_3_NATIVE_QMD_REAL_DIRECT_CBUF_PASS masks=reflected widths=bounded dynamic=64KiB atomics=authenticated no_nonatomic_fallback=1");
}
