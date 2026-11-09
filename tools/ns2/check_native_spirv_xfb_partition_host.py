#!/usr/bin/env python3
"""G02: execute native SPIR-V transform-feedback partition owner (Clang/GCC).

Reject overflowing varying count / component spans before index or output
publication. Real source is extracted unchanged; no synthetic replacement of
the partition routine or claim of real TransformFeedback Vulkan execution.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp").read_text()
marker="void DefineGenericOutput("
assert source.count(marker)==1
body=source.split(marker,1)[1].split("\n}\n",1)[0]
owner=marker+body+"\n}"
assert owner.count("Transform-feedback varying count exceeds backing")==1
assert owner.count("Invalid transform-feedback component partition")==1
assert owner.count("Invalid transform-feedback byte stride/offset")==1
stage_owner=source.split("void EmitContext::DefineOutputs(",1)[1].split(
    "\nvoid EmitContext::",1)[0]
assert "Transform feedback on unsupported shader stage" in stage_owner
assert stage_owner.index("stage != Stage::TessellationEval") < stage_owner.index(
    "if (stage == Stage::Task || stage == Stage::Mesh)")
assert owner.index("num_components > (xfb_varying->stride - xfb_varying->offset)") < owner.index("ctx.F32[num_components]")
assert owner.index("num_components > remainder") < owner.index("ctx.F32[num_components]")
assert owner.index("xfb_count > ctx.runtime_info.xfb_varyings.size()") < owner.index("while (element < 4)")
fixture=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
using u32=std::uint32_t;
struct Id {u32 value{};};
enum class Stage {VertexB,Geometry};
namespace IR {enum class Attribute:u32 {Generic0X=0};}
namespace spv {
enum class Decoration {Location,Component,XfbBuffer,XfbStride,Offset,Stream};
}
namespace fmt {
template<class... Args> std::string format(std::string_view,Args...) {
    return "xfb_output";
}
}
struct NotImplementedException:std::runtime_error {
    template<class... T> explicit NotImplementedException(const char*,T&&...)
        :std::runtime_error("invalid transform feedback") {}
};
struct TransformFeedbackVarying {
    u32 buffer{},stride{},offset{},components{},stream{};
};
struct GenericElementInfo {
    Id id{};
    u32 first_element{},num_components{};
};
struct RuntimeInfo {
    std::array<TransformFeedbackVarying,256> xfb_varyings{};
    u32 xfb_count{};
};
struct EmitContext {
    Stage stage{Stage::Geometry};
    RuntimeInfo runtime_info{};
    std::array<Id,5> F32{{Id{1},Id{2},Id{3},Id{4},Id{5}}};
    std::array<std::array<GenericElementInfo,4>,2> output_generics{};
    unsigned outputs{},decorations{},named{};
    Id Decorate(Id id,spv::Decoration,u32) {++decorations;return id;}
    void Name(Id,std::string) {++named;}
};
Id DefineOutput(EmitContext& ctx,Id type,std::optional<u32>) {
    assert(type.value!=0);
    return Id{10+ ++ctx.outputs};
}
__REAL_OWNER__
int main(){
    {
        EmitContext c;
        DefineGenericOutput(c,0,std::nullopt);
        assert(c.outputs==1);
        for(const auto& e:c.output_generics[0])
            assert(e.num_components==4 && e.first_element==0 && e.id.value==11);
    }
    {
        EmitContext c;
        c.runtime_info.xfb_count=4;
        c.runtime_info.xfb_varyings[0]={0,16,0,2,1};
        c.runtime_info.xfb_varyings[2]={0,16,8,2,1};
        DefineGenericOutput(c,0,1);
        assert(c.outputs==2);
        for(u32 j=0;j<2;++j) {
            assert(c.output_generics[0][j].num_components==2);
            assert(c.output_generics[0][j].first_element==0);
        }
        for(u32 j=2;j<4;++j) {
            assert(c.output_generics[0][j].num_components==2);
            assert(c.output_generics[0][j].first_element==2);
        }
    }
    {
        EmitContext c;
        c.runtime_info.xfb_count=257;
        bool rejected{};
        try{DefineGenericOutput(c,0,std::nullopt);}
        catch(const NotImplementedException&){rejected=true;}
        assert(rejected && c.outputs==0 && c.decorations==0);
    }
    {
        EmitContext c;
        c.runtime_info.xfb_count=1;
        c.runtime_info.xfb_varyings[0]={0,16,0,5,0};
        bool rejected{};
        try{DefineGenericOutput(c,0,std::nullopt);}
        catch(const NotImplementedException&){rejected=true;}
        assert(rejected && c.outputs==0 && c.decorations==0);
    }
    {
        EmitContext c;
        c.runtime_info.xfb_count=3;
        c.runtime_info.xfb_varyings[0]={0,16,0,2,0};
        c.runtime_info.xfb_varyings[2]={0,16,8,3,0};
        bool rejected{};
        try{DefineGenericOutput(c,0,std::nullopt);}
        catch(const NotImplementedException&){rejected=true;}
        assert(rejected && c.outputs==1);
        assert(c.output_generics[0][2].id.value==0);
        assert(c.output_generics[0][3].id.value==0);
    }
    // Byte offsets, alignment and complete vertex-stride coverage are
    // properties of the guest's real interleaved stream, not just SPIR-V
    // vector component counts.
    for(const TransformFeedbackVarying bad : {
        TransformFeedbackVarying{0,8,8,2,0}, // 8+8 exceeds stride
        TransformFeedbackVarying{0,16,2,1,0}, // misaligned offset
        TransformFeedbackVarying{0,14,0,1,0}, // misaligned stride
        TransformFeedbackVarying{0,0,0,1,0},  // no space for any byte
        TransformFeedbackVarying{0,4,0xfffffffcu,1,0} // huge offset
    }) {
        EmitContext c;
        c.runtime_info.xfb_count=1;
        c.runtime_info.xfb_varyings[0]=bad;
        bool rejected{};
        try{DefineGenericOutput(c,0,std::nullopt);}
        catch(const NotImplementedException&){rejected=true;}
        assert(rejected && c.outputs==0 && c.decorations==0);
    }
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Clang/GCC required"
with tempfile.TemporaryDirectory(prefix="encore-g02-xfb-owner-") as temp:
    file=Path(temp)/"owner.cpp";file.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            command=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                     "-fsanitize=undefined","-fno-sanitize-recover=all",
                     str(file),"-o",str(exe)]
            built=subprocess.run(command,capture_output=True,text=True,timeout=60,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert run.returncode==0,run.stderr[-5000:]
            print("G02_NATIVE_TRANSFORM_FEEDBACK_PARTITION_PASS",Path(cc).name,opt,
                  "full_vector=1 partitioned_2x2=1 invalid_count_rejected=1"
                  " overrun_rejected=1 partial_partition_rejected=1 xfb_byte_range=checked",flush=True)
