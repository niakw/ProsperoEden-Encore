#!/usr/bin/env python3
"""H01: run the actual NSO LoadModule argument admission block, Clang/GCC.

The shared NS1/NS2 loader uses a fixed NSO_ARGUMENT_DATA_ALLOCATION_SIZE;
an oversized program_args string must be denied in both layout and materialize
passes before any codeset allocation or guest memcpy.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor"
owner=(VENDOR/"encore-active/ns2-runtime/metadata/core/loader/nso.cpp").read_text()
header=(VENDOR/"sources/eden/src/core/loader/nso.h").read_text()
start="    // Both NS1 and NS2 use this fixed guest argument allocation."
end="    // N3t: native NSO entry gate"
assert owner.count(start)==owner.count(end)==1
real=owner.split(start,1)[1].split(end,1)[0]
assert "Settings::values.program_args.GetValue().size()" in real
assert "NSO_ARGUMENT_DATA_ALLOCATION_SIZE - sizeof(NSOArgumentHeader)" in real
assert real.index("if (should_pass_arguments &&") < real.index("return std::nullopt;")
assert owner.index(start) < owner.index("const u64 initialized_size =")
assert "std::memcpy(codeset.memory.data() + end_offset + sizeof(NSOArgumentHeader)," in owner
assert "arg_data.data(), arg_data.size()" in owner
m=re.search(r"constexpr u32 NSO_ARGUMENT_DATA_ALLOCATION_SIZE\s*=\s*(0x[0-9A-Fa-f]+|\d+);",header)
assert m, "original NSO argument capacity not found"
capacity=int(m.group(1),0)
assert 0 < capacity < 0xffffffff
fixture=r"""
#include <cassert>
#include <cstdint>
#include <optional>
#include <string>
using u32=std::uint32_t;
constexpr u32 NSO_ARGUMENT_DATA_ALLOCATION_SIZE=__CAPACITY__;
struct NSOArgumentHeader{
    u32 allocated_size{},actual_size{};
    unsigned char reserved[24]{};
};
static_assert(sizeof(NSOArgumentHeader)==32);
namespace Settings {
struct Arg{
    std::string value{};
    const std::string& GetValue() const{return value;}
};
inline struct Values {Arg program_args;} values;
}
std::optional<int> RealNsOArgsAdmission(bool should_pass_arguments){
__REAL_OWNER__
    return 1;
}
int main(){
    constexpr std::size_t allowed=NSO_ARGUMENT_DATA_ALLOCATION_SIZE-
        sizeof(NSOArgumentHeader);
    static_assert(allowed>0);
    using namespace Settings;
    assert(RealNsOArgsAdmission(true).has_value()); // empty
    values.program_args.value.assign(allowed,'X');
    assert(RealNsOArgsAdmission(true).has_value()); // exact boundary
    values.program_args.value.push_back('Y');
    assert(!RealNsOArgsAdmission(true).has_value());
    assert(RealNsOArgsAdmission(false).has_value()); // no copy requested
    values.program_args.value.assign(NSO_ARGUMENT_DATA_ALLOCATION_SIZE*2,'Z');
    assert(!RealNsOArgsAdmission(true).has_value());
    values.program_args.value.assign(1,'A');
    assert(RealNsOArgsAdmission(true).has_value());
}
""".replace("__CAPACITY__",str(capacity)).replace("__REAL_OWNER__",real)
compilers=list(dict.fromkeys(cc for cc in (shutil.which("clang++"),shutil.which("g++")) if cc))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-h01-nso-args-") as temp:
    cpp=Path(temp)/"real.cpp";cpp.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  str(cpp),"-o",str(exe)]
            built=subprocess.run(args,capture_output=True,text=True,timeout=65,
                                 env=os.environ.copy())
            assert built.returncode==0,(cc,built.stderr[-4500:])
            tested=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            assert tested.returncode==0,(cc,tested.stderr[-4500:])
            print("H01_REAL_NSO_ARGUMENT_ADMISSION_PASS",Path(cc).name,opt,
                  "max_valid=1 over_capacity=refused no_copy_unaffected=1",
                  flush=True)
