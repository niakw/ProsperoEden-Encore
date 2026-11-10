#!/usr/bin/env python3
"""G01: execute the native SPIR-V emitter's actual descriptor-array index guard.

Clang/GCC UBSan verify valid first/last reflected texel-array descriptors,
foreign immediate indices and malformed index types. Real native source and
all five texture/texel/image array sites are checked, not a reimplemented
bounds predicate. Dynamic runtime descriptor bounds remain an open G01 gate.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
owner=ROOT/"vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_image.cpp"
source=owner.read_text()
start="void CheckSingletonTextureIndex("
end="\nId Texture("
assert source.count(start)==source.count(end)==1
method=start+source.split(start,1)[1].split(end,1)[0]
assert source.count("CheckedTextureArrayIndex(ctx, index, def.count)") == 5
assert source.count("CheckSingletonTextureIndex(index, def.count);") == 5
assert source.count("CheckedImageDescriptor(ctx.") == 7
assert "ctx.textures.at(info.descriptor_index)" not in source
assert 'throw LogicError("Missing reflected image/texture descriptor");' in method
assert "if (count != 1)" in method
assert 'Invalid singleton texture descriptor count' in method
assert "void CheckSingletonTextureIndex(" in method
strict_singleton = 'Dynamic singleton texture descriptor index unsupported' in method
if strict_singleton:
    assert "if (!index.IsImmediate())" in method
    assert "if (index.U32() != 0)" in method
else:
    # The still-pinned legacy vendor permits dynamic singleton indices.
    # Report that missing negative explicitly; never label it a proof.
    assert "index.IsImmediate() && index.U32() != 0" in method
assert method.count("selected >= count") == 1
assert method.index("selected >= count") < method.index("ctx.Const(selected)")
assert "index.Type() != IR::Type::U32" in method
assert "return ctx.Def(index);" in method
assert "NativeSpirvCbufBoundsActive()" in method
assert "NativeBoundedImageIndexMaximum(index)" in method
assert "Native dynamic image descriptor index unbounded" in method

fixture=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <limits>
#include <optional>
#include <algorithm>
using u32=std::uint32_t;
namespace Shader::Ampere {
inline bool host_native_image_bounds = false;
bool NativeSpirvCbufBoundsActive() noexcept {return host_native_image_bounds;}
}
namespace Shader::Backend::SPIRV {
struct Id {
    u32 value{};
    explicit operator bool() const { return value != 0; }
};
struct LogicError : std::runtime_error { using std::runtime_error::runtime_error; };
namespace IR {
enum class Type { U32, U64 };
enum class Opcode {
    Other, BitwiseAnd32, UMin32, BitFieldUExtract, ShiftRightLogical32,
    SelectU32, IAdd32
};
struct Inst;
struct Value {
    bool immediate{}, empty{};
    ::Shader::Backend::SPIRV::IR::Type type{::Shader::Backend::SPIRV::IR::Type::U32};
    u32 word{};
    const Inst* instruction{};
    bool IsEmpty() const { return empty; }
    bool IsImmediate() const { return immediate; }
    auto Type() const -> ::Shader::Backend::SPIRV::IR::Type { return type; }
    Value Resolve() const {return *this;}
    const Inst* TryInstRecursive() const {return instruction;}
    u32 U32() const {
        assert(immediate && type==::Shader::Backend::SPIRV::IR::Type::U32);
        return word;
    }
};
struct Inst {
    Opcode opcode{Opcode::Other};
    std::array<Value,3> args{};
    Opcode GetOpcode() const {return opcode;}
    const Value& Arg(unsigned n) const {return args.at(n);}
};
}
struct EmitContext {
    Id Const(u32 value) { return Id{value+100}; }
    Id Def(const IR::Value& value) { return Id{value.word+200}; }
};
__REAL_OWNER__
}
int main() {
    using namespace Shader::Backend::SPIRV;
    EmitContext ctx;
    const std::array<u32,3> textures{11,22,33};
    assert(CheckedImageDescriptor(textures,0)==11);
    assert(CheckedImageDescriptor(textures,2)==33);
    bool missing=false;
    try {(void)CheckedImageDescriptor(textures,3);} catch(const LogicError&){missing=true;}
    assert(missing);
    const std::array<u32,0> empty{};
    missing=false;
    try {(void)CheckedImageDescriptor(empty,0);} catch(const LogicError&){missing=true;}
    assert(missing);
    auto good=[](u32 i) { return IR::Value{true,false,IR::Type::U32,i}; };
    auto dynamic=[](u32 i) { return IR::Value{false,false,IR::Type::U32,i}; };
    assert(CheckedTextureArrayIndex(ctx,good(0),4).value==100);
    assert(CheckedTextureArrayIndex(ctx,good(3),4).value==103);
    assert(CheckedTextureArrayIndex(ctx,dynamic(2),4).value==202);
    CheckSingletonTextureIndex(IR::Value{false,true,IR::Type::U32,0},1);
    CheckSingletonTextureIndex(good(0),1);
    auto reject_singleton=[](const IR::Value& value,u32 count=1){
        try { CheckSingletonTextureIndex(value,count); }
        catch(const LogicError&) { return; }
        assert(false && "Foreign singleton descriptor index accepted");
    };
    __DYNAMIC_SINGLETON_TEST__
    reject_singleton(good(0),0);
    reject_singleton(dynamic(0),0);
    reject_singleton(good(1));
    reject_singleton(good(std::numeric_limits<u32>::max()));
    reject_singleton(IR::Value{true,false,IR::Type::U64,1});
    reject_singleton(IR::Value{false,false,IR::Type::U64,1});
    const auto reject=[&](const IR::Value& value,u32 count) {
        try { (void)CheckedTextureArrayIndex(ctx,value,count); }
        catch(const LogicError&) { return; }
        assert(false && "Malformed descriptor array admitted");
    };
    reject(good(0),0);
    reject(good(4),4);
    reject(good(std::numeric_limits<u32>::max()),4);
    reject(IR::Value{true,false,IR::Type::U64,1},4);
    reject(IR::Value{false,false,IR::Type::U64,1},4);
    reject(IR::Value{false,true,IR::Type::U32,0},4);
    // Native QMD3 uses an independent thread-local mode: unknown runtime
    // guest index -> refusal, but literal mask/min/extract/select and bounded
    // additions keep the actual OpAccessChain when their max is in range.
    Shader::Ampere::host_native_image_bounds=true;
    const IR::Inst mask{IR::Opcode::BitwiseAnd32,{dynamic(99),good(3),{}}};
    const IR::Value masked{false,false,IR::Type::U32,3,&mask};
    assert(CheckedTextureArrayIndex(ctx,masked,4).value==203);
    reject(masked,3); // masked maximum 3 does NOT fit a three-element array
    reject(dynamic(2),4); // raw guest SSBO/register index is not proven
    const IR::Inst minimum{IR::Opcode::UMin32,{dynamic(99),good(2),{}}};
    assert(CheckedTextureArrayIndex(ctx,
        IR::Value{false,false,IR::Type::U32,2,&minimum},3).value==202);
    const IR::Inst shifted{IR::Opcode::ShiftRightLogical32,
                           {dynamic(0),good(31),{}}};
    assert(CheckedTextureArrayIndex(ctx,
        IR::Value{false,false,IR::Type::U32,1,&shifted},2).value==201);
    const IR::Inst extracted{IR::Opcode::BitFieldUExtract,
                             {dynamic(0),good(3),good(2)}};
    assert(CheckedTextureArrayIndex(ctx,
        IR::Value{false,false,IR::Type::U32,3,&extracted},4).value==203);
    reject(IR::Value{false,false,IR::Type::U32,3,&extracted},3);
    const IR::Inst addition{IR::Opcode::IAdd32,{masked,good(1),{}}};
    assert(CheckedTextureArrayIndex(ctx,
        IR::Value{false,false,IR::Type::U32,4,&addition},5).value==204);
    reject(IR::Value{false,false,IR::Type::U32,4,&addition},4);
    const IR::Inst wrapped{IR::Opcode::IAdd32,
                          {good(std::numeric_limits<u32>::max()),good(1),{}}};
    reject(IR::Value{false,false,IR::Type::U32,1,&wrapped},4);
    const IR::Inst selected{IR::Opcode::SelectU32,{good(0),masked,good(1)}};
    assert(CheckedTextureArrayIndex(ctx,
        IR::Value{false,false,IR::Type::U32,3,&selected},4).value==203);
    const IR::Inst uncertain{IR::Opcode::SelectU32,{good(0),masked,dynamic(5)}};
    reject(IR::Value{false,false,IR::Type::U32,3,&uncertain},4);
    Shader::Ampere::host_native_image_bounds=false;
    assert(CheckedTextureArrayIndex(ctx,dynamic(5),4).value==205);
}
""".replace("__REAL_OWNER__",method)
if strict_singleton:
    fixture=fixture.replace("__DYNAMIC_SINGLETON_TEST__",
                            "reject_singleton(dynamic(0));\n    reject_singleton(dynamic(33));")
else:
    fixture=fixture.replace("__DYNAMIC_SINGLETON_TEST__",
                            "CheckSingletonTextureIndex(dynamic(0),1);\n    CheckSingletonTextureIndex(dynamic(33),1);")
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-g01-texel-index-") as d:
    src=Path(d)/"owner.cpp";src.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(d)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 str(src),"-o",str(exe)]
            build=subprocess.run(cmd,capture_output=True,text=True,timeout=60,
                                 env=os.environ.copy())
            assert build.returncode==0,build.stderr[-4500:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert run.returncode==0,run.stderr[-4500:]
            print("G01_REAL_SPIRV_DESCRIPTOR_INDEX_PASS",Path(cc).name,opt,
                  "valid=2 ns1_dynamic_unchanged=1 oob=2"
                  " native_unbounded=refused mask_min_extract_shift=bounded"
                  " select_add=bounded overflow=refused"
                  " invalid_type=2 empty=1 zero_count=1"
                  " singleton_invalid_imm=2 invalid_type=2 count_zero=2"
                  " dynamic_singleton=" + ("refused" if strict_singleton else "unchecked")
                  + " missing_descriptor=refused",flush=True)
