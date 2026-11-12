#!/usr/bin/env python3
"""Build actual pinned Eden Maxwell/IR/SPIR-V and validate synthetic graphics modules.

Uses the upstream CMake source inventories, with real Sirit and SPIRV-Headers.
Does not attach this compiler to production Vulkan or Switch 1 shader caches.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "vendor/sources/eden/src"
SHADER = SRC / "shader_recompiler"
SIRIT = ROOT / "build-ns2-deps/sirit"
HEADERS = ROOT / "build-ns2-deps/spirv-headers"
FMT = ROOT / "build-ns2-a64/fmt/include"
OUT = ROOT / "build-ns2-real-spirv"

def run(cmd):
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        print("FAILED:", " ".join(map(str, cmd)), file=sys.stderr)
        print(result.stdout[-6000:], result.stderr[-18000:], file=sys.stderr)
        raise RuntimeError("real SPIR-V build or validation failed")
    return result

def cmake_sources(file, prefix, pattern, minimum, required):
    cmake = file.read_text().split("add_library(" + prefix, 1)[1].split("\n)", 1)[0]
    names = re.findall(r"^\s*(" + pattern + r")\s*$", cmake, re.M)
    if len(names) < minimum or any(name not in names for name in required):
        raise RuntimeError("unexpected pinned CMake source inventory: " + str(file))
    return names

def main():
    cxx = shutil.which(os.environ.get("CXX", "g++"))
    validator = shutil.which("spirv-val")
    if not cxx or not validator:
        raise RuntimeError("requires C++20 compiler and spirv-val")
    if not (FMT / "fmt/format.h").is_file() or not (SIRIT / "include/sirit/sirit.h").is_file() or not (HEADERS / "include/spirv/unified1/spirv.hpp11").is_file():
        raise RuntimeError("pinned fmt/Sirit/SPIRV-Headers are missing")
    shaders = cmake_sources(
        SHADER / "CMakeLists.txt", "shader_recompiler STATIC",
        r"(?:frontend|ir_opt|backend/spirv)/[^\s()]+\.cpp", 135,
        ["frontend/maxwell/translate_program.cpp",
         "backend/spirv/emit_spirv.cpp",
         "backend/spirv/spirv_emit_context.cpp"])
    sirit_sources = cmake_sources(
        SIRIT / "src/CMakeLists.txt", "siritobj OBJECT",
        r"(?:instructions/)?[^\s()/]+\.cpp", 18,
        ["sirit.cpp", "instructions/type.cpp"])
    overlay = ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere"
    mesh_root = ROOT / "vendor/encore-active/eden-shader/src"
    # Use the SAME production shader headers and translation units as the
    # single PS5 CMake shader target. Mixed pinned headers with native TES
    # emitters cannot compile and do not represent a real ABI witness.
    native_owners = {
        "backend/spirv/spirv_emit_context.cpp":
            ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp",
        "backend/spirv/emit_spirv_context_get_set.cpp":
            ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp",
        "backend/spirv/emit_spirv_image.cpp":
            ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_image.cpp",
    }
    mesh_owners = (
        "backend/spirv/emit_spirv.cpp",
        "backend/spirv/emit_spirv_special.cpp",
        "frontend/ir/ir_emitter.cpp",
        "frontend/ir/microinstruction.cpp",
        "frontend/ir/opcodes.cpp",
        "frontend/maxwell/decode.cpp",
        "frontend/maxwell/opcodes.cpp",
        "frontend/maxwell/structured_control_flow.cpp",
        "frontend/maxwell/translate/impl/internal_stage_buffer_entry_read.cpp",
        "frontend/maxwell/translate_program.cpp",
        "ir_opt/collect_shader_info_pass.cpp",
    )
    for name in mesh_owners:
        if name in native_owners:
            raise RuntimeError("native shader owner collision: " + name)
        native_owners[name] = mesh_root / "shader_recompiler" / name
    if any(shaders.count(name) != 1 for name in native_owners):
        raise RuntimeError("pinned SPIR-V/Task/Mesh source owner changed")
    # All three opcode owners must use the same table. An extra pseudo-opcode
    # shifts subsequent enum values, so mixing old names or decoder is unsafe.
    opcode_root = mesh_root / "shader_recompiler/frontend/maxwell"
    opcode_table = (opcode_root / "maxwell.inc").read_text()
    opcode_enum = (opcode_root / "opcodes.h").read_text()
    opcode_decoder = (opcode_root / "decode.cpp").read_text()
    opcode_names = (opcode_root / "opcodes.cpp").read_text()
    if ("INST(ISBE_nx2" not in opcode_table or
            '#include "maxwell.inc"' not in opcode_enum or
            '#include "shader_recompiler/frontend/maxwell/maxwell.inc"' not in opcode_decoder or
            '#include "shader_recompiler/frontend/maxwell/maxwell.inc"' not in opcode_names):
        raise RuntimeError("mixed native Maxwell/NS2 opcode table ABI")
    extra_mesh = mesh_root / "shader_recompiler/backend/spirv/emit_spirv_mesh.cpp"
    if not extra_mesh.is_file():
        raise RuntimeError("missing actual SPIR-V mesh emitter")
    # R23 #72: maintained TranslateProgram now links GeometryCompactionPass.
    # The original upstream CMake does not contain this new native owner.
    # Compile the exact reviewed source selected by native PS5 CMake once.
    geometry_owner = mesh_root / "shader_recompiler/ir_opt/geometry_compaction_pass.cpp"
    if not geometry_owner.is_file():
        raise RuntimeError("missing R23 native GeometryCompactionPass implementation")
    if "ir_opt/geometry_compaction_pass.cpp" in shaders:
        raise RuntimeError("R23 GeometryCompactionPass unexpectedly duplicated in upstream inventory")
    sources = [native_owners.get(name, SHADER / name)
               for name in shaders] + [extra_mesh, geometry_owner] + [
        overlay / (name + ".cpp") for name in
        ("ir_bridge", "renderer_spirv_bridge", "maxwell_environment", "maxwell_image", "lower_bridge", "probe")
    ] + [overlay / "capture.cpp",
         overlay / "translation_cache.cpp",
         ROOT / "vendor/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.cpp",
         SRC / "common/settings_common.cpp",
         ROOT / "tools/ns2/jit-host/common_shim.cpp",
         ROOT / "tools/ns2/test_ampere_real_spirv.cpp"]
    sources += [SIRIT / "src" / name for name in sirit_sources]
    # Compile the host fixture FIRST: all source owners must still build,
    # but a local C++ fixture typo must fail in seconds rather than after
    # compiling ~150 unrelated shader objects.
    fixture = ROOT / "tools/ns2/test_ampere_real_spirv.cpp"
    if sources.count(fixture) != 1:
        raise RuntimeError("real SPIR-V host fixture owner missing or duplicated")
    sources = [fixture] + [source for source in sources if source != fixture]
    if len({str(p) for p in sources}) != len(sources):
        raise RuntimeError("duplicate SPIR-V translation unit")
    maintained_header = (mesh_root / "shader_recompiler/backend/spirv/spirv_emit_context.h").read_text()
    for name in ("input_tess_level_outer", "input_tess_level_inner",
                 "output_tess_level_outer", "output_tess_level_inner"):
        if name not in maintained_header:
            raise RuntimeError("maintained TES/TCS patch interface missing: " + name)
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise RuntimeError("missing pinned shader sources: " + ", ".join(missing))
    OUT.mkdir(parents=True, exist_ok=True)
    flags = [cxx, "-std=c++20", "-O0", "-g0", "-DFMT_HEADER_ONLY",
             "-ffunction-sections", "-fdata-sections", "-Wno-unused-parameter",
             "-pthread", "-I" + str(FMT),
              "-I" + str(mesh_root),
             "-I" + str(ROOT / "vendor/encore-active/ns2-runtime/ampere"),
             "-I" + str(ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch"),
             "-I" + str(ROOT / "vendor/encore-active/ns2-runtime/hle"), "-I" + str(SRC),
             "-I" + str(SRC / "dynarmic/src"),
             "-I" + str(SIRIT / "include"), "-I" + str(SIRIT / "src"),
             "-I" + str(HEADERS / "include")]
    jobs = [(p, OUT / f"{i:03d}.o") for i, p in enumerate(sources)]
    print("Compiling true Maxwell, IR, SPIR-V and Sirit C++ units:", len(jobs), flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(run, flags + ["-c", str(src), "-o", str(obj)]): src
                   for src, obj in jobs}
        for item in as_completed(futures):
            try:
                item.result()
            except Exception:
                print("Failing source:", futures[item], file=sys.stderr)
                for other in futures:
                    other.cancel()
                raise
    binary = OUT / "ns2-real-spirv"
    run([cxx, "-pthread", "-Wl,--gc-sections", "-o", str(binary)] +
        [str(obj) for _, obj in jobs] + ["-latomic"])
    print(run([str(binary), str(OUT / "synthetic")]).stdout, end="")
    # Real live native LDC 0xb82 reaches QMD3 CBUF banks 0 and 7; BRX
    # reaches the actual Maxwell CFG/IR/Sirit loop+conditional dispatch.
    # Validate the executable-structure SPIR-V modules, not only headers or
    # reflected descriptor plans. No PS5 GPU work is submitted here.
    for mode in ("direct", "dispatcher", "fragment", "merged", "compute", "cbuf0", "cbuf7", "brx"):
        path = OUT / f"synthetic-{mode}.spv"
        print(run([validator, "--target-env", "spv1.5", str(path)]).stdout, end="")
        print(f"spirv-val SPIR-V 1.5 {mode}: PASS")
        print(run([validator, "--target-env", "vulkan1.2", str(path)]).stdout, end="")
        print(f"spirv-val Vulkan 1.2 {mode}: PASS")
    # The seven QMD3 floating atomic operations now reach the actual
    # maintained SPIR-V backend. Check emitted OpAtomicCompareExchange
    # bodies under BOTH SPIR-V 1.5 and Vulkan 1.2 validation rules.
    for kind in ("u32-cas", "f32-add", "f16x2-add", "f16x2-min", "f16x2-max",
                 "f32x2-add", "f32x2-min", "f32x2-max"):
        path = OUT / f"synthetic-{kind}.spv"
        for env in ("spv1.5", "vulkan1.2"):
            run([validator, "--target-env", env, str(path)])
            print(f"P2_3_REAL_FLOAT_CAS_SPIRV_VALIDATED {kind} {env}",flush=True)
    # G06: authentic native 64-bit global CAS router and CBUF/SSBO
    # addressing. Do not accept a header-only CAS conformance claim.
    for env in ("spv1.5", "vulkan1.2"):
        # Packed legacy U32/U32x2 UBO views require the explicit Vulkan 1.2
        # uniformBufferStandardLayout feature; the host Vulkan test must
        # independently query and ENABLE this feature on the real device.
        opts = ["--uniform-buffer-standard-layout"] if env == "vulkan1.2" else []
        run([validator, "--target-env", env, *opts,
             str(OUT / "synthetic-global-cas.spv")])
        print(f"G06_REAL_GLOBAL_CAS_SPIRV_VALIDATED {env} feature=standard_layout", flush=True)
    # P2.4: validate REAL EXT shader opcodes emitted from synthetic
    # Task and Mesh IR, not just a C++ compile or the legacy VertexB module.
    for stage in ("task", "mesh"):
        path = OUT / f"synthetic-{stage}.spv"
        for env in ("spv1.5", "vulkan1.2"):
            run([validator, "--target-env", env, str(path)])
            print(f"P2_4_REAL_{stage.upper()}_SPIRV_VALIDATED {env}", flush=True)
    # Actual SPIR-V descriptor-array module, not a stub header source check.
    for env in ("spv1.5", "vulkan1.2"):
        run([validator, "--target-env", env,
             str(OUT / "synthetic-texbuf-array.spv")])
        print(f"P2_2C_REAL_TEXTURE_BUFFER_ARRAY_VALIDATED {env}", flush=True)
    # G07: real native image-buffer reads are committed to an SSBO and
    # verified with Vulkan host dispatch + a completion fence (not PS5).
    g07_module = OUT / "synthetic-g07-texel-ssbo.spv"
    for env in ("spv1.5", "vulkan1.2"):
        run([validator, "--target-env", env, str(g07_module)])
        print(f"G07_NATIVE_TEXEL_SSBO_SPIRV_VALIDATED {env}", flush=True)
    g07_exe = OUT / "ns2-g07-vulkan"
    run([cxx, "-std=c++20", "-O2", "-DFMT_HEADER_ONLY",
         "-I" + str(ROOT / "vendor/sources/fmt/include"),
         "-I" + str(ROOT / "vendor/encore-active/ns2-runtime/ampere"),
         "-I" + str(ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch"),
         "-I" + str(ROOT / "vendor/sources/eden/src"),
         str(ROOT / "tools/ns2/test_g07_real_vulkan_texel.cpp"),
         "-o", str(g07_exe), "-lvulkan"])
    print(run([str(g07_exe), str(g07_module)]).stdout, end="")
    # G09: require real native EXT Task/Mesh graphics pipeline creation,
    # if (and only if) the host Vulkan device supports the extension.
    # An unavailable feature is recorded explicitly and never counted as proof.
    g09_exe = OUT / "ns2-g09-mesh-pipeline"
    run([cxx, "-std=c++20", "-O2",
         str(ROOT / "tools/ns2/test_g09_native_mesh_pipeline.cpp"),
         "-o", str(g09_exe), "-lvulkan"])
    print(run([str(g09_exe),
               str(OUT / "synthetic-task.spv"),
               str(OUT / "synthetic-mesh.spv")]).stdout, end="")
    # G02: the actual emitted VertexB split XFB module must pass the
    # SPIR-V 1.5 and Vulkan 1.2 structural/resource validation rules.
    # The emitted OpStores, component splits and two guest byte offsets are
    # verified by the C++ real-owner fixture above.
    for env in ("spv1.5", "vulkan1.2"):
        run([validator, "--target-env", env,
             str(OUT / "synthetic-xfb-split.spv")])
        print(f"P2_G02_REAL_XFB_SPIRV_VALIDATED {env}", flush=True)
    # G03: independently validate TCS output and TES input for all six
    # built-in tessellation patch levels, not merely C++ emitter symbols.
    for kind in ("tess-control", "tess-eval"):
        path = OUT / f"synthetic-{kind}.spv"
        for env in ("spv1.5", "vulkan1.2"):
            run([validator, "--target-env", env, str(path)])
            print(f"P2_4_REAL_{kind.upper().replace('-', '_')}_PATCH_VALIDATED {env}", flush=True)
    module_test = OUT / "ns2-vulkan-modules"
    run([cxx, "-std=c++20", "-O2",
         str(ROOT / "tools/ns2/test_ampere_vulkan_module.cpp"),
         "-o", str(module_test), "-lvulkan"])
    print(run([str(module_test),
               str(OUT / "synthetic-direct.spv"),
               str(OUT / "synthetic-dispatcher.spv"),
               str(OUT / "synthetic-fragment.spv"),
               str(OUT / "synthetic-merged.spv"),
               str(OUT / "synthetic-compute.spv"),
               str(OUT / "synthetic-u32-cas.spv"),
               str(OUT / "synthetic-global-cas.spv")]).stdout, end="")
    # G06: this genuine CAS shader runs a real Vulkan storage-buffer atomic
    # with old-value readback and fence-completed host memory visibility.
    print("SPIR-V validation and Vulkan CAS memory-readback passed; "
          "real PS5 Vulkan renderer not exercised.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(error, file=sys.stderr)
        sys.exit(1)
