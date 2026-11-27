#!/usr/bin/env python3
"""Qualify the CURRENT engine/vendor runtime graph for FC27 and NS2 P0.

This gate deliberately has no historical SHA allowlist.  vendor/sources is a
frozen upstream dependency; maintained Encore owners live in encore-active and
the engine must select the current vendor gitlink directly.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
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
).strip(), "vendor checkout is dirty"
subprocess.run(["git", "diff", "--quiet", "--", "sources"], cwd=VENDOR, check=True)

# One source-of-truth gate owns path/CMake selection.  Do not duplicate a
# revision catalogue here.
subprocess.run(
    [sys.executable, "-B", str(ROOT / "tools/check-active-cmake-source-boundary.py")],
    check=True,
)

cmake = (ROOT / "headless/CMakeLists.txt").read_text()
for token in (
    "vendor/encore-active",
    "EDEN_GPU_WORKER",
    "encore-active/eden",
):
    assert token in cmake, token
for forbidden in ("encore-active/eden-gpu", "gpu_thread_quiet.cpp", "gpu_thread_dev.cpp"):
    assert forbidden not in cmake, ("legacy GPU owner selected", forbidden)

owners = {
    "eden/src/video_core/gpu_thread.cpp": (
        "scheduler.HasPendingNativeChannels()",
        "state.signaled_fence.store(next.fence, std::memory_order_release)",
        "Eden::RecordGpuFailure(std::current_exception())",
    ),
    "eden/src/video_core/buffer_cache/word_manager.h": (
        "class DeferredPageCaching",
        "delta < 0",
        "t_deferred_page_caching",
    ),
    "eden/src/core/device_memory_manager.h": (
        "BeginDeferredCachedUpdates",
        "EndDeferredCachedUpdates",
        "deferred_cached_updates",
    ),
    "eden-vulkan/vulkan_rasterizer.cpp": (
        "VideoCommon::DeferredPageCaching",
        "device_memory.BeginDeferredCachedUpdates()",
        "deferred.ApplyAll()",
    ),
    "ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": (
        "HasCpuBlockedNativeChannels",
        "m_previous_fence_id",
        "RegisterGuestAction",
    ),
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp": (
        "HasCpuBlockedNativeChannels",
        "ResumePendingNative",
    ),
    "ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp": (
        "NativeGpuProcessRegistry",
        "RecordGpuSemaphoreValue",
        "ProcessNativeSemaphoreExecute",
    ),
}
for relative, markers in owners.items():
    path = ACTIVE / relative
    assert path.is_file(), ("missing current owner", relative)
    source = path.read_text()
    for marker in markers:
        assert marker in source, (relative, marker)

gsv = (ACTIVE / "ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp").read_text()
for forbidden in (
    "DonkeyKongBananzaProgramId",
    "OcarinaOfTimeProgramId",
    "DuskbloodsProgramId",
    "WaitForBananzaPresentFence",
):
    assert forbidden not in gsv, ("title-specific Present policy returned", forbidden)

for test in (
    "fc27_deferred_page_protection_host.py",
    "fc27_gpu_page_sibling_preservation_host.py",
    "ns2_gpu_identity_mapping_source.py",
    "ns2_syncpt_bootstrap_source.py",
):
    path = VENDOR / "tests" / test
    assert path.is_file(), test
    subprocess.run([sys.executable, "-B", str(path)], cwd=VENDOR, check=True)

print(
    "CURRENT_VENDOR_RUNTIME_GRAPH_PASS "
    "gitlink=1 sources_frozen=1 encore_active=1 "
    "fc27_page_untrack=1 ns2_generic_present=1 title_id_policy=0"
)
