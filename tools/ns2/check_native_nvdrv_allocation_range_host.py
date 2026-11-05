#!/usr/bin/env python3
"""P1.2/NS2 NVDRV: real fixed/remap allocation owner + C++ range oracle."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
vendor = root / "vendor/encore-active/ns2-runtime/nvdrv_as"
header = vendor / "core/hle/service/nvdrv/devices/native_gpu_allocation_range.h"
source = (vendor / "core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp").read_text()
assert header.is_file()
assert 'native_gpu_allocation_range.h' in source
assert source.count("NativeGpuAllocation::FindContaining(") == 2
assert "alloc-- == allocation_map.begin()" not in source
assert "if (alloc == allocation_map.end())" in source
assert "bytes > gpu_limit - address" in header.read_text()
assert "bytes > it->second.size - offset" in header.read_text()
assert "it == allocations.begin()" in header.read_text()
assert "ContainsSubrange(" in header.read_text()

# The research 4-KiB GPU owner can outlive its GMMU (session teardown /
# invalidated address space). A VM initialised bit is NOT evidence of a
# still-bound GMMU. The lifetime gate must precede all side effects.
for entrypoint in (
    "MapNative4K", "MapNativeImage", "ReserveNativeSparse4K",
    "RemapNativeSparse", "ReleaseNativeSparse4K",
    "UnmapNative4K", "ModifyNativeKind",
):
    marker = "NvResult nvhost_as_gpu::" + entrypoint + "("
    assert source.count(marker) == 1, ("Missing native GPU owner", entrypoint)
    body = source.split(marker, 1)[1].split("\nNvResult nvhost_as_gpu::", 1)[0]
    gate = body.find("!vm.initialised || !gmmu")
    assert gate >= 0, ("Native GMMU can be dereferenced without an owner", entrypoint)
    lock = body.find("const std::scoped_lock lock{mutex};")
    assert lock >= 0 and lock < gate, ("Native GMMU check must hold AS mutex", entrypoint)
    for mutation in ("gmmu->", "vm.small_page_allocator->AllocateFixed(",
                     "nvmap.PinHandle(", "FreeMappingLocked("):
        first = body.find(mutation)
        assert first == -1 or gate < first, (
            "Native GMMU lifetime gate must precede side effects",
            entrypoint, mutation)
remap = source.split("NvResult nvhost_as_gpu::MapBufferEx(", 1)[1].split(
    "NvResult nvhost_as_gpu::UnmapBuffer(", 1)[0]
assert remap.index("NativeGpuAllocation::ContainsSubrange(handle->orig_size") < remap.index(
    "nvmap.PinHandle(params.handle, false)")
assert remap.index("fixed_alloc = NativeGpuAllocation::FindContaining(") < remap.index(
    "nvmap.PinHandle(params.handle, false)")
assert "nvmap.UnpinHandle(params.handle); // Allocation failed after NvMap pin." in remap
assert "NativeGpuAllocation::ContainsSubrange(" in remap.split(
    "auto handle{nvmap.GetHandle(params.handle)};", 1)[0]

env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
with tempfile.TemporaryDirectory(prefix="encore-nvdrv-range-") as tmp:
    for compiler in ("clang++", "g++"):
        for opt in ("-O0", "-O2"):
            exe = Path(tmp) / f"allocation-{compiler}-{opt}"
            args = [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    "-I", str(vendor),
                    str(root / "tools/ns2/test_native_nvdrv_allocation_range.cpp"),
                    "-o", str(exe)]
            result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, (compiler, opt, result.stderr[-5000:])
            run_env = {**env, "ASAN_OPTIONS": "detect_leaks=0", "UBSAN_OPTIONS": "halt_on_error=1"}
            result = subprocess.run([str(exe)], env=run_env,
                                    capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, (compiler, opt, result.stderr[-5000:])
            assert "P1_2_NVDRV_ALLOCATION_RANGE_HOST_PASS" in result.stdout
            print(f"P1_2_NVDRV_RANGE_PASS compiler={compiler} opt={opt} "
                  "before_begin=guarded overflow=guarded zero=refused "
                  "source_owners=2 ASAN_UBSAN=pass")
