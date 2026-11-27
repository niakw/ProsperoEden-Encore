#!/usr/bin/env python3
"""Validate the current R457 sparse/GPU owners selected by main.

No historical vendor SHA list is maintained here. vendor/sources is a frozen
dependency; every maintained source checked below lives in vendor/encore-active
and the engine CMake must select that current owner directly.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
ACTIVE = VENDOR / "encore-active"
SOURCES = VENDOR / "sources"

entry = subprocess.check_output(
    ["git", "ls-tree", "HEAD", "vendor"], cwd=ROOT, text=True
).split()
assert len(entry) == 4 and entry[0] == "160000" and entry[1] == "commit"
vendor_head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=VENDOR, text=True
).strip()
assert vendor_head == entry[2], ("vendor/gitlink mismatch", vendor_head, entry[2])
assert not subprocess.check_output(
    ["git", "status", "--porcelain", "--untracked-files=no"], cwd=VENDOR, text=True
).strip()
assert ACTIVE.is_dir() and SOURCES.is_dir()

cmake = (ROOT / "headless/CMakeLists.txt").read_text()
for marker in (
    "set(EDEN_NS2_SPARSE_BACKING ON)",
    "target_compile_definitions(common PRIVATE EDEN_NS2_SPARSE_BACKING=1)",
    "target_compile_definitions(core PRIVATE EDEN_NS2_SPARSE_BACKING=1)",
    "vendor/encore-active/ns2-runtime/sparse-residency",
    "vendor/encore-active/eden-core/overrides",
    "set(EDEN_NS2_NATIVE_GPU_PULLER",
    "vendor/encore-active/ns2-runtime/gpu_dispatch",
):
    assert marker in cmake, marker

owners = {
    "ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp": (
        "EdenNs2CommitGuestBacking",
        "CommitKernelDirectGuestRange",
        "ResultOutOfMemory",
    ),
    "ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp": (
        "EdenNs2CommitGuestBacking",
        "TranslateSlabAddrToPhysical",
        "throw std::bad_alloc",
    ),
    "eden-core/overrides/core/device_memory_manager.h": (
        "BeginDeferredCachedUpdates",
        "EndDeferredCachedUpdates",
        "deferred_cached_updates",
    ),
    "ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp": (
        "NativeGpuProcessRegistry",
        "RecordGpuSemaphoreValue",
        "ProcessNativeSemaphoreAcquire",
    ),
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp": (
        "HasCpuBlockedNativeChannels",
        "HasCpuBlockedNativeAcquire",
        "ResumePendingNative",
    ),
    "ns2-runtime/gpu_dispatch/video_core/native_ampere_macro_state.h": (
        "ExecuteStagedWithEffects",
        "MaxCodeWords",
        "MaxPendingMethods",
    ),
}
for relative, markers in owners.items():
    path = ACTIVE / relative
    assert path.is_file(), relative
    text = path.read_text()
    for marker in markers:
        assert marker in text, (relative, marker)

# Frozen dependencies are read-only inputs to this qualification.
subprocess.run(["git", "diff", "--quiet", "--", "sources"], cwd=VENDOR, check=True)
print("R457_CURRENT_OWNER_PASS gitlink=1 frozen_sources=1 active_sparse=1 active_gpu=1")
