// SPDX-License-Identifier: GPL-3.0-or-later
// Real Ampere graphics guest-PC capture, lowering, image, and LRU witnesses.
// Synthetic LEPC/EXIT shader; this does NOT execute a PS5/Vulkan shader.
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <span>
#include <vector>

#include "shader_recompiler/frontend/ampere/capture.h"
#include "shader_recompiler/frontend/ampere/translation_cache.h"
#include "shader_recompiler/frontend/ampere/lower_to_maxwell.h"
#include "shader_recompiler/stage.h"

using namespace Shader::Ampere;
static constexpr u32 pt=7U<<12;
static constexpr Instruction Nop{{pt|0x918U,0,0,0x000fea00U}};
static constexpr Instruction Lepc{{pt|0x34eU|(4U<<16),0,0,0x000fea00U}};
static constexpr Instruction Exit{{pt|0x94dU,0,7U<<23,0x000fea00U}};
static void Append(std::vector<u8>& out, Instruction instruction) {
    for (u32 word:instruction.words)
        for (u32 shift=0;shift<32;shift+=8)
            out.push_back(static_cast<u8>(word>>shift));
}
struct Reader {
    u64 gpu_base{};
    std::vector<u8> memory{};
    u32 reads{};
};
static bool Read(void* context,u64 address,void* data,std::size_t size) {
    auto& reader=*static_cast<Reader*>(context);
    ++reader.reads;
    if (!data || address<reader.gpu_base || !size) return false;
    const u64 offset=address-reader.gpu_base;
    if (offset>reader.memory.size() || size>reader.memory.size()-offset) return false;
    std::memcpy(data,reader.memory.data()+offset,size);
    return true;
}
static void Require(bool b,const char* why) {
    if (!b) {std::fprintf(stderr,"LEPC failure: %s\n",why); std::abort();}
}
static u32 EncodedImmediate(u64 word) {
    return static_cast<u32>((word>>20)&0xffffffffU);
}
int main() {
    const std::array shader{Nop,Lepc,Exit};
    constexpr u64 baseA=0x13000000400ULL;
    constexpr u64 baseB=0x14000000400ULL;
    constexpr u64 codeA=baseA+0x80U;
    constexpr u64 codeB=baseB+0x80U;
    const auto directA=LowerToMaxwell(shader,{},false,{},codeA);
    const auto directB=LowerToMaxwell(shader,{},false,{},codeB);
    Require(directA && directB,"real LowerToMaxwell accepts checked guest PC");
    Require(directA.source_instruction_offsets.size()==shader.size(),
            "source PC map accounts for the LEPC instruction");
    const u32 ai=directA.source_instruction_offsets[1];
    const u32 bi=directB.source_instruction_offsets[1];
    const u64 guest_pc_A=codeA+16;
    const u64 guest_pc_B=codeB+16;
    Require(ai+2==directA.source_instruction_offsets[2],
            "native LEPC is exactly two Maxwell MOV immediates");
    Require((directA.instructions[ai]&0xffU)==4 &&
            (directA.instructions[ai+1]&0xffU)==5 &&
            EncodedImmediate(directA.instructions[ai])==
              static_cast<u32>(guest_pc_A) &&
            EncodedImmediate(directA.instructions[ai+1])==
              static_cast<u32>(guest_pc_A>>32),
            "LEPC materializes actual 64-bit native guest PC, not Maxwell PC");
    Require(EncodedImmediate(directB.instructions[bi+1])==
            static_cast<u32>(guest_pc_B>>32) &&
            directB.instructions[bi+1]!=directA.instructions[ai+1],
            "same shader bytes at different guest VA yields distinct PC");
    const auto unavailable=LowerToMaxwell(shader);
    Require(!unavailable && unavailable.error==
        "native dynamic program counter unsupported",
        "source-only LEPC cannot manufacture a zero/translated guest PC");
    Require(!LowerToMaxwell(shader,{},false,{},u64{1}<<49),
            "out-of-range GPU code VA rejected before MOV");
    auto malformed=Lepc;
    malformed.words[1]=1;
    Require(!LowerToMaxwell(std::array{Nop,malformed,Exit},
                           {},false,{},codeA),
            "unknown LEPC offset mode must fail closed");
    // Predicated LEPC writes the authenticated PC as TWO equally predicated
    // Maxwell MOV instructions; a false predicate must preserve both GPRs.
    for (const u32 execution : std::array{6U,14U}) {
        auto predicated=Lepc;
        predicated.words[0]=(predicated.words[0]&~0xf000U)|(execution<<12);
        const std::array source{Nop,predicated,Exit};
        const auto lowered=LowerToMaxwell(source,{},false,{},codeA);
        Require(bool(lowered),"predicated LEPC needs authenticated GMMU PC");
        const u32 pos=lowered.source_instruction_offsets[1];
        Require(pos+2==lowered.source_instruction_offsets[2],
                "predicated LEPC emits two Maxwell MOVs");
        for (u32 word=0;word<2;++word) {
            const u64 emitted=lowered.instructions[pos+word];
            Require(((emitted>>16)&15U)==execution &&
                    (emitted&255U)==4U+word &&
                    EncodedImmediate(emitted)==
                        static_cast<u32>(guest_pc_A>>(32*word)),
                    "both halves retain source predicate and PC");
        }
        Require(!LowerToMaxwell(source),
                "predicated LEPC without authenticated GMMU PC must refuse");
        const auto relocated=LowerToMaxwell(source,{},false,{},codeB);
        Require(bool(relocated) &&
                relocated.instructions[relocated.source_instruction_offsets[1]+1]!=
                    lowered.instructions[pos+1],
                "predicated LEPC cannot reuse another guest code VA");
    }
    auto invalid_predicate=Lepc;
    invalid_predicate.words[0]=(invalid_predicate.words[0]&~0xf000U)|(15U<<12);
    Require(!LowerToMaxwell(std::array{Nop,invalid_predicate,Exit},
                           {},false,{},codeA),
            "inverted PT is not a reviewed execution predicate");
    auto high=Lepc;
    high.words[0]=(high.words[0]&0xff00ffffU)|(252U<<16);
    Require(!LowerToMaxwell(std::array{Nop,high,Exit},
                           {},false,{},codeA),
            "LEPC pair cannot alias Maxwell high scratch");

    std::array<u8,0x50> header{};
    std::vector<u8> native;
    for (const auto instruction:shader) Append(native,instruction);
    const u32 geom=static_cast<u32>(Shader::Stage::Geometry);
    const u32 vert=static_cast<u32>(Shader::Stage::VertexB);
    const u32 compute=static_cast<u32>(Shader::Stage::Compute);
    const std::array stages{
        static_cast<u32>(Shader::Stage::VertexA),
        vert,static_cast<u32>(Shader::Stage::TessellationControl),
        static_cast<u32>(Shader::Stage::TessellationEval),geom,
        static_cast<u32>(Shader::Stage::Fragment)};
    const auto without_pc=BuildMaxwellShaderImage(header,native,geom);
    const auto direct_image_A=BuildMaxwellShaderImage(header,native,geom,{},codeA);
    const auto direct_image_B=BuildMaxwellShaderImage(header,native,geom,{},codeB);
    for (u32 stage : stages) {
        const auto stage_image=BuildMaxwellShaderImage(header,native,stage,{},codeA);
        Require(stage_image.ValidForCompiler(),
                "every known graphics stage uses its own real guest PC");
    }
    Require(!BuildMaxwellShaderImage(header,native,compute,{},codeA).Ready(),
            "Compute must not fabricate a graphics shader header/LEPC PC");
    // Task=VertexA+1 and Mesh=VertexA+2 are now authenticated graphics
    // stages. Never reject Task as "unknown" merely because its ABI ID is 7.
    // The first stage *after* Mesh is truly unsupported and must fail closed.
    static_assert(static_cast<u32>(Shader::Stage::Task) ==
                  static_cast<u32>(Shader::Stage::VertexA) + 1U);
    static_assert(static_cast<u32>(Shader::Stage::Mesh) ==
                  static_cast<u32>(Shader::Stage::Task) + 1U);
    constexpr u32 unknown_stage = static_cast<u32>(Shader::Stage::Mesh) + 1U;
    Require(!BuildMaxwellShaderImage(header,native,unknown_stage,{},codeA).Ready(),
            "unknown stage cannot opt into untrusted graphics source PC");
    Require(!without_pc.Ready() &&
            direct_image_A.ValidForCompiler() &&
            direct_image_B.ValidForCompiler() &&
            direct_image_A.diagnostic_cache_key!=
                direct_image_B.diagnostic_cache_key,
            "native shader code VA belongs to image key and valid CFG");
    NativeTranslationCache cache{1024*1024,8};
    const auto cachedA=cache.GetOrTranslate(header,native,geom,codeA);
    const auto cachedB=cache.GetOrTranslate(header,native,geom,codeB);
    const auto cachedAagain=cache.GetOrTranslate(header,native,geom,codeA);
    const auto stats=cache.Stats();
    Require(cachedA.Ready() && cachedB.Ready() && cachedAagain.Ready() &&
            cachedA.code!=cachedB.code && cachedA.code==cachedAagain.code &&
            stats.translations==2 && stats.hits==1 &&
            stats.entries==2,
            "LRU compares guest code base as well as full shader bytes");
    // The real source capture, not the test caller, supplies this PC and
    // uses the same GMMU mapping/authentication on every cache replay.
    Reader first{baseA,std::vector<u8>(0x80)};
    Reader second{baseB,std::vector<u8>(0x80)};
    for (const auto inst:shader) {
        Append(first.memory,inst);
        Append(second.memory,inst);
    }
    NativeTranslationCache capture_cache{1024*1024,8};
    const auto capA=CaptureNativeGraphicsShader(
        baseA,geom,Read,&first,&capture_cache);
    const auto capB=CaptureNativeGraphicsShader(
        baseB,geom,Read,&second,&capture_cache);
    const auto capAagain=CaptureNativeGraphicsShader(
        baseA,geom,Read,&first,&capture_cache);
    if (!capA.Ready() || !capB.Ready())
        std::fprintf(stderr,
            "Capture geometry LEPC statuses A=%u B=%u\n",
            static_cast<unsigned>(capA.status),static_cast<unsigned>(capB.status));
    Require(capA.Ready() && capB.Ready() && capAagain.Ready() &&
            capA.image.diagnostic_cache_key!=
                capB.image.diagnostic_cache_key &&
            capture_cache.Stats().translations==2 &&
            capture_cache.Stats().hits==1 &&
            first.reads>0 && second.reads>0,
            "real GMMU capture pipes code PC into cache with revalidation");
    NativeTranslationCache stage_cache{1024*1024,16};
    std::vector<u64> distinct_stage_keys;
    for (const u32 stage : stages) {
        const auto staged=CaptureNativeGraphicsShader(
            baseA,stage,Read,&first,&stage_cache);
        const auto different_va=CaptureNativeGraphicsShader(
            baseB,stage,Read,&second,&stage_cache);
        Require(staged.Ready() && different_va.Ready(),
                "every graphics stage captures authenticated GMMU LEPC");
        Require(staged.image.diagnostic_cache_key !=
                    different_va.image.diagnostic_cache_key,
                "LEPC shader at two guest VAs has distinct compiled identity");
        for (u64 key : distinct_stage_keys)
            Require(key != staged.image.diagnostic_cache_key,
                    "LEPC image identity must encode graphics stage");
        distinct_stage_keys.push_back(staged.image.diagnostic_cache_key);
    }
    Require(distinct_stage_keys.size()==6 &&
            stage_cache.Stats().translations==12 &&
            !CaptureNativeGraphicsShader(baseA,compute,Read,&first).Ready(),
            "only six recognized graphics stages can use their GMMU PC");

    // Without any LEPC opcode the same byte-identical graphics shader
    // at different VAs is NOT address-dependent and can share its image.
    Reader no_pc_first{baseA,std::vector<u8>(0x80)};
    Reader no_pc_second{baseB,std::vector<u8>(0x80)};
    for (const auto inst : std::array{Nop,Exit}) {
        Append(no_pc_first.memory,inst);
        Append(no_pc_second.memory,inst);
    }
    NativeTranslationCache no_pc_cache{1024*1024,8};
    const auto without_lepc_a=CaptureNativeGraphicsShader(
        baseA,vert,Read,&no_pc_first,&no_pc_cache);
    const auto without_lepc_b=CaptureNativeGraphicsShader(
        baseB,vert,Read,&no_pc_second,&no_pc_cache);
    Require(without_lepc_a.Ready() && without_lepc_b.Ready() &&
            without_lepc_a.image.diagnostic_cache_key ==
                without_lepc_b.image.diagnostic_cache_key &&
            no_pc_cache.Stats().translations==1 &&
            no_pc_cache.Stats().hits==1,
            "LEPC-free shaders preserve shared cache reuse across guest VAs");
    // Capture has a true guest VA only while GMMU memory exists.
    first.memory.resize(0x80+16);
    const auto invalidated=CaptureNativeGraphicsShader(
        baseA,geom,Read,&first,&capture_cache);
    Require(!invalidated.Ready(),
            "unmapped LEPC instruction never served from a stale LRU");
    std::puts("P2_4_NATIVE_LEPC_GMMU_CAPTURE_PASS guest_pc_64=1"
              " graphics_stages=6 compute_rejected=1"
              " pc_sensitive_only_when_LEPC=1 verified_cache_key=1"
              " source_replay=1 out_of_range_refused=1 ns1_unchanged=1");
}
