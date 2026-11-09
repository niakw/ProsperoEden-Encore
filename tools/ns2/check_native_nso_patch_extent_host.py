#!/usr/bin/env python3
"""H01: execute actual NSO patched-image copy owner against adversarial IPS size.

The original CodeSet has a fixed authenticated segment layout. Reject resized
IPS/IPSwitch output before writing a byte to guest executable staging. The
real production copy block is extracted, compiled and executed by two C++20
compilers with UBSan in O0/O2. This is not full KProcess admission.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"vendor/encore-active/ns2-runtime/metadata/core/loader/nso.cpp"
source=SOURCE.read_text()
start="    // Apply patches if necessary\n    if (patched || full_image) {"
end="\n#ifdef HAS_NCE\n    // If we are computing"
assert source.count(start)==source.count(end)==1
owner=source.split(start,1)[1].split(end,1)[0]
body="    if (patched || full_image) {"+owner
assert owner.count("pi_header = pm->PatchNSO(pi_header, name);")==1
assert owner.count("if (pi_header.size() != sizeof(NSOHeader) + patchable_section.size())")==1
assert owner.index("if (pi_header.size() !=") < owner.index("std::copy(pi_header.begin()")
assert "return std::nullopt;" in owner

cpp=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <optional>
#include <span>
#include <string>
#include <vector>
using u8=std::uint8_t;
struct NSOHeader {std::array<u8,256> bytes{};};
struct PatchManager {
    enum class Change {Same,Expand,Truncate,Unchanged};
    Change change{Change::Same};
    std::vector<u8> PatchNSO(std::vector<u8> bytes, const std::string&) const {
        if(change==Change::Expand) bytes.push_back(0xFE);
        if(change==Change::Truncate) bytes.resize(bytes.size()-1);
        if(change==Change::Same)
            for(std::size_t i=sizeof(NSOHeader);i<bytes.size();++i)bytes[i]=0xAB;
        return bytes;
    }
};
struct CodeSet {std::vector<u8> memory;};
std::optional<int> TestRealOwner(const PatchManager* pm,CodeSet& codeset,
                                  const NSOHeader& nso_header,bool patched,
                                  bool full_image,std::size_t module_start,
                                  const std::string& name) {
__OWNER__
    return 1;
}
void Unmodified(const std::vector<u8>& bytes,u8 expected) {
    for(u8 b:bytes) assert(b==expected);
}
int main(){
    NSOHeader hdr{};
    PatchManager pm{};
    const std::string name{"main"};
    constexpr std::size_t region=1024;
    const auto check=[&](PatchManager::Change change,bool expected_ok){
        CodeSet image{std::vector<u8>(region,0x34)};
        pm.change=change;
        const auto result=TestRealOwner(&pm,image,hdr,true,false,0,name);
        assert(result.has_value()==expected_ok);
        if(expected_ok)Unmodified(image.memory,0xAB);
        else Unmodified(image.memory,0x34);
    };
    check(PatchManager::Change::Same,true);
    check(PatchManager::Change::Expand,false);
    check(PatchManager::Change::Truncate,false);
    // A no-patch layout does not dereference an absent patch manager.
    CodeSet raw{std::vector<u8>(region,0x34)};
    assert(TestRealOwner(nullptr,raw,hdr,false,false,0,name));
    Unmodified(raw.memory,0x34);
    // Header-only result is still invalid if it truncates even one payload
    // byte; ensure zero-length payload cannot cause pointer overrun.
    CodeSet empty{std::vector<u8>{}};
    pm.change=PatchManager::Change::Unchanged;
    assert(TestRealOwner(&pm,empty,hdr,true,false,0,name));
    pm.change=PatchManager::Change::Expand;
    assert(!TestRealOwner(&pm,empty,hdr,true,false,0,name));
    assert(empty.memory.empty());
    std::puts("H01_REAL_NSO_PATCH_EXTENT_PASS in_place=1"
              " oversized=refused truncated=refused"
              " no_patch=1 zero_size=guarded guest_bytes_preserved=1");
}
""".replace("__OWNER__",body)
compilers=list(dict.fromkeys(c for c in
    (shutil.which("clang++"),shutil.which("g++")) if c))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h01-nso-ips-") as tmp:
    src=Path(tmp)/"real_nso_ips.cpp";src.write_text(cpp)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(tmp)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 str(src),"-o",str(exe)]
            build=subprocess.run(cmd,capture_output=True,text=True,timeout=60,
                                 env=os.environ.copy())
            assert build.returncode==0,(cc,build.stderr[-5000:])
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,(cc,run.stderr[-5000:])
            print(Path(cc).name,opt,run.stdout.strip(),flush=True)
