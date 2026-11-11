#!/usr/bin/env python3
"""C02 pinned source parity and real EmitSetFragColor body host sanitizer test.
Not proof of valid SPIR-V binary, native compiler linkage or PS5 Vulkan pixels.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
ORIG=ROOT/"vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp"
ACTIVE=ROOT/"headless/c02_spirv_fragcolor_ps5.cpp"
PIN="f768235d3a6667f18ee5900311364c7d9a7853ba"
OLD="""        const Id pointer{ctx.OpAccessChain(ctx.output_f32, ctx.frag_color.at(index), component_id)};
        ctx.OpStore(pointer, value);"""
NEW="""        const Id pointer{ctx.OpAccessChain(ctx.output_f32, ctx.frag_color.at(index), component_id)};
        ctx.OpStore(pointer, ctx.OpSelect(ctx.F32[1], ctx.OpIsNan(ctx.U1, value), ctx.Const(0.0f), value));"""
def verify():
    raw=ORIG.read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert sha==PIN,sha
    original=raw.decode()
    selected=ACTIVE.read_text()
    i=selected.index("// SPDX-FileCopyrightText")
    assert original.count(OLD)==2
    assert selected[i:]==original.replace(OLD,NEW)
    cm=(ROOT/"headless/CMakeLists.txt").read_text()
    for marker in ("C02 pinned shared fragment emitter owner changed",
                   "c02_spirv_fragcolor_ps5.cpp",
                   "list(APPEND eden_ns2_shader_sources"):
        assert marker in cm,marker
    print("AB_NS1_C02_SPIRV_PINNED_SOURCE_PARITY_PASS")
def test():
    source=ACTIVE.read_text()
    first=source.index("void EmitSetFragColor(")
    end=source.index("\nvoid EmitSetSampleMask(",first)
    method=source[first:end]
    assert method.count("ctx.OpSelect(")==2
    c=r"""
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
#include <initializer_list>
using u32=std::uint32_t;
using Id=float;
enum class AttributeType {Float,UnsignedInt,SignedInt,Disabled};
namespace spv {enum class StorageClass {Output};}
struct RuntimeInfo {std::array<AttributeType,4> color_output_types{};};
struct EmitContext {
 RuntimeInfo runtime_info;
 std::array<Id,2> F32{0,1},U32{0,1},S32{0,1};
 std::array<Id,4> frag_color{};
 Id output_f32{},output_u32{},U1{},last_value{};
 int nan_checks{},selections{},bitcasts{};
 template<class T> Id Const(T v) {return static_cast<Id>(v);}
 template<class... T> Id OpAccessChain(T...){return Id{1};}
 Id TypePointer(spv::StorageClass,Id){return Id{1};}
 Id OpBitcast(Id,Id v){++bitcasts;return v;}
 bool OpIsNan(Id,Id v){++nan_checks;return std::isnan(v);}
 Id OpSelect(Id,bool test,Id yes,Id no){++selections;return test?yes:no;}
 void OpStore(Id,Id v){last_value=v;}
};
"""+method+r"""
int main(){
 EmitContext ctx{};
 const Id nan=std::numeric_limits<Id>::quiet_NaN();
 const Id inf=std::numeric_limits<Id>::infinity();
 for(auto kind:{AttributeType::Float,AttributeType::Disabled}){
  ctx.runtime_info.color_output_types[0]=kind;
  EmitSetFragColor(ctx,0,0,nan);
  assert(ctx.last_value==0.0f);
  EmitSetFragColor(ctx,0,0,inf);
  assert(std::isinf(ctx.last_value));
  EmitSetFragColor(ctx,0,0,-0.0f);
  assert(std::signbit(ctx.last_value));
  EmitSetFragColor(ctx,0,0,0.75f);
  assert(ctx.last_value==0.75f);
 }
 const int n=ctx.nan_checks,s=ctx.selections,b=ctx.bitcasts;
 for(auto kind:{AttributeType::UnsignedInt,AttributeType::SignedInt}){
  ctx.runtime_info.color_output_types[0]=kind;
  EmitSetFragColor(ctx,0,0,nan);
  assert(std::isnan(ctx.last_value));
 }
 assert(ctx.nan_checks==n && ctx.selections==s && ctx.bitcasts==b+2);
}
"""
    with tempfile.TemporaryDirectory(prefix="ab-c02-spv-") as tmp:
        src,out=Path(tmp)/"spv.cpp",Path(tmp)/"spv"
        src.write_text(c)
        subprocess.run(["clang++","-std=c++20","-O1","-g","-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-omit-frame-pointer",
                        str(src),"-o",str(out)],check=True,cwd=ROOT,timeout=90)
        subprocess.run([str(out)],check=True,cwd=ROOT,timeout=15,
                       env={**os.environ,"ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1"})
    print("AB_NS1_C02_NAN_FLOAT_INT_PASSTHROUGH_HOST_ASAN_PASS")
if __name__=="__main__":
    try:
        verify()
        test()
    except (ValueError,AssertionError,OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        print("AB_NS1_C02_SPIRV_HOST_FAIL",exc,file=sys.stderr)
        sys.exit(1)
