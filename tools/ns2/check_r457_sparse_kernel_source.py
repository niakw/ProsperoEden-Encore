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
    "vendor/encore-active/eden/src",
    "vendor/encore-active/eden/src",
    "set(EDEN_NS2_NATIVE_GPU_PULLER",
    "vendor/encore-active/eden/src",
):
    assert marker in cmake, marker

owners = {
    "eden/src/core/hle/kernel/k_memory_manager.cpp": (
        "EdenNs2CommitGuestBacking",
        "CommitKernelDirectGuestRange",
        "ResultOutOfMemory",
    ),
    "eden/src/core/hle/kernel/init/init_slab_setup.cpp": (
        "EdenNs2CommitGuestBacking",
        "TranslateSlabAddrToPhysical",
        "throw std::bad_alloc",
    ),
    "eden/src/core/device_memory_manager.h": (
        "UpdatePagesCachedBatch",
        "mapping_guard",
        "process_registry_guard",
    ),
    "eden/src/video_core/engines/puller.cpp": (
        "NativeGpuProcessRegistry",
        "RecordGpuSemaphoreValue",
        "ProcessNativeSemaphoreExecute",
    ),
    "eden/src/video_core/control/scheduler.cpp": (
        "HasCpuBlockedNativeChannels",
        "HasCpuBlockedNativeAcquire",
        "ResumePendingNative",
    ),
    "eden/src/video_core/native_ampere_macro_state.h": (
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

# Sparse backing does not depend on the withdrawn FC27 deferred-untrack
# optimization. Keep active device memory on the synchronous publication path.
device_owner = (ACTIVE / "eden/src/core/device_memory_manager.h").read_text()
device_impl = (ACTIVE / "eden/src/core/device_memory_manager.inc").read_text()
for forbidden in (
    "BeginDeferredCachedUpdates",
    "EndDeferredCachedUpdates",
    "deferred_cached_updates",
):
    assert forbidden not in device_owner + device_impl, forbidden

# Frozen dependencies are read-only inputs to this qualification.
subprocess.run(["git", "diff", "--quiet", "--", "sources"], cwd=VENDOR, check=True)
print("R457_CURRENT_OWNER_PASS gitlink=1 frozen_sources=1 active_sparse=1 active_gpu=1")
