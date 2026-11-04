#!/usr/bin/env python3
"""P2.3: prove native U32x2 reads across 8-/16-byte uniform vector rows.

Checks the production SPIR-V owner syntax with pinned headers, the exact
guest-byte/word admission predicates, and a source-aligned C++ oracle
against real sequential 32-bit words. No Vulkan driver or PS5 is run.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp"
CBUF = ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_indirect_cbuf.h"
SHARED = ROOT / "vendor/sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp"
source = SRC.read_text()
assert "NativeSpirvCbufBoundsActive()" in source
assert "native_access_bytes" in source
assert "offset.U32() > 0x10000U - native_access_bytes" in source
assert "ctx.Def(offset), ctx.Const(0x10000U - native_access_bytes)" in source
assert "native_access_bytes == 8 && (offset.U32() & 3U)" in source
assert "native_access_bytes != 8 ? valid_span :" in source
assert "ctx.OpLogicalAnd(ctx.U1, valid_span," in source
assert "ctx.OpBitwiseAnd(ctx.U32[1], ctx.Def(offset), ctx.Const(3U))" in source
assert "buffer_offset, ctx.Const(~u32{0})" in source
assert "ctx.OpSelect(ctx.U32[1], valid_offset," in source
assert "op == Shader::IR::Opcode::GetCbufU32x2 && (byte_offset & 3U)" in CBUF.read_text()
assert "op == Shader::IR::Opcode::GetCbufU32x2" in CBUF.read_text()
assert "NativeQmdStaticCbufReadExtent(last_reflected_byte)" in CBUF.read_text()
assert "ctx.Const(element_size - 4U)" in source
assert "ctx.Const(element_size - 1U)" in source
assert "GetCbufElement(ctx, first_row, offset, 0u, 2)" in source
assert "GetCbufElement(ctx, second_row, offset, 1u, 2)" in source
assert "ctx.load_const_func_u32x2, 8, true)" in source
assert "GetCbufU32x4(ctx, binding, offset, 8, true)" in source
assert "GetCbufElement(ctx, second_row, offset, 1u)" in source
assert "GetCbufElement(ctx, first_row, offset, 0u)" in source
assert "OpUGreaterThanEqual(" in source
assert "ctx.Const(element_size - 4U)" in source
assert "ctx.Const(element_size - 1U)" in source
assert "element % vector_components" in source
assert "element = ctx.OpBitwiseAnd(ctx.U32[1], element," in source
assert "ctx.OpULessThan(" in source
assert "if (!Shader::Ampere::NativeSpirvCbufBoundsActive()) {" in source
assert "NativeSpirvCbufBoundsActive()" not in SHARED.read_text()
assert "NativeQmdStaticCbufReadExtent(" in CBUF.read_text()

# The emitted SPIR-V storage vector can be U32x4 even when the original
# guest instruction reads just U8/U16. Inspect actual call-site widths.
for function, width in (
    ("EmitGetCbufU8", 1), ("EmitGetCbufS8", 1),
    ("EmitGetCbufU16", 2), ("EmitGetCbufS16", 2),
):
    start = source.index("Id " + function + "(")
    end = source.index("\nId EmitGetCbuf", start + 1)
    body = source[start:end]
    assert f"GetCbufU32(ctx, binding, offset, {width})" in body
    assert f"GetCbufU32x4(ctx, binding, offset, {width})" in body
    assert f"ctx.load_const_func_u{8 if width == 1 else 16}, {width})" in body
u32 = source.split("Id EmitGetCbufU32(", 1)[1].split("Id EmitGetCbufF32(", 1)[0]
assert "GetCbufU32(ctx, binding, offset)" in u32
assert "GetCbufU32x4(ctx, binding, offset)" in u32
wide = source.split("Id EmitGetCbufU32x2(", 1)[1].split("Id EmitGetAttribute(", 1)[0]
assert "ctx.load_const_func_u32x2, 8)" in wide
assert "NativeSpirvCbufBoundsActive()" in wide

CPP = r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
using u32=std::uint32_t;
constexpr u32 CBUF_BYTES=0x10000;
constexpr bool Within(u32 byte,u32 width) {
 return (width==1 || width==2 || width==4 || width==8) &&
        byte<=CBUF_BYTES-width && (width!=8 || (byte & 3U)==0);
}
struct WordPair {u32 first,second;};
constexpr WordPair pair_from_rows(u32 byte,const std::array<u32,CBUF_BYTES/4>& words) {
 if(!Within(byte,8))return {};
 const u32 first_row=byte/16;
 const u32 first_element=(byte/4)&3;
 const u32 second_row=first_row+((byte&15)>=12);
 const u32 second_element=(first_element+1)&3;
 return {words[first_row*4+first_element],
         words[second_row*4+second_element]};
}
constexpr WordPair pair_from_u32x2_vectors(
    u32 byte,const std::array<u32,CBUF_BYTES/4>& words) {
 if(!Within(byte,8))return {};
 // Exact native GetCbuf(element_size=8,next_vector_for_pair=true)
 // plus GetCbufElement(...,vector_components=2).
 const u32 first_vector=byte/8;
 const u32 second_vector=first_vector+((byte&7)>=4);
 const u32 first_element=(byte/4)&1;
 const u32 second_element=(first_element+1)&1;
 return {words[first_vector*2+first_element],
         words[second_vector*2+second_element]};
}
int main(){
 for(auto width:{1U,2U,4U,8U}) {
  for(u32 offset=0;offset<=CBUF_BYTES+16;++offset) {
   const bool expected=offset<=CBUF_BYTES-width &&
                       (width!=8 || (offset & 3U)==0);
   assert(Within(offset,width)==expected);
   if(!expected) {
    // The actual native SPIR-V builder injects ~0U as its element
    // index, forcing direct/indirect 64-KiB guards to produce zero.
    constexpr u32 sentinel=std::numeric_limits<u32>::max();
    assert(sentinel>=CBUF_BYTES/width);
   }
  }
 }
 static std::array<u32,CBUF_BYTES/4> words{};
 for(u32 i=0;i<words.size();++i) words[i]=0xa0000000U ^ (i*131U);
 for(u32 offset=0;offset<CBUF_BYTES+16;offset+=4){
  const auto pair=pair_from_rows(offset,words);
  const auto pair_alias=pair_from_u32x2_vectors(offset,words);
  assert(pair.first==pair_alias.first && pair.second==pair_alias.second);
  if(!Within(offset,8)) {assert(pair.first==0 && pair.second==0);continue;}
  const u32 i=offset/4;
  assert(pair.first==words[i] && pair.second==words[i+1]);
 }
 for(u32 start: {0U,4U,8U,12U,16U,20U,28U,44U,60U,
                  0xffe8U,0xffecU,0xfff0U,0xfff4U,0xfff8U,
                  0xfffcU,0x10000U}){
  const auto p=pair_from_rows(start,words);
  const auto q=pair_from_u32x2_vectors(start,words);
  assert(p.first==q.first && p.second==q.second);
  if(Within(start,8))
    assert(p.first==words[start/4] && p.second==words[start/4+1]);
  else assert(p.first==0 && p.second==0);
 }
 assert(Within(0xffff,1));
 assert(Within(0xfffe,2) && !Within(0xffff,2));
 assert(Within(0xfffc,4) && !Within(0xfffd,4));
 assert(Within(0xfff8,8) && !Within(0xfffc,8));
 assert(Within(4,8) && Within(12,8) && Within(0xfff4,8));
 assert(!Within(2,8) && !Within(6,8) && !Within(0xfff6,8));
 assert(Within(0,8) && Within(8,8) && Within(0xfff0,8));
 assert(!Within(std::numeric_limits<u32>::max(),8));
 std::puts("P2_3_CBUF_NATIVE_ORIGINAL_BYTE_SPAN_PASS sizes=1/2/4/8"
           " cross_row_u32x2=1 unaligned_subword_refused=1 invalid_sentinel=1");
}
'''
compilers = list(dict.fromkeys(filter(None, (shutil.which("clang++"), shutil.which("g++")))))
assert compilers
env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sys.platform == "darwin" and sdk.is_dir():
    env["SDKROOT"] = str(sdk)
with tempfile.TemporaryDirectory(prefix="encore-cbuf-guest-span-") as temp:
    file = Path(temp)/"span.cpp"
    file.write_text(CPP)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(compiler).name+opt)
            built=subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                "-fsanitize=undefined","-fno-sanitize-recover=all",str(file),"-o",str(exe)],
                env=env,text=True,capture_output=True,timeout=65)
            assert built.returncode==0,(opt,built.stderr[-5500:])
            ran=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=25)
            assert ran.returncode==0,(opt,ran.stdout,ran.stderr)
            print(Path(compiler).name,opt,ran.stdout.strip(),flush=True)

# Parse the *whole changed SPIR-V emitter*, not an isolated mock, when the
# pinned modular libraries are present (Mac dev checkout). Linux CI may rely
# on fetched Boost/SPIR-V headers; absence is a documented SKIP, not success.
boost=ROOT/"vendor/sources/eden-cpm/boost/boost-1.90.0/libs"
sirit=ROOT/"vendor/sources/eden-cpm/sirit/v1.0.5/include/sirit/sirit.h"
spirv=ROOT/"vendor/sources/eden-cpm/spirv-headers/vulkan-sdk-1.4.341.0/include/spirv/unified1/spirv.hpp11"
if boost.is_dir() and sirit.is_file() and spirv.is_file():
    includes=[ROOT/"vendor/encore-active/ns2-runtime/ampere",
        ROOT/"vendor/sources/eden/src",
        ROOT/"vendor/sources/fmt/include",
        sirit.parents[1],spirv.parents[2],
        ROOT/"vendor/sources/eden-cpm/vulkanheaders/v1.4.345/include",
        ROOT/"vendor/encore-active/ns2-helpers/include",
        *sorted(boost.glob("*/include"))]
    extra=[]
    libc=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk/usr/include/c++/v1")
    if sys.platform == "darwin" and libc.is_dir():
        extra=["-nostdinc++","-isystem",str(libc)]
    for opt in ("-O0","-O2"):
        args=[compilers[0],"-std=c++20","-fsyntax-only",opt,
              "-Wno-unused-parameter","-DFMT_HEADER_ONLY",*extra]
        args+=["-I"+str(folder) for folder in includes if folder.is_dir()]
        done=subprocess.run([*args,str(SRC)],env=env,capture_output=True,text=True,timeout=100)
        assert done.returncode==0,(opt,done.stderr[-7000:])
        print("P2_3_CBUF_REAL_SPIRV_OWNER_SYNTAX_PASS",opt,flush=True)
else:
    print("P2_3_CBUF_REAL_SPIRV_OWNER_SYNTAX_SKIPPED pinned modular host headers unavailable")
