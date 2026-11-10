#!/usr/bin/env python3
"""R23: exact pinned-source ownership plus extracted actual F2I/BCAT unit tests.
No native PS5 build, vendor edit, binary linkage, or gameplay is claimed.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
V=ROOT/"vendor/sources/eden/src"
CASES={
 "f2i":(V/"shader_recompiler/frontend/maxwell/translate/impl/floating_point_conversion_integer.cpp",
        ROOT/"headless/r23_f2i_conversion_ps5.cpp",
        "c8c9e26248f92d4f5d97d670f4974ffd63c453fa",
        "    BitField<45, 1, u64> abs;\n    BitField<47, 1, u64> cc;\n    BitField<49, 1, u64> neg;",
        "    BitField<45, 1, u64> neg;\n    BitField<47, 1, u64> cc;\n    BitField<49, 1, u64> abs;"),
 "bcat":(V/"core/hle/service/bcat/delivery_cache_file_service.cpp",
         ROOT/"headless/r23_bcat_delivery_cache_file_ps5.cpp",
         "b75fac4bfefadcad35af430c8afe530cb426c1c3",
         "    R_TRY(VerifyNameValidDir(file_name_raw));",
         "    R_TRY(VerifyNameValidFile(file_name_raw));")
}

def gitblob(p):
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def verify():
    cm=(ROOT/"headless/CMakeLists.txt").read_text()
    for marker in (
        "list(FIND eden_r23_core_sources",
        "list(REMOVE_ITEM eden_r23_core_sources",
        "r23_bcat_delivery_cache_file_ps5.cpp",
        "list(FIND eden_r23_shader_sources",
        "list(REMOVE_ITEM eden_r23_shader_sources",
        "r23_f2i_conversion_ps5.cpp",
        "R23 BCAT source owner moved:",
        "R23 Maxwell F2I source owner moved:"):
        assert cm.count(marker)==1, ("CMake owner contract",marker)
    for name,(src,port,sha,old,new) in CASES.items():
        assert gitblob(src)==sha, ("unpinned vendor source",name)
        before,after=src.read_text(),port.read_text()
        assert before.count(old)==1 and not before.count(new),name
        i=after.find("// SPDX-FileCopyrightText")
        assert i>=0 and after[i:]==before.replace(old,new),("source code drift",name)
    print("R23_EXACT_TWO_MAINTAINED_SOURCE_OWNERS_PASS")

def run(folder,name,body):
    p=folder/(name+".cpp")
    p.write_text(body)
    exe=folder/name
    subprocess.run(["clang++","-std=c++20","-O1","-g","-Wall","-Wextra","-Werror",
                    "-fsanitize=address,undefined","-fno-omit-frame-pointer",
                    str(p),"-o",str(exe)],check=True,cwd=ROOT,timeout=100)
    subprocess.run([str(exe)],check=True,cwd=ROOT,timeout=15,
                   env={**os.environ,"ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1"})

def f2i(folder):
    src=CASES["f2i"][1].read_text()
    first=src.index("enum class DestFormat : u64")
    end=src.index("\n};\n\nsize_t BitSize",src.index("union F2I {"))+len("\n};")
    code=r"""
#include <cassert>
#include <cstdint>
using u64=std::uint64_t;
template<int Offset,int Width,typename T> struct BitField {
    u64 raw;
    operator T() const {return static_cast<T>((raw>>Offset)&((u64{1}<<Width)-1));}
};
namespace Shader {
namespace IR {using Reg=u64;}
namespace Maxwell {
"""+src[first:end]+r"""
}}
int main(){
    Shader::Maxwell::F2I x{};
    x.raw=u64{1}<<45;
    assert(static_cast<u64>(x.neg)==1 && static_cast<u64>(x.abs)==0);
    x.raw=u64{1}<<49;
    assert(static_cast<u64>(x.abs)==1 && static_cast<u64>(x.neg)==0);
    x.raw=(u64{1}<<45)|(u64{1}<<49);
    assert(static_cast<u64>(x.abs)==1 && static_cast<u64>(x.neg)==1);
}
"""
    run(folder,"f2i",code)
    print("R23_F2I_EXTRACTED_UNION_HOST_ASAN_PASS")

def bcat(folder):
    src=(V/"core/hle/service/bcat/bcat_util.h").read_text()
    i=src.index("constexpr Result VerifyNameValidInternal(")
    j=src.index("} // namespace Service::BCAT",i)
    code=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cctype>
#include <cstdint>
#include <cstring>
using u8=std::uint8_t;
using Result=int;
constexpr Result ResultInvalidArgument=-1,ResultSuccess=0;
using DirectoryName=std::array<char,0x20>;
using FileName=std::array<char,0x20>;
#define LOG_ERROR(...) ((void)0)
namespace Service::BCAT {
"""+src[i:j]+r"""
}
template<class T>T make_name(const char*s){
    T a{};auto n=std::strlen(s);assert(n<a.size());
    std::memcpy(a.data(),s,n);return a;
}
int main(){
    using namespace Service::BCAT;
    assert(VerifyNameValidFile(make_name<FileName>("game.dat"))==ResultSuccess);
    assert(VerifyNameValidDir(make_name<DirectoryName>("game.dat"))==ResultInvalidArgument);
    assert(VerifyNameValidFile(make_name<FileName>("DATA-01"))==ResultInvalidArgument);
    assert(VerifyNameValidDir(make_name<DirectoryName>("DATA-01"))==ResultSuccess);
    assert(VerifyNameValidFile(make_name<FileName>("_slot1"))==ResultSuccess);
    assert(VerifyNameValidFile(make_name<FileName>("BAD/path"))==ResultInvalidArgument);
    assert(VerifyNameValidFile(FileName{})==ResultInvalidArgument);
    FileName invalid{};invalid.fill('A');
    assert(VerifyNameValidFile(invalid)==ResultInvalidArgument);
}
"""
    run(folder,"bcat",code)
    print("R23_BCAT_EXTRACTED_VALIDATORS_HOST_ASAN_PASS")

def main():
    verify()
    with tempfile.TemporaryDirectory(prefix="ab-r23-") as dirname:
        folder=Path(dirname)
        f2i(folder)
        bcat(folder)
    print("R23_SELECTED_OWNERS_HOST_TESTS_PASS native_PS5_not_tested=1")

if __name__=="__main__":
    try:
        main()
    except (AssertionError,OSError,ValueError,subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as error:
        print("R23_SELECTED_OWNERS_HOST_FAIL",str(error),file=sys.stderr)
        sys.exit(1)
