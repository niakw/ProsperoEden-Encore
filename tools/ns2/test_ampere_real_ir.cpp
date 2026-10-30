// SPDX-License-Identifier: GPL-3.0-or-later
// True pinned Eden Maxwell TranslateProgram integration; synthetic instructions only.
#include <array>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <vector>
#define CANNOT_EXPLICITLY_INSTANTIATE
#include "common/settings.h"
#include "shader_recompiler/frontend/ampere/ir_bridge.h"
#include "shader_recompiler/host_translate_info.h"
namespace Settings { Values values{}; }
using namespace Shader::Ampere;
static void Require(bool ok,const char* why) {
    if (!ok) { std::fprintf(stderr,"NS2 real IR: %s\n",why); std::exit(1); }
}
struct SyntheticSource final : Shader::Environment {
    SyntheticSource() { stage=Shader::Stage::VertexB; start_address=0; }
    u64 ReadInstruction(u32) override { std::abort(); }
    u32 ReadCbufValue(u32,u32) override { return 0; }
    Shader::TextureType ReadTextureType(u32) override { return {}; }
    Shader::TexturePixelFormat ReadTexturePixelFormat(u32) override { return {}; }
    bool IsTexturePixelFormatInteger(u32) override { return false; }
    u32 ReadViewportTransformState() override { return 0; }
    u32 TextureBoundBuffer() const override { return 0; }
    u32 LocalMemorySize() const override { return 0; }
    u32 SharedMemorySize() const override { return 0; }
    std::array<u32,3> WorkgroupSize() const override { return {}; }
    bool HasHLEMacroState() const override { return false; }
    std::optional<Shader::ReplaceConstant> GetReplaceConstBuffer(u32,u32) override { return {}; }
    void Dump(u64,u64) override { std::abort(); }
};
static void Emit(std::vector<u8>& bytes,u32 a,u32 b=0,u32 c=0,u32 d=0) {
    for (u32 word:{a,b,c,d})
        for (u32 shift=0;shift<32;shift+=8) bytes.push_back(static_cast<u8>(word>>shift));
}
int main() {
    std::array<u8,0x50> header{};
    constexpr u32 pred=7U<<12, exit_true=7U<<23;
    std::vector<u8> code;
    Emit(code,pred|0x918);
    Emit(code,pred|0x202|(1U<<16),2,15U<<8);
    Emit(code,pred|0x918);
    Emit(code,pred|0x918);
    Emit(code,pred|0x94d,0,exit_true);
    auto image=BuildMaxwellShaderImage(header,code,static_cast<u32>(Shader::Stage::VertexB));
    Require(image.ValidForCompiler(),"native->Maxwell image failed");
    auto env=NativeMaxwellEnvironment::CreateOwned(std::make_unique<SyntheticSource>(),std::move(image));
    Require(bool(env),"owned Maxwell environment failed");
    Shader::HostTranslateInfo host{};
    host.min_ssbo_alignment=64;
    host.support_float64=true;
    host.support_float16=true;
    host.support_int64=true;
    host.support_conditional_barrier=true;
    for (bool dispatcher:{false,true}) {
        Shader::ObjectPool<Shader::IR::Inst> inst_pool{4096};
        Shader::ObjectPool<Shader::IR::Block> block_pool{256};
        Shader::ObjectPool<Shader::Maxwell::Flow::Block> flow_pool{256};
        auto ir=TranslateReviewedGraphicsIR(inst_pool,block_pool,flow_pool,*env,host,dispatcher);
        Require(ir.stage==Shader::Stage::VertexB,"wrong IR stage");
        Require(!ir.blocks.empty()&&!ir.post_order_blocks.empty(),"empty real IR");
        Require(!ir.syntax_list.empty(),"missing real structured syntax");
    }
    std::puts("NS2 real Maxwell IR passes: PASS (host synthetic; no SPIR-V/Vulkan/PS5)");
}
