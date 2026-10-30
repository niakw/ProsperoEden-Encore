// SPDX-License-Identifier: GPL-3.0-or-later
// Actual Eden Maxwell Flow::CFG execution, not just a bridge syntax check.
// Synthetic NOP/MOV/EXIT only; no copyrighted game shader or GPU execution.
#include <array>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <vector>
#include "shader_recompiler/frontend/ampere/maxwell_environment.h"
#include "shader_recompiler/frontend/maxwell/control_flow.h"

using namespace Shader::Ampere;
static void Require(bool pass, const char* reason) {
    if (!pass) { std::fprintf(stderr, "NS2 Maxwell CFG: %s\n", reason); std::exit(1); }
}
struct NativeSource final : Shader::Environment {
    NativeSource() {
        stage=Shader::Stage::VertexB;
        start_address=0;
    }
    u64 ReadInstruction(u32) override {
        // The real CFG must NEVER decode the raw native Ampere instruction.
        std::abort();
    }
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
static void Emit(std::vector<u8>& v,u32 a,u32 b=0,u32 c=0,u32 d=0) {
    for (u32 w : {a,b,c,d})
        for (u32 shift=0;shift<32;shift+=8)
            v.push_back(static_cast<u8>(w>>shift));
}
int main() {
    std::array<u8,0x50> header{};
    constexpr u32 pt=7U<<12, exit_true=7U<<23;
    std::vector<u8> native;
    Emit(native,pt|0x918);                        // NOP
    Emit(native,pt|0x202|(1U<<16),2,15U<<8);    // MOV R1,R2
    Emit(native,pt|0x918);                        // NOP, crosses scheduling slot
    Emit(native,pt|0x918);                        // NOP
    Emit(native,pt|0x94d,0,exit_true);            // unconditional EXIT
    auto translated=BuildMaxwellShaderImage(
        header,native,static_cast<u32>(Shader::Stage::VertexB));
    Require(translated.ValidForCompiler() &&
            translated.ReadMaxwellInstruction(0x50).has_value() &&
            !translated.ReadMaxwellInstruction(0x60).has_value(),
            "translated synthetic graphics program must be well formed");
    auto env=NativeMaxwellEnvironment::CreateOwned(
        std::make_unique<NativeSource>(),std::move(translated));
    Require(env && env->StartAddress()==0,
            "owned source metadata and start address must be coherent");
    for (bool dispatcher : {false,true}) {
        Shader::ObjectPool<Shader::Maxwell::Flow::Block> blocks{64};
        Shader::Maxwell::Flow::CFG cfg{
            *env,blocks,env->StartAddress()+sizeof(Shader::ProgramHeader),dispatcher};
        Require(cfg.ExitsToDispatcher()==dispatcher && !cfg.Functions().empty(),
                "real Maxwell CFG decoded reviewed native translation");
        const auto& first=cfg.Functions().front();
        Require(first.entrypoint.Offset()==0x50 && !first.blocks.empty(),
                "real CFG begins after the SPH, not at the native header");
        bool saw_exit=false;
        for (const auto& block : first.blocks) {
            if (block.end_class==Shader::Maxwell::Flow::EndClass::Exit ||
                (dispatcher && block.end_class==Shader::Maxwell::Flow::EndClass::Branch))
                saw_exit=true;
        }
        Require(saw_exit,"translated EXIT yields a terminating CFG edge");
    }
    std::puts("NS2 actual Maxwell CFG: PASS (IR/SPIR-V/Vulkan not executed)");
}
