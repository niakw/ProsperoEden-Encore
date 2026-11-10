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

fixture=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <limits>
using u32=std::uint32_t;
namespace Shader::Backend::SPIRV {
struct Id {
    u32 value{};
    explicit operator bool() const { return value != 0; }
};
struct LogicError : std::runtime_error { using std::runtime_error::runtime_error; };
namespace IR {
enum class Type { U32, U64 };
struct Value {
    bool immediate{}, empty{};
    ::Shader::Backend::SPIRV::IR::Type type{::Shader::Backend::SPIRV::IR::Type::U32};
    u32 word{};
    bool IsEmpty() const { return empty; }
    bool IsImmediate() const { return immediate; }
    auto Type() const -> ::Shader::Backend::SPIRV::IR::Type { return type; }
    u32 U32() const {
        assert(immediate && type==::Shader::Backend::SPIRV::IR::Type::U32);
        return word;
    }
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
                  "valid=2 dynamic_preexisting=1 oob=2"
                  " invalid_type=2 empty=1 zero_count=1"
                  " singleton_invalid_imm=2 invalid_type=2 count_zero=2"
                  " dynamic_singleton=" + ("refused" if strict_singleton else "unchecked")
                  + " missing_descriptor=refused",flush=True)
