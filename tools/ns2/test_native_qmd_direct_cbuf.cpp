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
int main() {
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
    Check(Opcode::GetCbufU32x2,0,0xfff8,1,1,false,false,true,0x10000);
    Check(Opcode::GetCbufU32x2,0,0xfffc,1,1,false,false,false,0);
    Check(Opcode::GetCbufU32,0,0,1,1,false,true,true,0x10000);
    Check(Opcode::GetCbufU32,1,0,1,3,false,false,false,0);
    Check(Opcode::GetCbufU32,0,0,1,1,true,false,false,0);
    Check(Opcode::GetCbufU32,0,0,1,0,false,false,false,0);
    std::puts("P2_3_NATIVE_QMD_REAL_DIRECT_CBUF_PASS masks=reflected widths=bounded dynamic=64KiB");
}
