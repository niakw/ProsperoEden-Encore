#!/usr/bin/env python3
"""Compile the REAL PS5/NS1/NS2 Vulkan texture cache owner, host-only.

Unlike the extracted F07 math tests, this verifies that the production TU
actually parses with all active pinned shader/cache/Boost/Vulkan interfaces.
No PS5 ELF, host object, native shader, CI poll or GPU command is generated.

On an Apple Silicon developer host, SDK 26.5 headers are deliberately used
because older macOS command-line libc++ omits std::stop_token/std::jthread.
The tiny builtin alias is syntax-only to permit the x86 pause intrinsic in
an arm64 parse; it does not modify the production owner or emit machine code.
"""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp"

def require_file(path: Path) -> Path:
    assert path.is_file(), f"Missing pinned Vulkan owner/dependency: {path}"
    return path

def require_dir(path: Path) -> Path:
    assert path.is_dir(), f"Missing pinned Vulkan include directory: {path}"
    return path

def run() -> None:
    require_file(OWNER)
    source = OWNER.read_text()
    required = (
        "const bool dual_planes = src_both && dst_both;",
        "from_stencil.imageSubresource.aspectMask = VK_IMAGE_ASPECT_STENCIL_BIT;",
        "to_stencil.bufferOffset = scratch_used + plane_bytes;",
        "scratch_used += plane_bytes * (dual_planes ? 2U : 1U);",
        "VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, vk_out_copies);",
    )
    for marker in required:
        assert marker in source, f"Missing maintained owner: {marker}"
    for workflow in ("encore-core-fast-gate.yml", "encore-core-preflight.yml"):
        contents = (ROOT / ".github/workflows" / workflow).read_text()
        assert ("python3 -B tools/check-ps5-vulkan-texture-tu-syntax-host.py"
                in contents), f"Missing full Vulkan texture TU gate in {workflow}"

    cxx = (shutil.which("clang++-18") or shutil.which("clang++"))
    assert cxx, "A real Clang C++20 host compiler is required"
    pinned = ROOT / "vendor/sources/eden-cpm"
    includes = [
        ROOT / "headless",
        ROOT / "vendor/encore-active/eden-vulkan/include",
        ROOT / "vendor/encore-active/ns2-astc/include",
        ROOT / "vendor/encore-active/ns2-helpers/include",
        ROOT / "vendor/sources/eden/src",
        pinned / "vulkanheaders/v1.4.345/include",
        pinned / "vulkanmemoryallocator/v3.3.0/include",
        pinned / "fmt/12.1.0/include",
        pinned / "sirit/v1.0.5/include",
        pinned / "spirv-headers/vulkan-sdk-1.4.341.0/include",
    ]
    boost = pinned / "boost/boost-1.90.0/libs"
    require_dir(boost)
    boost_modules = sorted(boost.glob("*/include"))
    assert len(boost_modules) >= 90, "Incomplete pinned modular Boost headers"
    includes.extend(boost_modules)
    for inc in includes:
        require_dir(inc)
    command = [
        cxx, "-std=c++20", "-O0", "-fsyntax-only",
        *[f"-I{inc}" for inc in includes],
    ]
    environment = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="eden-vk-owner-syntax-") as folder:
        if platform.system() == "Darwin":
            # Use a CLT SDK with C++20 stop_token support; no developer or
            # toolkit system headers are copied into the deliverable.
            sdks = [
                Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk"),
                Path("/Library/Developer/CommandLineTools/SDKs/MacOSX27.0.sdk"),
            ]
            sdk = next((candidate for candidate in sdks
                        if (candidate / "usr/include/c++/v1/__thread/jthread.h").is_file()), None)
            assert sdk is not None, "macOS 26.5+ libc++ SDK needed for real C++20 owner parse"
            environment["SDKROOT"] = str(sdk)
            shim = Path(folder) / "arm64-pause-syntax.h"
            shim.write_text(
                "#pragma once\n"
                "#ifdef __aarch64__\n"
                "#ifndef __builtin_ia32_pause\n"
                '#define __builtin_ia32_pause() __asm__ __volatile__("yield")\n'
                "#endif\n#endif\n")
            command += [
                "-target", "arm64-apple-macos15", "-nostdinc++",
                "-isystem", str(sdk / "usr/include/c++/v1"),
                "-include", str(shim),
            ]

        modes = [
            ("desktop_ns1", []),
            ("native_shared_ps5", ["-DPS5_NATIVE=1"]),
            # Research-only N73 must compile only with the separately pinned
            # N72 scheduler bridge. Both remain OFF in the release profile.
            ("native_research_sparse_syntax_only", [
                "-DPS5_NATIVE=1",
                "-DEDEN_NS2_ASTC_LAYER_DECODE=1",
                "-DEDEN_NS2_SPARSE_CACHE_PROBE=1",
                "-DEDEN_NS2_SPARSE_QUEUE_BRIDGE=1",
                "-DEDEN_NS2_VIEW_DIMENSION_GUARD=1",
            ]),
        ]
        for mode, flags in modes:
            cmd = command + flags + [str(OWNER)]
            result = subprocess.run(
                cmd, cwd=ROOT, env=environment, capture_output=True,
                text=True, timeout=100,
            )
            if result.returncode:
                raise AssertionError(
                    f"Real Vulkan TU syntax failed for {mode}:\n"
                    + result.stdout[-2000:] + result.stderr[-8000:]
                )
            print(f"F07_REAL_VULKAN_TEXTURE_TU_PASS mode={mode} "
                  "owner=maintained pinned_dependencies=1 syntax_only=1")
    print("P2_2C_REAL_TEXTURE_CACHE_OWNER_HOST_PASS "
          "desktop_ns1=1 native_ps5=1 research_interface_only=1 "
          "gpu_execution=NOT_TESTED")

if __name__ == "__main__":
    run()
