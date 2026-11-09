#!/usr/bin/env python3
"""G03: execute actual tessellation patch write owner under Clang/GCC UBSan.

Negative stage/missing-variable cases and valid TCS generic/outer/inner writes;
does not claim final tessellation Vulkan/SPIR-V pipeline conformance.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
src=(ROOT/"vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp").read_text()
start="void EmitSetPatch("
stop="\nvoid EmitSetFragColor("
assert src.count(start)==src.count(stop)==1
owner=start+src.split(start,1)[1].split(stop,1)[0]
assert owner.count("Undeclared tessellation outer patch output") == 1
assert owner.count("Undeclared tessellation inner patch output") == 1
assert owner.count("Undeclared generic tessellation patch") == 1
assert owner.index("if (ctx.stage != Stage::TessellationControl)") < owner.index("ctx.OpStore(pointer, value)")
harness=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <utility>
using u32=std::uint32_t;
enum class Stage { VertexB, TessellationControl, TessellationEval };
namespace IR {
enum class Patch : u32 {
    TessellationLodLeft=0,TessellationLodTop=1,
    TessellationLodRight=2,TessellationLodBottom=3,
    TessellationLodInteriorU=4,TessellationLodInteriorV=5,
    Generic0=256,Generic1=257,Generic2=258,Generic3=259,
    Generic4=260,Unsupported=999
};
constexpr bool IsGeneric(Patch p) { return u32(p)>=256 && u32(p)<264; }
constexpr u32 GenericPatchIndex(Patch p) { return (u32(p)-256)/4; }
constexpr u32 GenericPatchElement(Patch p) { return (u32(p)-256)%4; }
}
struct Id { u32 value{}; };
constexpr bool ValidId(Id id) { return id.value != 0; }
struct NotImplementedException : std::runtime_error {
    template<class... Args>
    explicit NotImplementedException(const char*,Args&&...)
        :std::runtime_error("unsupported tessellation patch") {}
};
struct EmitContext {
    Stage stage{Stage::TessellationControl};
    Id output_f32{1},output_tess_level_outer{},output_tess_level_inner{};
    Id u32_zero_value{100};
    std::array<Id,2> patches{};
    unsigned stores{},chains{};
    u32 last_base{},last_element{};
    Id Const(u32 v) { return Id{100+v}; }
    Id OpAccessChain(Id type,Id base,Id element) {
        assert(ValidId(type) && ValidId(base) && ValidId(element));
        ++chains;
        last_base=base.value;last_element=element.value;
        return Id{500+chains};
    }
    void OpStore(Id pointer,Id value) {
        assert(ValidId(pointer) && ValidId(value));
        ++stores;
    }
};
__REAL_OWNER__
int main() {
    EmitContext c{};
    auto denied=[&](IR::Patch patch) {
        const auto old=c.stores,old_chains=c.chains;
        bool rejected{};
        try { EmitSetPatch(c,patch,Id{777}); }
        catch(const NotImplementedException&) { rejected=true; }
        assert(rejected && c.stores==old && c.chains==old_chains);
    };
    for(const auto stage:{Stage::VertexB,Stage::TessellationEval}) {
        c.stage=stage;
        denied(IR::Patch::TessellationLodLeft);
        denied(IR::Patch::Generic0);
    }
    c.stage=Stage::TessellationControl;
    denied(IR::Patch::TessellationLodLeft);
    denied(IR::Patch::TessellationLodInteriorU);
    denied(IR::Patch::TessellationLodInteriorV);
    denied(IR::Patch::Generic0);
    denied(IR::Patch::Unsupported);
    c.output_tess_level_outer=Id{17};
    c.output_tess_level_inner=Id{18};
    c.patches[0]=Id{19};
    EmitSetPatch(c,IR::Patch::TessellationLodLeft,Id{777});
    assert(c.last_base==17 && c.stores==1);
    EmitSetPatch(c,IR::Patch::TessellationLodBottom,Id{777});
    assert(c.last_base==17 && c.last_element==103 && c.stores==2);
    EmitSetPatch(c,IR::Patch::TessellationLodInteriorU,Id{777});
    assert(c.last_base==18 && c.stores==3);
    EmitSetPatch(c,IR::Patch::TessellationLodInteriorV,Id{777});
    assert(c.last_base==18 && c.last_element==101 && c.stores==4);
    EmitSetPatch(c,IR::Patch::Generic2,Id{777});
    assert(c.last_base==19 && c.last_element==102 && c.stores==5);
    denied(IR::Patch::Generic4);
    denied(IR::Patch::Unsupported);
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Clang/GCC required"
with tempfile.TemporaryDirectory(prefix="encore-g03-patch-owner-") as temp:
    code=Path(temp)/"owner.cpp";code.write_text(harness)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  str(code),"-o",str(exe)]
            built=subprocess.run(args,capture_output=True,text=True,timeout=60,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-4000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert run.returncode==0,run.stderr[-4000:]
            print("G03_REAL_PATCH_WRITE_OWNER_PASS",Path(cc).name,opt,
                  "tcs_write=5 tes_vertex_rejected=1 undeclared_refused=1",flush=True)
