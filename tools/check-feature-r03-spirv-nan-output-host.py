#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""R03 native shader source boundary: verify exact upstream diff, CMake selection,
and compile real EmitSetFragColor under UBSan (-O0 and -O2).
Not a PS5 gameplay or pixel-quality benchmark.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT/"vendor/sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp"
ACTIVE = ROOT/"vendor/encore-active/eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp"
pinned = ORIGINAL.read_text()
native = ACTIVE.read_text()
cmake = (ROOT/"headless/CMakeLists.txt").read_text()
old = """        const Id pointer{ctx.OpAccessChain(ctx.output_f32, ctx.frag_color.at(index), component_id)};
        ctx.OpStore(pointer, value);
    } else if (type == AttributeType::UnsignedInt) {"""
new = """        const Id pointer{ctx.OpAccessChain(ctx.output_f32, ctx.frag_color.at(index), component_id)};
        // A NaN pixel can poison temporal history, glow and bloom in later
        // passes. Isolate only floating-point fragment colours; never
        // mutate integer outputs, depth, sample masks or guest shader inputs.
        ctx.OpStore(pointer, ctx.OpSelect(ctx.F32[1], ctx.OpIsNan(ctx.U1, value),
                                       ctx.Const(0.0f), value));
    } else if (type == AttributeType::UnsignedInt) {"""
assert pinned.count(old) == 1, "pinned Float output drift"
assert native == pinned.replace(old, new), "R03 changed more than Float fragment output"
for term in (
    'set(EDEN_MAINTAINED_SPIRV_FRAG_COLOR',
    'list(REMOVE_ITEM eden_spirv_sources "backend/spirv/emit_spirv_context_get_set.cpp")',
    'list(APPEND eden_spirv_sources "${EDEN_MAINTAINED_SPIRV_FRAG_COLOR}")',
    'set_property(TARGET shader_recompiler PROPERTY SOURCES "${eden_spirv_sources}")',
):
    assert term in cmake, ("emitter not selected", term)
assert cmake.count('list(APPEND eden_spirv_sources "${EDEN_MAINTAINED_SPIRV_FRAG_COLOR}")') == 1
start = native.index("void EmitSetFragColor(EmitContext& ctx, u32 index, u32 component, Id value) {")
end = native.index("\nvoid EmitSetSampleMask", start)
method = native[start:end]
assert method.count("ctx.OpIsNan(") == 1 and method.count("ctx.OpStore(") == 4
cpp = r"""
#include <array>
#include <bit>
#include <cassert>
#include <cmath>
#include <cstdint>
using u32 = uint32_t;
using Id = uint32_t;
enum class AttributeType { Float, UnsignedInt, SignedInt, Other };
namespace spv { enum class StorageClass { Output }; }
struct EmitContext {
    struct Runtime { std::array<AttributeType,4> color_output_types{}; } runtime_info;
    std::array<Id,4> frag_color{};
    std::array<Id,2> F32{}, S32{}, U32{};
    Id U1=0;
    Id output_f32=0, output_u32=0, latest=0;
    unsigned stores=0;
    Id Const(u32 x) { return x; }
    Id Const(float x) { return std::bit_cast<u32>(x); }
    Id OpAccessChain(Id, Id, Id) { return 1; }
    Id TypePointer(spv::StorageClass, Id) { return 1; }
    Id OpIsNan(Id, Id x) { return std::isnan(std::bit_cast<float>(x)) ? 1u : 0u; }
    Id OpSelect(Id, Id condition, Id a, Id b) { return condition ? a : b; }
    Id OpBitcast(Id, Id x) { return x; }
    void OpStore(Id, Id x) { latest=x; ++stores; }
};
""" + method + r"""
int main() {
    EmitContext ctx{};
    const Id samples[] = {0u, 0x3f800000u, 0x7f800000u, 0xff800000u,
                          0x7fc00001u, 0xffc02000u, 0x80000000u};
    for (const auto kind : {AttributeType::Float, AttributeType::UnsignedInt,
                             AttributeType::SignedInt, AttributeType::Other}) {
        ctx.runtime_info.color_output_types[0] = kind;
        for (Id value : samples) {
            const auto count=ctx.stores;
            EmitSetFragColor(ctx, 0, 2, value);
            assert(ctx.stores == count + 1);
            const bool nan = std::isnan(std::bit_cast<float>(value));
            assert(ctx.latest == (kind==AttributeType::Float && nan ? 0u : value));
        }
    }
}
"""
for opt in ("-O0", "-O2"):
    with tempfile.TemporaryDirectory(prefix="encore-r03-nan-") as folder:
        source=Path(folder)/"nan.cpp"
        binary=Path(folder)/"nan"
        source.write_text(cpp)
        subprocess.run([os.environ.get("CXX","g++"), "-std=c++20", opt,
                        "-Wall","-Wextra","-Werror","-fsanitize=undefined",
                        "-fno-sanitize-recover=all",str(source),"-o",str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
        print("R03_SPIRV_NAN_GUARD_PASS mode="+opt+" output_types=4 samples=7 "
              "upstream_parity=1 native_cmake=1",flush=True)
