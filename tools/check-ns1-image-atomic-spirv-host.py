#!/usr/bin/env python3
"""Build the genuine selected NS1 Eden IR/SPIR-V image-atomic path and validate it.

This is a host-only proof for SH-06. It does not submit GPU work and it does not
replace the native PS5 build; it verifies the exact maintained image/descriptor
owners selected by headless/CMakeLists.txt can emit validator-clean SPIR-V.
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
ACTIVE = ROOT / "vendor/encore-active/eden/src"
ACTIVE_INCLUDE = ROOT / "vendor/encore-active/eden/src"
SIRIT = ROOT / "vendor/sources/eden-cpm/sirit/v1.0.5"
HEADERS = ROOT / "vendor/sources/eden-cpm/spirv-headers/vulkan-sdk-1.4.341.0"
FMT = ROOT / "vendor/sources/eden-cpm/fmt/12.1.0/include"
OUT = ROOT / "build-ns1-image-atomic-spirv"
FIXTURE = ROOT / "tools/ns1/test_image_atomic_real_spirv.cpp"

def run(cmd):
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        print("FAILED:", " ".join(map(str, cmd)), file=sys.stderr)
        print(result.stdout[-6000:], result.stderr[-18000:], file=sys.stderr)
        raise RuntimeError("NS1 real image-atomic SPIR-V build or validation failed")
    return result

def cmake_sources(file, prefix, pattern, minimum, required):
    text = file.read_text()
    try:
        block = text.split("add_library(" + prefix, 1)[1].split("\n)", 1)[0]
    except IndexError as exc:
        raise RuntimeError("unexpected CMake source inventory: " + str(file)) from exc
    names = re.findall(r"^\s*(" + pattern + r")\s*$", block, re.M)
    if len(names) < minimum or any(name not in names for name in required):
        raise RuntimeError("unexpected pinned CMake source inventory: " + str(file))
    return names

def main():
    cxx = shutil.which(os.environ.get("CXX", "g++"))
    validator = shutil.which("spirv-val")
    if not cxx or not validator:
        raise RuntimeError("requires a C++20 compiler and spirv-val")
    for path in (
        FMT / "fmt/format.h",
        SIRIT / "include/sirit/sirit.h",
        HEADERS / "include/spirv/unified1/spirv.hpp11",
        FIXTURE,
    ):
        if not path.is_file():
            raise RuntimeError("missing vendored host dependency: " + str(path))

    shaders = cmake_sources(
        SHADER / "CMakeLists.txt",
        "shader_recompiler STATIC",
        r"(?:backend/spirv|frontend/ir)/[^\s()]+\.cpp",
        30,
        [
            "backend/spirv/emit_spirv.cpp",
            "backend/spirv/emit_spirv_image.cpp",
            "backend/spirv/emit_spirv_image_atomic.cpp",
            "backend/spirv/spirv_emit_context.cpp",
            "frontend/ir/basic_block.cpp",
            "frontend/ir/opcodes.cpp",
            "frontend/ir/program.cpp",
        ],
    )
    sirit_sources = cmake_sources(
        SIRIT / "src/CMakeLists.txt",
        "siritobj OBJECT",
        r"(?:instructions/)?[^\s()/]+\.cpp",
        18,
        ["sirit.cpp", "instructions/type.cpp", "instructions/atomic.cpp"],
    )

    # Match the owners selected by the native PS5 target for this path.
    # Do not use Ampere/NS2 backend owners in this NS1 proof.
    native_owners = {
        "backend/spirv/emit_spirv.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv.cpp",
        "backend/spirv/emit_spirv_special.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_special.cpp",
        "backend/spirv/emit_spirv_context_get_set.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp",
        "backend/spirv/emit_spirv_atomic.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_atomic.cpp",
        "backend/spirv/emit_spirv_floating_point.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_floating_point.cpp",
        "backend/spirv/emit_spirv_image.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_image.cpp",
        "backend/spirv/emit_spirv_image_atomic.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_image_atomic.cpp",
        "backend/spirv/emit_spirv_memory.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_memory.cpp",
        "backend/spirv/spirv_emit_context.cpp":
            ACTIVE / "shader_recompiler/backend/spirv/spirv_emit_context.cpp",
        "frontend/ir/ir_emitter.cpp":
            ACTIVE / "shader_recompiler/frontend/ir/ir_emitter.cpp",
        "frontend/ir/microinstruction.cpp":
            ACTIVE / "shader_recompiler/frontend/ir/microinstruction.cpp",
        "frontend/ir/opcodes.cpp":
            ACTIVE / "shader_recompiler/frontend/ir/opcodes.cpp",
    }
    for name, owner in native_owners.items():
        if shaders.count(name) != 1 or not owner.is_file():
            raise RuntimeError("native NS1 shader owner changed: " + name)

    # Confirm the production CMake graph still selects the three SH-06 owners.
    cmake = (ROOT / "headless/CMakeLists.txt").read_text()
    for path in (
        "backend/spirv/spirv_emit_context.cpp",
        "backend/spirv/emit_spirv_atomic.cpp",
        "backend/spirv/emit_spirv_image.cpp",
        "backend/spirv/emit_spirv_image_atomic.cpp",
        "frontend/maxwell/translate/impl/atomic_operations_shared_memory.cpp",
    ):
        if path not in cmake:
            raise RuntimeError("production NS1 CMake owner missing: " + path)

    sources = [native_owners.get(name, SHADER / name) for name in shaders]
    mesh_emitter = ACTIVE / "shader_recompiler/backend/spirv/emit_spirv_mesh.cpp"
    if mesh_emitter.is_file():
        sources.append(mesh_emitter)
    sources += [
        SRC / "common/settings_common.cpp",
        FIXTURE,
    ]
    sources += [SIRIT / "src" / name for name in sirit_sources]

    # Compile the small fixture first so a local test typo fails immediately.
    sources = [FIXTURE] + [source for source in sources if source != FIXTURE]
    if len({str(p) for p in sources}) != len(sources):
        raise RuntimeError("duplicate NS1 SPIR-V translation unit")
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise RuntimeError("missing NS1 SPIR-V source: " + ", ".join(missing))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    flags = [
        cxx, "-std=c++20", "-O0", "-g0", "-DFMT_HEADER_ONLY",
        "-ffunction-sections", "-fdata-sections", "-Wno-unused-parameter",
        "-pthread",
        "-I" + str(FMT),
        # Match target_include_directories(shader_recompiler BEFORE ...):
        # the maintained source ABI must shadow the legacy include snapshot.
        "-I" + str(ACTIVE),
        "-I" + str(ACTIVE_INCLUDE),
        "-I" + str(SRC),
        "-I" + str(SRC / "dynarmic/src"),
        "-I" + str(SIRIT / "include"),
        "-I" + str(SIRIT / "src"),
        "-I" + str(HEADERS / "include"),
    ]
    jobs = [(source, OUT / f"{index:03d}.o") for index, source in enumerate(sources)]
    print("Compiling genuine NS1 IR/SPIR-V/Sirit units:", len(jobs), flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            pool.submit(run, flags + ["-c", str(source), "-o", str(obj)]): source
            for source, obj in jobs
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                print("Failing source:", futures[future], file=sys.stderr)
                for other in futures:
                    other.cancel()
                raise

    binary = OUT / "ns1-image-atomic-real-spirv"
    run([cxx, "-pthread", "-Wl,--gc-sections", "-o", str(binary)] +
        [str(obj) for _, obj in jobs] + ["-latomic"])

    prefix = OUT / "synthetic"
    print(run([str(binary), str(prefix)]).stdout, end="")
    for module in ("scalar", "array"):
        path = OUT / f"synthetic-{module}.spv"
        if not path.is_file():
            raise RuntimeError("real image-atomic module missing: " + str(path))
        for env in ("spv1.5", "vulkan1.2"):
            run([validator, "--target-env", env, str(path)])
            print(f"NS1_IMAGE_ATOMIC_REAL_SPIRV_VALIDATED {module} {env}", flush=True)

    print("NS1_IMAGE_ATOMIC_REAL_SPIRV_PASS "
          "real_emit=1 scalar=1 descriptor_array=1 inc_dec_cas=1 shared_cas=1 "
          "nonuniform_guard=1 bounds_guard=1", flush=True)

if __name__ == "__main__":
    main()
