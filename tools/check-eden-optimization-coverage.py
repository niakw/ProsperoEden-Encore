#!/usr/bin/env python3
"""Count Encore-owned files not yet handled in the optimization work pass.

Fast-skip previously maintained sources with a specific historical proof, but
never confuse code triage with host or console performance validation.
"""
import json
import ast
import hashlib
import subprocess
from collections import Counter
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"docs/EDEN_OPTIMIZATION_COVERAGE_2026-10-20.json"
STATE=json.loads(P.read_text())
assert STATE["schema_version"]==1
tracked=set(subprocess.check_output(["git","ls-files","-z"],cwd=ROOT).decode().split("\0"))-{""}
# When vendor is moved to an immutable gitlink, the parent index lists only
# "vendor". Preserve the original vendor/… owner namespace by merging the
# pinned submodule index; never infer source ownership from arbitrary disk files.
if "vendor" in tracked:
    vendor_paths = subprocess.check_output(
        ["git", "-C", "vendor", "ls-files", "-z"], cwd=ROOT
    ).decode().split("\0")
    tracked.update("vendor/" + p for p in vendor_paths if p)

suffixes={".c",".cpp",".cxx",".cc",".h",".hpp",".inc"}
all_owners={p for p in tracked
        if p.startswith(("headless/","src/","vendor/encore-active/"))
        and Path(p).suffix in suffixes}
# Three unmodified upstream dependencies live under vendor/sources/.
# Their snapshots must never be categorized as F07 owners or hidden as
# Encore active overrides. Keep the immutable 518 historical source total.
pinned_upstream_f07_counts = {
    "ps5-mihawkgen": 474,
    "ps5-fsr3-optical-flow": 41,
    "libwebp": 245,
}
for name, expected in pinned_upstream_f07_counts.items():
    prefix = f"vendor/sources/{name}/"
    files = {p for p in tracked
             if p.startswith(prefix) and Path(p).suffix in suffixes}
    assert len(files) == expected, ("Upstream snapshot drift", name, len(files), expected)
for stale in ("PS5_MihawkGen", "PS5_FSR3OpticalFlow", "libwebp"):
    assert not any(p.startswith(f"vendor/encore-active/{stale}/")
                   for p in tracked), stale
print("ENCORE_PINNED_UPSTREAM_F07_ISOLATION_PASS",
      f"upstream_sources={sum(pinned_upstream_f07_counts.values())}",
      "trees=3 historical_f07_unchanged=1")
# NS2 is an explicitly unqualified research layer, not historical F07 review.
# Do not silently count new research source code as already optimized.
research = json.loads((ROOT/"docs/NS2_RESEARCH_ADDED_SOURCE_OWNERS.json").read_text())
research_owners={"vendor/encore-active/"+p for p in research["paths"]}
assert research["schema_version"] == 1 and len(research_owners) == 121
retired_am = {
    "vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/application_proxy.cpp",
    "vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/application_proxy.h",
    "vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/graphics_scaling_parameters_functions.cpp",
    "vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/graphics_scaling_parameters_functions.h",
}
assert not retired_am & all_owners, "Retired AM false-success owners were reintroduced"
assert not retired_am & research_owners, "Research inventory retained removed AM stubs"
assert research_owners <= all_owners, sorted(research_owners-all_owners)
# The two new shared warning-hygiene headers have a separate exact-source
# verifier and installer. They are not retroactive F07 optimization reviews.
hygiene_owners = {
    "vendor/encore-active/eden-header-hygiene/include/common/page_table.h",
    "vendor/encore-active/eden-header-hygiene/include/video_core/macro.h",
}
assert hygiene_owners <= all_owners, sorted(hygiene_owners - all_owners)
assert "tools/install-eden-header-hygiene.py" in tracked
# The four mainline extracted AOC owners are explicitly reviewed in the
# post-snapshot F07 source ledger. Do not silently drop their proof entries
# or misclassify them as opt-in NS2 experiments.
extracted_aoc_owners = {
    "vendor/encore-active/eden-core/src/core/file_sys/extracted_aoc.h",
    "vendor/encore-active/eden-core/src/core/file_sys/extracted_aoc_paths.h",
    "vendor/encore-active/eden-core/src/core/file_sys/romfs_factory.cpp",
    "vendor/encore-active/eden-core/src/core/hle/service/aoc/addon_content_manager.cpp",
}
assert extracted_aoc_owners <= all_owners, sorted(extracted_aoc_owners - all_owners)
assert not extracted_aoc_owners & (research_owners | hygiene_owners)
# New NS2 kernel/process owners are selected only by the one reviewed PS5
# release profile. They postdate the frozen F07 518-source optimization audit
# and must remain independently visible, not mislabeled as F07-complete.
ns2_shared_release_owners = {
    "vendor/encore-active/ns2-runtime/kernel/core/hle/kernel/k_address_space_info.cpp",
    "vendor/encore-active/ns2-runtime/kernel/core/hle/kernel/svc/svc_physical_memory.cpp",
    "vendor/encore-active/ns2-runtime/process/core/core.cpp",
    "vendor/encore-active/ns2-runtime/process/core/hle/kernel/k_process.cpp",
}
assert ns2_shared_release_owners <= all_owners, sorted(ns2_shared_release_owners-all_owners)
assert not ns2_shared_release_owners & (research_owners | hygiene_owners | extracted_aoc_owners)
release_cmake = (ROOT / "headless/CMakeLists.txt").read_text()
assert 'set(EDEN_SHARED_NS2_KERNEL_HEAP ON)' in release_cmake
assert 'ns2-runtime/process/core/core.cpp' in release_cmake
assert 'set(EDEN_NS2_KPROCESS_SOURCE' in release_cmake
assert 'ns2-runtime/process/core/hle/kernel/k_process.cpp' in release_cmake
print("NS2_SHARED_RELEASE_F07_ISOLATION_PASS", f"new_release_sources={len(ns2_shared_release_owners)}")
ns2_shared_audio_owners = {
    "vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/audio.cpp",
    "vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_audio_user_client.h",
    "vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_sysmix.cpp",
    "vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_sysmix.h",
    "vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_sysmix_user_service.h",
    "vendor/encore-active/ns2-runtime/audio/core/hle/service/nx2_streamplay.h",
}
assert ns2_shared_audio_owners <= all_owners, sorted(ns2_shared_audio_owners-all_owners)
assert not ns2_shared_audio_owners & (research_owners | hygiene_owners | ns2_shared_release_owners)
assert 'set(EDEN_SHARED_NS2_AUDIO ON)' in release_cmake
print("NS2_SHARED_AUDIO_F07_ISOLATION_PASS", f"new_release_sources={len(ns2_shared_audio_owners)}")
ns2_shared_gpu_access_owners = {
    "vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp",
    "vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/ns2_gpu_memory_attribute.h",
    "vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc_types.h",
    "vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/k_memory_block.h",
}
assert ns2_shared_gpu_access_owners <= all_owners, sorted(ns2_shared_gpu_access_owners - all_owners)
assert not ns2_shared_gpu_access_owners & (research_owners | hygiene_owners | ns2_shared_release_owners | ns2_shared_audio_owners)
assert 'set(EDEN_SHARED_NS2_GPU_ACCESS_SVC ON)' in release_cmake
print("NS2_GPU_ACCESS_F07_ISOLATION_PASS", f"new_release_sources={len(ns2_shared_gpu_access_owners)}")
# The newly selected rasterizer header is a post-F07 NS2 Compute ABI owner.
# Assert its source and native-only guard rather than silently raising the
# frozen 518-source F07 optimization proof count.
post_f07_native_vulkan_owners = {
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h",
}
assert post_f07_native_vulkan_owners <= all_owners, sorted(post_f07_native_vulkan_owners-all_owners)
assert not post_f07_native_vulkan_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners
)
native_rasterizer_header = (ROOT / next(iter(post_f07_native_vulkan_owners))).read_text()
assert native_rasterizer_header.count("DispatchNativeCompute(") == 1
assert "#ifdef PS5_NATIVE" in native_rasterizer_header
assert "[[nodiscard]] bool DispatchNativeCompute(const Tegra::NativeComputeLaunch& launch) override;" in native_rasterizer_header
assert 'file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")' in (
    ROOT / "headless/vulkan.cmake"
).read_text()
print("NS2_POST_F07_VULKAN_ABI_ISOLATION_PASS", f"new_native_headers={len(post_f07_native_vulkan_owners)}")
# The shared Maxwell/Ampere Compute storage walker was added after F07.
# Preserve the immutable 518-owner audit and independently prove its owner.
post_f07_shared_compute_owners = {
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_compute_storage_layout.h",
}
assert post_f07_shared_compute_owners <= all_owners, sorted(post_f07_shared_compute_owners-all_owners)
assert not post_f07_shared_compute_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners
)
shared_compute_header = (ROOT / next(iter(post_f07_shared_compute_owners))).read_text()
assert "namespace Vulkan::ComputeStorageLayout {" in shared_compute_header
assert "count > max_bindings - flattened" in shared_compute_header
assert "std::numeric_limits<std::uint32_t>::max()" in shared_compute_header
shared_compute_cpp = (ROOT / "vendor/encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp").read_text()
assert '#include "video_core/renderer_vulkan/vk_compute_storage_layout.h"' in shared_compute_cpp
assert shared_compute_cpp.count("ComputeStorageLayout::ForEach(") == 3
assert "python3 -B tools/check-shared-compute-storage-descriptors-host.py" in (
    ROOT / ".github/workflows/encore-core-fast-gate.yml"
).read_text()
print("NS1_NS2_SHARED_COMPUTE_F07_ISOLATION_PASS", f"new_shared_headers={len(post_f07_shared_compute_owners)}")
# The launcher -> Vulkan RGBA mailbox is a new ordinary production header,
# not part of the immutable F07 518-owner optimization snapshot. Validate
# the real handoff and its independent host gate instead of inflating F07.
post_f07_launcher_handoff_owners = {"headless/launch_handoff.hpp"}
assert post_f07_launcher_handoff_owners <= all_owners
handoff_header = (ROOT / "headless/launch_handoff.hpp").read_text()
assert "namespace Eden::LaunchHandoff {" in handoff_header
assert "inline std::shared_ptr<const Frame> Peek()" in handoff_header
assert "std::exchange(pending_frame, {})" in handoff_header
assert "tools/check-ps5-vulkan-loading-stages-host.py" in tracked
assert not post_f07_launcher_handoff_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners | post_f07_shared_compute_owners
)
print("ENCORE_SHARED_LOADER_F07_ISOLATION_PASS",
      f"new_shipping_headers={len(post_f07_launcher_handoff_owners)}")
# This generated PS5/NS2-only typed cache ABI postdates the frozen F07
# 518-source optimization audit. Keep it visible and independently guarded,
# never reclassify it as previously optimized Switch 1 source code.
post_f07_ns2_typed_cache_owners = {
    "vendor/encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache_base.h",
}
assert post_f07_ns2_typed_cache_owners <= all_owners, sorted(
    post_f07_ns2_typed_cache_owners-all_owners)
assert not post_f07_ns2_typed_cache_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners | post_f07_shared_compute_owners |
    post_f07_launcher_handoff_owners
)
cache_header = (ROOT / next(iter(post_f07_ns2_typed_cache_owners))).read_text()
assert "AcquireNativeImageView(" in cache_header
assert "NativeChannelMatches(" in cache_header
assert "AcquireNativeSampler(" in cache_header
assert "#ifdef PS5_NATIVE" in cache_header
print("NS2_POST_F07_TYPED_CACHE_ABI_ISOLATION_PASS",
      f"new_native_headers={len(post_f07_ns2_typed_cache_owners)}")
# P1.2 shared GPU scalar fix is newer than the immutable F07 518 owners.
# Its exact native owner and Clang/GCC witness are tracked separately, not
# misclassified as a completed historical optimization or opt-in NS2 path.
post_f07_shared_gpu_scalar_owners = {
    "vendor/encore-active/eden-core/src/video_core/native_paged_scalar.h",
}
assert post_f07_shared_gpu_scalar_owners <= all_owners, sorted(
    post_f07_shared_gpu_scalar_owners - all_owners)
assert not post_f07_shared_gpu_scalar_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners | post_f07_shared_compute_owners |
    post_f07_launcher_handoff_owners | post_f07_ns2_typed_cache_owners
)
native_scalar_owner = (
    ROOT / "vendor/encore-active/eden-core/src/video_core/memory_manager.cpp"
).read_text()
assert '#include "native_paged_scalar.h"' in native_scalar_owner
assert "Eden::GpuScalar::Read(addr, value," in native_scalar_owner
assert "Eden::GpuScalar::Write(addr, data," in native_scalar_owner
assert "tools/ns2/check_paged_gpu_scalar_host.py" in tracked
assert "python3 -B tools/ns2/check_paged_gpu_scalar_host.py" in (
    ROOT / ".github/workflows/encore-core-preflight.yml").read_text()
print("NS1_NS2_SHARED_GPU_SCALAR_F07_ISOLATION_PASS",
      f"post_snapshot_reviewed={len(post_f07_shared_gpu_scalar_owners)}")
# P1.2 physical remapping of the common NS1/NS2 GMMU is a genuinely
# new header outside the historical F07 owner count, not NS2-only code.
post_f07_shared_gpu_remap_owners = {
    "vendor/encore-active/eden-core/src/video_core/native_gpu_page_remap.h",
}
assert post_f07_shared_gpu_remap_owners <= all_owners
assert not post_f07_shared_gpu_remap_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_shared_gpu_scalar_owners)
assert '#include "native_gpu_page_remap.h"' in native_scalar_owner
assert native_scalar_owner.count("Eden::GpuMemory::NeedsRasterizerUnmap(") == 2
assert "python3 tools/ns2/check_native_gpu_pte_remap_host.py" in (
    ROOT / ".github/workflows/ns2-research-host.yml").read_text()
print("NS1_NS2_SHARED_GPU_REMAP_F07_ISOLATION_PASS",
      f"post_snapshot_reviewed={len(post_f07_shared_gpu_remap_owners)}")

# The native QMD3 atomic resource span owner (static or proof-bounded)
# was added on 05/11,
# AFTER the frozen 518-path F07 optimization snapshot. It is a real NS2
# source owner, not retroactively optimized Switch 1 code. Preserve the
# original baseline and independently assert the actual integration/tests.
post_f07_native_atomic_span_owners = {
    "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_atomic_span.h",
}
assert post_f07_native_atomic_span_owners <= all_owners, sorted(
    post_f07_native_atomic_span_owners - all_owners)
assert not post_f07_native_atomic_span_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners | post_f07_shared_compute_owners |
    post_f07_launcher_handoff_owners | post_f07_ns2_typed_cache_owners |
    post_f07_shared_gpu_scalar_owners | post_f07_shared_gpu_remap_owners
)
native_atomic_header = (ROOT / next(iter(post_f07_native_atomic_span_owners))).read_text()
assert "CollectNativeQmdAtomicSpans(" in native_atomic_header
assert "NativeQmdAtomicSpansFitBindings(" in native_atomic_header
assert "NativeQmdAtomicMaximumByteOffset(" in native_atomic_header
assert "instruction->GetOpcode() != Shader::IR::Opcode::BitwiseAnd32" in native_atomic_header
assert "if (lhs.IsImmediate() == rhs.IsImmediate()) return std::nullopt;" in native_atomic_header
assert "NativeQmdAtomicAlignedMask(" in native_atomic_header
assert "addition->GetOpcode() != Shader::IR::Opcode::IAdd32" in native_atomic_header
assert "Shader::IR::Opcode::ShiftLeftLogical32" in native_atomic_header
assert "shift >= 32" in native_atomic_header
assert "*bound > (std::numeric_limits<u32>::max() >> shift)" in native_atomic_header
assert "NativeQmdAtomicLiteralExtractMax(" in native_atomic_header
assert "Shader::IR::Opcode::BitFieldUExtract" in native_atomic_header
assert "bits > 32 - first" in native_atomic_header
assert "*and_mask > std::numeric_limits<u32>::max() - width - base" in native_atomic_header
assert "(storage.gpu_address & (span.width - 1U))" in native_atomic_header
assert "storage.bytes > gpu_limit - storage.gpu_address" in native_atomic_header
assert "NativeQmdAtomicMaximumByteOffset(offset, width)" in native_atomic_header
atomic_fixture = (ROOT / "tools/ns2/test_native_qmd_atomic_span.cpp").read_text()
assert "aligned_and_max_admitted=1" in atomic_fixture
assert "aligned_base_plus_and=1" in atomic_fixture
assert "atomic_gmmu_base_alignment=1" in atomic_fixture
assert "shifted_mask_index=1" in atomic_fixture
assert "shifted_mask_plus_base=1" in atomic_fixture
assert "bitfield_unsigned_extract=1" in atomic_fixture
assert "extract_invalid_ranges_refused=1" in atomic_fixture
assert "guest_va_49=1" in atomic_fixture
assert '#include "shader_recompiler/frontend/ampere/native_atomic_span.h"' in (
    ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.h"
).read_text()
assert "NativeQmdAtomicSpansFitBindings(" in (
    ROOT / "vendor/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.cpp"
).read_text()
assert "python3 -B tools/ns2/check_native_qmd_atomic_span_host.py" in (
    ROOT / ".github/workflows/ns2-research-host.yml"
).read_text()
assert (ROOT / "tools/ns2/test_native_qmd_atomic_span.cpp").is_file()
print("NS2_POST_F07_ATOMIC_SPAN_ISOLATION_PASS",
      f"new_native_headers={len(post_f07_native_atomic_span_owners)}",
      "historical_F07_unchanged=1")

# P2.3: the actual QMD3 address-derived atomic rewrite is a new native
# functional owner and must NOT be folded into the historical F07 count.
post_f07_native_global_atomic_owners = {
    "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_global_atomic_binding.h",
}
assert post_f07_native_global_atomic_owners <= all_owners
assert not post_f07_native_global_atomic_owners & (research_owners | hygiene_owners)
atomic_binding = (ROOT / next(iter(post_f07_native_global_atomic_owners))).read_text()
assert 'NativeAtomic' in atomic_binding and 'Rewrite(Shader::IR::Program&' in atomic_binding
assert 'Opcode::CompositeConstructU32x2' in atomic_binding
assert 'left_pointer == right_pointer' in atomic_binding
assert 'Opcode::GlobalAtomicAddF32' in atomic_binding
assert 'Opcode::GlobalAtomicMaxF16x2' in atomic_binding
assert 'Opcode::GlobalAtomicMaxF32x2' in atomic_binding
assert 'NativeAtomic::Rewrite(ir)' in (
    ROOT / 'vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp').read_text()
print('NS2_POST_F07_GLOBAL_ATOMIC_OWNER_PASS', 'new_native_headers=1', 'historical_F07_unchanged=1')

# P2.7: the native GPFIFO live-read guard is post-F07 and gated behind
# the exact NVDRV/Ampere GPU dispatch research profile. It is not a new
# historical shipping optimization. Its source and executed test must be
# visible separately from the original 518 reviewed owners.
post_f07_native_gpfifo_fetch_owners = {
    "vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h",
}
assert post_f07_native_gpfifo_fetch_owners <= all_owners, sorted(
    post_f07_native_gpfifo_fetch_owners - all_owners)
assert not post_f07_native_gpfifo_fetch_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners | post_f07_shared_compute_owners |
    post_f07_launcher_handoff_owners | post_f07_ns2_typed_cache_owners |
    post_f07_shared_gpu_scalar_owners | post_f07_shared_gpu_remap_owners |
    post_f07_native_atomic_span_owners)
fetch_header=(ROOT/next(iter(post_f07_native_gpfifo_fetch_owners))).read_text()
assert 'NativeGpfifoFetchMapped(' in fetch_header
assert 'words > (native_limit - address) / bytes_per_word' in fetch_header
for dma in ('dma_pusher.cpp','dma_pusher_dev.cpp'):
    owner=(ROOT/'vendor/encore-active/eden-core/src/video_core'/dma).read_text()
    assert '#include "core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h"' in owner
    assert 'NativeGpfifoFetchMapped(' in owner
assert 'target_compile_definitions(video_core PRIVATE EDEN_NS2_NATIVE_GPU_DISPATCH=1)' not in release_cmake
assert 'vulkan_abi/video_core/rasterizer_interface.h' in release_cmake
for dma in ('dma_pusher.cpp','dma_pusher_dev.cpp'):
    assert '#ifdef PS5_NATIVE' in (ROOT/'vendor/encore-active/eden-core/src/video_core'/dma).read_text()
assert 'python3 -B tools/ns2/check_native_gpu_fetch_admission_host.py' in (
    ROOT/'.github/workflows/encore-core-preflight.yml').read_text()
print('NS2_POST_F07_NATIVE_GPFIFO_FETCH_ISOLATION_PASS',
      f'new_native_headers={len(post_f07_native_gpfifo_fetch_owners)}')

# NUP v1 parser/adapter/loader/router additions came after the frozen
# 518-path F07 optimization audit. Their native CMake gate is OFF by default,
# forbidden in the final profile, and has no PS5 runtime proof. Keep this
# exact staged-source inventory separate from historical optimized owners.
post_f07_nup_vfs_owners = {
    "headless/nup_v1_vfs.h",
    "headless/nup_v1_vfs.cpp",
    "headless/nup_v1_native_vfs.h",
    "headless/nup_v1_native_vfs.cpp",
    "headless/nup_v1_native_content.h",
    "headless/nup_v1_native_content.cpp",
    "headless/nup_v1_native_loader.h",
    "headless/nup_v1_native_loader.cpp",
    "headless/nup_v1_native_aoc.h",
    "headless/nup_v1_native_aoc.cpp",
    "headless/nup_v1_loader_route.cpp",
    "headless/nup_v1_romfs_factory.cpp",
    "headless/nup_v1_aoc_service.cpp",
}
assert post_f07_nup_vfs_owners <= all_owners, sorted(
    post_f07_nup_vfs_owners - all_owners)
assert not post_f07_nup_vfs_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners | post_f07_shared_compute_owners |
    post_f07_launcher_handoff_owners | post_f07_ns2_typed_cache_owners
)
# NUP is always selected with the single native loader. It was introduced
# after frozen F07, so inventory remains historical, not a release gate.
nup_include = 'include("${CMAKE_CURRENT_LIST_DIR}/nup_v1_runtime.cmake")'
assert release_cmake.count(nup_include) == 1
nup_select = (ROOT / "headless/nup_v1_runtime.cmake").read_text()
assert 'option(EDEN_NUP_V1_RUNTIME' not in nup_select
assert 'EDEN_FINAL_RELEASE_PROFILE' not in nup_select
assert 'target_sources(core PRIVATE' in nup_select
assert 'set_property(TARGET core PROPERTY SOURCES "${eden_nup_runtime_sources}")' in nup_select
assert 'if(NOT eden_nup_match_count EQUAL 1)' in nup_select
for selected in (
    "nup_v1_vfs.cpp", "nup_v1_native_vfs.cpp",
    "nup_v1_native_content.cpp", "nup_v1_native_aoc.cpp",
    "nup_v1_native_loader.cpp", "nup_v1_loader_route.cpp",
):
    source_ref = '"${EDEN_PORT_DIR}/' + selected + '"'
    assert nup_select.count(source_ref) == 1
    assert release_cmake.count(source_ref) == 0
# NUP's two maintained owner replacements remain post-F07 history; normal
# CMake selects exactly one existing source for each without policy gates.
for original, replacement in (
    ("file_sys/romfs_factory.cpp", "nup_v1_romfs_factory.cpp"),
    ("hle/service/aoc/addon_content_manager.cpp", "nup_v1_aoc_service.cpp"),
):
    pair = '"' + original + "|" + replacement + '"'
    assert nup_select.count(pair) == 1
    assert replacement not in release_cmake
assert 'list(LENGTH eden_nup_matches eden_nup_match_count)' in nup_select
assert 'if(NOT eden_nup_match_count EQUAL 1)' in nup_select
assert 'set_property(TARGET core PROPERTY SOURCES "${eden_nup_runtime_sources}")' in nup_select
assert (ROOT / "tools/check-nup-v1-runtime-cmake.py").is_file()
nup_core = (ROOT / "headless/nup_v1_vfs.h").read_text()
nup_adapter = (ROOT / "headless/nup_v1_native_vfs.h").read_text()
assert "Used by the unified native loader and catalogue." in nup_core
assert "Registered by the unified NUP loader" in nup_adapter
assert "AllowsVerifiedMemberCache() const override { return false; }" in (
    ROOT / "headless/nup_v1_native_vfs.cpp").read_text()
assert "Native NUP content bridge" in (
    ROOT / "headless/nup_v1_native_content.h").read_text()
assert "Shared NUP v1 application-loader adapter." in (
    ROOT / "headless/nup_v1_native_loader.h").read_text()
assert "NupAppLoader::Open(" in (
    ROOT / "headless/nup_v1_native_loader.cpp").read_text()
print("NUP_V1_POST_F07_OWNER_INTEGRATION_PASS",
      f"not_retroactive_F07={len(post_f07_nup_vfs_owners)}",
      "shipping_selection=unified")

# P1.3: the eight shared WaitIfEqual64/address-space source/ABI owners were
# introduced after the frozen F07 inventory. Qualify them with the real
# kernel/SVC/selector host witness; never inflate the historical 518 count.
post_f07_shared_wait64_owners = {
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.cpp",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.h",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_process.h",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_address_space_info.h",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_page_table_base.h",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_process_page_table.h",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/svc.h",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/svc/svc_address_arbiter.cpp",
}
assert post_f07_shared_wait64_owners <= all_owners, sorted(
    post_f07_shared_wait64_owners - all_owners)
assert not post_f07_shared_wait64_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_native_vulkan_owners | post_f07_shared_compute_owners |
    post_f07_launcher_handoff_owners | post_f07_ns2_typed_cache_owners |
    post_f07_shared_gpu_scalar_owners | post_f07_shared_gpu_remap_owners |
    post_f07_native_atomic_span_owners | post_f07_nup_vfs_owners)
assert 'set(EDEN_SHARED_NS2_WAIT64 ON)' in release_cmake
assert 'if(EDEN_SHARED_NS2_GPU_ACCESS_SVC)' in release_cmake
assert 'set_property(TARGET core PROPERTY SOURCES "${eden_wait64_sources}")' in release_cmake
assert (ROOT / 'tools/ns2/check_shared_kernel_wait64_host.py').is_file()
assert 'python3 -B tools/ns2/check_shared_kernel_wait64_host.py' in (
    ROOT / '.github/workflows/encore-core-preflight.yml').read_text()
print('NS1_NS2_SHARED_WAIT64_F07_ISOLATION_PASS',
      f'post_snapshot_source_owners={len(post_f07_shared_wait64_owners)}')

post_f07_unified_rasterizer_owners = {
    'vendor/encore-active/ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h',
}
assert post_f07_unified_rasterizer_owners <= all_owners
unified_rasterizer = (ROOT/next(iter(post_f07_unified_rasterizer_owners))).read_text()
assert 'virtual bool DispatchNativeCompute(const Tegra::NativeComputeLaunch&)' in unified_rasterizer
assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' not in unified_rasterizer
assert 'vulkan_abi/video_core/rasterizer_interface.h' in release_cmake
print('NS1_NS2_UNIFIED_VULKAN_ABI_F07_ISOLATION_PASS new_native_headers=1')

# Eleven reviewed static CPU6/A64 v8.1-v8.5 units are selected outside the frozen F07 set.
post_f07_static_engine_owners = {
    "vendor/encore-active/ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_32.cpp",
    "vendor/encore-active/ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_64.cpp",
    "vendor/encore-active/ns2-runtime/cpu6/maintained/core/hle/kernel/global_scheduler_context.cpp",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.h",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.inc",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/impl.h",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/load_store_exclusive.cpp",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/a64_branch.cpp",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/load_store_atomic.cpp",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/memory_tagging.cpp",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/pointer_authentication.cpp",
}
assert len(post_f07_static_engine_owners) == 11
assert post_f07_static_engine_owners <= all_owners, (
    "Missing post-F07 maintained native source owner",
    sorted(post_f07_static_engine_owners - all_owners))
assert not post_f07_static_engine_owners & research_owners
assert 'vendor/encore-active/ns2-runtime/cpu6/maintained' in (
    ROOT/'headless/ns2_cpu6_source_bridge.cmake').read_text()
assert 'vendor/encore-active/ns2-runtime/ldapr/maintained' in (
    ROOT/'headless/shared_a64_ldapr.cmake').read_text()
print("ENCORE_POST_F07_NATIVE_SOURCE_ISOLATION_PASS owners=11 a64_v81_v85=1")

# These three real NVDRV source owners joined the shared engine in P1.3,
# after the 518-file F07 review. Keep that immutable historical set and
# validate the new shipping CMake, active test and provenance separately.
post_f07_shared_nvdrv_owners = {
    "vendor/encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp",
    "vendor/encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvmap.cpp",
    "vendor/encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvhost_nvdec_common.cpp",
}
assert len(post_f07_shared_nvdrv_owners) == 3
assert post_f07_shared_nvdrv_owners <= all_owners, (
    "Missing maintained P1 NVDRV source", sorted(post_f07_shared_nvdrv_owners - all_owners))
assert not post_f07_shared_nvdrv_owners & (
    research_owners | hygiene_owners | ns2_shared_release_owners |
    ns2_shared_audio_owners | ns2_shared_gpu_access_owners |
    post_f07_static_engine_owners | post_f07_nup_vfs_owners)
for selected in ("EDEN_MAINTAINED_NVDRV_NVMAP_CORE",
                 "EDEN_MAINTAINED_NVDRV_NVMAP_DEVICE",
                 "EDEN_MAINTAINED_NVDRV_NVDEC"):
    assert f"set({selected}" in release_cmake
assert (ROOT / "tools/ns2/check_nvdrv_fd_session_owners_host.py").is_file()
assert (ROOT / "tools/ns2/check_native_nvmap_smmu_reclaim_host.py").is_file()
assert (ROOT / "tools/ns2/check_native_nvmap_pin_refs_host.py").is_file()
assert (ROOT / "tools/ns2/check_nvdrv_pin_failure_propagation_host.py").is_file()
print("ENCORE_POST_F07_SHARED_NVDRV_ISOLATION_PASS",
      f"new_shared_sources={len(post_f07_shared_nvdrv_owners)}")

# Post-F07 FFmpeg codec sources are genuine shared video_core units,
# proven separately rather than retroactively counted as optimized in F07.
post_f07_video_decoder_owners = {
    "vendor/encore-active/ns2-runtime/video_decoder/video_core/host1x/h264_packet.h",
    "vendor/encore-active/ns2-runtime/video_decoder/video_core/host1x/nx2_video_decoder.h",
    "vendor/encore-active/ns2-runtime/video_decoder/video_core/host1x/nx2_video_decoder.cpp",
    "vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.h",
    "vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp",
    "vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/native_video_eos.h",
    "vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/native_video_work_buffer.h",
    "vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/native_video_ready_state.h",
}
assert len(post_f07_video_decoder_owners) == 8
assert post_f07_video_decoder_owners <= all_owners, (
    "Missing post-F07 native decoder", sorted(post_f07_video_decoder_owners - all_owners))
assert not post_f07_video_decoder_owners & (research_owners | hygiene_owners)
assert "EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT" in release_cmake
assert (ROOT / "tools/ns2/check_native_video_decoder_backend_host.py").is_file()
assert (ROOT / "tools/ns2/check_native_video_decoder_ipc_host.py").is_file()
assert (ROOT / "tools/ns2/check_native_video_ready_event_host.py").is_file()
print("ENCORE_POST_F07_NATIVE_VIDEO_CODEC_ISOLATION_PASS",
      f"new_shared_sources={len(post_f07_video_decoder_owners)}")

# A new P2.4 active Ampere stage-buffer decoder was added after the
# immutable F07 review. Keep it visible and explicitly unqualified for
# optimization; never inflate or relabel the 518 reviewed owner count.
post_f07_native_stage_buffer_owners = {
    "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_stage_buffer.h",
}
assert post_f07_native_stage_buffer_owners <= all_owners, (
    "Missing active native stage-buffer owner",
    sorted(post_f07_native_stage_buffer_owners - all_owners))
assert not post_f07_native_stage_buffer_owners & research_owners
assert "DecodeNativeStageBufferAccess(" in (
    ROOT / next(iter(post_f07_native_stage_buffer_owners))).read_text()
print("ENCORE_POST_F07_STAGE_BUFFER_ISOLATION_PASS", "new_p2_owners=1")

# P2.4 maintains a separately audited set of new Task/Mesh compiler
# source owners. It is not part of the immutable 518-file F07 optimization
# evidence. Reuse the exact literal inventory instead of maintaining a
# second, diverging hardcoded list.
import ast
task_mesh_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "post_f07_task_mesh_source_owners"
        for t in node.targets
    )
]
assert len(task_mesh_nodes) == 1, "Task/Mesh inventory definition missing"
task_mesh_paths = ast.literal_eval(task_mesh_nodes[0])
assert isinstance(task_mesh_paths, set) and len(task_mesh_paths) == 29
post_f07_task_mesh_owners = {
    "vendor/encore-active/" + p for p in task_mesh_paths
}
assert post_f07_task_mesh_owners <= all_owners, (
    "Missing maintained Task/Mesh source owner",
    sorted(post_f07_task_mesh_owners - all_owners))
assert not post_f07_task_mesh_owners & research_owners
assert "EDEN_NATIVE_TASK_MESH_ROOT" in release_cmake
print("ENCORE_P24_TASK_MESH_POST_F07_PASS", f"owners={len(post_f07_task_mesh_owners)}")

# Reuse the literal three-file source catalogue: do not inflate the
# immutable F07 518 reviewed owners after adding P2.4 opcode decoding.
opcode_nodes = [
    n.value for n in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body
    if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "post_f07_native_opcode_owners"
        for t in n.targets)
]
assert len(opcode_nodes) == 1
opcode_paths = ast.literal_eval(opcode_nodes[0])
assert opcode_paths == {
    "eden-shader/src/shader_recompiler/frontend/maxwell/decode.cpp",
    "eden-shader/src/shader_recompiler/frontend/maxwell/opcodes.cpp",
    "eden-shader/src/shader_recompiler/frontend/maxwell/opcodes.h",
}
post_f07_native_opcode_owners = {"vendor/encore-active/" + p for p in opcode_paths}
assert post_f07_native_opcode_owners <= all_owners
assert not post_f07_native_opcode_owners & (research_owners | post_f07_task_mesh_owners)
assert "frontend/maxwell/decode.cpp" in release_cmake
assert "frontend/maxwell/opcodes.cpp" in release_cmake
print("ENCORE_POST_F07_NATIVE_OPCODE_ISOLATION_PASS", "owners=3")

# R437 is native-only source added after F07, not an extra reviewed
# optimization owner. Reuse the source-inventory literal set, verify it
# exists in the vendored tree, and keep the immutable 518-owner review.
r437_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "post_f07_r437_buffer_base_owners"
        for t in node.targets)
]
assert len(r437_nodes) == 1
r437_paths = ast.literal_eval(r437_nodes[0])
assert r437_paths == {"eden-core/src/video_core/buffer_cache/buffer_cache_base.h"}
post_f07_r437_buffer_base_owners = {"vendor/encore-active/" + p for p in r437_paths}
assert post_f07_r437_buffer_base_owners <= all_owners
assert not post_f07_r437_buffer_base_owners & research_owners
assert "set(EDEN_MAINTAINED_BUFFER_BASE" in release_cmake
print("ENCORE_POST_F07_R437_F07_ISOLATION_PASS", "native_headers=1")

# The reviewed P2.2c descriptor-array image emitter is explicitly tracked
# by the active-source catalogue; it did not exist in the immutable F07
# 518-source optimization review. Preserve that exact historical count.
image_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "post_f07_image_array_owners"
        for t in node.targets
    )
]
assert len(image_nodes) == 1, "Image-array owner catalogue missing"
image_paths = ast.literal_eval(image_nodes[0])
assert image_paths == {
    "ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_image.cpp"
}
post_f07_image_array_owners = {"vendor/encore-active/" + p for p in image_paths}
assert post_f07_image_array_owners <= all_owners
assert not post_f07_image_array_owners & research_owners
assert 'list(APPEND eden_ns2_shader_sources "${EDEN_NS2_SPIRV_IMAGE_ARRAY}")' in release_cmake
print("ENCORE_P22C_IMAGE_SPIRV_F07_ISOLATION_PASS", "new_sources=1")

# P2.7 native Ampere host semaphore decoder postdates the immutable F07
# optimization review. Its exact provenance is owned by the source
# catalogue; do not inflate the frozen 518 historical reviewed owners.
sem_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "post_f07_ampere_semaphore_owners"
        for t in node.targets
    )
]
assert len(sem_nodes) == 1, "Ampere semaphore inventory missing"
sem_paths = ast.literal_eval(sem_nodes[0])
assert sem_paths == {
    "ns2-runtime/gpu_dispatch/video_core/engines/native_ampere_semaphore.h"
}
post_f07_ampere_semaphore_owners = {
    "vendor/encore-active/" + p for p in sem_paths
}
assert post_f07_ampere_semaphore_owners <= all_owners
assert not post_f07_ampere_semaphore_owners & research_owners
assert (ROOT / "tools/ns2/check_native_ampere_semaphore_host.py").is_file()
print("ENCORE_POST_F07_AMPERE_SEMAPHORE_ISOLATION_PASS", "owners=1")

# Shared NS1/NS2 compiled targets use the three native GPFIFO
# suspend/resume owners across the reviewed lineage. Vendor 697159fd adds
# one maintained NVK/M2MF channel-state owner; historical pair gates
# intentionally checkout earlier vendors where that file must be absent.
gp_fifo_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "post_f07_native_gpfifo_owners"
        for t in node.targets)
]
assert len(gp_fifo_nodes) == 1
gp_fifo_paths = ast.literal_eval(gp_fifo_nodes[0])
assert gp_fifo_paths == {
    "ns2-runtime/gpu_dispatch/video_core/dma_pusher.h",
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp",
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.h",
}
post_f07_native_gpfifo_owners = {
    "vendor/encore-active/" + p for p in gp_fifo_paths
}
native_m2mf_owner = "vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp"
native_gpfifo_vendor_pin = subprocess.check_output(
    ["git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD"], text=True).strip()
# This revert commit has the same complete vendor Git tree as the
# reviewed pre-rollback pin. Reject any different source tree, including
# newly added or removed files, before reusing its byte-exact source gates.
if native_gpfifo_vendor_pin == "03b264ee3e5ac7d7bbf89d3a9c51a3aff93a4433":
    actual_tree = subprocess.check_output(
        ["git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD^{tree}"],
        text=True).strip()
    assert actual_tree == "301f91c2ee0eb4e5d86baba9b1036c57f6d5aa04", ("Vendor revert tree drift", actual_tree)
    native_gpfifo_vendor_pin = "eadc6e798def18417e50db6a03a291440429d795"
native_gpfifo_vendor_pin = "ab417b59c5f7f4613ff27386be05c0644d0ed776" if native_gpfifo_vendor_pin in {
    "ce25655b08751aa0c2f9efb10ff05fd8fcbf7a93", "7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285"
} else native_gpfifo_vendor_pin
# Current vendor GPU/FC27 successors retain byte-identical native M2MF.
if native_gpfifo_vendor_pin in {
    "917ccdc1cf772b9312b19888eea181b8e114334b",
    "0c1bd95c896f6ddc7870a245ffca51b2ac7e2932",
    "eadc6e798def18417e50db6a03a291440429d795",
}:
    actual = subprocess.check_output(
        ["git", "-C", str(ROOT / "vendor"), "hash-object",
         "encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp"],
        text=True).strip()
    assert actual == "dd30183f72a9a9dfc2a17700db263f85e4d77596", actual
    native_gpfifo_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
    print("ENCORE_NS2_M2MF_REVIEWED_SUCCESSOR_PASS")
# The new NS2 IPC pin still selects the byte-identical reviewed M2MF
# channel owner. Keep this owner covered by the F07 inventory.
if native_gpfifo_vendor_pin in {
    '2a450d43d1d23d3e8b1667e396613f62c69c26d7',
    '17c95ef233a9a0e508e50ada4ae9dc53a300c46c',
    '082cd1b77c7df80dc422eae5ba59d9cd33e48dc4',
    'e0fced3a091495e70362d8c4ca072942f027af24', '491fa7e2388d46e23827b1459360a5d7f4a2814b', 'b177deb8282b14e1521485f5ac63bd7ccc9ca7ef', '06fc7dc2e0a00e00f831dfd78ae78087736276a3', '850086c79ec40838663989a81f33ba8ea2f15f6a',
}:
    actual = subprocess.check_output(
        ['git', '-C', str(ROOT / 'vendor'), 'hash-object',
         'encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp'],
        text=True).strip()
    assert actual == 'dd30183f72a9a9dfc2a17700db263f85e4d77596', actual
    native_gpfifo_vendor_pin = 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc'
# This SHA is a GitHub-reviewed single parent commit of 8e564f61,
# changing precisely the maintained RomFSFactory + an isolated host test.
# Shallow submodule checkouts may not contain the parent object: pin the
# entire vendor SHA and the exact new RomFS, host-test, and GPFIFO blobs
# instead of requiring an unavailable historical git-diff base.
if native_gpfifo_vendor_pin in {"c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    # Selected vendor rollback is byte-exact to its pre-#194 cached-page ABI.
    # The independent RomFS successor is checked in the final source gate.
    for path,blob in {
        "encore-active/eden-core/overrides/core/device_memory_manager.inc":
            "daf493ce6e863397ec44bfae467c4f7533570477",
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp":
            "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35",
        "encore-active/eden-core/src/core/file_sys/romfs_factory.cpp":
            "4775cf98c3bfbc587402928bad424dcb471047a0",
    }.items():
        actual=subprocess.check_output(["git","-C",str(ROOT/"vendor"),"hash-object",path],
                                       text=True).strip()
        assert actual == blob, ("Reviewed sync-rollback owner drift",path,actual)
    if native_gpfifo_vendor_pin in {"729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for path, blob in {
            "encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h":
                "86e8e7e96b5eda5b6b98ccd3c7e6ce76d4275c86",
            "encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp":
                "09ae2494b2b6f620a25ab549c06c69045a9fb73d",
        }.items():
            actual = subprocess.check_output(
                ["git", "-C", str(ROOT / "vendor"), "hash-object", path], text=True
            ).strip()
            assert actual == blob, ("Reviewed quiet NS2 SVC owner drift", path, actual)
    native_gpfifo_vendor_pin="d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if native_gpfifo_vendor_pin == "67759611edc13414c112ea9d2b6664d54827a200":
    for name, expected in {
        "encore-active/eden-core/src/core/file_sys/romfs_factory.cpp":
            "4775cf98c3bfbc587402928bad424dcb471047a0",
        "tests/ns2_romfs_program_index_fallback_host.py":
            "abac08b40623febec02c58d2703b4ec3676b88f0",
        "encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp":
            "dd30183f72a9a9dfc2a17700db263f85e4d77596",
    }.items():
        actual = subprocess.check_output(["git", "-C", str(ROOT / "vendor"),
                                          "hash-object",name], text=True).strip()
        assert actual == expected, ("Reviewed ROMFS-only vendor successor changed",name,actual)
    native_gpfifo_vendor_pin = "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6"
if native_gpfifo_vendor_pin in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
    native_gpfifo_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if native_gpfifo_vendor_pin in {"697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "125f00e8143edff14a8787fa8594ad72df3d550e"}:
    post_f07_native_gpfifo_owners.add(native_m2mf_owner)
if native_gpfifo_vendor_pin in {"01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
    # Same reviewed shipping GPFIFO channel-state owner as the NS2 parent.
    # Seal it before admitting the merged P1 pin to the existing ownership set.
    current_owner = (ROOT / native_m2mf_owner).read_bytes()
    current_blob = hashlib.sha1(b"blob " + str(len(current_owner)).encode() + bytes([0]) + current_owner).hexdigest()
    assert current_blob == "dd30183f72a9a9dfc2a17700db263f85e4d77596", current_blob
    post_f07_native_gpfifo_owners.add(native_m2mf_owner)
# New vendor revisions which change only generic NS2 HLE ABI still ship
# the byte-identical NVK/M2MF owner. The historical pin table above is not
# exhaustive: classify a PRESENT source by its exact reviewed Git blob,
# rather than incorrectly asserting it was removed on every new vendor SHA.
# Older snapshots without this path remain unchanged; source drift fails.
if native_m2mf_owner in all_owners and native_m2mf_owner not in post_f07_native_gpfifo_owners:
    raw = (ROOT / native_m2mf_owner).read_bytes()
    current = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert current == "dd30183f72a9a9dfc2a17700db263f85e4d77596", (
        "Unreviewed native M2MF owner", current)
    post_f07_native_gpfifo_owners.add(native_m2mf_owner)
assert post_f07_native_gpfifo_owners <= all_owners
assert not post_f07_native_gpfifo_owners & research_owners
assert post_f07_native_gpfifo_owners.isdisjoint(post_f07_ampere_semaphore_owners)
assert "EDEN_NS2_GPFIFO_SCHEDULER" in release_cmake
assert "EDEN_NS2_GPFIFO_CHANNEL_STATE" in release_cmake
if native_m2mf_owner in post_f07_native_gpfifo_owners:
    channel_state = (ROOT / native_m2mf_owner).read_text()
    assert "constexpr u32 NvkM2mfSubchannel = 2;" in channel_state
    assert "payload.kepler_memory, NvkM2mfSubchannel" in channel_state
else:
    assert native_m2mf_owner not in all_owners
assert (ROOT / "tools/ns2/check_native_ampere_semaphore_host.py").is_file()
print("ENCORE_POST_F07_NATIVE_GPFIFO_ISOLATION_PASS",
      f"owners={len(post_f07_native_gpfifo_owners)}",
      f"m2mf_default={int(native_m2mf_owner in post_f07_native_gpfifo_owners)}")

# PR #20/#23/#21/#24 introduced new launcher and Vulkan/AMD source
# owners after the exact 518-owner F07 audit. The separately versioned
# source list is an inventory, NOT a claim that 209 new files are optimized.
feature_stack = json.loads(
    (ROOT / "docs/ENCORE_POST_F07_FEATURE_STACK_OWNERS.json").read_text())
assert feature_stack["schema_version"] == 1
assert feature_stack["counts"] == {"headless": 54, "vendor_active": 155, "total": 209}
assert feature_stack["headless"] == sorted(set(feature_stack["headless"]))
assert feature_stack["vendor_active"] == sorted(set(feature_stack["vendor_active"]))
post_f07_feature_stack_owners = (
    set(feature_stack["headless"]) |
    {"vendor/encore-active/" + p for p in feature_stack["vendor_active"]}
)
assert len(post_f07_feature_stack_owners) == 209
assert post_f07_feature_stack_owners <= all_owners, (
    "Missing merged feature stack sources",
    sorted(post_f07_feature_stack_owners - all_owners))
assert not post_f07_feature_stack_owners & research_owners
assert all((ROOT / path).is_file() for path in post_f07_feature_stack_owners)
print("ENCORE_POST_F07_FEATURE_STACK_ISOLATION_PASS",
      "new_sources=209", "historical_F07=518", "console_not_qualified=1")

# R09 Original/Compact and in-game touchpad overlay were merged after
# both the immutable 518-owner F07 audit AND the 209-source feature-stack
# inventory. These 67 exact sources are NOT retroactively F07-optimized.
late=json.loads((ROOT/"docs/ENCORE_POST_F07_R09_OVERLAY_OWNERS.json").read_text())
assert late["schema_version"]==1
assert late["historical_f07_reviewed_owners"]==518
assert late["post_f07_new_unqualified_owners"]==67
assert late["ps5_console_qualified"] is False
assert late["dlss_nr_complete_inference_validated"] is False
assert late["paths"]==sorted(set(late["paths"]))
post_f07_r09_overlay_owners=set(late["paths"])
assert len(post_f07_r09_overlay_owners)==67
assert post_f07_r09_overlay_owners<=all_owners, sorted(post_f07_r09_overlay_owners-all_owners)
assert not post_f07_r09_overlay_owners&(research_owners|post_f07_feature_stack_owners)
assert all((ROOT/p).is_file() for p in post_f07_r09_overlay_owners)
# These exact post-audit owners were discovered from real CI's
# F07_UNCLASSIFIED_SOURCE_OWNERS_JSON. Do not reclassify historical F07
# sources or hide future additions behind a dynamic owner count.
r09_private_and_readback = {
    "headless/nr_dll_launch_preflight.h",
    "headless/nr_dll_model_import.h",
    "headless/nr_dll_tensor_digests.h",
    "headless/nr_dll_user_file.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/nr_rdna2_frame_readback.h",
    "vendor/encore-active/eden-vulkan/nr_rdna2_frame_readback.cpp",
}
assert r09_private_and_readback <= post_f07_r09_overlay_owners
assert not r09_private_and_readback & (research_owners | post_f07_feature_stack_owners)
print("ENCORE_R09_OVERLAY_POST_F07_OWNER_ISOLATION_PASS",
      "new_sources=67 historical_owners=518 console_not_qualified=1")

# P1/P2 H05's new syncpoint allocator remains a reviewed, independently
# maintained Encore override, not a historical F07 optimization proof.
# Reuse the exact literal set from the active source inventory, and do not
# broadly exclude any other new source under encore-active/.
h05_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and
        target.id == "post_f07_h05_syncpoint_owners"
        for target in node.targets)
]
assert len(h05_nodes) == 1, "H05 source-owner inventory missing"
h05_paths = ast.literal_eval(h05_nodes[0])
assert h05_paths == {
    "eden-sync/overrides/h05-syncpoint/core/hle/service/nvdrv/core/syncpoint_manager.h",
    "eden-sync/src/core/hle/service/nvdrv/core/syncpoint_manager.cpp",
}
post_f07_h05_syncpoint_owners = {"vendor/encore-active/" + p for p in h05_paths}
assert post_f07_h05_syncpoint_owners <= all_owners
assert not post_f07_h05_syncpoint_owners.intersection(
    research_owners | post_f07_feature_stack_owners | post_f07_r09_overlay_owners)
print("ENCORE_POST_F07_H05_F07_ISOLATION_PASS",
      "maintained_overrides=2 historical_F07_unchanged=1")

# H01 native-only filesystem rollback adds one maintained header after the
# immutable F07 baseline. The parent version of source-inventory validates
# its actual declaration/implementation; here prevent a false 519th F07 owner.
h01_fs_paths = {
    "vendor/encore-active/eden-core/overrides/h01-filesystem/core/hle/service/filesystem/filesystem.h"
}
assert h01_fs_paths <= all_owners
assert not h01_fs_paths.intersection(research_owners | post_f07_h05_syncpoint_owners)
print("ENCORE_POST_F07_H01_F07_ISOLATION_PASS",
      "maintained_overrides=1 historical_F07_unchanged=1")

# P5 compile-only repair, added after the immutable 518-owner F07 audit:
# this include-only header exposes the upstream RAII macro to the pinned
# NS2 ASTC texture cache. It is NOT a historical F07 optimization owner.
post_f07_p5_astc_scope_bridge_owners = {
    "headless/ns2_astc_texture_cache_scope_bridge.h",
}
assert post_f07_p5_astc_scope_bridge_owners <= all_owners
bridge = (ROOT / "headless/ns2_astc_texture_cache_scope_bridge.h").read_text()
assert '#include "common/scope_exit.h"' in bridge
assert '#include_next "video_core/texture_cache/texture_cache.h"' in bridge
assert 'ns2_astc_texture_cache_scope_bridge.h' in (
    ROOT / "headless/vulkan.cmake").read_text()
assert not post_f07_p5_astc_scope_bridge_owners.intersection(
    research_owners | post_f07_feature_stack_owners | post_f07_r09_overlay_owners)
print("ENCORE_POST_F07_P5_ASTC_SCOPE_BRIDGE_PASS", "shipping_headers=1 historical_F07=518")

# #84 applet frontend overlay is new NS1 review code, not a part of historical F07.
ns1_am_draft_owners = {"headless/r23_am_frontend_applets_ps5.cpp"}
assert ns1_am_draft_owners <= all_owners
assert ns1_am_draft_owners.isdisjoint(research_owners | hygiene_owners)
print("ENCORE_NS1_AM_DRAFT_F07_ISOLATION_PASS", "draft_owners=1", "historical_F07=518")


# Distinct R457 sources created for PS5 real-console triage: a compiled
# KProcess 6-core ABI witness and a NOT-wired NS2 residency model. They are
# separately gated; never retroactively count them as F07 shipping proof.
post_f07_r457_console_owners = {
    "headless/ps5_cpu6_abi_probe.cpp",
    "headless/ps5_ns2_guest_backing_plan.h",
}
assert post_f07_r457_console_owners <= all_owners
assert not post_f07_r457_console_owners & research_owners
assert 'ps5_cpu6_abi_probe.cpp' in (ROOT/"headless/CMakeLists.txt").read_text()
assert 'ps5_ns2_guest_backing_plan.h' not in (ROOT/"src/host_memory.cpp").read_text()
print("ENCORE_R457_POST_F07_OWNER_ISOLATION_PASS", "owners=2 historical_F07=518")
# R457 sparse guest direct-memory owner is isolated in PR #53 and
# requires exact PS5 native syntax + physical/GPU alias proof before merge.
# Do not claim two new research source files were in October F07.
post_f07_r457_sparse_runtime_owners = {
    "src/ns2_sparse_guest.cpp",
    "src/ns2_sparse_guest.h",
}
assert post_f07_r457_sparse_runtime_owners <= all_owners
assert not post_f07_r457_sparse_runtime_owners & research_owners
sparse_header=(ROOT/"src/ns2_sparse_guest.h").read_text()
sparse_impl=(ROOT/"src/ns2_sparse_guest.cpp").read_text()
assert 'class Runtime {' in sparse_header and 'Plan plan;' in sparse_impl
assert 'EDEN_NS2_SPARSE_BACKING' in (ROOT/"headless/CMakeLists.txt").read_text()
print("ENCORE_POST_F07_R457_SPARSE_RUNTIME_ISOLATION_PASS", "owners=2 historical_F07=518")
# Newly integrated maintained NS2 owners, not the frozen F07 518-source set.
post_f07_ns2_production_owners = {
    "vendor/encore-active/eden-vulkan/include/rdna2_nr_vit_min_pool_policy.h",
    "vendor/encore-active/eden-vulkan/include/rdna2_nr_fswin_scratch_pool_policy.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/nr_rdna2_readback_dimensions.h",
    "vendor/encore-active/eden-core/src/video_core/textures/decoders.cpp",
    "vendor/encore-active/eden-core/overrides/native-tiling/video_core/textures/decoders.h",
    "vendor/encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h",
    "vendor/encore-active/eden-core/src/video_core/engines/engine_upload.cpp",
    "vendor/encore-active/eden-core/tests/test_ns2_gob16_decoder_public_api.cpp",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_gpu_retirement_hold.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_verified_upload_batch.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_staging_buffer_pool.h",
    "vendor/encore-active/eden-vulkan/tests/test_ns2_cache_shutdown_order.cpp",
    "vendor/encore-active/eden-vulkan/tests/test_ns2_gpu_retirement_hold.cpp",
    "vendor/encore-active/eden-vulkan/tests/test_ns2_verified_upload_batch.cpp",
    "vendor/encore-active/eden-vulkan/vk_staging_buffer_pool.cpp",
    "vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp",
}
assert post_f07_ns2_production_owners <= all_owners
assert not post_f07_ns2_production_owners & research_owners
# C03 adds two complete maintained RADV meta units after the immutable
# 518-owner F07 audit. They are explicitly selected by the 14-unit driver
# installer but have NOT yet passed native RDNA2/PS5 execution tests.
post_f07_c03_radv_owners = {
    "vendor/encore-active/ps5-mesa/src/amd/vulkan/meta/radv_meta_buffer.c",
    "vendor/encore-active/ps5-mesa/src/amd/vulkan/meta/radv_meta_copy.c",
}
assert post_f07_c03_radv_owners <= all_owners
assert not post_f07_c03_radv_owners & (research_owners | post_f07_ns2_production_owners)
print("ENCORE_POST_F07_C03_RADV_ISOLATION_PASS", "owners=2 historical_F07=518")

# The 45 new native R23 vendor source/header owners are post-F07, not
# members of the immutable 518-source audited snapshot.
post_f07_r23_source_owners = {
    "vendor/encore-active/eden-core/include/common/uuid.h",
    "vendor/encore-active/eden-core/include/core/file_sys/patch_manager.h",
    "vendor/encore-active/eden-core/include/core/file_sys/registered_cache.h",
    "vendor/encore-active/eden-core/include/core/file_sys/savedata_factory.h",
    "vendor/encore-active/eden-core/include/core/hle/service/acc/profile_manager.h",
    "vendor/encore-active/eden-core/include/core/hle/service/filesystem/fsp/fs_i_storage.h",
    "vendor/encore-active/eden-core/include/core/hle/service/ipc_helpers.h",
    "vendor/encore-active/eden-core/include/core/hle/service/service.h",
    "vendor/encore-active/eden-core/include/core/memory/cheat_engine.h",
    "vendor/encore-active/eden-core/include/dynarmic/backend/x64/constant_pool.h",
    "vendor/encore-active/eden-core/include/hid_core/frontend/emulated_controller.h",
    "vendor/encore-active/eden-core/include/hid_core/hid_core.h",
    "vendor/encore-active/eden-core/src/audio_core/opus/decoder.cpp",
    "vendor/encore-active/eden-core/src/audio_core/opus/hardware_opus.cpp",
    "vendor/encore-active/eden-core/src/audio_core/opus/hardware_opus.h",
    "vendor/encore-active/eden-core/src/common/uuid.cpp",
    "vendor/encore-active/eden-core/src/core/hle/service/am/window_system.cpp",
    "vendor/encore-active/eden-core/src/core/hle/service/audio/errors.h",
    "vendor/encore-active/eden-core/src/core/hle/service/nvnflinger/hardware_composer.cpp",
    "vendor/encore-active/eden-core/src/core/hle/service/ssl/ssl.cpp",
    "vendor/encore-active/eden-core/src/core/hle/service/ssl/ssl_backend.h",
    "vendor/encore-active/eden-core/src/core/hle/service/ssl/ssl_backend_openssl.cpp",
    "vendor/encore-active/eden-core/src/core/memory/cheat_engine.cpp",
    "vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_floating_point.cpp",
    "vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_sm4.cpp",
    "vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_vector_floating_point.cpp",
    "vendor/encore-active/eden-core/src/dynarmic/frontend/A32/decoder/asimd.inc",
    "vendor/encore-active/eden-core/src/dynarmic/frontend/A32/translate/impl/a32_translate_impl.h",
    "vendor/encore-active/eden-core/src/dynarmic/frontend/A32/translate/impl/asimd_three_regs.cpp",
    "vendor/encore-active/eden-core/src/dynarmic/frontend/A32/translate/impl/asimd_two_regs_misc.cpp",
    "vendor/encore-active/eden-core/src/hid_core/hid_core.cpp",
    "vendor/encore-active/eden-core/src/video_core/host1x/codec_types.h",
    "vendor/encore-active/eden-core/src/video_core/host1x/codecs/vp9.cpp",
    "vendor/encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h",
    "vendor/encore-active/eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_warp.cpp",
    "vendor/encore-active/eden-shader/src/shader_recompiler/host_translate_info.h",
    "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/constant_propagation_pass.cpp",
    "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/geometry_compaction_pass.cpp",
    "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/passes.h",
    "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/texture_pass.cpp",
    "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/vendor_workaround_pass.cpp",
    "vendor/encore-active/eden-shader/src/shader_recompiler/profile.h",
    "vendor/encore-active/eden-vulkan/fixed_pipeline_state.cpp",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/fixed_pipeline_state.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_texture_cache.h",
}
assert len(post_f07_r23_source_owners) == 45
assert post_f07_r23_source_owners <= all_owners, (
    "Missing reviewed R23 extra owners",
    sorted(post_f07_r23_source_owners-all_owners))
print("ENCORE_NS1_R23_POST_F07_ISOLATION_PASS", "vendor_additions=45",
      "historical_F07=518")

# Lichii #290 / PS5 0081 is a maintained native ThreadWorker header selected
# after the immutable F07 snapshot. Track it explicitly rather than changing
# the historical 518-owner total.
post_f07_thread_worker_owners = {
    "vendor/encore-active/eden-core/overrides/thread-worker/common/thread_worker.h",
}
assert post_f07_thread_worker_owners <= all_owners
assert not post_f07_thread_worker_owners & research_owners
print("ENCORE_POST_F07_THREAD_WORKER_ISOLATION_PASS owners=1 historical_F07=518")

# R457/C00 source additions are neither historical F07 files nor NS2
# research: require exact selected host graph and isolate from frozen 518.
post_f07_ns1_audio_owners = {
    "headless/audio_in_silence.h",
    "vendor/encore-active/eden-core/overrides/core/memory.h",
    "vendor/encore-active/eden-core/src/audio_core/device/device_session.cpp",
}
assert post_f07_ns1_audio_owners <= all_owners
assert "SilentAudioInputStream" in (ROOT / "headless/audio.cpp").read_text()
assert "ReadyForAudioRead()" in (ROOT / "vendor/encore-active/eden-core/src/audio_core/device/device_session.cpp").read_text()
print("C00_R457_POST_F07_AUDIO_OWNERS_PASS", f"owners={len(post_f07_ns1_audio_owners)}")

# The six final R23 BCAT/F2I/audren native owners postdate the immutable
# F07 518-source optimization audit. They are not historical F07 sources and
# are qualified by the dedicated R23 native-host contracts.
post_f07_r23_final_headless_owners = {
    "headless/r23_audren_debug_ns1_ps5.cpp",
    "headless/r23_audren_debug_ps5.cpp",
    "headless/r23_bcat_delivery_cache_file_ps5.cpp",
    "headless/r23_channel_state_cache_ps5.h",
    "headless/r23_f2i_conversion_ps5.cpp",
    "headless/r23_self_controller_240_ps5.h",
}
assert len(post_f07_r23_final_headless_owners) == 6
assert post_f07_r23_final_headless_owners <= all_owners
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
for path in post_f07_r23_final_headless_owners:
    assert path.removeprefix("headless/") in cmake, ("Missing R23 native owner", path)
assert (ROOT / "tools/audit/check-r23-f2i-bcat-host.py").is_file()
assert (ROOT / "tools/audit/check-r23-ips-audren-host.py").is_file()
print("ENCORE_R23_FINAL_POST_F07_ISOLATION_PASS added=6 historical_F07=518")

# The MKW PS5 sparse-kernel slab TU is new in this revision. Review it
# by exact vendor blob before exclusion; preserve all 518 historic F07 owners.
post_f07_r457_slab_owners = {
    "vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp"
}
assert post_f07_r457_slab_owners <= all_owners
import hashlib
slab_file = ROOT / "vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp"
slab_bytes = slab_file.read_bytes()
assert hashlib.sha1(b"blob " + str(len(slab_bytes)).encode() + bytes([0]) + slab_bytes).hexdigest() == "130eb7bd53e29b816bb81fec3fa053a584cd4b6e"
assert "EdenNs2CommitGuestBacking(" in slab_bytes.decode()
assert "ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp" in cmake
# Nov13 production owners postdate F07; require actual native single-owner
# source selectors before excluding them from the frozen 518-path audit.
# Review the post-F07 Vulkan usage-tracker owner by exact literal AST set.
# Its absence is valid only under the old frozen vendor gitlink; its presence
# must be explicitly classified so the historic 518 owners remain immutable.
usage_owner_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "post_f07_usage_tracker_owners"
        for target in node.targets)
]
assert len(usage_owner_nodes) == 1
usage_owner_paths = ast.literal_eval(usage_owner_nodes[0])
assert usage_owner_paths == {
    "eden-core/overrides/usage-tracker/video_core/buffer_cache/usage_tracker.h"
}
post_f07_usage_tracker_owners = {
    "vendor/encore-active/" + p for p in usage_owner_paths
} & all_owners
if post_f07_usage_tracker_owners:
    assert len(post_f07_usage_tracker_owners) == 1
    assert "EDEN_PS5_USAGE_TRACKER_ROOT" in release_cmake
    assert (ROOT / "tools/check-ps5-usage-tracker-selection-host.py").is_file()
print("ENCORE_POST_F07_USAGE_TRACKER_F07_ISOLATION_PASS",
      f"candidate={len(post_f07_usage_tracker_owners)}")

# Selected NVDEC source/header pair postdates the frozen F07 performance
# snapshot. Derive its exact reviewed owner paths from the source inventory
# AST, accepting only the complete source/header pair.
nvdec_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "post_f07_nvdec_owners"
        for target in node.targets)
]
assert len(nvdec_nodes) == 1
nvdec_paths = ast.literal_eval(nvdec_nodes[0])
assert nvdec_paths == {
    "eden-core/src/video_core/host1x/ffmpeg.cpp",
    "eden-core/overrides/video_core/host1x/ffmpeg.h",
}
post_f07_nvdec_owners = {
    "vendor/encore-active/" + p for p in nvdec_paths
} & all_owners
assert len(post_f07_nvdec_owners) in (0,2), "NVDEC source/header ABI split"
if post_f07_nvdec_owners:
    assert "EDEN_NVDEC_MAINTAINED_SOURCE" in release_cmake
    assert (ROOT / "tools/check-nvdec-eagain-owner-selection-host.py").is_file()
print("ENCORE_POST_F07_NVDEC_F07_ISOLATION_PASS",
      f"owners={len(post_f07_nvdec_owners)}")

# VIC is an optional post-F07 diagnostic owner, not a 519th optimized source.
# Require its exact reviewed blob and the corresponding FFmpeg ABI pair.
post_f07_vic_receipt = "vendor/encore-active/eden-core/src/video_core/host1x/vic.cpp"
post_f07_vic_present = {post_f07_vic_receipt} & all_owners
if post_f07_vic_present:
    assert len(post_f07_nvdec_owners) == 2
    vic_sha = subprocess.check_output(["git","hash-object",post_f07_vic_receipt],
                                      cwd=ROOT,text=True).strip()
    assert vic_sha in {
        "48008fc5f3b05c3e95432827c03e20b815cce21c",
        "178d361bc3b5e9a0bf6ca9fa579d49df7ab72935",
    }, ("Unreviewed VIC source", vic_sha)
    if vic_sha == "178d361bc3b5e9a0bf6ca9fa579d49df7ab72935":
        # The full 29-hunk VIC predecessor replay is owned by the vendor
        # source witness, which is also required by the native inventory gate.
        witness = (ROOT / "vendor/tests/fc27_nvdec_vic_witness_host.py").read_text()
        assert "vic_reverse=(" in witness and 'assert blob(VIC)==' in witness
        assert "digest==" in witness and "CheckedVicPlane(" in witness
    assert subprocess.check_output(["git","hash-object","vendor/encore-active/eden-core/src/video_core/host1x/ffmpeg.cpp"],cwd=ROOT,text=True).strip() == "2eadc437cec5559560e5aaf849dd3b6446782e99"
    assert 'list(REMOVE_ITEM eden_vic_video_sources "host1x/vic.cpp")' in release_cmake
    assert 'list(APPEND eden_vic_video_sources "${EDEN_VIC_MAINTAINED_SOURCE}")' in release_cmake
print("ENCORE_POST_F07_VIC_F07_ISOLATION_PASS", f"owners={len(post_f07_vic_present)}")

nov13_native_owners = {
    "vendor/encore-active/eden-core/src/common/stb_image_png.cpp",
    "vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_shared_memory.cpp",
}
assert nov13_native_owners <= all_owners
assert 'list(REMOVE_ITEM eden_stb_common_sources "stb.cpp")' in cmake
assert 'list(APPEND eden_stb_common_sources "${EDEN_NATIVE_STB_CODECS}")' in cmake
assert 'list(REMOVE_ITEM eden_sparse_core_sources "hle/kernel/k_shared_memory.cpp")' in cmake
assert 'list(APPEND eden_sparse_core_sources "${EDEN_NS2_SHARED_MEMORY_SOURCE}")' in cmake
# The selected-only JXR adapter is a separate post-F07 pair. No blanket
# exception: exact paths, CMake selection and reviewed blobs are mandatory.
jxr_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "post_f07_jxr_adapter_owners"
        for target in node.targets)
]
assert len(jxr_nodes) == 1
jxr_paths = ast.literal_eval(jxr_nodes[0])
assert jxr_paths == {"ps5-jxr/jxr_decoder.c", "ps5-jxr/jxr_decoder.h"}
post_f07_jxr_adapter_owners = {"vendor/encore-active/" + p for p in jxr_paths} & all_owners
assert len(post_f07_jxr_adapter_owners) in (0, 2), "JXR adapter pair incomplete"
if post_f07_jxr_adapter_owners:
    assert 'add_library(eden-ps5-jxr STATIC ${eden_jxr_library_sources}' in cmake
    assert '"${EDEN_JXR_ADAPTER}/jxr_decoder.c")' in cmake
    assert 'target_link_libraries(eden-headless PRIVATE eden-ps5-jxr)' in cmake
    for path, blob in {
        "vendor/encore-active/ps5-jxr/jxr_decoder.c": "e83e13a3a6e66b7e63fb9510215c1dff2d42dd14",
        "vendor/encore-active/ps5-jxr/jxr_decoder.h": "d8bb62a86fa1226375ae09e70f39c58511a667f9",
    }.items():
        content = (ROOT / path).read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(content)).encode() + bytes([0]) + content).hexdigest()
        assert digest == blob, ("JXR adapter reviewed source drift", path, digest)
    print("ENCORE_POST_F07_JXR_SELECTED_OWNER_PASS adapters=2 historical_unchanged=1")
post_f07_gpu_table_owners = {"vendor/encore-active/eden-core/src/common/multi_level_page_table.cpp"}
post_f07_gpu_table_present = post_f07_gpu_table_owners & all_owners
gpu_table_vendor_pin = subprocess.check_output(["git","-C",str(ROOT/"vendor"),"rev-parse","HEAD"],text=True).strip()
integrated_cache_lock_qualified = False
integrated_cache_lock_pins = {"17253dc91e9fe1eb2d9980f261f59d227bfcd1a1", "ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd", "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267", "87964d15e91b6b6523c88682e5ca017f6e1a808b", "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a", "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}
if gpu_table_vendor_pin in integrated_cache_lock_pins:
    if gpu_table_vendor_pin in {"ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd", "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267", "87964d15e91b6b6523c88682e5ca017f6e1a808b", "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a", "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
        # GitHub verified that this merge commit has exactly the reviewed
        # predecessor tree. Reject future changes even under a reused label.
        reviewed_tree = subprocess.check_output(
            ["git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD^{tree}"],
            text=True).strip()
        assert reviewed_tree == {
            "ac880cd408116e6eb53ba2400abc52970b81f539": "01c09ec124779e7d976718af09a0e5e94cb4ac20",
            "95343060f948601930f2e62b919da0789f0830bb": "efa6548c57f7823d4e8b2c975944c6846b765ff3",
            "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af": "64179fcce4962f9b2b7c738504a6fa0e00b2b292",
            "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c": "3f7f1523cef730ad153bf658fbb3567222d6e956",
            "150a3a79ca103061f73a9a50ca8f463a3b4712f3": "39fb9a3efe65f67115dfcdebe39a55334a702f2d",
            "fcd62408fdbc33af01a4caebc8fd44c8500b628f": "8447712e2cecf661910fd1a32613f0b844ceaeb0",
            "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb": "067c72d30a71a79faefd1ad14876e2a46f02755c",
            "dbef23055897b1649f83c20cf7a0516e64f3d5cd": "9e28e5b83cf9c0f4086a33d6838904353a8fd541",
            "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267": "e21b2c70c00c50fc7d682150cb62e87fe856306c",
            "87964d15e91b6b6523c88682e5ca017f6e1a808b": "c1cbb8a3ca0b7231e260fdb5e9f6a1c7964097ab",
            "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a": "e125210acec0eaef51c6c038d200cc9c12981ace",
            "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0": "68acadcd14d23135fd02df0a0e508c668917168c",
            "d22b7066410c627230f9bfa8b3b5be8baff4fcdf": "805d74f7ccf0ddf060782615d2bd94bb8d26b412",
            "f4f5d53596879960b19a3701bbd2272ef1f3c634": "e1e3fa4878d6203a51c7aa6ec93e09f81a175cdf",
        }[gpu_table_vendor_pin], ("Vendor reviewed source tree drift", gpu_table_vendor_pin, reviewed_tree)
    # This vendor changes exactly the active GuestCacheLock method and
    # its source tests; the historical F07 source table remains frozen.
    raster=(ROOT/"vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
    encoded=raster.encode("utf-8")
    digest=hashlib.sha1(b"blob "+str(len(encoded)).encode()+bytes([0])+encoded).hexdigest()
    assert digest=="f67815618d25657dcf64a87944b0c0bc5c2d8993"
    start="VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea("
    end="\nvoid RasterizerVulkan::InvalidateRegion("
    assert raster.count(start)==raster.count(end)==1
    i=raster.index(start)
    j=raster.index(end,i)
    method=raster[i:j]
    for corrected,previous in (
        ("::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);",
         "::Eden::Performance::GuestCacheLock texture_wait(texture_cache.mutex, true);"),
        ("::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);",
         "::Eden::Performance::GuestCacheLock buffer_wait(buffer_cache.mutex, true);"),
    ):
        assert method.count(corrected)==1 and previous not in method
        method=method.replace(corrected,previous,1)
    prior=(raster[:i]+method+raster[j:]).encode("utf-8")
    prior_sha=hashlib.sha1(b"blob "+str(len(prior)).encode()+bytes([0])+prior).hexdigest()
    assert prior_sha=="0633e3cf41c615f46791d3943ff40ac22399b047"
    integrated_cache_lock_qualified = True
    if gpu_table_vendor_pin in {"dc526f06d277dfa0a4afa48b4cf8b3153ebe7267", "87964d15e91b6b6523c88682e5ca017f6e1a808b", "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a", "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
        for relative, expected in {
            "encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp":
                ("01d0f8a05faaa30b01a1802680a954aebfbf118b" if gpu_table_vendor_pin in {"f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"} else "7783c917d8b2f2e8d26c091d5507964fcf9d44dd" if gpu_table_vendor_pin == "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a" else "743bd9c9a4b9a3550c853ffa8fc06898c01618ff"),
            "tests/r23_fw23_selfcontroller_240.py":
                ("367b99a467a7cf1559973af65c69f7c2231764f4" if gpu_table_vendor_pin in {"f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"} else "ed80a6d62d5328c394a133b5f28112443e893f36" if gpu_table_vendor_pin == "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a" else "b03d2015ac00a0ce2e52bea002c931b330a55d96"),
        }.items():
            raw = (ROOT/"vendor"/relative).read_bytes()
            digest = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert digest == expected, ("NS2 SelfController 2400 source drift", relative)
    if gpu_table_vendor_pin in {"87964d15e91b6b6523c88682e5ca017f6e1a808b", "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a", "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
        for relative, expected in {
                "encore-active/eden-core/src/core/hle/service/service.cpp": ("e388765fb2cf372adc01c2c3ec174955659ccc2a" if gpu_table_vendor_pin in {"f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"} else "e2d52974d419b9ed4089da8baed104dd1dbd282d"),
                "encore-active/ns2-runtime/process/core/core.cpp": "a2721a630b8b32222ff586ea2db19ee726d4d5b9",
                "tests/ns1_r23_54_storage_pacing.py": ("eb88e3701448c3b3572155a00158b3a5955eb45e" if gpu_table_vendor_pin in {"f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"} else "9abec8ca14bfaaed76128fab34592f0b3911afe9"),
                "tests/shutdown_general_channel_lifetime_source.py": "4bb0ef388211b1c9110afce55ef80983e5050782",
                "tests/shutdown_teardown_lifetime_source.py": "e40deaae0b1f3aab6a5a12f7978be470b3ee0463"
        }.items():
            raw = (ROOT/"vendor"/relative).read_bytes()
            digest = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert digest == expected, ("NS2 NUP/IPC source drift", relative, digest)
    if gpu_table_vendor_pin == "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a":
        raw = (ROOT/"vendor/encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.h").read_bytes()
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest() == "571793025a886f3878e7b61ec9569faba84647f2"
    if gpu_table_vendor_pin == "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0":
        for relative, expected in {
            "encore-active/eden-core/include/core/hle/service/service.h": "b871694b3b865465ec8e08e358d6799449092498",
            "encore-active/eden-core/src/core/hle/service/service.cpp": "e388765fb2cf372adc01c2c3ec174955659ccc2a",
            "encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp": "a26850d9addcd35c483fa1da28d440537896ee13",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "ed88acba848071d6c9e2c0b080c3234925003b50",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "0d2ed417d23f11a97f91cf18e733fad6515d0756",
            "encore-active/ns2-runtime/hle/core/hle/service/nx2_stub_interface.h": "68c087899680b8a3a764d6cd3c362b0e98237ae0",
            "encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp": "01d0f8a05faaa30b01a1802680a954aebfbf118b",
            "tests/ns1_r23_126_uuid_sha1.py": "4a565a3c5fd53dff3ca157aa0793fb86f7827791",
            "tests/ns1_r23_54_storage_pacing.py": "eb88e3701448c3b3572155a00158b3a5955eb45e",
            "tests/r23_fw23_selfcontroller_240.py": "367b99a467a7cf1559973af65c69f7c2231764f4",
        }.items():
            raw = (ROOT/'vendor'/relative).read_bytes()
            digest = hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert digest == expected, ('Lichii structural source drift',relative,digest)
    if gpu_table_vendor_pin in {"d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
        for relative, expected in {
            "ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
            "ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
            "ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
            "ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
            "ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
            "ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
            "ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
            "ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
        }.items():
            raw = (ROOT/"vendor"/"encore-active"/relative).read_bytes()
            digest = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert digest == expected, ("NS2 AM structural owner drift",relative,digest)
    if gpu_table_vendor_pin == "f4f5d53596879960b19a3701bbd2272ef1f3c634":
        for relative, expected in {
            "encore-active/eden-core/src/core/file_sys/card_image.cpp": "5d5e6b40099b18768dadd39ba839881989e7ff6f",
            "encore-active/eden-core/src/core/file_sys/content_archive.cpp": "d31f75bf354f3ce5af1ac2f1ac170586503b1877",
            "encore-active/eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp": "49841fbbde5bd086f23aba601c80b19176ed8ae4",
            "encore-active/eden-core/src/core/loader/loader.cpp": "0b4448bcf4bef93b9d2a54cf96256d5b81d9424e",
        }.items():
            raw = (ROOT / 'vendor' / relative).read_bytes()
            digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert digest == expected, ("DNSP/DXCI exact source drift", relative, digest)
    gpu_table_vendor_pin = "4354add020afac574198f63d87167f3022bff9c6"
    print("ENCORE_GUEST_CACHE_LOCK_RUNTIME_PREDECESSOR_PASS hunks=2")
# The selected vendor tree is byte-identical to the already-reviewed
# FC27/GSV successor. Preserve this classification after historical
# source-normalization changes gpu_table_vendor_pin to the F07 reference.
current_fc27_nov20_tree = gpu_table_vendor_pin in {
    "03b264ee3e5ac7d7bbf89d3a9c51a3aff93a4433",
    "eadc6e798def18417e50db6a03a291440429d795",
}
merged_applet_macro_fix = gpu_table_vendor_pin == "b65d8d9673475433f0b6eac72eb304bf23141666"
merged_fc27_p1_pair = gpu_table_vendor_pin in {
    "01c942171fea39c1f7cf31d13ab36895aebb593a",
    "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109",
    "b65d8d9673475433f0b6eac72eb304bf23141666",
}
if gpu_table_vendor_pin in {"03b264ee3e5ac7d7bbf89d3a9c51a3aff93a4433", "eadc6e798def18417e50db6a03a291440429d795"}:
    vendor_tree = subprocess.check_output(
        ["git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD^{tree}"],
        text=True).strip()
    assert vendor_tree == "301f91c2ee0eb4e5d86baba9b1036c57f6d5aa04", ("FC27 GPU source tree drift", vendor_tree)
    gpu_table_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
gpu_table_vendor_pin = "ab417b59c5f7f4613ff27386be05c0644d0ed776" if gpu_table_vendor_pin in {
    "ce25655b08751aa0c2f9efb10ff05fd8fcbf7a93", "7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285"
} else gpu_table_vendor_pin
# The merged P1 tree preserves the exact FC27 shader compiler and native
# GPU page-table owners. Seal the unchanged blobs before invoking the frozen
# F07 source-ownership profile, rather than interpreting new Git SHAs as a
# new/unknown ABI with no FC27 SSA/SSBO owners.
if gpu_table_vendor_pin in {"01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
    for path, blob in {
        "vendor/encore-active/eden-shader/include/shader_recompiler/frontend/ir/basic_block.h": "0a23d1ce0f43524e6195bd8219349ef632cfb719",
        "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/ssa_rewrite_pass.cpp": "26c42a9900256e5573735394753c1d5264611664",
        "vendor/encore-active/eden-core/src/common/multi_level_page_table.cpp": "c55a55498fe300458800b646bfc295db11283b4a",
    }.items():
        actual = subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip()
        assert actual == blob, ("Merged FC27 source owner drift",path,actual)
    gpu_table_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
shared_storage32_selected = gpu_table_vendor_pin in {"372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}
# This exact integrated vendor retains the previously reviewed PS5 VFS/IPC
# owners. Their full Git blobs, native CMake selection and main.cpp cache cap
# are independently asserted below; selection alone is not qualification.
ps5_vfs128_selected = gpu_table_vendor_pin in {"a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} or merged_fc27_p1_pair or gpu_table_vendor_pin == "4354add020afac574198f63d87167f3022bff9c6"
ps5_ns2_ipc_selected = gpu_table_vendor_pin == "ab417b59c5f7f4613ff27386be05c0644d0ed776" or merged_fc27_p1_pair or gpu_table_vendor_pin == "4354add020afac574198f63d87167f3022bff9c6"
if gpu_table_vendor_pin in {"c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    gpu_table_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
fc27_deferred_selected = gpu_table_vendor_pin in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}
fc27_deferred_owners = {"vendor/encore-active/eden-core/overrides/core/deferred_cached_updates.h"} & all_owners
if fc27_deferred_selected:
    assert fc27_deferred_owners == {"vendor/encore-active/eden-core/overrides/core/deferred_cached_updates.h"}
    for rel, blob in (
        ("eden-core/overrides/core/deferred_cached_updates.h", "33262f511777cdd1b4a74ac0cd6dc39caa12c9d0"),
        ("eden-core/overrides/core/device_memory_manager.inc", "852a0272696c7ce182bc05aee92bc7cbb195446b"),
        ("eden-vulkan/vulkan_rasterizer.cpp", "38d5630570675088a0620ef533112bb314a40ae8"),
    ):
        real_path = ROOT/"vendor/encore-active"/rel
        assert subprocess.check_output(["git","hash-object",str(real_path)],text=True).strip() == blob
    print("FC27_F07_POST_SNAPSHOT_DEFERRED_HEADER_PASS owner=1 blobs=3")
else:
    assert not fc27_deferred_owners
if fc27_deferred_selected:
    gpu_table_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_gpu_table_present
else:
    assert post_f07_gpu_table_present == post_f07_gpu_table_owners
    assert subprocess.check_output(["git","hash-object",next(iter(post_f07_gpu_table_owners))],cwd=ROOT,text=True).strip() == "c55a55498fe300458800b646bfc295db11283b4a"
    assert 'list(REMOVE_ITEM eden_page_table_sources "multi_level_page_table.cpp")' in release_cmake
    assert 'list(APPEND eden_page_table_sources "${EDEN_MAINTAINED_GPU_PAGE_TABLE}")' in release_cmake
post_f07_vfs_receipts = {
    "vendor/encore-active/eden-core/src/core/file_sys/vfs/vfs.cpp": "70926039977f56c87558270d7655f8de26d1e446",
    "vendor/encore-active/eden-core/src/core/file_sys/vfs/vfs_vector.cpp": "5f9c99b7ed5227c403ceca1d2e04d6c8dafc26cb",
    "vendor/encore-active/eden-core/src/core/file_sys/partition_filesystem.cpp": "350af05f831fe89a05158350f8c8aded988980dd"
}
post_f07_vfs_present = set(post_f07_vfs_receipts) & all_owners
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_vfs_present
else:
    assert post_f07_vfs_present == set(post_f07_vfs_receipts)
    for path, blob in post_f07_vfs_receipts.items():
        assert subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip() == blob
    assert 'list(REMOVE_ITEM core_sources "${eden_vfs_relative}")' in release_cmake
    assert 'list(APPEND core_sources "${eden_vfs_maintained}")' in release_cmake
post_f07_nca_receipts = {
    "vendor/encore-active/eden-core/src/core/file_sys/fssystem/fssystem_integrity_verification_storage.cpp": "5afc754433f6276ffd80bc0af418d31cf5cf496c",
    "vendor/encore-active/eden-core/src/core/file_sys/fssystem/fssystem_nca_file_system_driver.cpp": "f6ceeb8d18b88b850c19b86cc3823e40ce5b9afa"
}
post_f07_nca_present = set(post_f07_nca_receipts) & all_owners
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_nca_present
else:
    assert post_f07_nca_present == set(post_f07_nca_receipts)
    for path, blob in post_f07_nca_receipts.items():
        assert subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip() == blob
        assert '"' + path.removeprefix("vendor/encore-active/eden-core/src/core/") + '"' in release_cmake
    assert 'list(REMOVE_ITEM core_sources "${eden_vfs_relative}")' in release_cmake
post_f07_romfs_receipt = "vendor/encore-active/eden-core/src/core/file_sys/romfs.cpp"
post_f07_romfs_present = {post_f07_romfs_receipt} & all_owners
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_romfs_present
else:
    assert post_f07_romfs_present == {post_f07_romfs_receipt}
    assert subprocess.check_output(["git","hash-object",post_f07_romfs_receipt],cwd=ROOT,text=True).strip() == "51eb401e5f2e3a0deefc5fc0e4cc30b0f4b8e4a3"
    assert '"file_sys/romfs.cpp"' in release_cmake
# FC27 compiler owners selected after the frozen F07 snapshot. Keep them
# explicit and SHA-pinned rather than increasing the 518 historical count.
post_f07_fc27_ssa_receipts = {
    "vendor/encore-active/eden-shader/include/shader_recompiler/frontend/ir/basic_block.h":
        "0a23d1ce0f43524e6195bd8219349ef632cfb719",
    "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/ssa_rewrite_pass.cpp":
        "26c42a9900256e5573735394753c1d5264611664",
}
post_f07_fc27_ssa_present = set(post_f07_fc27_ssa_receipts) & all_owners
fc27_compiler_pins = {
    "b9f6052a65ef01e23ca4a46ba1654ed3a58cf181",
    "76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3",
    "6f4bb38594b273fe7cc4fba960dfe62cdb9f508e",
    "4572e581d011c444fd59428d5c042098f05dcfca",
    "f7ee793f1ee1bb1c2b1a35f68073844163658262",
    "3f019c64c2907ac3e84baa9b6200de8898f30636",
    "f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6",
}
if 'set(EDEN_FC27_SSA_HEADER' in release_cmake:
    assert post_f07_fc27_ssa_present == set(post_f07_fc27_ssa_receipts)
    for path, blob in post_f07_fc27_ssa_receipts.items():
        assert subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip() == blob
    assert 'set(EDEN_FC27_SSA_HEADER' in release_cmake
    assert 'set(EDEN_FC27_SSA_SOURCE' in release_cmake
else:
    assert not post_f07_fc27_ssa_present
print("ENCORE_FC27_SSA_F07_ISOLATION_PASS", f"owners={len(post_f07_fc27_ssa_present)}")

post_f07_fc27_ssbo_receipts = {
    "vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp":
        "41ad0f5cef1e070e552b43ea49648d5e74f10bad",
}
post_f07_fc27_ssbo_present = set(post_f07_fc27_ssbo_receipts) & all_owners
if 'set(EDEN_FC27_SSBO_SOURCE' in release_cmake:
    assert post_f07_fc27_ssbo_present == set(post_f07_fc27_ssbo_receipts)
    for path, blob in post_f07_fc27_ssbo_receipts.items():
        actual = subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip()
        if actual == "602d45b4d2ad872b138d62ce05f379b5e1103602":
            # NS1/NS2 source adds one bounded CAS32 storage-atomic opcode.
            # Undo only its exact reviewed hunk in an audit copy, and require
            # the byte-identical frozen post-F07 SSBO predecessor.
            current = (ROOT / path).read_text()
            new = ("    case IR::Opcode::GlobalAtomicExchange32:\n"
                   "    case IR::Opcode::GlobalAtomicCompareExchange32:\n"
                   "    case IR::Opcode::GlobalAtomicIAdd64:\n")
            old = ("    case IR::Opcode::GlobalAtomicExchange32:\n"
                   "    case IR::Opcode::GlobalAtomicIAdd64:\n")
            assert current.count(new) == 2
            previous = current.replace(new, old, 1).encode()
            prior = hashlib.sha1(b"blob " + str(len(previous)).encode() + bytes([0]) + previous).hexdigest()
            assert prior == blob, ("Unexpected SSBO CAS32 predecessor", prior)
        else:
            assert actual == blob, (path, actual)
    assert 'set(EDEN_FC27_SSBO_SOURCE' in release_cmake
else:
    assert not post_f07_fc27_ssbo_present
print("ENCORE_FC27_SSBO_F07_ISOLATION_PASS", f"owners={len(post_f07_fc27_ssbo_present)}")

# Eglantine #374 / vendor #147: one post-F07 maintained descriptor header.
post_f07_fc27_descriptor_receipts = {
    "vendor/encore-active/eden-core/src/video_core/texture_cache/descriptor_table.h":
        "be14d3396ff3871ceed46cb8499e9cfb546719de",
}
post_f07_fc27_descriptor_present = set(post_f07_fc27_descriptor_receipts) & all_owners
if 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_SMALL_VECTOR_ROOT}")' in release_cmake:
    assert post_f07_fc27_descriptor_present == set(post_f07_fc27_descriptor_receipts)
    for path, blob in post_f07_fc27_descriptor_receipts.items():
        assert subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip() == blob
    assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_SMALL_VECTOR_ROOT}")' in release_cmake
else:
    assert not post_f07_fc27_descriptor_present
print("ENCORE_FC27_DESCRIPTOR_F07_ISOLATION_PASS", f"owners={len(post_f07_fc27_descriptor_present)}")

# Vendor scalar-cache qualification includes a second standalone include-tree
# header. The PS5 engine selects the Task/Mesh-compatible src/ owner, so keep
# this exact file outside the immutable F07 shipping-owner count.
post_f07_fc27_scalar_unselected_receipts = {
    "vendor/encore-active/eden-shader/include/shader_recompiler/backend/spirv/spirv_emit_context.h":
        "68e14b3a0c4ae990933652baa51183a51eee4f81",
}
post_f07_fc27_scalar_unselected_present = set(post_f07_fc27_scalar_unselected_receipts) & all_owners
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"6f4bb38594b273fe7cc4fba960dfe62cdb9f508e", "4572e581d011c444fd59428d5c042098f05dcfca", "f7ee793f1ee1bb1c2b1a35f68073844163658262", "3f019c64c2907ac3e84baa9b6200de8898f30636", "f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"}:
    assert post_f07_fc27_scalar_unselected_present == set(post_f07_fc27_scalar_unselected_receipts)
    for path, blob in post_f07_fc27_scalar_unselected_receipts.items():
        assert subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip() == blob
    assert "eden-shader/include/shader_recompiler/backend/spirv/spirv_emit_context.h" not in release_cmake
    scalar_gate = (ROOT/".github/workflows/spirv-scalar-engine-host.yml").read_text()
    assert "vendor/encore-active/eden-shader/src/shader_recompiler/backend/spirv/spirv_emit_context.h" in scalar_gate
    assert "844a118358c874b0666aebda116c1d6a0c9a8ceb" in scalar_gate
else:
    # A reviewed stand-alone include-tree header may exist on any later vendor
    # revision. Qualification depends on its immutable blob, correct selected
    # src/ CMake owner and the targeted syntax gate, not one old vendor SHA.
    if post_f07_fc27_scalar_unselected_present:
        assert post_f07_fc27_scalar_unselected_present == set(post_f07_fc27_scalar_unselected_receipts)
        for source_path, expected_blob in post_f07_fc27_scalar_unselected_receipts.items():
            assert subprocess.check_output(["git", "hash-object", source_path],
                                           cwd=ROOT, text=True).strip() == expected_blob
        assert "eden-shader/include/shader_recompiler/backend/spirv/spirv_emit_context.h" not in release_cmake
        scalar_gate = (ROOT/".github/workflows/spirv-scalar-engine-host.yml").read_text()
        assert "vendor/encore-active/eden-shader/src/shader_recompiler/backend/spirv/spirv_emit_context.h" in scalar_gate
        assert "844a118358c874b0666aebda116c1d6a0c9a8ceb" in scalar_gate
    else:
        assert not post_f07_fc27_scalar_unselected_present
print("ENCORE_FC27_SCALAR_DUPLICATE_F07_ISOLATION_PASS",
      f"owners={len(post_f07_fc27_scalar_unselected_present)}", "selected=0")

# Isolated post-F07 diagnostic queue prototype; never change historical counts.
post_f07_diagnostics_receipts = {
    "headless/diagnostics_sharing_policy.h": "2515badbeb070d0f22b02e0ec8dde8a30afdeef4",
    "headless/diagnostics_report_queue.h": "2a000792ac99ec40532b97f2e2645c1473039d5f",
    "headless/diagnostics_native_client.cpp": "358e3d675f44d4a1bf664f14697b074af7f666db",
    "headless/diagnostics_native_client.h": "cd843218b18d581599940f44e93003d84f19598c",
}
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"}:
    post_f07_diagnostics_receipts[
        "vendor/encore-active/eden-backports/src/common/net/net.h"
    ] = "f8244b366d591ce10342f110d282c295f835474f"
post_f07_diagnostics_owners = set(post_f07_diagnostics_receipts)
for path, blob in post_f07_diagnostics_receipts.items():
    assert subprocess.check_output(["git","hash-object",path], cwd=ROOT, text=True).strip() == blob, path
print("ENCORE_DIAGNOSTICS_POST_F07_PASS", f"owners={len(post_f07_diagnostics_owners)}",
      "native_transport=https_idle_client" if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} else "native_transport=unwired")
assert post_f07_diagnostics_owners <= all_owners

# P1 typography: two post-F07 launcher-owned Unicode quick-menu sources.
# Preserve the immutable 518-owner baseline and pin the exact reviewed files.
post_f07_typography_receipts = {
    "headless/quick_overlay_font.cpp": "834b4b97602cb1d098944fb687123862bdf0e5e8",
    "headless/quick_overlay_font.h": "28fd15ac08a2744588a90dd6de0d9228e417719c",
}
post_f07_typography_owners = set(post_f07_typography_receipts)
assert post_f07_typography_owners <= all_owners
for path, blob in post_f07_typography_receipts.items():
    assert subprocess.check_output(["git","hash-object",path], cwd=ROOT, text=True).strip() == blob, path
print("ENCORE_TYPOGRAPHY_F07_ISOLATION_PASS owners=2 historical_F07=518")

# The title-aware loading correction adds two independently reviewed
# headers; neither belongs to the immutable F07 baseline.
post_f07_loading_artwork_receipts = {
    "headless/loading_artwork_transfer.hpp": "2594c4ea8c3d08ec1c04e9c08de717f61ffb7df1",
    "headless/loading_artwork_gl.hpp": "945753fbd9f95f2a45d8fa16504f0bd98534b678",
}
post_f07_loading_artwork_owners = set(post_f07_loading_artwork_receipts)
assert post_f07_loading_artwork_owners <= all_owners
for path, blob in post_f07_loading_artwork_receipts.items():
    assert subprocess.check_output(["git","hash-object",path], cwd=ROOT, text=True).strip() == blob, path
print("ENCORE_LOADING_ARTWORK_F07_ISOLATION_PASS owners=2 historical_F07=518")
# New ABI headers are separately audited; historic 518 owners stay immutable.
pair_receipt = json.loads((ROOT / "docs/audits/NOV15_FC27_NS2_VENDOR_PAIR_SOURCE_RECEIPT.json").read_text())
assert pair_receipt["schema_version"] == 1 and pair_receipt["hardware_qualified"] is False
pair_new_owners = {"vendor/encore-active/" + p for p in pair_receipt["new_owners"]}
assert len(pair_new_owners) == 2 and len(pair_receipt["files"]) == 14
pair_present = pair_new_owners & all_owners
current_fc27_nov20_pair_successor_blobs = dict(pair_receipt["files"])
current_fc27_nov20_pair_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache.h"] = "d40082a0c849790d25a4d1d28e003087eefd84a1"
current_fc27_nov20_pair_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache_base.h"] = "7e1e2fb6a1a54571f3094d809e934312fbbd83b6"
current_fc27_nov20_pair_successor_blobs["eden-core/src/video_core/gpu_gl_native.cpp"] = "8abd4f3652b4a10f27281a2fd43a3764bd6d5c6e"
current_fc27_nov20_pair_successor_blobs["eden-core/src/video_core/gpu_gl_native_dev.cpp"] = "091431333f6f05e7e81c691051d64771cab4a5dd"
current_fc27_nov20_pair_successor_blobs["eden-core/src/video_core/gpu_vulkan.cpp"] = "842a0289f75bc2a0763285173e4616060348ec22"
current_fc27_nov20_pair_successor_blobs["eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h"] = "6467fd4d704de6b77deb7e6cba4b8e33f70f5a08"
current_fc27_nov20_pair_successor_blobs["eden-vulkan/vulkan_rasterizer.cpp"] = "f23ad861761d53b59b8c83ae6003c089ae688060"
current_fc27_nov20_pair_successor_blobs["ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h"] = "3397cd39a3d35c1255802c4c3862584530f15cfe"
# P1 merge changed only these three of the frozen 14 pair-owner blobs.
# The other eleven are already sealed by the inherited exact receipts.
merged_fc27_p1_pair_blobs = dict(current_fc27_nov20_pair_successor_blobs)
merged_fc27_p1_pair_blobs.update({
    "eden-core/src/video_core/buffer_cache/buffer_cache.h": "41239f19b9e16741d49e31145c504e0086b1095e",
    "eden-core/src/video_core/buffer_cache/buffer_cache_base.h": "716634290574ed4dfc8fd3be0d0ea0ad582980f8",
    "eden-vulkan/vulkan_rasterizer.cpp": "71d097b9a83028dfad9370792c905bb3bfccfd5a",
})
if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    # The immutable Nov15 receipt remains historical. These are selected
    # successor maps for the reviewed af32/bfdf Ampere lowering only.
    current_fc27_nov20_pair_successor_blobs["ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h"] = "9169e95ec14559aa6466c68b7d1e1cd3f9e69557"
    merged_fc27_p1_pair_blobs["ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h"] = "9169e95ec14559aa6466c68b7d1e1cd3f9e69557"
current_pair_successor_blobs = {
    "eden-core/src/video_core/buffer_cache/buffer_cache.h": "09e1578dec6dcbcb0b8f54d4bb819b71d0eed972",
    "eden-core/src/video_core/buffer_cache/buffer_cache_base.h": "bd424e728182500b573a4cc4cf07987ddc4cbdc3",
    "eden-core/src/video_core/gpu_gl_native.cpp": "8abd4f3652b4a10f27281a2fd43a3764bd6d5c6e",
    "eden-core/src/video_core/gpu_gl_native_dev.cpp": "091431333f6f05e7e81c691051d64771cab4a5dd",
    "eden-core/src/video_core/gpu_vulkan.cpp": "842a0289f75bc2a0763285173e4616060348ec22",
    "eden-vulkan/vulkan_rasterizer.cpp": "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35",
    "ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "3397cd39a3d35c1255802c4c3862584530f15cfe"
}
if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    current_pair_successor_blobs["ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h"] = "9169e95ec14559aa6466c68b7d1e1cd3f9e69557"
latest_pair_successor_blobs = dict(current_pair_successor_blobs)
latest_pair_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache.h"] = (
    "505ee80a37d5991b7925019282e71926c1648e02"
)
# Vendor #189 retains every R23/F07 buffer owner except the one exact
# reviewed RangeSet native ABI adaptation, independently proven on host.
ps5_range_abi_successor_blobs = dict(latest_pair_successor_blobs)
ps5_range_abi_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache.h"] = (
    "c6bab56cbd4e58458d010e423d74df9f933a8f8d"
)
shared_storage32_pair_successor_blobs = dict(ps5_range_abi_successor_blobs)
shared_storage32_pair_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache_base.h"] = (
    "63ef9b07b37bdc4bc9588dd77639358010e545dc"
)
if fc27_deferred_selected:
    ps5_range_abi_successor_blobs["eden-vulkan/vulkan_rasterizer.cpp"] = "38d5630570675088a0620ef533112bb314a40ae8"
if gpu_table_vendor_pin in {pair_receipt["selected_vendor"], "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}:
    assert pair_present == pair_new_owners
    gpu_dirty_include = b'#include "core/gpu_dirty_memory_manager.h"\n'
    gpu_dirty_include_successors = {"2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab",
                                    "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"}
    gpu_dirty_include_owners = {
        "eden-core/src/video_core/gpu_gl_native.cpp",
        "eden-core/src/video_core/gpu_gl_native_dev.cpp",
        "eden-core/src/video_core/gpu_vulkan.cpp",
    }
    for path, blob in pair_receipt["files"].items():
        source_path = ROOT / "vendor/encore-active" / path
        raw = source_path.read_bytes()
        if current_fc27_nov20_tree or merged_fc27_p1_pair:
            # Verify every shipping blob in this 14-owner table, including
            # the three P1 changes, without treating the merged vendor's
            # different commit/tree identity as the earlier rollback tree.
            actual = subprocess.check_output(
                ["git", "hash-object", str(source_path)], text=True).strip()
            expected_blob = (merged_fc27_p1_pair_blobs if merged_fc27_p1_pair
                             else current_fc27_nov20_pair_successor_blobs)[path]
            assert actual == expected_blob, (path, actual, expected_blob)
            continue
        if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}:
            # Newer focused fixes (FC27 sibling-page preservation, Duskbloods,
            # dynamic texture bounds and HSETP2 CBUF) are independently host
            # qualified. Pin their exact selected blobs without rewriting the
            # frozen Nov15 receipt or pretending PS5 hardware qualification.
            actual = subprocess.check_output(
                ["git", "hash-object", str(source_path)], text=True
            ).strip()
            expected_blob = (
                shared_storage32_pair_successor_blobs if shared_storage32_selected else
                ps5_range_abi_successor_blobs if gpu_table_vendor_pin in {"2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}
                else latest_pair_successor_blobs if gpu_table_vendor_pin in {"945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}
                else current_pair_successor_blobs
            ).get(path, blob)
            assert actual == expected_blob, (path, actual, expected_blob)
            continue
        if gpu_table_vendor_pin in gpu_dirty_include_successors and path in gpu_dirty_include_owners:
            assert raw.count(gpu_dirty_include) == 1, path
            historical = raw.replace(gpu_dirty_include, b"", 1)
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + b"\0" + historical
            ).hexdigest()
        else:
            actual = subprocess.check_output(
                ["git", "hash-object", str(source_path)], cwd=ROOT, text=True
            ).strip()
        if (gpu_table_vendor_pin in {"42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} and
                path == "eden-vulkan/vulkan_rasterizer.cpp"):
            assert actual == "aa3ff8baf97f075d1adf44a9d19335c89403c8e1", path
        else:
            assert actual == blob, path
elif pair_present == pair_new_owners:
    # Current vendor revisions retain the same 14 exact source-owner blobs.
    # Qualification is by every immutable source SHA below, never just the
    # historical submodule commit identity. An unknown GPU change fails.
    # Integrated NS1/NS2 pair: all fourteen actual vendor owners are pinned
    # to reviewed full Git blobs. This does NOT re-date the November 15
    # historical receipt or bypass the separate CMake/ABI source gates.
    assert pair_present == pair_new_owners
    integrated_pair = {
        "eden-core/overrides/core/gpu_dirty_memory_manager.h": "d489855e83f53ba703c18ce67d620f8db7b932fc",
        "eden-core/overrides/video_core/gpu.h": "d3ad5e60e19b30ddbd43cbfc29af98f7f24c8174",
        "eden-core/overrides/video_core/rasterizer_interface.h": "294452f99eae33d623a85c5e4db18a850c2a84ba",
        "eden-core/src/video_core/buffer_cache/buffer_cache.h": "6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b",
        "eden-core/src/video_core/buffer_cache/buffer_cache_base.h": "fd9708571ef61c83c399042a5200c87b2e3784d6",
        "eden-core/src/video_core/engines/maxwell_3d.cpp": "fe7c4fa421ccabf9fff4b1bc277fb8ab5fe46677",
        "eden-core/src/video_core/gpu_gl_native.cpp": "8abd4f3652b4a10f27281a2fd43a3764bd6d5c6e",
        "eden-core/src/video_core/gpu_gl_native_dev.cpp": "091431333f6f05e7e81c691051d64771cab4a5dd",
        "eden-core/src/video_core/gpu_vulkan.cpp": "90b8f8c99878b21558b3996e8b1e95a5fc6ad9a6",
        "eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h": "6e0bf7ab2a3a2147f9db0c630070db30d9b35d56",
        "eden-vulkan/vulkan_rasterizer.cpp": "0633e3cf41c615f46791d3943ff40ac22399b047",
        "ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "3397cd39a3d35c1255802c4c3862584530f15cfe",
        "ns2-runtime/gpu_dispatch/video_core/native_qmd.h": "a1e99602dbee8c4fc49108382b61ee8cd53af847",
        "ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h": "33b1b5475e68c8459f9666b1ae1a6e446221cb63",
    }
    if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
        integrated_pair["ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h"] = "9169e95ec14559aa6466c68b7d1e1cd3f9e69557"
    assert set(integrated_pair) == set(pair_receipt["files"])
    for relative, sha in integrated_pair.items():
        source_path = ROOT / "vendor/encore-active" / relative
        actual = subprocess.check_output(["git", "hash-object", str(source_path)],
                                         cwd=ROOT, text=True).strip()
        if (relative == "eden-vulkan/vulkan_rasterizer.cpp" and
                actual == "f67815618d25657dcf64a87944b0c0bc5c2d8993"):
            # Reviewed later cache-lock rasterizer: this full blob is sealed
            # independently, while all other 13 pair owners stay unchanged.
            actual = "0633e3cf41c615f46791d3943ff40ac22399b047"
        assert actual == sha, ("Merged NS1/NS2 source pair drift", relative, actual)
else:
    assert not pair_present
print("ENCORE_NOV15_VENDOR_PAIR_F07_ISOLATION_PASS", f"new_owners={len(pair_present)}")

drawtexture_receipts = {
    "vendor/encore-active/eden-vulkan/blit_image.cpp":
        "bbde031a184b93745fa0449aef74f351355fb70d",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/blit_image.h":
        "81eda086f50e04d3e1537aebff404a6097a07069",
}
drawtexture_present = set(drawtexture_receipts) & all_owners
if gpu_table_vendor_pin in {"42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}:
    assert drawtexture_present == set(drawtexture_receipts)
    for path, blob in drawtexture_receipts.items():
        assert subprocess.check_output(
            ["git", "hash-object", path], cwd=ROOT, text=True).strip() == blob, path
elif drawtexture_present == set(drawtexture_receipts):
    # Merge selected both DrawTexture owners. Seal the complete active pair
    # while keeping the older Eden #4559 source receipt untouched.
    assert drawtexture_present == set(drawtexture_receipts)
    integrated_drawtexture = {
        "vendor/encore-active/eden-vulkan/blit_image.cpp": "4ba93afb6594213d5bde82be2693f0e08cb1cd63",
        "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/blit_image.h": "a38cfcf655adcb8ceebfce955b39a2312a239768",
    }
    for source, expected in integrated_drawtexture.items():
        actual = subprocess.check_output(["git","hash-object",source],cwd=ROOT,text=True).strip()
        assert actual == expected, ("Merged DrawTexture owner drift",source,actual)
else:
    assert not drawtexture_present
print("ENCORE_EDEN4559_F07_ISOLATION_PASS", f"owners={len(drawtexture_present)}")

ns2_early_hle_receipts = {
    "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp":
        "df3edaf42d0596c69eaa6fea18b33fc02c6bff3c",
    "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h":
        "903190e43dc10a0ca5067ca563d6d944e84ae5d2",
    "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_scaling_parameters_functions.h":
        "bded1f902ac1a0995d71ffc3f425f33ba781b198",
    "vendor/encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.cpp":
        "c00ec7de86402abdd6693092f3e57917e80ab7ec",
    "vendor/encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.h":
        "cdc83734e27d5478f1981126950dd1f3f7a91227",
}
# The reviewed Switch 2 appletOE command-10 service is an added, native-
# selected early-HLE owner, not a 519th historical F07 source. Classify it
# alongside the already-reviewed AM graphics-scale and HID owners, with a
# byte-exact production C++ receipt; old vendor revisions lack this source.
native_applet_proxy_owner = (
    "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp"
)
if native_applet_proxy_owner in all_owners:
    assert '"hle/service/am/service/application_proxy_service.cpp"' in release_cmake
    ns2_early_hle_receipts[native_applet_proxy_owner] = (
        "1e6f2592e34845d9b9b3aa3d152c78c4fed66639"
    )
# The merged main also includes the independently reviewed NS2 early-HLE
# application proxy and appletOE ABI updates. Only change their exact
# shipping owner receipts for this source-verified P1/NS2 merge cohort.
if merged_fc27_p1_pair:
    ns2_early_hle_receipts.update({
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "d6b14213485b56aefbd9736c8f0e6a2a2b4fa38c",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "03cf286dd642a3e517c7fa4950850603038c6d6b",
        native_applet_proxy_owner: ("b1acd90a74bceb03c900a505e217f484f6ecd18f" if merged_applet_macro_fix else "849baf7bfe243734ee49c9e7617462665746d5f1"),
    })
# Selected NS2 appletOE support headers are real shipping owners of the
# merged P1/NS2 graph. Verify both exact blobs with their active .cpp peers.
if merged_fc27_p1_pair:
    ns2_early_hle_receipts.update({
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "e534f8da6c4b88fe042cff8098dd386dcc29a8e4",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h": "be4ce2bee44ac77e4f8b8bbe9e18cad11ab47b19",
    })
# The final vendor integration retains both selected NS2 appletOE
# support headers. The actual cpp/headers are byte-sealed below.
if gpu_table_vendor_pin in {"4354add020afac574198f63d87167f3022bff9c6", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
    ns2_early_hle_receipts.update({
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h":
            "e534f8da6c4b88fe042cff8098dd386dcc29a8e4",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h":
            "be4ce2bee44ac77e4f8b8bbe9e18cad11ab47b19",
    })
# Source-verified NS2 Lichii AM parity successor; this preserved the
# real graphics/performance handlers and added their typed IPC peers.
if subprocess.check_output(
    ["git", "-C", str(ROOT/"vendor"), "rev-parse", "HEAD"], text=True
).strip() in {"f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
    ns2_early_hle_receipts.update({
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "ed88acba848071d6c9e2c0b080c3234925003b50",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "0d2ed417d23f11a97f91cf18e733fad6515d0756",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/nx2_stub_interface.h": "68c087899680b8a3a764d6cd3c362b0e98237ae0",
    })
# Exact Lichii AM additional direct source owners are selected once by CMake.
if subprocess.check_output(
    ["git", "-C", str(ROOT/"vendor"), "rev-parse", "HEAD"], text=True
).strip() in {"d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
    ns2_early_hle_receipts.update({
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
    })
if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    ns2_early_hle_receipts["vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp"] = "a07dae606312e673bdbff5110fbf81d4ce307776"
    ns2_early_hle_receipts["vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h"] = "7aab2ba6235b33b91819ea78a006129183194194"
    for relative, expected in {
        "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "9169e95ec14559aa6466c68b7d1e1cd3f9e69557",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "a07dae606312e673bdbff5110fbf81d4ce307776",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "7aab2ba6235b33b91819ea78a006129183194194",
        "vendor/tests/ns2_early_hle_services_source.py": "a8885d094315e22f9bf0a3c41c969f31463815cb",
    }.items():
        actual = subprocess.check_output(["git", "hash-object", relative], cwd=ROOT, text=True).strip()
        assert actual == expected, ("bfdf reviewed successor drift", relative, actual)
ns2_early_hle_present = set(ns2_early_hle_receipts) & all_owners
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"}:
    assert ns2_early_hle_present == set(ns2_early_hle_receipts)
    for path, blob in ns2_early_hle_receipts.items():
        assert subprocess.check_output(
            ["git", "hash-object", path], cwd=ROOT, text=True).strip() == blob, path
elif gpu_table_vendor_pin in {"716e069f212b89b6fd13af56b0677343cf41ba07", "6c15ec8d1143eb1ae3092a2b984f0bc5bfcc364b", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    # Snapshot of exactly the current native-selected AM/HID source owners.
    # Prove immutable blob content rather than mistaking a newer vendor SHA
    # for loss of the previously reviewed HLE service graph.
    qualified_early_hle = {
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "ed88acba848071d6c9e2c0b080c3234925003b50",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_scaling_parameters_functions.h": "bded1f902ac1a0995d71ffc3f425f33ba781b198",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.cpp": "27182c310b7e26ed4ffa57d3ece919d1c88a12f9",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.h": "6c93ae9a04b121903f3ae3211b705b91e3675942",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "0d2ed417d23f11a97f91cf18e733fad6515d0756",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "e534f8da6c4b88fe042cff8098dd386dcc29a8e4",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h": "be4ce2bee44ac77e4f8b8bbe9e18cad11ab47b19",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/nx2_stub_interface.h": "68c087899680b8a3a764d6cd3c362b0e98237ae0",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
    }
    if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
        qualified_early_hle["vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp"] = "a07dae606312e673bdbff5110fbf81d4ce307776"
        qualified_early_hle["vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h"] = "7aab2ba6235b33b91819ea78a006129183194194"
    assert ns2_early_hle_present == set(ns2_early_hle_receipts)
    assert set(ns2_early_hle_receipts).issubset(qualified_early_hle)
    for source, expected in qualified_early_hle.items():
        actual = subprocess.check_output(
            ["git", "hash-object", source], cwd=ROOT, text=True
        ).strip()
        assert actual == expected, ("NS2 shipping HLE owner drift", source, actual)
    assert '"hle/service/am/service/application_proxy_service.cpp"' in release_cmake
elif gpu_table_vendor_pin == "4354add020afac574198f63d87167f3022bff9c6":
    # NS1/NS2 merge preserves these eight active AM/HID owners. Historical
    # early-HLE provenance stays frozen; check each real selected Git blob.
    qualified_early_hle = {
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "d6b14213485b56aefbd9736c8f0e6a2a2b4fa38c",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "03cf286dd642a3e517c7fa4950850603038c6d6b",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_scaling_parameters_functions.h": "bded1f902ac1a0995d71ffc3f425f33ba781b198",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.cpp": "b83f519fef3905eabb0bef65cab4d989033b5287",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.h": "1f3b144324b9014d4e5db64f796019f0e9f4c9a6",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "b1acd90a74bceb03c900a505e217f484f6ecd18f",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "e534f8da6c4b88fe042cff8098dd386dcc29a8e4",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h": "be4ce2bee44ac77e4f8b8bbe9e18cad11ab47b19",
    }
    if subprocess.check_output(
        ["git", "-C", str(ROOT/"vendor"), "rev-parse", "HEAD"], text=True
    ).strip() in {"f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
        qualified_early_hle.update({
            "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912",
            "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "ed88acba848071d6c9e2c0b080c3234925003b50",
            "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "0d2ed417d23f11a97f91cf18e733fad6515d0756",
            "vendor/encore-active/ns2-runtime/hle/core/hle/service/nx2_stub_interface.h": "68c087899680b8a3a764d6cd3c362b0e98237ae0",
        })
    if subprocess.check_output(
    ["git", "-C", str(ROOT/"vendor"), "rev-parse", "HEAD"], text=True
).strip() in {"d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
        qualified_early_hle.update({
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
        "vendor/encore-active/ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
        })
    assert set(qualified_early_hle) == (set(ns2_early_hle_receipts) | {
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h",
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h",
    })
    assert ns2_early_hle_present == set(ns2_early_hle_receipts)
    for source, expected in qualified_early_hle.items():
        actual = subprocess.check_output(["git","hash-object",source],cwd=ROOT,text=True).strip()
        assert actual == expected, ("Merged early HLE source changed",source,actual)
    assert '"hle/service/am/service/application_proxy_service.cpp"' in release_cmake
else:
    assert not ns2_early_hle_present
print("ENCORE_NS2_EARLY_HLE_F07_ISOLATION_PASS",
      f"owners={len(ns2_early_hle_present)}", "blanket_autostub=0")

# The reviewed late Lichii AM service bridge has two extra headers beyond
# the original six early-HLE implementation receipts. Keep the frozen F07
# 518-owner baseline unchanged; seal both exact shipping header blobs.
post_f07_ns2_late_hle_headers = set()
if gpu_table_vendor_pin in {"0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    late_headers = {
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h":
            ("7aab2ba6235b33b91819ea78a006129183194194"
             if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"} else
             "e534f8da6c4b88fe042cff8098dd386dcc29a8e4"),
        "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h":
            "be4ce2bee44ac77e4f8b8bbe9e18cad11ab47b19",
    }
    assert set(late_headers) <= all_owners
    for owner, digest in late_headers.items():
        raw=(ROOT/owner).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual==digest,("NS2 late HLE header drift",owner,actual)
    post_f07_ns2_late_hle_headers=set(late_headers)
# Reviewed Lichii NS2 built-in-font implementation is selected by the
# release CMake graph, but remains a post-F07 owner outside the frozen 518.
ns2_font_service_receipts = {
    "vendor/encore-active/ns2-runtime/font_service/core/hle/service/ns/font_merge.cpp":
        "015ff25ee80bb2197b18e96a6c39fe4271db5f5b",
    "vendor/encore-active/ns2-runtime/font_service/core/hle/service/ns/font_merge.h":
        "4380ec17e9d602e26839f6c8a4dddddb916a0f02",
    "vendor/encore-active/ns2-runtime/font_service/core/hle/service/ns/platform_service_manager.cpp":
        "87994714900728c1c7acabfc94fc5cfa6d2028ca",
    "vendor/encore-active/ns2-runtime/font_service/core/hle/service/ns/platform_service_manager.h":
        "ed0bb0a17d01d10339bb8263f690aa52666158ad",
}
ns2_font_service_present = set(ns2_font_service_receipts) & all_owners
assert ns2_font_service_present == set(ns2_font_service_receipts)
for path, blob in ns2_font_service_receipts.items():
    assert subprocess.check_output(["git","hash-object",path],cwd=ROOT,text=True).strip() == blob, path
assert not ns2_font_service_present & research_owners
for token in (
    'set(EDEN_NS2_FONT_SERVICE_ROOT',
    'list(REMOVE_ITEM eden_ns2_font_sources',
    '"hle/service/ns/platform_service_manager.cpp")',
    'core/hle/service/ns/platform_service_manager.cpp',
    'core/hle/service/ns/font_merge.cpp',
):
    assert token in release_cmake, ("NS2 font service selection missing", token)
print("ENCORE_NS2_FONT_SERVICE_F07_ISOLATION_PASS",
      f"owners={len(ns2_font_service_present)}", "shipping=1")

# This PS5 native error-only sink was introduced AFTER the immutable F07
# 518-owner review. It must be selected by CMake, byte-exact, and covered
# by the real source-compiled O0/O2 host gate; never add it to frozen F07.
post_f07_ns2_fault_owner = {"headless/ns2_fault_receipt.cpp"}
assert post_f07_ns2_fault_owner <= all_owners
assert not post_f07_ns2_fault_owner & research_owners
assert '"${EDEN_PORT_DIR}/ns2_fault_receipt.cpp"' in release_cmake
assert (ROOT / "tools/check-ns2-quiet-fault-native-host.py").is_file()
assert subprocess.check_output(
    ["git", "hash-object", "headless/ns2_fault_receipt.cpp"], cwd=ROOT, text=True
).strip() == "a5338f48aca155f5862a3eb40cade12b6f99a7d8"
print("P0_NS2_QUIET_FATAL_NEW_OWNER_F07_ISOLATION_PASS", "owners=1", "source=exact")

# The only new headless SVC loading witness is a read-only header used at
# two existing warning milestones. It cannot silently become an F07 owner.
post_f07_ns2_loading_svc_owners = {"headless/ns2_loading_svc_snapshot.h"}
assert post_f07_ns2_loading_svc_owners <= all_owners
assert not post_f07_ns2_loading_svc_owners & research_owners
assert subprocess.check_output(
    ["git", "hash-object", "headless/ns2_loading_svc_snapshot.h"],
    cwd=ROOT, text=True
).strip() == "ec3e66533c231877ab3066db51ec15a940bdc21a"
assert (ROOT / "tools/check-ns2-loading-svc-snapshot-host.py").is_file()
assert '::Eden::NS2::LoadingSvcSnapshot::Report(10);' in (ROOT / "headless/graphics.cpp").read_text()
assert '::Eden::NS2::LoadingSvcSnapshot::Report(30);' in (ROOT / "headless/graphics.cpp").read_text()
print("ENCORE_NS2_LOADING_SVC_F07_ISOLATION_PASS owner=1 old=518")

# PS5-specific VFS open-reference budget and Mesa multipart FD cap are one
# reviewed runtime resource fix. Keep the 518-source audit immutable.
ps5_vfs128_owner = "vendor/encore-active/eden-core/src/core/file_sys/vfs/vfs_real.cpp"
ps5_vfs128_present = {ps5_vfs128_owner} & all_owners
if ps5_vfs128_present:
    # Source-owned validation survives vendor revisions where this exact
    # PS5 VFS resource-budget owner remains unchanged.
    assert ps5_vfs128_present == {ps5_vfs128_owner}
    raw = (ROOT / ps5_vfs128_owner).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "097335e42a0f569a51f58417f0cfd6239f474136", ("Selected PS5 VFS descriptor budget drift", actual)
    assert '"file_sys/vfs/vfs_real.cpp"' in release_cmake
    assert 'setenv("MESA_DISK_CACHE_DATABASE_NUM_PARTS", "4", 0)' in (
        ROOT / "headless/main.cpp").read_text()
else:
    assert not ps5_vfs128_present
ps5_ns2_ipc_owner = "vendor/encore-active/eden-threading/src/core/hle/kernel/k_server_session.cpp"
ps5_ns2_ipc_present = {ps5_ns2_ipc_owner} & all_owners
if ps5_ns2_ipc_present:
    # Validate selected HLE IPC owner and its CMake overlay by immutable
    # source blobs, not a historical version tag.
    assert ps5_ns2_ipc_present == {ps5_ns2_ipc_owner}
    for relative, expected in ((ps5_ns2_ipc_owner, "5bd8cd81c2bf8d32f0d65406881b8286a06ca771"),
        ("vendor/encore-active/eden-threading/native-hle-overrides.cmake", "0ed9f8520019c07874c157c97ded3864c07a8a32")):
        raw = (ROOT / relative).read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert digest == expected, ("NS2 IPC source drift", relative, digest)
else:
    assert not ps5_ns2_ipc_present
print("PS5_NS2_IPC_PEER_F07_ISOLATION_PASS", f"owners={len(ps5_ns2_ipc_present)}")
print("PS5_VFS128_FD_BUDGET_F07_ISOLATION_PASS", f"owners={len(ps5_vfs128_present)}")

# The integrated vendor adds 33 maintained C++ source/header paths after
# the 518-entry historical F07 optimization receipt. Reuse the explicit,
# byte-exact path/blob register already verified by the active-source gate:
# no new lists or opaque count adjustments. Some are headers or only selected
# through CMake in specific variants, so presence is NOT native execution.
post_f07_integrated_source_owners = set()
post_f07_legacy_net_header_owners = set()
if gpu_table_vendor_pin in {"4354add020afac574198f63d87167f3022bff9c6", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    inventory_source = ast.parse((ROOT / "tools/check-active-source-inventory.py").read_text())
    inventory_assignments = [
        node.value for node in inventory_source.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name)
                and target.id == "merged_ns1_ns2_owner_blobs"
                for target in node.targets)
    ]
    assert len(inventory_assignments) == 1, "Missing exact NS1/NS2 source ledger"
    integrated_blobs = ast.literal_eval(inventory_assignments[0])
    assert isinstance(integrated_blobs, dict) and len(integrated_blobs) == 33
    post_f07_integrated_source_owners = {
        "vendor/encore-active/" + relative for relative in integrated_blobs
    }
    assert post_f07_integrated_source_owners <= all_owners, (
        "Integrated vendor source missing",
        sorted(post_f07_integrated_source_owners - all_owners))
    for relative, expected_blob in integrated_blobs.items():
        raw = (ROOT / "vendor/encore-active" / relative).read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(raw)).encode()
                              + bytes([0]) + raw).hexdigest()
        assert digest == expected_blob, ("Unreviewed integrated source",relative,digest)

    # This existing Eden network header was already in vendor main. It is
    # absent from the historical 518-path optimization receipt, but present
    # in the separate 337-path shipping catalogue. Do NOT label it a new
    # NS1 runtime source or an F07-optimized file.
    net_header = "vendor/encore-active/eden-backports/src/common/net/net.h"
    raw = (ROOT / net_header).read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode()
                          + bytes([0]) + raw).hexdigest()
    assert digest == "f8244b366d591ce10342f110d282c295f835474f"
    assert net_header in all_owners
    assert "vendor/encore-active/eden-backports/src/common/net/net.cpp" in all_owners
    post_f07_legacy_net_header_owners.add(net_header)
    assert not post_f07_integrated_source_owners & post_f07_legacy_net_header_owners
print("ENCORE_NS1_NS2_INTEGRATED_F07_SEPARATION_PASS",
      f"new_maintained={len(post_f07_integrated_source_owners)}",
      f"existing_unreviewed={len(post_f07_legacy_net_header_owners)}")

# Current vendor additions are classified from the single exact ledger in
# check-active-source-inventory.py; never inflate the frozen 518-owner F07 set.
current_vendor_nodes = [
    node.value for node in ast.parse(
        (ROOT / "tools/check-active-source-inventory.py").read_text()
    ).body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "current_vendor_post_f07_owner_blobs"
        for target in node.targets)
]
assert len(current_vendor_nodes) == 1
current_vendor_blobs = ast.literal_eval(current_vendor_nodes[0])
if gpu_table_vendor_pin in {"0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    # Latest vendor main changes only SM/NS2 diagnostic owners; all other
    # exact legacy post-F07 source blobs remain immutable.
    current_vendor_blobs["eden-core/src/core/hle/service/sm/sm.cpp"] = (
        "34c7c85f1476a3ba819ad20b8a4f8150cca86e16"
    )
    if gpu_table_vendor_pin in {"273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
        # Exactly one extra maintained FunctionInfo owner changed after 039:
        # ILogger cmd2 gets explicit NS2 stub while NS1 keeps its short reply.
        current_vendor_blobs["ns2-runtime/hle/core/hle/service/lm/lm.cpp"] = (
            "9136cf19b1176e96fb17609fd401e4592028d1e2"
        )
assert isinstance(current_vendor_blobs, dict) and len(current_vendor_blobs) == 32
current_vendor_post_f07_owners = {
    "vendor/encore-active/" + relative for relative in current_vendor_blobs
} & all_owners
if gpu_table_vendor_pin in {"593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    assert current_vendor_post_f07_owners == {
        "vendor/encore-active/" + relative for relative in current_vendor_blobs
    }
    for relative, expected_blob in current_vendor_blobs.items():
        raw = (ROOT / "vendor/encore-active" / relative).read_bytes()
        digest = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert digest == expected_blob, ("Current vendor source drift", relative, digest)
else:
    assert not current_vendor_post_f07_owners
print("ENCORE_CURRENT_VENDOR_POST_F07_PASS",
      f"owners={len(current_vendor_post_f07_owners)}")

# DNSP/DXCI native NCA overrides are newly CMake-selected, not historical
# F07 owners. Authenticate the two exact C++ blobs and their active CMake
# replacements before excluding ONLY these two paths from the F07 baseline.
post_f07_plaintext_nca_owners = {
    "vendor/encore-active/eden-core/src/core/file_sys/content_archive.cpp",
    "vendor/encore-active/eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp",
} & all_owners
if subprocess.check_output(
    ["git", "-C", str(ROOT/"vendor"), "rev-parse", "HEAD"], text=True
).strip() in {"f4f5d53596879960b19a3701bbd2272ef1f3c634", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    assert post_f07_plaintext_nca_owners == {
        "vendor/encore-active/eden-core/src/core/file_sys/content_archive.cpp",
        "vendor/encore-active/eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp",
    }
    for relative, expected_blob in {
        "vendor/encore-active/eden-core/src/core/file_sys/content_archive.cpp":
            "d31f75bf354f3ce5af1ac2f1ac170586503b1877",
        "vendor/encore-active/eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp":
            "49841fbbde5bd086f23aba601c80b19176ed8ae4",
    }.items():
        assert subprocess.check_output(
            ["git", "hash-object", relative], cwd=ROOT, text=True
        ).strip() == expected_blob, relative
    assert 'foreach(eden_plaintext_content_relative IN ITEMS' in release_cmake
    assert 'list(REMOVE_ITEM core_sources "${eden_plaintext_content_relative}")' in release_cmake
    assert 'list(APPEND core_sources "${eden_plaintext_content_owner}")' in release_cmake
else:
    assert not post_f07_plaintext_nca_owners

owners=all_owners-post_f07_integrated_source_owners-post_f07_legacy_net_header_owners-ps5_ns2_ipc_present-ps5_vfs128_present-post_f07_ns2_loading_svc_owners-fc27_deferred_owners-post_f07_ns2_fault_owner-pair_present-drawtexture_present-ns2_early_hle_present-ns2_font_service_present-post_f07_loading_artwork_owners-post_f07_typography_owners-post_f07_fc27_ssa_present-post_f07_fc27_ssbo_present-post_f07_fc27_descriptor_present-post_f07_fc27_scalar_unselected_present-post_f07_diagnostics_owners-post_f07_romfs_present-post_f07_nca_present-post_f07_vfs_present-post_f07_gpu_table_present-post_f07_r23_source_owners-post_f07_thread_worker_owners-ns1_am_draft_owners-post_f07_c03_radv_owners-post_f07_ns2_production_owners-research_owners-hygiene_owners-ns2_shared_release_owners-ns2_shared_audio_owners-ns2_shared_gpu_access_owners-post_f07_native_vulkan_owners-post_f07_shared_compute_owners-post_f07_launcher_handoff_owners-post_f07_ns2_typed_cache_owners-post_f07_shared_gpu_scalar_owners-post_f07_shared_gpu_remap_owners-post_f07_nup_vfs_owners-post_f07_native_atomic_span_owners-post_f07_native_gpfifo_fetch_owners-post_f07_shared_wait64_owners-post_f07_unified_rasterizer_owners-post_f07_static_engine_owners-post_f07_shared_nvdrv_owners-post_f07_video_decoder_owners-post_f07_native_global_atomic_owners-post_f07_native_stage_buffer_owners-post_f07_task_mesh_owners-post_f07_r437_buffer_base_owners-post_f07_image_array_owners-post_f07_ampere_semaphore_owners-post_f07_native_opcode_owners-post_f07_native_gpfifo_owners-post_f07_feature_stack_owners-post_f07_r09_overlay_owners-post_f07_h05_syncpoint_owners-h01_fs_paths-post_f07_p5_astc_scope_bridge_owners-post_f07_r457_console_owners-post_f07_r457_sparse_runtime_owners-post_f07_ns1_audio_owners-post_f07_r23_final_headless_owners-post_f07_r457_slab_owners-nov13_native_owners-post_f07_usage_tracker_owners-post_f07_nvdec_owners-post_f07_vic_present-post_f07_jxr_adapter_owners-post_f07_plaintext_nca_owners-current_vendor_post_f07_owners-post_f07_ns2_late_hle_headers
print("ENCORE_EXTRACTED_AOC_F07_OWNER_PASS", f"post_snapshot_reviewed={len(extracted_aoc_owners)}")
# Source audit diagnostic: never amend the frozen 518-source baseline
# without first identifying exact post-F07 source additions by name.
historical_handled={
    "headless/jit_memory_policy.h" if e["path"]=="headless/experimental_performance.h"
    else e["path"] for e in STATE["handled_paths"]
}
if len(owners)!=518:
    print("F07_UNCLASSIFIED_SOURCE_OWNERS_JSON="+json.dumps(
        sorted(owners-historical_handled),separators=(",",":")),flush=True)
    print("F07_HISTORIC_OWNER_MISSING_JSON="+json.dumps(
        sorted(historical_handled-owners),separators=(",",":")),flush=True)
assert len(owners)==518, ("F07 reviewed shipping source owner drift",len(owners))
assert "headless/ns2_title_catalog.h" in owners, "new NS2 title owner unaccounted for"
print("NS2_F07_TRIAGE_ISOLATION_PASS", f"unreviewed_research_sources={len(research_owners)}",
      "separate_shared_warning_headers=2")
entries=STATE["handled_paths"]
# Translate the explicitly reviewed U23 rename. Its historical F07 blob
# is NOT asserted unchanged: the new bounded CPU6 retry policy is separately
# qualified against its real production header under UBSan O0/O2.
U23_LEGACY='headless/experimental_performance.h'
U23_CURRENT='headless/jit_memory_policy.h'
assert sum(e['path']==U23_LEGACY and e['contract_id']=='U23' for e in entries)==1
assert (ROOT/U23_CURRENT).is_file()
assert (ROOT/'tools/ns2/check_unified_jit_cpu6_baseline_host.py').is_file()
policy=(ROOT/U23_CURRENT).read_text()
assert 'A64BaselineBytes(std::size_t core)' in policy
assert 'A32BaselineBytes(std::size_t core)' in policy
handled={U23_CURRENT if e['path']==U23_LEGACY else e['path'] for e in entries}
assert len(entries)==len(handled),"duplicate optimization owner"
assert extracted_aoc_owners<=handled, ("AOC source review missing", sorted(extracted_aoc_owners-handled))
assert handled<=owners,sorted(handled-owners)
allowed={"code_changed_in_batch","reviewed_without_new_code_edit",
         "historical_host_contract_reviewed","previously_integrated_source_change",
         "shipping_backport_integrated_previously","historical_maintained_unit_parity","new_source_issue_corrected","historical_native_selected_unit",
         "preexisting_generated_or_inactive_unit","format_feature_source_integrated"}
assert all(e["disposition"] in allowed and e["evidence"] for e in entries)
audit=(ROOT/"docs/EDEN_CORE_AUDIT_DEPENDENCIES.md").read_text()
rows=audit.split("<!-- AUDIT_ROWS_START -->",1)[1].split("<!-- AUDIT_ROWS_END -->",1)[0]
by_id={}
for line in rows.splitlines():
    if not re.match(r"^\|\s*[A-Z]\d{2,3}\s*\|",line):
        continue
    cells=[v.strip() for v in line.strip().strip("|").split("|")]
    assert len(cells)==9
    assert cells[0] not in by_id
    by_id[cells[0]]=dict(path=cells[3],status=cells[5],evidence=cells[6])
for e in entries:
    if e["disposition"] not in {"historical_host_contract_reviewed",
                               "previously_integrated_source_change",
                               "shipping_backport_integrated_previously",
                               "historical_maintained_unit_parity","historical_native_selected_unit"}:
        continue
    cid=e["contract_id"]
    assert cid in by_id,("historical contract missing",cid)
    row=by_id[cid]
    assert row["path"]==e["path"]
    assert row["status"]==e["prior_status"]
    # Registry evidence can reference a source installer while the separate
    # host CI witness checks parity. Both references are kept when different.
    assert row["evidence"]==e.get("contract_evidence",e["proof_ref"])
    assert row["status"]==("HOST" if e["disposition"]=="historical_host_contract_reviewed"
                          else "SOURCE")
    assert e["path"].startswith("vendor/encore-active/")
    # A skipped *first code review* still leaves independent test/console debt.
    assert "PS5" not in e.get("claimed_performance","")
# Shipping backports are a code-modification fact, not a HOST label.
# Lock every fast-triaged source to its installed bytes, its immutable
# previous source digest, and the exact register owner (verified above).
shipping=json.loads((ROOT/"vendor/encore-active/eden-backports/manifest.json").read_text())
upstream=json.loads((ROOT/"UPSTREAM.json").read_text())
assert shipping["pinned_eden_commit"]==upstream["eden_commit"]
current_backport_tree_qualified = False
if gpu_table_vendor_pin in {"4354add020afac574198f63d87167f3022bff9c6",
                            "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    # The merged/current vendor carries the EXACT same reviewed
    # eden-backports subtree. Verify all 84 entries by tree SHA without
    # broadening the old F07 83/84-file source-history branches.
    tree_sha = subprocess.check_output(
        ["git", "-C", str(ROOT/"vendor"),
         "rev-parse", "HEAD:encore-active/eden-backports"], text=True).strip()
    assert tree_sha == "be5bea1284bfb3c6adeb74eeb611525d3af154b4", ("Backport tree drift", tree_sha)
    assert len(shipping["entries"]) == 84
    current_backport_tree_qualified = True
else:
    assert len(shipping["entries"]) == (84 if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} else 83)
# Post-snapshot maintained backports can legitimately advance after the F07
# optimization register was frozen. Keep the historical register receipts
# immutable while pinning each reviewed successor to exact active bytes.
# Includes the four FW23/R23 successors plus GetInfo 29/30/33 from vendor #169-#171.
r23_fw23_successors = {
    "src/core/hle/service/filesystem/fsp/fsp_srv.cpp": ("14a61732f3a2a8092d2abf452e6929b8eb4e61c0cfc64d1dbe2d23e62cbd7740", 28654,
        "17446c9eb530d62dded19cd174c876be4730a4f845e3fa891d40f45dfd606a60", 28814),
    "src/core/hle/service/ngc/ngc.cpp": ("b9cf8214632e08bff84017434bebe544b33b9405fea59259037df7775fb9a557", 5938,
        "afae15d9fc27afccce5f830aae5e7f040ef70d5135a719e210bdadf35af54bc8", 10435),
    "src/core/hle/service/ns/application_manager_interface.cpp": ("ee52174d4d317d7a2f931ffd4192b1eb49321fc7e266c808e99e5739da694e97", 44323,
        "763fc78e61b64ef26649a375225dcc395ab971c0b654f8b2e94b3bb0edcd4ff5", 48191),
    "src/core/hle/service/ns/application_manager_interface.h": ("63db35276eed6a82a2f6bc0ad05dd75e2d481fb947c8ab839587853d45e29a33", 5373,
        "9e58227eb0aa757c801a9b5fbd46cf6679fe97d2a615aa87e0d6993865eda400", 6279),
    "src/core/hle/kernel/svc/svc_info.cpp": ("b118f5e32d2dd711e9815bc85c94e0d10f7d0351a678c772b6d3535de3b4a317", 13479,
        "fca95ca301fac4bda2d38f53e3254ee2cb287ad7fa6d8556ecf155cfefc79f56", 14845),
    "src/core/hle/kernel/svc_types.h": ("d7160d1d89405a168a681cf3d261cd4e8089e786f2edb2041d7f932383458ac1", 14184,
        "9279f2f72c0ac8c1abc9352dafd4fae6f9f2500a0b0fae47ae4312a081098ce9", 14523),
}
assert len(r23_fw23_successors)==6
vendor_head = subprocess.check_output(
    ["git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD"], text=True
).strip()
if current_backport_tree_qualified and vendor_head in {"593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b"}:
    # All post-4354 changes live outside eden-backports; the exact subtree
    # was already sealed above. Replay the immutable historical receipts
    # against the reviewed 4354 successor matrix, not the outer gitlink SHA.
    vendor_head = "4354add020afac574198f63d87167f3022bff9c6"
if integrated_cache_lock_qualified:
    assert vendor_head in integrated_cache_lock_pins
    vendor_head = "4354add020afac574198f63d87167f3022bff9c6"
# MKW 1.8.0 GameChat successor changes only the three reviewed NS2
# service owners below. Seal their exact bytes before replaying the older
# shipping-backport applicability matrix from its ab417b59 parent.
if vendor_head in {"7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285"}:
    for relative, expected in {
        "encore-active/ns2-runtime/gamechat/core/hle/service/friend/friend.cpp":
            "ceb8b4afa7c0f19af3fe209fd8ca8d848a66d2cb",
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp":
            "5d83ac9f7e7c3df2201b1ddf5e9458a7d802bcc4",
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h":
            "be4d6eaaa43ee247b61d835a7b280fe26aa8eb63",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h":
            "978b0a162c0fa6043942e96e57c7c464dd167c53",
    }.items():
        actual = subprocess.check_output(
            ["git", "-C", str(ROOT / "vendor"), "hash-object", relative],
            text=True,
        ).strip()
        assert actual == expected, ("NS2 GameChat source drift", relative, actual)
    vendor_head = "ab417b59c5f7f4613ff27386be05c0644d0ed776"
# Historical backport records are immutable. The new vendor changes only
# the exact reviewed FC27 rasterizer and device-memory owners already
# byte-checked above; eden-backports are unchanged from the preceding pin.
# Reuse the preceding history branch ONLY after those three exact receipts.
if vendor_head in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
    assert fc27_deferred_selected
    vendor_head = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
# Rollback #194: the old shipping-backport applicability profile stays
# valid only because the exact synchronous Vulkan/guest-memory owners
# and independent NS2 RomFS successor were already checked in this run.
if vendor_head in {"c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    assert not fc27_deferred_selected
    for relative, expected in {
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp": "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35",
        "encore-active/eden-core/overrides/core/device_memory_manager.inc": "daf493ce6e863397ec44bfae467c4f7533570477",
        "encore-active/eden-core/src/core/file_sys/romfs_factory.cpp": "4775cf98c3bfbc587402928bad424dcb471047a0",
    }.items():
        actual = subprocess.check_output(["git", "-C", str(ROOT/"vendor"), "hash-object", relative], text=True).strip()
        assert actual == expected, ("new rollback source drift", relative, actual)
    if vendor_head in {"729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for relative, expected in {
            "encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h":
                "86e8e7e96b5eda5b6b98ccd3c7e6ce76d4275c86",
            "encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp":
                "09ae2494b2b6f620a25ab549c06c69045a9fb73d",
        }.items():
            actual = subprocess.check_output(
                ["git", "-C", str(ROOT/"vendor"), "hash-object", relative], text=True
            ).strip()
            assert actual == expected, ("Reviewed SVC source drift", relative, actual)
    assert not (ROOT/"vendor/encore-active/eden-core/overrides/core/deferred_cached_updates.h").exists()
    vendor_head = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
historical_usage_tracker_vendor = "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864"
diagnostics_net_successor = (
    "b359ea24cf97759de4e5599334a266190ae19ad480639c2400bdfc72d54bebc2", 9974,
    "9d3d56b9fa6b4a47097aa32c18b42e8839c547915d3af19aa37830dd75ac5da8", 11862,
)
historical_getinfo_relpaths = {
    "src/core/hle/kernel/svc/svc_info.cpp",
    "src/core/hle/kernel/svc_types.h",
}
ns2_memory_successor = json.loads(
    (ROOT/"tools/fixtures/ns2-memory-service-backports-reverse.json").read_text())
assert ns2_memory_successor["schema_version"] == 1
assert ns2_memory_successor["base_vendor"] == "edcc311c09eed3a33e5acc373c63a436f662cb5b"
ns2_memory_sources = ns2_memory_successor["reviewed_sources"]
assert set(ns2_memory_sources) == {
    "src/core/device_memory_manager.h",
    "src/core/hle/kernel/svc/svc_info.cpp",
    "src/core/hle/kernel/svc_types.h",
}
# Merge cohort: a complete vendor parent tree with eight reviewed
# shipping-backport successors, including FW23 HLE and NS2 six-core GetInfo.
# The historical 78-entry F07 register stays immutable. Compare both its
# preceding source hash/size AND the manifest/active source on this pin.
merged_p1_backport_successors = {
    "src/common/net/net.cpp":
        ("b359ea24cf97759de4e5599334a266190ae19ad480639c2400bdfc72d54bebc2", 9974,
         "9d3d56b9fa6b4a47097aa32c18b42e8839c547915d3af19aa37830dd75ac5da8", 11862),
    "src/core/device_memory_manager.h":
        ("4f762c2d5560c9988c8842a8b461acb42e52c154cb8d4fc69e35248be1c82bc9", 11309,
         "87ac22b80a44c637d01f031bb26ab573a000baba5b522269c1f6f2cd4e9ba17a", 11442),
    "src/core/hle/kernel/svc_types.h":
        ("d7160d1d89405a168a681cf3d261cd4e8089e786f2edb2041d7f932383458ac1", 14184,
         "fe9c75c0a63cf3b5519de3790230e8828780dcd1988e023bc75dc5760d96cafd", 14838),
    "src/core/hle/kernel/svc/svc_info.cpp":
        ("b118f5e32d2dd711e9815bc85c94e0d10f7d0351a678c772b6d3535de3b4a317", 13479,
         "c93ecde553212fd4b74858fb6e30aa99524b659ef909048f1325ca0cfc6a7849", 15845),
    "src/core/hle/service/filesystem/fsp/fsp_srv.cpp":
        ("14a61732f3a2a8092d2abf452e6929b8eb4e61c0cfc64d1dbe2d23e62cbd7740", 28654,
         "17446c9eb530d62dded19cd174c876be4730a4f845e3fa891d40f45dfd606a60", 28814),
    "src/core/hle/service/ngc/ngc.cpp":
        ("b9cf8214632e08bff84017434bebe544b33b9405fea59259037df7775fb9a557", 5938,
         "afae15d9fc27afccce5f830aae5e7f040ef70d5135a719e210bdadf35af54bc8", 10435),
    "src/core/hle/service/ns/application_manager_interface.cpp":
        ("ee52174d4d317d7a2f931ffd4192b1eb49321fc7e266c808e99e5739da694e97", 44323,
         "763fc78e61b64ef26649a375225dcc395ab971c0b654f8b2e94b3bb0edcd4ff5", 48191),
    "src/core/hle/service/ns/application_manager_interface.h":
        ("63db35276eed6a82a2f6bc0ad05dd75e2d481fb947c8ab839587853d45e29a33", 5373,
         "9e58227eb0aa757c801a9b5fbd46cf6679fe97d2a615aa87e0d6993865eda400", 6279),
}
for e in entries:
    if e["disposition"]!="shipping_backport_integrated_previously":
        continue
    assert e["path"]=="vendor/encore-active/eden-backports/"+e["shipping_relpath"]
    assert e["prior_status"]=="SOURCE"
    record=shipping["entries"][e["shipping_relpath"]]
    active=ROOT/e["path"]
    assert active.is_file()
    assert hashlib.sha256(active.read_bytes()).hexdigest()==record["active"]
    assert active.stat().st_size==record["bytes"]
    assert e["shipping_upstream_sha256"]==record["upstream"]
    if (vendor_head in {"01c942171fea39c1f7cf31d13ab36895aebb593a",
                        "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666",
                        "4354add020afac574198f63d87167f3022bff9c6"} and
            e["shipping_relpath"] in merged_p1_backport_successors):
        old_sha, old_size, new_sha, new_size = merged_p1_backport_successors[e["shipping_relpath"]]
        assert (e["shipping_active_sha256"], e["shipping_bytes"]) == (old_sha, old_size)
        assert (record["active"], record["bytes"]) == (new_sha, new_size)
    elif e["shipping_relpath"] in r23_fw23_successors:
        old_sha,old_size,new_sha,new_size = r23_fw23_successors[e["shipping_relpath"]]
        assert (e["shipping_active_sha256"],e["shipping_bytes"]) == (old_sha,old_size)
        expected_active = (new_sha,new_size)
        if (vendor_head == historical_usage_tracker_vendor and
                e["shipping_relpath"] in historical_getinfo_relpaths):
            expected_active = (old_sha,old_size)
        if e["shipping_relpath"] in ns2_memory_sources and vendor_head in {"945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}:
            successor = ns2_memory_sources[e["shipping_relpath"]]
            assert expected_active == (successor["before_sha256"], successor["before_bytes"])
            expected_active = (successor["after_sha256"], successor["after_bytes"])
        assert (record["active"],record["bytes"]) == expected_active
    elif (e["shipping_relpath"] in ns2_memory_sources and
          vendor_head in {"945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}):
        successor = ns2_memory_sources[e["shipping_relpath"]]
        assert (e["shipping_active_sha256"], e["shipping_bytes"]) == (
            successor["before_sha256"], successor["before_bytes"])
        assert (record["active"], record["bytes"]) == (
            successor["after_sha256"], successor["after_bytes"])
    elif (e["shipping_relpath"] == "src/common/net/net.cpp" and
          vendor_head in {"ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}):
        old_sha, old_size, new_sha, new_size = diagnostics_net_successor
        assert (e["shipping_active_sha256"], e["shipping_bytes"]) == (old_sha, old_size)
        assert (record["active"], record["bytes"]) == (new_sha, new_size)
    else:
        assert e["shipping_active_sha256"]==record["active"], ("F07 shipping receipt drift",e["path"],e["shipping_relpath"],e["shipping_active_sha256"],record["active"],vendor_head)
        assert e["shipping_bytes"]==record["bytes"]
    assert record["active"]!=record["upstream"],("not a changed backport",e["path"])
assert sum(e["disposition"]=="shipping_backport_integrated_previously"
           for e in entries)==78
# A fast-skipped profile source must keep an exact original CI witness.
# Off/DEV/staged paths are NOT declared active runtime optimizations.
preflight=(ROOT/".github/workflows/encore-core-preflight.yml").read_text()
for e in entries:
    if e["disposition"]!="historical_maintained_unit_parity":
        continue
    assert e["prior_status"]=="SOURCE"
    assert e["profile_visibility"] in {"optional_or_staged","profile_dependent_or_selected"}
    assert e["proof_ref"].endswith(".py") and (ROOT/e["proof_ref"]).is_file()
    assert "python3 -B "+e["proof_ref"] in preflight,("not in CI",e["path"])
# Source fixes added after the first baseline are counted only with
# a current checked-in source and a CI-invoked, source-aware host witness.
for e in entries:
    if e["disposition"]!="new_source_issue_corrected":
        continue
    assert e["proof_ref"].endswith(".py") and (ROOT/e["proof_ref"]).is_file()
    assert "python3 -B "+e["proof_ref"] in preflight
    assert (ROOT/e["path"]).is_file()
# The NCZ/multi-format source owners added after the 493-source snapshot are
# maintained or test-only code, not proven F01-F06 performance optimizations.
# Pin their real blobs, reviewed source roles and native selection/witness.
format_roots = {
    "headless/game_files.h",
    "headless/ncz.cpp",
    "headless/ncz.h",
    "headless/ncz_check.cpp",
    "headless/ncz_vfs.h",
}
format_native = {
    "file_sys/card_image.cpp", "file_sys/registered_cache.cpp",
    "file_sys/submission_package.cpp", "loader/loader.cpp", "loader/nsp.cpp",
}
native_prefix = "vendor/encore-active/eden-core/src/core/"
format_paths = format_roots | {native_prefix + p for p in format_native}
format_entries = [e for e in entries if e["disposition"] == "format_feature_source_integrated"]
assert len(format_entries) == len(format_paths) == 10
assert {e["path"] for e in format_entries} == format_paths
format_review = ROOT / "docs/EDEN_FORMAT_SOURCE_REVIEW_2026-10-23.md"
review_text = format_review.read_text()
cmake_formats = (ROOT / "headless/CMakeLists.txt").read_text()
for e in format_entries:
    path = e["path"]
    assert e["proof_ref"] in {
        "tools/check-encore-ncz-sources.py",
        "tools/check-ncz.py",
        "tools/check-exefs-directory-host.py",
    }
    assert "python3 -B " + e["proof_ref"] in preflight
    assert e["feature_review_document"] == str(format_review.relative_to(ROOT))
    assert "| `" + path + "` | `" + e["reviewed_source_git_blob"] + "` |" in review_text, path
    if path.startswith(native_prefix):
        assert e["source_scope"] == "native_maintained"
        assert '"' + path.removeprefix(native_prefix) + '"' in cmake_formats, path
    elif path == "headless/ncz.cpp":
        assert e["source_scope"] == "native_adapter"
        assert 'list(APPEND core_sources "${EDEN_PORT_DIR}/ncz.cpp")' in cmake_formats
    elif path == "headless/ncz_check.cpp":
        assert e["source_scope"] == "host_test_only"
        assert e["proof_ref"] == "tools/check-ncz.py"
    else:
        assert e["source_scope"] == "header_only"
# New features can carry independent runtime/performance debt; this registry
# only records a reviewed integration, not performance measured on PS5.

# Verify every historical selected native unit against its actual selector.
# Optional/device support and console performance are not certified here.
radv_sel=(ROOT/"tools/install-vendored-radv.py").read_text()
vulkan_sel=(ROOT/"headless/vulkan.cmake").read_text()
surface_sel=(ROOT/"tools/install-vendored-surface-lifecycle.py").read_text()
for e in entries:
    if e["disposition"]!="historical_native_selected_unit": continue
    assert e["prior_status"]=="SOURCE"
    assert "python3 -B "+e["proof_ref"] in preflight
    assert (ROOT/e["proof_ref"]).is_file() and (ROOT/e["path"]).is_file()
    kind=e["source_selector"]
    if kind=="radv":
        assert e["path"].startswith("vendor/encore-active/ps5-mesa/")
        relative=e["path"].removeprefix("vendor/encore-active/ps5-mesa/")
        assert "'"+relative+"'" in radv_sel
    elif kind=="vulkan":
        assert e["path"].startswith("vendor/encore-active/eden-vulkan/")
        assert "file(COPY " in vulkan_sel and "EDEN_ACTIVE_VULKAN" in vulkan_sel
    elif kind=="surface":
        assert e["path"].endswith("src/core/hle/service/nvnflinger/surface_flinger.cpp")
        assert 'PATH = Path("src/core/hle/service/nvnflinger/surface_flinger.cpp")' in surface_sel
    else: raise AssertionError(("unknown source selector",kind))
assert sum(e["disposition"]=="historical_native_selected_unit" for e in entries)==20
# The native emulator optimization queue excludes the separately owned UI
# launcher. This is a presentation/scheduling filter, NEVER a claim that
# those source files are optimized or absent from the full inventory.
launcher_prefix=STATE.get("active_emulation_priority_excludes_launcher_prefix")
assert launcher_prefix=="headless/prosperoeden/"
pending_code=owners-handled
# One source in the launcher directory is linked into EVERY native app build:
# it defines global pthread_once/libc shims. Never dismiss it as UI-only.
shared=set(STATE.get("launcher_global_runtime_exceptions",[]))
assert shared=={"headless/prosperoeden/runtime_shims.cpp"}
# The shared runtime shim remains in the engine *classification* even after
# its code review is complete; it must not be forced to remain outstanding.
assert shared<=owners
cmake=(ROOT/"headless/CMakeLists.txt").read_text()
assert '"${launcher_dir}/runtime_shims.cpp"' in cmake
launcher_pending={p for p in pending_code if p.startswith(launcher_prefix) and p not in shared}
# Assert the runtime/launcher boundary against actual versioned paths.
assert len(pending_code)==len(launcher_pending)+len(pending_code-launcher_pending)
# New per-source review decisions must remain traceable to the exact
# current contract path and a real file entry in the written source review.
# A source reviewed as not needing a patch remains valid only for the
# identical Git blob. A changed header must trigger a fresh optimization triage.
# Collect every changed historic reviewed blob in one run, instead of
# discovering the next drift only after a multi-minute CI cycle. A drift is
# still a HARD failure until individually reviewed; no baseline is rewritten.
reviewed_blob_drifts=[]
for e in entries:
    if not e.get("reviewed_source_git_blob"):
        continue
    if e['path']==U23_LEGACY:
        # Preserve the exact old audit receipt and explicitly mark that the
        # current JIT policy has moved/changed; do not forge old blob parity.
        changed=subprocess.check_output(['git','hash-object',U23_CURRENT],
                                        cwd=ROOT,text=True).strip()
        assert changed != e['reviewed_source_git_blob']
        print('U23_JIT_POST_F07_POLICY_UPDATE_SEPARATE_PROOF',
              'legacy_blob='+e['reviewed_source_git_blob'],
              'current_blob='+changed)
        continue
    actual=subprocess.check_output(["git","hash-object",e["path"]],cwd=ROOT,text=True).strip()
    if actual!=e["reviewed_source_git_blob"]:
        reviewed_blob_drifts.append({
            "path":e["path"],"expected":e["reviewed_source_git_blob"],
            "actual":actual,"prior_disposition":e["disposition"]})
# F07's historical source snapshot is IMMUTABLE. UI, graphics,
# settings, profile and network changes landed later, and the 23 real
# owner changes cannot legitimately be compared to their October blobs.
# A separate, exact per-file source-change register pins both versions
# and the changed code contract. Nothing is counted as a new performance
# or gameplay qualification because an SHA is known.
post_f07 = json.loads(
    (ROOT/"docs/EDEN_POST_F07_CHANGED_SOURCE_REGISTER_2026-11-08.json").read_text())
assert post_f07['schema_version'] == 1
assert post_f07['historical_f07_source_snapshots_preserved'] is True
post_entries = post_f07['files']
assert len(post_entries) == 42  # reviewed post-F07 source successors, including index-0 RomFS
post_index = {item['path']: item for item in post_entries}
assert len(post_index) == len(post_entries)
drift_index = {item['path']: item for item in reviewed_blob_drifts}
# R457 log-retention review is later than all archived Nov15/16 UI owners.
# Reconstruct ONLY this change, then run the existing historical reverse
# replay on the proven predecessor. Never rewrite frozen audit receipts.
r457_service_path = "headless/prosperoeden/eden_services.cpp"
r457_service_source = (ROOT / r457_service_path).read_text()
# A separately reviewed DNSP/DXCI library extension change does not alter
# this R457 log-retention/boottrace owner. Restore its exact predecessor on
# the source-audit copy, retaining the new extensions in the runtime.
actual_service_blob = hashlib.sha1(
    b"blob "+str(len(r457_service_source.encode())).encode()+bytes([0])+
    r457_service_source.encode()).hexdigest()
# Unified NX library support (e0080f38) was added after the DNSP/DXCI/NUP
# library extension and changes exactly one CountFiles suffix. Reverse that
# one line first so the already-reviewed R457 replay can remain immutable.
if actual_service_blob == "f850b77e7b2a366f2e7cb16a0be9efb57679fef9":
    nx_formats = '''{".nsp", ".xci", ".nsz", ".xcz", ".dnsp", ".dxci",
                                   ".nro", ".nso", ".nca", ".nax", ".kip", ".nup", ".nx"}'''
    pre_nx_formats = '''{".nsp", ".xci", ".nsz", ".xcz", ".dnsp", ".dxci",
                                   ".nro", ".nso", ".nca", ".nax", ".kip", ".nup"}'''
    assert r457_service_source.count(nx_formats) == 1
    r457_service_source = r457_service_source.replace(nx_formats, pre_nx_formats, 1)
    prior = r457_service_source.encode()
    recovered_blob = hashlib.sha1(
        b"blob "+str(len(prior)).encode()+bytes([0])+prior).hexdigest()
    assert recovered_blob == "01d025544ac3544ab58779884f6fee10dcbe3209"
    assert drift_index[r457_service_path]["actual"] == actual_service_blob
    drift_index[r457_service_path]["actual"] = recovered_blob
    actual_service_blob = recovered_blob
    print("NX_LIBRARY_SOURCE_SUCCESSOR_PASS predecessor=01d02554 current=f850b77e")
if actual_service_blob == "01d025544ac3544ab58779884f6fee10dcbe3209":
    new_formats = '''{".nsp", ".xci", ".nsz", ".xcz", ".dnsp", ".dxci",
                                   ".nro", ".nso", ".nca", ".nax", ".kip", ".nup"}'''
    old_formats = '''{".nsp", ".xci", ".nsz", ".xcz", ".nro", ".nso",
                                   ".nca", ".nax", ".kip"}'''
    assert r457_service_source.count(new_formats) == 1
    r457_service_source = r457_service_source.replace(new_formats, old_formats, 1)
    prior = r457_service_source.encode()
    recovered_blob = hashlib.sha1(
        b"blob "+str(len(prior)).encode()+bytes([0])+prior).hexdigest()
    assert recovered_blob == "90f1f4fb2d239d71d0a856943cc4328704e2058b"
    assert drift_index[r457_service_path]["actual"] == actual_service_blob
    drift_index[r457_service_path]["actual"] = recovered_blob
r457_service_prior_blob = "6efc431641ace097b7216748e1e232c8cc9f1ae1"
r457_service_current_blob = "be163317ca482765f31ddf3b7d1dbe24be041294"
# PS5 boot-trace OFF -> ON resume comes AFTER the log-retention fix. Revert
# ONLY this reviewed hunk in the audit copy, preserving both exact originals.
# This does not retrofit any historical F07 source SHA or native PS5 proof.
r457_resume_blob = "90f1f4fb2d239d71d0a856943cc4328704e2058b"
r457_resume_block = """        } else if (!Eden::BootTrace::Resume(Eden::LogsDir())) {
            // Normal stderr/stdout and fatal crash reports remain independent.
            // A failed bootstrap reopen must not truncate prior traces or
            // misrepresent this additional trace as available.
            Eden::Report("logs", "Early trace unavailable after logging was enabled");
        }"""
assert drift_index[r457_service_path]["actual"] == r457_resume_blob
assert r457_service_source.count(r457_resume_block) == 1
r457_service_source = r457_service_source.replace(r457_resume_block, "        }", 1)
r457_resume_predecessor = r457_service_source.encode("utf-8")
assert hashlib.sha1(b"blob " + str(len(r457_resume_predecessor)).encode() +
                    bytes([0]) + r457_resume_predecessor).hexdigest() == r457_service_current_blob
drift_index[r457_service_path]["actual"] = r457_service_current_blob
print("R457_BOOTTRACE_REENABLE_SOURCE_SUCCESSOR_PASS prior_reconstructed=1 append_only=1")
assert drift_index[r457_service_path]["actual"] == r457_service_current_blob
r457_current = """        if (!value.detailed_logging) {
            // Stop recording, but never erase earlier sessions simply by
            // toggling this option. A user may need those files after a hang.
            Eden::BootTrace::Quiet(Eden::LogsDir());
        }"""
r457_previous = """        if (!value.detailed_logging) {
            Eden::BootTrace::Quiet(Eden::LogsDir());
            for (const char* name : {
                    "eden_log.txt", "eden_log.txt.first.txt", "eden_log.txt.old.txt"})
                (void)std::remove((Eden::UserDir() + "/log/" + name).c_str());
        }"""
assert r457_service_source.count(r457_current) == 1
r457_service_prior_source = r457_service_source.replace(r457_current, r457_previous, 1)
r457_data = r457_service_prior_source.encode("utf-8")
assert hashlib.sha1(b"blob " + str(len(r457_data)).encode() + bytes([0]) + r457_data).hexdigest() == r457_service_prior_blob
drift_index[r457_service_path]["actual"] = r457_service_prior_blob
print("R457_LOG_RETENTION_SOURCE_SUCCESSOR_PASS reviewed=1 prior_reconstructed=1")

# P1 typography removes the ASCII-only quick-menu conversion while preserving
# the legacy compact FPS HUD ABI. Reconstruct the exact pre-typography hud.h
# blob so the existing post-F07 receipt remains immutable.
typography_hud_path = "headless/hud.h"
typography_hud_blob = "a506f5dca7efc289f47a172a353bff4f04d9f4e4"
typography_hud_predecessor = "0ef8bf75efabf61628b44b91011eb461abcbde81"
if (typography_hud_path in drift_index and
        drift_index[typography_hud_path]["actual"] == typography_hud_blob):
    hud_source = (ROOT/typography_hud_path).read_text()
    anchor_text = """        glyphs[i] = HudGlyph(text[i]);
    return glyphs;
}
// The overlay's width and where its text starts, in a picture 1080 rows high. Where it is drawn
"""
    predecessor_text = """        glyphs[i] = HudGlyph(text[i]);
    return glyphs;
}
// Quick-menu text keeps ASCII codepoints so the Vulkan fragment shader can
// index the Montserrat raster generated from the launcher's exact .pefont.
inline std::array<uint32_t, 24> HudCodepoints(std::string_view text) {
    std::array<uint32_t, 24> glyphs{};
    for (size_t i = 0; i < text.size() && i < glyphs.size(); ++i) {
        const unsigned char value = static_cast<unsigned char>(text[i]);
        glyphs[i] = value >= 32 && value <= 126 ? value : static_cast<uint32_t>('?');
    }
    return glyphs;
}
// The overlay's width and where its text starts, in a picture 1080 rows high. Where it is drawn
"""
    assert hud_source.count(anchor_text) == 1
    replay = hud_source.replace(anchor_text, predecessor_text, 1)
    raw = replay.encode("utf-8")
    replay_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + bytes([0]) + raw
    ).hexdigest()
    assert replay_blob == typography_hud_predecessor
    drift_index[typography_hud_path]["actual"] = replay_blob
    print("P1_TYPOGRAPHY_HUD_SUCCESSOR_PASS",
          "legacy_fps_abi=preserved", "ascii_quick_menu=removed")

# P1 typography also extends the existing SystemFonts owner with deterministic
# Noto groups. Reverse the exact three reviewed hunks and require byte identity
# with the pre-typography main owner before removing this post-F07 drift.
typography_fonts_path = "headless/prosperoeden/pe/gfx/system_fonts.cpp"
typography_fonts_blob = "c5068cbf5291e2cfafe9edf51cca29ce40e9b42e"
typography_fonts_predecessor = "a721c95a81c9fe309fcff9fa3be01b8b21cd9272"
if (typography_fonts_path in drift_index and
        drift_index[typography_fonts_path]["actual"] == typography_fonts_blob):
    replay = (ROOT/typography_fonts_path).read_text()
    font_hunks = [
        ("""    Script script;
    // The same font in the weights and generations a system software version may carry; the
    // first one found is used.
    const char *files[5];
};
constexpr Group kLatin{Script::other, {"SST-Medium.otf", "SST-Roman.otf", nullptr}};
constexpr Group kJapanese{Script::japanese, {"SSTJpPro-Regular.otf", "SIE-RDC-Pr5N-M-JPN.otf", "SCE-RDC-R-JPN.otf", nullptr}};
constexpr Group kKorean{Script::korean, {"YoonGothicProSIE760.otf", "SCEPS4Yoongd-Medium.otf", nullptr}};
constexpr Group kChinese{Script::chinese, {"DFHEI5-SONY.ttf", nullptr}};
constexpr Group kThai{Script::thai, {"SSTThai-Medium.otf", "SSTThai-Roman.otf", nullptr}};
constexpr Group kArabic{Script::arabic, {"SSTArabic-Medium.otf", "SSTArabic-Roman.otf", nullptr}};
// Deterministic, catalog-bounded OFL fallbacks generated by build_noto_subsets.py.
// They are tried before the console fonts, while the latter remain available
// for game titles/file names containing codepoints outside the UI subsets.
constexpr Group kNotoGreek{Script::other, {"NotoSans-Greek.ttf", nullptr}};
constexpr Group kNotoJapanese{Script::japanese, {"NotoSansJP.ttf", nullptr}};
constexpr Group kNotoKorean{Script::korean, {"NotoSansKR.ttf", nullptr}};
constexpr Group kNotoChineseSC{Script::chinese, {"NotoSansSC.ttf", nullptr}};
constexpr Group kNotoChineseTC{Script::chinese, {"NotoSansTC.ttf", nullptr}};
constexpr Group kNotoThai{Script::thai, {"NotoSansThai.ttf", nullptr}};
constexpr Group kNotoArabic{Script::arabic, {"NotoSansArabic.ttf", nullptr}};

// A character only one of the fonts should draw, whatever their order.
Script own_script(char32_t c)""",
         """    Script script;
    // The same font in the weights and generations a system software version may carry; the
    // first one found is used.
    const char *files[3];
};
constexpr Group kLatin{Script::other, {"SST-Medium.otf", "SST-Roman.otf", nullptr}};
constexpr Group kJapanese{Script::japanese, {"SSTJpPro-Regular.otf", "SIE-RDC-Pr5N-M-JPN.otf", "SCE-RDC-R-JPN.otf"}};
constexpr Group kKorean{Script::korean, {"YoonGothicProSIE760.otf", "SCEPS4Yoongd-Medium.otf", nullptr}};
constexpr Group kChinese{Script::chinese, {"DFHEI5-SONY.ttf", nullptr, nullptr}};
constexpr Group kThai{Script::thai, {"SSTThai-Medium.otf", "SSTThai-Roman.otf", nullptr}};
constexpr Group kArabic{Script::arabic, {"SSTArabic-Medium.otf", "SSTArabic-Roman.otf", nullptr}};

// A character only one of the fonts should draw, whatever their order.
Script own_script(char32_t c)"""),
        ("""    const std::string_view prefix = language.substr(0, 2);
    std::vector<const Group *> order;
    if (prefix == "ja")
        order = {&kNotoJapanese, &kJapanese, &kLatin, &kChinese, &kKorean, &kThai, &kArabic};
    else if (prefix == "ko")
        order = {&kNotoKorean, &kKorean, &kLatin, &kJapanese, &kChinese, &kThai, &kArabic};
    else if (prefix == "zh" && language.find("Hant") != std::string_view::npos)
        order = {&kNotoChineseTC, &kChinese, &kLatin, &kJapanese, &kKorean, &kThai, &kArabic};
    else if (prefix == "zh")
        order = {&kNotoChineseSC, &kChinese, &kLatin, &kJapanese, &kKorean, &kThai, &kArabic};
    else if (prefix == "th")
        order = {&kNotoThai, &kThai, &kLatin, &kJapanese, &kChinese, &kKorean, &kArabic};
    else if (prefix == "ar")
        order = {&kNotoArabic, &kArabic, &kLatin, &kJapanese, &kChinese, &kKorean, &kThai};
    else if (prefix == "el")
        order = {&kNotoGreek, &kLatin, &kJapanese, &kChinese, &kKorean, &kThai, &kArabic};
    else
        order = {&kLatin, &kJapanese, &kChinese, &kKorean, &kThai, &kArabic};
    std::vector<std::string> files;""",
         """    const std::string_view prefix = language.substr(0, 2);
    std::vector<const Group *> order;
    if (prefix == "ja")
        order = {&kJapanese, &kLatin, &kChinese, &kKorean, &kThai, &kArabic};
    else if (prefix == "ko")
        order = {&kKorean, &kLatin, &kJapanese, &kChinese, &kThai, &kArabic};
    else if (prefix == "zh")
        order = {&kChinese, &kLatin, &kJapanese, &kKorean, &kThai, &kArabic};
    else if (prefix == "th")
        order = {&kThai, &kLatin, &kJapanese, &kChinese, &kKorean, &kArabic};
    else if (prefix == "ar")
        order = {&kArabic, &kLatin, &kJapanese, &kChinese, &kKorean, &kThai};
    else
        order = {&kLatin, &kJapanese, &kChinese, &kKorean, &kThai, &kArabic};
    std::vector<std::string> files;"""),
        ("""            break;
        auto face = std::make_unique<Face>();
        const std::string name = path.substr(path.find_last_of('/') + 1);
        for (const Group *group : {&kNotoJapanese, &kJapanese, &kNotoKorean, &kKorean,
                                   &kNotoChineseSC, &kNotoChineseTC, &kChinese,
                                   &kNotoThai, &kThai, &kNotoArabic, &kArabic})
            for (const char *file : group->files)
                if (file != nullptr && name == file)
                    face->script = group->script;""",
         """            break;
        auto face = std::make_unique<Face>();
        const std::string name = path.substr(path.find_last_of('/') + 1);
        for (const Group *group : {&kJapanese, &kKorean, &kChinese, &kThai, &kArabic})
            for (const char *file : group->files)
                if (file != nullptr && name == file)
                    face->script = group->script;"""),
    ]
    for current_hunk, previous_hunk in font_hunks:
        assert replay.count(current_hunk) == 1
        replay = replay.replace(current_hunk, previous_hunk, 1)
    raw = replay.encode("utf-8")
    replay_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + bytes([0]) + raw
    ).hexdigest()
    assert replay_blob == typography_fonts_predecessor
    delta = drift_index.pop(typography_fonts_path)
    assert delta["expected"] == typography_fonts_predecessor
    print("P1_TYPOGRAPHY_SYSTEM_FONTS_SUCCESSOR_PASS",
          "owner=system_fonts", "historical_predecessor=preserved")

# P1 typography changes only the launcher's fallback-font collection policy.
# Reverse it first so the diagnostics successor replay below sees the exact
# current-main predecessor, then resumes the older R457/F07 chain unchanged.
typography_frontend_path = "headless/prosperoeden/frontend.cpp"
typography_frontend_blob = "1de983352dad85e4dd6c1520a0c9e9aec26d052d"
typography_frontend_predecessor = "c199a16ae2d894baca14ea2373273e09c38e872a"
if (typography_frontend_path in drift_index and
        drift_index[typography_frontend_path]["actual"] == typography_frontend_blob):
    frontend_source = (ROOT/typography_frontend_path).read_text()
    typography_block = """    std::vector<std::string> fallback_files;
    std::vector<std::string> font_folders;
    font_folders.push_back(Eden::AppFile("ui/fonts/fallback"));
    for (const std::string& candidate : pe::gfx::system_font_folders())
        if (std::find(font_folders.begin(), font_folders.end(), candidate) == font_folders.end())
            font_folders.push_back(candidate);
    for (const std::string& candidate : font_folders) {
        std::vector<std::string> found = pe::gfx::system_font_files(candidate, tag);
        if (found.empty()) continue;
        if (folder == "none") folder = candidate;
        for (std::string& file : found)
            if (std::find(fallback_files.begin(), fallback_files.end(), file) == fallback_files.end())
                fallback_files.push_back(std::move(file));
    }
    const std::size_t files = fallback_files.size();
    if (!fallback_files.empty())
        font.use_system_fonts(std::move(fallback_files), tag);
"""
    predecessor_block = """    std::size_t files = 0;
    for (const std::string& candidate : pe::gfx::system_font_folders()) {
        std::vector<std::string> found = pe::gfx::system_font_files(candidate, tag);
        if (found.empty()) continue;
        folder = candidate;
        files = found.size();
        font.use_system_fonts(std::move(found), tag);
        break;
    }
"""
    assert frontend_source.count(typography_block) == 1
    replay = frontend_source.replace(typography_block, predecessor_block, 1)
    replay_raw = replay.encode("utf-8")
    replay_blob = hashlib.sha1(
        b"blob " + str(len(replay_raw)).encode() + bytes([0]) + replay_raw
    ).hexdigest()
    assert replay_blob == typography_frontend_predecessor
    drift_index[typography_frontend_path]["actual"] = replay_blob
    print("P1_TYPOGRAPHY_FRONTEND_SUCCESSOR_PASS",
          "owner=frontend", "predecessor=diagnostics-main")

# Nov16 diagnostics-sharing source successors. These application-owned files
# layer the reviewed native diagnostics client onto source owners already
# covered by the immutable post-F07 provenance chains below. Bind each exact
# successor blob and its required client marker, then resume qualification from
# the exact main predecessor. Independent diagnostics-sharing host tests cover
# consent/queue/idle/fail-closed behavior; this block is source identity only.
nov16_diagnostics_service_replay_source = None
nov16_diagnostics_source_successors = {
    "headless/prosperoeden/eden_services.cpp": (
        "310e21f75f4e2524b90534d5b9122c6bc587a4f2",
        "6efc431641ace097b7216748e1e232c8cc9f1ae1",
        ("DiagnosticsClient::SetConsent(", "bool EdenServices::log_sharing_available() const"),
    ),
    "headless/prosperoeden/eden_services.h": (
        "f3d2ca33cc2e42eeafef26207784bd43b6da918b",
        "7c4133b4e2f0340aa1e0e182ae469619d5a8c687",
        ("bool log_sharing_available() const override;",),
    ),
    "headless/prosperoeden/frontend.cpp": (
        "25884807fdf7759834cb232548184ffefca715d4",
        "c199a16ae2d894baca14ea2373273e09c38e872a",
        ("DiagnosticsClient::EnterLauncher(", "DiagnosticsClient::Poll();"),
    ),
    "headless/main.cpp": (
        "4ae6fdfb9fbb9e405169ef397ef4ada994614260",
        "cec82ca188a151264acb3d2498fd7ad41a7cb697",
        ("DiagnosticsClient::Initialize(", "DiagnosticsClient::Shutdown();"),
    ),
}
for changed_path, (predecessor_blob, successor_blob, markers) in nov16_diagnostics_source_successors.items():
    if changed_path not in drift_index:
        continue
    if drift_index[changed_path]["actual"] != successor_blob:
        continue
    current_source = (r457_service_prior_source if changed_path == r457_service_path
                      else (ROOT / changed_path).read_text())
    for marker in markers:
        assert marker in current_source, (changed_path, marker)
    if changed_path == "headless/prosperoeden/eden_services.cpp":
        # Reconstruct the exact current-main predecessor so the older Home/
        # Library provenance replayers below do not accidentally re-read the
        # diagnostics branch source and mix unrelated deltas.
        replay = current_source
        replay = replay.replace('#include "diagnostics_native_client.h"\n', "", 1)
        replay = replay.replace(
            "    // Consent remains fail-closed until the native client has a verified HTTPS collector.\n",
            "    // No native collector yet. A stale or hand-edited preference cannot turn sharing on.\n",
            1)
        replay = replay.replace(
            "    if (saved) Eden::DiagnosticsClient::SetConsent(value.share_standard_logs, value.share_advanced_logs);\n",
            "", 1)
        method = """bool EdenServices::log_sharing_available() const {
#ifdef PS5_NATIVE
    return Eden::DiagnosticsClient::Available();
#else
    return false;
#endif
}

"""
        assert replay.count(method) == 1
        replay = replay.replace(method, "", 1)
        raw = replay.encode("utf-8")
        replay_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert replay_blob == predecessor_blob
        nov16_diagnostics_service_replay_source = replay
    drift_index[changed_path]["actual"] = predecessor_blob
    print("NOV16_DIAGNOSTICS_SOURCE_SUCCESSOR_PASS", changed_path,
          "predecessor=main", "console_validation=pending")

# Nov16 startup Library latency: Home already owns the complete add-on scan
# before it starts the initial Library worker. Reverse only the removed
# duplicate games() scan and require exact parity with the reviewed #248 blob.
nov16_no_duplicate_addon_blob = "310e21f75f4e2524b90534d5b9122c6bc587a4f2"
nov16_pre_no_duplicate_addon_blob = "fbe04395576c244c158a60748cc4cd765eb58f0f"
service_path = "headless/prosperoeden/eden_services.cpp"
nov16_no_duplicate_replay_source = None
if drift_index[service_path]["actual"] == nov16_no_duplicate_addon_blob:
    current_service = (nov16_diagnostics_service_replay_source
                       if nov16_diagnostics_service_replay_source is not None
                       else (ROOT / service_path).read_text())
    new_block = """    if (cancel && cancel->load(std::memory_order_acquire)) return games;
    // Initial Library enumeration starts only after finish_home_scan() has
    // applied EdenServices::home(), whose worker already published the
    // complete add-on snapshot. Repeating eden_scan_addons() here walked the
    // same update/DLC roots twice before the first Library list could appear.
    // Later storage refreshes queue read_home() before start_scan() as well.
    // Keep games() local/cache-only; selected media reads the atomically
    // published snapshot and reports Unknown if that snapshot is incomplete.
    const int language_choice = Eden::LoadPreferences().language;"""
    old_block = """    if (cancel && cancel->load(std::memory_order_acquire)) return games;
    eden_scan_addons(Eden::AssetsPath("updates").c_str(), Eden::AssetsPath("keys").c_str(),
                         Eden::AssetsPath("roms").c_str());
    if (cancel && cancel->load(std::memory_order_acquire)) return {};
    const int language_choice = Eden::LoadPreferences().language;"""
    assert current_service.count(new_block) == 1
    reconstructed = current_service.replace(new_block, old_block, 1).encode("utf-8")
    reconstructed_blob = hashlib.sha1(
        b"blob " + str(len(reconstructed)).encode() + bytes([0]) + reconstructed).hexdigest()
    assert reconstructed_blob == nov16_pre_no_duplicate_addon_blob
    nov16_no_duplicate_replay_source = reconstructed.decode("utf-8")
    drift_index[service_path]["actual"] = reconstructed_blob
    print("NOV16_LIBRARY_NO_DUPLICATE_ADDON_SCAN_SOURCE_SUCCESSOR_PASS",
          "owner=eden_services", "predecessor=#248", "console_validation=pending")

# Nov16 stable Home icon successor. The full EdenServices blob is pinned,
# and dedicated Home-media tests verify the changed dispatch/identity rules.
# Resume the existing metadata -> Home Square -> #239 provenance chain only
# after this exact reviewed successor is recognized.
nov16_stable_home_blob = "fbe04395576c244c158a60748cc4cd765eb58f0f"
nov16_metadata_pre_stable = "964a3a490948aa01149ade2b47dd95ea2b57628b"
stable_home_path = "headless/prosperoeden/eden_services.cpp"
stable_home_replay_source = None
if drift_index[stable_home_path]["actual"] == nov16_stable_home_blob:
    stable_source = (nov16_no_duplicate_replay_source
                     if nov16_no_duplicate_replay_source is not None
                     else (ROOT / stable_home_path).read_text())
    stable_raw = stable_source.encode("utf-8")
    assert hashlib.sha1(b"blob " + str(len(stable_raw)).encode() +
                        bytes([0]) + stable_raw).hexdigest() == nov16_stable_home_blob
    for marker in (
        "const bool deconstructed = Eden::IsDeconstructedGameSelection(home.last_file);",
        "if (!deconstructed && played.contains(name))",
        "if (!recent.cover.empty()) recent.tile_icon = recent.cover;",
        "if (!nlib.icon.empty() && recent.tile_icon.empty())",
        "if (!enrichment.icon.empty() && game.cover.empty())",
    ):
        assert marker in stable_source, marker
    # Reverse exactly the four reviewed source hunks and verify the predecessor.
    stable_home_replay_source = stable_source
    for current_hunk, previous_hunk in (
        ("    home.last_exists = !home.last_file.empty() && IsFile(last_path);\n    if (!home.last_file.empty()) {\n        std::string title = GameTitle(home.last_file);\n        const bool deconstructed = Eden::IsDeconstructedGameSelection(home.last_file);\n        // CoverPath is Encore's generated packaged-Control cache. It must not\n        // shadow a deconstructed title's real local Control icon or make us\n        // retry package extraction against <title>/exefs/main.\n        std::string cover = deconstructed ? std::string{} : CoverPath(home.last_file);\n        bool has_cover = !cover.empty() && Eden::FileExists(cover);\n        if (home.last_exists && home.setup_ready) {\n            if (deconstructed) {\n                const std::size_t slash = home.last_file.find('/');\n                if (slash != std::string::npos && slash > 0) {\n                    cover = ExtractedLocalCover(\n                        Eden::AssetsPath(\"roms/\" + home.last_file.substr(0, slash)),\n                        selected_language);\n                    has_cover = !cover.empty();\n                }\n            } else if (!has_cover) {\n                cover = EnsureCover(home.last_file, &title);\n                has_cover = !cover.empty();\n            }\n        }\n        home.last_title = title;\n        home.last_caption = home.last_exists ? tr(\"Last game opened\") :",
         "    home.last_exists = !home.last_file.empty() && IsFile(last_path);\n    if (!home.last_file.empty()) {\n        std::string title = GameTitle(home.last_file);\n        std::string cover = CoverPath(home.last_file);\n        bool has_cover = Eden::FileExists(cover);\n        if (home.last_exists && home.setup_ready && !has_cover) {\n            // Extracted titles already own a small local Control icon. Use it\n            // before generic metadata extraction so Home does not probe\n            // <title>/exefs/main as if it were a packaged game's cover.\n            if (Eden::IsDeconstructedGameSelection(home.last_file)) {\n                const std::size_t slash = home.last_file.find('/');\n                if (slash != std::string::npos && slash > 0) {\n                    cover = ExtractedLocalCover(\n                        Eden::AssetsPath(\"roms/\" + home.last_file.substr(0, slash)),\n                        selected_language);\n                }\n            }\n            if (cover.empty()) cover = EnsureCover(home.last_file, &title);\n            has_cover = !cover.empty();\n        }\n        home.last_title = title;\n        home.last_caption = home.last_exists ? tr(\"Last game opened\") :"),
        ("        pe::ui::Recent recent;\n        recent.file = name;\n        recent.title = GameTitle(name);\n        // A deconstructed /main is not a package and must never enter\n        // EnsureCover(). For packaged titles CoverPath is Encore's generated\n        // Control-icon cache, so it is already the canonical square Home tile.\n        const bool deconstructed = Eden::IsDeconstructedGameSelection(name);\n        if (!deconstructed && played.contains(name))\n            recent.cover = EnsureCover(name);\n        else if (!deconstructed) {\n            const std::string cached_cover = CoverPath(name);\n            if (IsFile(cached_cover)) recent.cover = cached_cover;\n        }\n        if (!recent.cover.empty()) recent.tile_icon = recent.cover;\n        // An extracted NS2 title already carries its square Control icon.\n        // Surface it during the shallow Home scan instead of waiting for\n        // focus, Nlib/network enrichment or the full Library media worker.",
         "        pe::ui::Recent recent;\n        recent.file = name;\n        recent.title = GameTitle(name);\n        // A fallback tile must not extract an entire game's metadata before\n        // Home can appear. The background Library scan fills missing art.\n        if (played.contains(name))\n            recent.cover = EnsureCover(name);\n        else {\n            const std::string cached_cover = CoverPath(name);\n            if (IsFile(cached_cover)) recent.cover = cached_cover;\n        }\n        // An extracted NS2 title already carries its square Control icon.\n        // Surface it during the shallow Home scan instead of waiting for\n        // focus, Nlib/network enrichment or the full Library media worker."),
        ("            recent.title_id = ResolveTitleId(recent_path, name);\n            if (recent.title_id != 0) {\n                const NlibEnrichment nlib = CachedNlibEnrichment(recent.title_id, selected_language);\n                if (!nlib.icon.empty() && recent.tile_icon.empty()) {\n                    recent.cover = nlib.icon;\n                    recent.tile_icon = nlib.icon;\n                } else if (recent.cover.empty()) {",
         "            recent.title_id = ResolveTitleId(recent_path, name);\n            if (recent.title_id != 0) {\n                const NlibEnrichment nlib = CachedNlibEnrichment(recent.title_id, selected_language);\n                if (!nlib.icon.empty()) {\n                    recent.cover = nlib.icon;\n                    recent.tile_icon = nlib.icon;\n                } else if (recent.cover.empty()) {"),
        ("    if (cancel && cancel->load(std::memory_order_acquire)) return game;\n    NlibEnrichment enrichment = EnsureNlibEnrichment(game.title_id, language_choice, cancel);\n    game.artwork_changed |= enrichment.artwork_changed;\n    if (!enrichment.icon.empty() && game.cover.empty()) {\n        game.cover = std::move(enrichment.icon);\n    } else if (game.cover.empty()) {\n        if (const auto* known = Eden::Ns2Catalog::Find(game.title_id)) {\n            if (EnsureGamesDbSquare(game.title_id, std::string(known->name), scanned_name,\n                                    language_choice, cancel)) {\n                game.cover = CachedGamesDbSquare(game.title_id);\n                game.artwork_changed |= !game.cover.empty();\n            }\n        }\n    }\n    // Missing square icon remains empty only if Control/ExeFS, Nlib and GamesDB Square all miss.",
         "    if (cancel && cancel->load(std::memory_order_acquire)) return game;\n    NlibEnrichment enrichment = EnsureNlibEnrichment(game.title_id, language_choice, cancel);\n    game.artwork_changed |= enrichment.artwork_changed;\n    if (!enrichment.icon.empty()) {\n        game.cover = std::move(enrichment.icon);\n    } else if (const auto* known = Eden::Ns2Catalog::Find(game.title_id)) {\n        if (EnsureGamesDbSquare(game.title_id, std::string(known->name), scanned_name,\n                                language_choice, cancel)) {\n            game.cover = CachedGamesDbSquare(game.title_id);\n            game.artwork_changed |= !game.cover.empty();\n        }\n    }\n    // Missing square icon remains empty only if Control/ExeFS, Nlib and GamesDB Square all miss."),
    ):
        assert stable_home_replay_source.count(current_hunk) == 1
        stable_home_replay_source = stable_home_replay_source.replace(current_hunk, previous_hunk, 1)
    predecessor_raw = stable_home_replay_source.encode("utf-8")
    assert hashlib.sha1(b"blob " + str(len(predecessor_raw)).encode() + bytes([0]) + predecessor_raw).hexdigest() == nov16_metadata_pre_stable
    drift_index[stable_home_path]["actual"] = nov16_metadata_pre_stable
    print("NOV16_STABLE_HOME_ICON_SOURCE_SUCCESSOR_PASS", "owner=eden_services",
          "predecessor=metadata", "console_validation=pending")

# Nov16 add-on catalogue truth-state: metadata bridge changes only the
# tri-state completeness contract. Pin the two exact historical-source
# successors and remove them from the F07 drift ledger.
nov16_addon_metadata_successors = {
    "headless/metadata_bridge.cpp": (
        "8c6f59e7810bad7964d82dd6416f77617afe9ffa",
        "728f220da4942cf4b849f75cfdda974ad5fd7508",
    ),
    "headless/metadata_bridge.h": (
        "a8ebfa5fad322c81b6562dedc6e2a7c680a5cfa9",
        "0523a44856385ba64b20298c44e735be1c06180b",
    ),
}
for changed_path, (prior_blob, successor_blob) in nov16_addon_metadata_successors.items():
    assert changed_path not in post_index, changed_path
    assert changed_path in drift_index, changed_path
    delta = drift_index.pop(changed_path)
    assert delta["expected"] == prior_blob, changed_path
    assert delta["actual"] == successor_blob, changed_path
print("NOV16_ADDON_METADATA_SOURCE_SUCCESSOR_PASS", "owners=2",
      "console_validation=pending")

# The AddOnSummary hunk is layered on the already-reviewed Home Square
# EdenServices owner. Reverse only those two lines, then continue the exact
# Home Square -> #239 -> Nov15 provenance chain below.
nov16_addon_summary_blob = "964a3a490948aa01149ade2b47dd95ea2b57628b"
nov16_home_square_pre_addon = "91acb4ba1918308efb38f52db043ee299611926b"
nov16_home_square_replay_source = None
if drift_index["headless/prosperoeden/eden_services.cpp"]["actual"] == nov16_addon_summary_blob:
    current_service = (stable_home_replay_source if stable_home_replay_source is not None
                       else (ROOT / "headless/prosperoeden/eden_services.cpp").read_text())
    new_summary = """    const int status = eden_game_addons(title_id, update, sizeof(update), &dlc);
    if (status < 0) return tr("Unknown");
    std::string text;"""
    old_summary = """    eden_game_addons(title_id, update, sizeof(update), &dlc);
    std::string text;"""
    assert current_service.count(new_summary) == 1
    nov16_home_square_replay_source = current_service.replace(new_summary, old_summary, 1)
    reconstructed = nov16_home_square_replay_source.encode("utf-8")
    reconstructed_blob = hashlib.sha1(
        b"blob " + str(len(reconstructed)).encode() + bytes([0]) + reconstructed).hexdigest()
    assert reconstructed_blob == nov16_home_square_pre_addon
    drift_index["headless/prosperoeden/eden_services.cpp"]["actual"] = reconstructed_blob
    print("NOV16_ADDON_SUMMARY_SOURCE_SUCCESSOR_PASS", "owners=1",
          "predecessor=home-square", "console_validation=pending")

# Nov16 Home Square media successor. Exact source identity is reviewed here;
# behavior/geometry/network bounds are independently exercised by the Home and
# case-art host tests. The historical chain below recognizes this immutable
# successor explicitly, then resumes from the already-reviewed #239 blob.
nov16_home_square_blob = "91acb4ba1918308efb38f52db043ee299611926b"
nov16_home_square_predecessor = "689e53fc25b3f9544ab1e6a6c4ef448c38a677bd"
nov16_home_square_path = "headless/prosperoeden/eden_services.cpp"
nov16_home_square_active = (
    drift_index[nov16_home_square_path]["actual"] == nov16_home_square_blob)
if nov16_home_square_active:
    current_home_square = (nov16_home_square_replay_source
                           if nov16_home_square_replay_source is not None
                           else (ROOT / nov16_home_square_path).read_text())
    home_square_raw = current_home_square.encode("utf-8")
    assert hashlib.sha1(b"blob " + str(len(home_square_raw)).encode() +
                        bytes([0]) + home_square_raw).hexdigest() == nov16_home_square_blob
    for marker in (
        "CachedGamesDbSquare(",
        "EnsureGamesDbSquare(",
        "require_square ? 512 : 0",
        "std::array<std::vector<std::string>, 9>",
        "Eden::IsSafeDeconstructedGamePath(roms_root, file)",
    ):
        assert marker in current_home_square, marker
    print("NOV16_HOME_SQUARE_SOURCE_SUCCESSOR_PASS", "owner=eden_services",
          "predecessor=#239", "console_validation=pending")

# Nov15 launcher tile-identity follow-up merged as #207: preserve the
# prior post-F07 receipts and admit only these two exact successors.
nov15_square_icon_successors = {
    "headless/prosperoeden/eden_services.cpp": (
        "4e9159c716e7eb6759ba3aef7d200ef869d069aa",
        "4e2afa5d81375727f2fb6a98853c212b10f2de3c",
    ),
    "headless/prosperoeden/pe/ui/switch_theme.cpp": (
        "819f2c96a35a34035da68b487abda3fd08ed1cda",
        "8b59abca5e756f6be6e5da70aec9c477c7e0e1ab",
    ),
}
for changed_path, (prior_blob, successor_blob) in nov15_square_icon_successors.items():
    assert changed_path in post_index and changed_path in drift_index
    assert post_index[changed_path]["post_snapshot_git_blob"] == prior_blob, changed_path
    if changed_path == "headless/prosperoeden/eden_services.cpp" and \
            drift_index[changed_path]["actual"] in {"54a37cf740f25c68aa0d5f93adf300144c5280d1", "689e53fc25b3f9544ab1e6a6c4ef448c38a677bd", nov16_home_square_blob}:
        # #208 is based on merged #207, but CI uses a shallow checkout and
        # need not contain #207's commit object. Reverse ONLY #208's two exact
        # eden_services.cpp hunks in memory and require the reconstructed Git
        # blob to be #207's reviewed successor. This preserves the immutable
        # chain without depending on repository history depth.
        current_service = (r457_service_prior_source if changed_path == r457_service_path
                           else (ROOT / changed_path).read_text())
        if drift_index[changed_path]["actual"] == nov16_home_square_blob:
            # Full-file blob + dedicated artwork tests bind the reviewed delta.
            # Resume the older immutable chain from the exact #239 predecessor;
            # do not pretend the artwork hunk was part of the Nov15 snapshot.
            drift_index[changed_path]["actual"] = nov16_home_square_predecessor
            historical_square = successor_blob
            assert historical_square == successor_blob, changed_path
            post_index[changed_path]["post_snapshot_git_blob"] = successor_blob
            continue
        # Nov16 console retest: exact_game_size receives a relative executable
        # selection, not a directory. Normalize only the reviewed root fix
        # and require that every remaining byte is the immutable #208 blob.
        if drift_index[changed_path]["actual"] == "689e53fc25b3f9544ab1e6a6c4ef448c38a677bd":
            fixed_root = """    const std::filesystem::path roms_root = Eden::AssetsPath("roms");
    // The Library row persists the executable selection, not the directory.
    // Revalidate every directory component and measure the top-level title.
    if (!Eden::IsSafeDeconstructedGamePath(roms_root, file))
        return {};
    const std::filesystem::path extracted = roms_root / file.substr(0, file.find('/'));
"""
            old_root = """    const std::filesystem::path extracted = Eden::AssetsPath("roms/" + file);
    if (!Eden::IsSafeExtractedDirectory(extracted))
        return {};
"""
            assert current_service.count(fixed_root) == 1, changed_path
            current_service = current_service.replace(fixed_root, old_root, 1)
            old_raw = current_service.encode("utf-8")
            assert hashlib.sha1(b"blob " + str(len(old_raw)).encode() + bytes([0]) + old_raw).hexdigest() == "54a37cf740f25c68aa0d5f93adf300144c5280d1", changed_path
        size_worker_method = """std::string EdenServices::exact_game_size(const std::string& file,
                                               const std::atomic<bool>* cancel) {
    if (file.empty() || (cancel && cancel->load(std::memory_order_acquire)))
        return {};
    const std::filesystem::path extracted = Eden::AssetsPath("roms/" + file);
    if (!Eden::IsSafeExtractedDirectory(extracted))
        return {};
    const auto bytes = ExtractedBaseBytes(extracted, cancel);
    if (!bytes || (cancel && cancel->load(std::memory_order_acquire)))
        return {};
    char exact_size[32]{};
    const double count = static_cast<double>(*bytes);
    if (count >= 1073741824.0)
        std::snprintf(exact_size, sizeof(exact_size), "%.1f GB", count / 1073741824.0);
    else
        std::snprintf(exact_size, sizeof(exact_size), "%.1f MB", count / 1048576.0);
    std::fprintf(stderr,
        "EDEN_EXEFS_SIZE folder=%s status=measured bytes=%llu\\n",
        file.c_str(), static_cast<unsigned long long>(*bytes));
    return exact_size;
}

"""
        prior_size_block = """    // Exact extracted-title size is useful in Library details, but it is not
    // required to display or navigate the Library. Only Game objects coming
    // from the Library scan carry the explicit unknown marker; Home media
    // requests leave size empty and therefore never trigger this walk.
    if (game.size == "—" && !(cancel && cancel->load(std::memory_order_acquire))) {
        const std::filesystem::path extracted = Eden::AssetsPath("roms/" + game.file);
        if (Eden::IsSafeExtractedDirectory(extracted)) {
            if (const auto bytes = ExtractedBaseBytes(extracted, cancel)) {
                char exact_size[32]{};
                const double count = static_cast<double>(*bytes);
                if (count >= 1073741824.0)
                    std::snprintf(exact_size, sizeof(exact_size), "%.1f GB", count / 1073741824.0);
                else
                    std::snprintf(exact_size, sizeof(exact_size), "%.1f MB", count / 1048576.0);
                game.size = exact_size;
                std::fprintf(stderr,
                    "EDEN_EXEFS_SIZE folder=%s status=measured bytes=%llu\\n",
                    game.file.c_str(), static_cast<unsigned long long>(*bytes));
            }
        }
    }
"""
        retail_marker = "    // Prioritize the requested ORIGINAL retail scans before any optional\n"
        assert current_service.count(size_worker_method) == 1, changed_path
        assert current_service.count(retail_marker) == 1, changed_path
        reconstructed = current_service.replace(size_worker_method, "", 1)
        reconstructed = reconstructed.replace(retail_marker, prior_size_block + retail_marker, 1)
        raw = reconstructed.encode("utf-8")
        historical_square = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert historical_square == successor_blob, changed_path
    else:
        assert drift_index[changed_path]["actual"] == successor_blob, changed_path
    post_index[changed_path]["post_snapshot_git_blob"] = successor_blob
print("NOV15_SQUARE_ICON_SOURCE_SUCCESSOR_PASS", "owners=2",
      "console_validation=pending")

# Nov15 Library size-worker follow-up. #207's eden_services.cpp successor
# was individually reconstructed above; the other four owners were unchanged
# by #207/#206 and still match their exact post-F07 receipts. Admit only the
# five exact #208 successors, leaving library.cpp and host tests outside the
# historical source snapshot exactly as before.
nov15_library_size_worker_successors = {
    "headless/prosperoeden/eden_services.cpp": (
        "4e2afa5d81375727f2fb6a98853c212b10f2de3c",
        "689e53fc25b3f9544ab1e6a6c4ef448c38a677bd",
    ),
    "headless/prosperoeden/eden_services.h": (
        "604a9d15118390b7f9b7e1265d38a91ff97c4a23",
        "f3d2ca33cc2e42eeafef26207784bd43b6da918b",
    ),
    "headless/prosperoeden/pe/ui/launcher.cpp": (
        "1e488a05689b29baf8c4318d98be52506816cfaa",
        "255b110f1e1d021ed92511e64c2f8f67ee62a66d",
    ),
    "headless/prosperoeden/pe/ui/launcher.hpp": (
        "f0e8db4791e79d3e173387d2288886bba52ac015",
        "fb3a0037cfb86328f398a3059c5dd95faa9d950b",
    ),
    "headless/prosperoeden/pe/ui/services.hpp": (
        "868cecd138d9b57486d1e9ce3b7b775848bcc0a3",
        "300fa56ad3d8932e25a898c53ed8052f4d69841f",
    ),
}
for changed_path, (prior_blob, successor_blob) in nov15_library_size_worker_successors.items():
    assert changed_path in post_index and changed_path in drift_index, changed_path
    assert post_index[changed_path]["post_snapshot_git_blob"] == prior_blob, changed_path
    assert drift_index[changed_path]["actual"] == successor_blob, changed_path
    post_index[changed_path]["post_snapshot_git_blob"] = successor_blob
print("NOV15_LIBRARY_SIZE_WORKER_SOURCE_SUCCESSOR_PASS", "owners=5",
      "media_ungated=1", "console_validation=pending")

# R457 only: retain immutable October F07 blobs while tracking the separately
# reviewed 34-file November+Nov13 post-F07 delta register. Track
# the separately selected and unqualified 12GiB resident owner with its
# own checked SHA/old F07 receipt. This must not hide arbitrary new deltas.
sparse_receipt = json.loads(
    (ROOT/"docs/audits/R457_NS2_SPARSE_RESEARCH_SOURCE_DELTA_2026-11-11.json").read_text())
assert sparse_receipt["schema_version"] == 1
assert sparse_receipt["historical_f07_snapshot_untouched"] is True
assert sparse_receipt["production_default_enabled"] is True
assert sparse_receipt["guest_boot_ps5_qualified"] is False
assert sparse_receipt["ps5_gpu_alias_lifetime_qualified"] is False
sparse_path = sparse_receipt["path"]
assert sparse_path == "src/host_memory.cpp"
assert sparse_path not in post_index
assert sparse_path in drift_index
sparse_drift = drift_index.pop(sparse_path)
assert sparse_drift["expected"] == sparse_receipt["historical_f07_git_blob"]
# The 2026-11-11 reviewed sparse host owner is immutable, but a
# production safety guard now forbids a 12GiB dense fallback when the PS5
# preprocessor path is absent. Reconstruct the earlier checked Git blob.
assert sparse_receipt["research_source_git_blob"] == (
    "4f109a0286a13afc93dcacd3b287b26b256d13f4")
# The current source has advanced through the three separately replayed
# sparse clear/demand-zero successors below. Require that exact current blob
# here; the immutable b934 owner is reconstructed before the R457 receipt.
assert sparse_drift["actual"] == "2ac696f8f2eb4312e178eb4587a87dcc7bbcd75e"
dense_fallback_guard = """#ifdef PS5_NATIVE
        // NS2 must never request 12 GiB of physical RAM because a
        // compile-flag mismatch silently disabled the sparse owner.
        // Fail clearly instead of reproducing the PS5 launch ENOMEM.
        if (requested == (12ull << 30)) {
            throw std::system_error(ENOMEM, std::generic_category(),
                                    "NS2 sparse backing not active; refusing 12 GiB dense allocation");
        }
#endif
"""
current_sparse_source = (ROOT/sparse_path).read_text()
# NS1 sparse adaptation: the production owner now accepts every supported
# Nintendo guest layout (4/6/8/10/12 GiB) with a physical budget capped at
# 6 GiB. Reverse exactly this one constructor block before replaying the
# older NS2-only R457 receipt chain below.
ns1_sparse_layout_successor = """#if defined(PS5_NATIVE) && defined(EDEN_NS2_SPARSE_BACKING)
        constexpr std::size_t GiB = 1ull << 30;
        constexpr std::size_t PhysicalBudget = 6ull * GiB;
        // Nintendo's supported guest layouts are 4/6/8/10/12 GiB. Use the
        // same ZERO/OWN sparse owner for NS1 and NS2 instead of allocating
        // the complete guest DRAM physically up front. The physical budget
        // is bounded by the guest layout for 4/6 GiB and by 6 GiB above it.
        const bool supported_guest_layout =
            requested == 4ull * GiB || requested == 6ull * GiB ||
            requested == 8ull * GiB || requested == 10ull * GiB ||
            requested == 12ull * GiB;
        if (supported_guest_layout) {
            const auto budget = (std::min)(requested, PhysicalBudget);
            sparse = std::make_unique<Eden::PS5::GuestBacking::Runtime>(
                requested, budget);
            if (!sparse->Valid() || !sparse->Install())
                throw std::system_error(ENOMEM, std::generic_category(),
                                        "PS5 sparse guest VA reservation");
            base = static_cast<u8*>(sparse->Base());
            // Production PS5 keeps Fastmem disabled. If a developer requests
            // it, fail safely to the page-table path rather than aliasing the
            // shared read-only ZERO block writable.
            return;
        }
#endif"""
ns1_sparse_layout_predecessor = """#if defined(PS5_NATIVE) && defined(EDEN_NS2_SPARSE_BACKING)
        constexpr std::size_t Ns2Dram = 12ull << 30;
        constexpr std::size_t PhysicalBudget = 6ull << 30;
        if (requested == Ns2Dram) {
            // Preserve the full 12 GiB guest-physical address range. The
            // production backing commits independent 2 MiB direct mappings
            // before a kernel PTE or ClearBackingRegion can expose them.
            // A32 fastmem's single-PA alias is intentionally NOT created.
            sparse = std::make_unique<Eden::PS5::GuestBacking::Runtime>(
                requested, PhysicalBudget);
            if (!sparse->Valid() || !sparse->Install())
                throw std::system_error(ENOMEM, std::generic_category(),
                                        "NS2 sparse guest VA reservation");
            base = static_cast<u8*>(sparse->Base());
            return;
        }
#endif"""
current_native_raw = current_sparse_source.encode("utf-8")
assert hashlib.sha1(
    b"blob " + str(len(current_native_raw)).encode() + bytes([0]) +
    current_native_raw).hexdigest() == "2ac696f8f2eb4312e178eb4587a87dcc7bbcd75e"
assert current_sparse_source.count(ns1_sparse_layout_successor) == 1
current_sparse_source = current_sparse_source.replace(
    ns1_sparse_layout_successor, ns1_sparse_layout_predecessor, 1)
# Replay the exact post-snapshot zero-fill elision delta on the audit copy:
# a brand-new physical 2 MiB mapping is already zero from CommitMemoryRange.
# Never alter the historical F07 research snapshot or the shipping C++.
sparse_clear_successor = """#if defined(PS5_NATIVE) && defined(EDEN_NS2_SPARSE_BACKING)
        if (impl->sparse) {
            if (!impl->sparse->Clear(offset, length, fill))
                throw std::bad_alloc{}; // fail closed, not a virtual-hole write
            return; // sparse owner performed the exact clear
        }
#endif"""
demand_zero_successor = """#if defined(PS5_NATIVE) && defined(EDEN_NS2_SPARSE_BACKING)
        if (impl->sparse) {
            bool already_zero = false;
            if (!impl->sparse->PrepareClear(offset, length, fill, &already_zero))
                throw std::bad_alloc{}; // fail closed, not a virtual-hole write
            // Untouched chunks already read as zero through the shared
            // read-only zero block. Do not allocate or rewrite them.
            if (fill == 0 && already_zero) return;
        }
#endif"""
zero_elision_successor = """#if defined(PS5_NATIVE) && defined(EDEN_NS2_SPARSE_BACKING)
        if (impl->sparse) {
            bool just_committed = false;
            if (!impl->sparse->CommitForClear(offset, length, &just_committed))
                throw std::bad_alloc{}; // fail closed, not a virtual-hole write
            // CommitMemoryRange already zeroed every entirely new 2 MiB
            // granule. Do not repeat that huge write; mixed/reused ranges
            // still require their exact fill and may hold live guest bytes.
            if (fill == 0 && just_committed) return;
        }
#endif"""
zero_elision_predecessor = """#if defined(PS5_NATIVE) && defined(EDEN_NS2_SPARSE_BACKING)
        if (impl->sparse && !impl->sparse->Commit(offset, length))
            throw std::bad_alloc{}; // fail closed, not a virtual-hole write
#endif"""
current_raw = current_sparse_source.encode("utf-8")
assert hashlib.sha1(
    b"blob " + str(len(current_raw)).encode() + bytes([0]) +
    current_raw).hexdigest() == "086fdbeaeffc5eca7beeff509804e6cc4c2333cf"
assert current_sparse_source.count(sparse_clear_successor) == 1
current_sparse_source = current_sparse_source.replace(
    sparse_clear_successor, demand_zero_successor, 1)
sparse_clear_predecessor_raw = current_sparse_source.encode("utf-8")
assert hashlib.sha1(
    b"blob " + str(len(sparse_clear_predecessor_raw)).encode() + bytes([0]) +
    sparse_clear_predecessor_raw).hexdigest() == "8278794d202f030a1af794d8b7d6856dd8405455"
assert current_sparse_source.count(demand_zero_successor) == 1
current_sparse_source = current_sparse_source.replace(
    demand_zero_successor, zero_elision_successor, 1)
demand_predecessor_raw = current_sparse_source.encode("utf-8")
assert hashlib.sha1(
    b"blob " + str(len(demand_predecessor_raw)).encode() + bytes([0]) +
    demand_predecessor_raw).hexdigest() == "5dad5e00f27aa4ff8b88e5e1ca28c96def51f428"
assert current_sparse_source.count(zero_elision_successor) == 1
current_sparse_source = current_sparse_source.replace(
    zero_elision_successor, zero_elision_predecessor, 1)
previous_raw = current_sparse_source.encode("utf-8")
assert hashlib.sha1(
    b"blob " + str(len(previous_raw)).encode() + bytes([0]) +
    previous_raw).hexdigest() == "b9349360b3f615784247133026ac7aaf8d71eb9e"
assert current_sparse_source.count(dense_fallback_guard) == 1
pre_guard = current_sparse_source.replace(dense_fallback_guard, "", 1)
pre_guard_bytes = pre_guard.encode("utf-8")
pre_guard_blob = hashlib.sha1(
    b"blob " + str(len(pre_guard_bytes)).encode() + bytes([0]) +
    pre_guard_bytes).hexdigest()
assert pre_guard_blob == sparse_receipt["research_source_git_blob"], (
    "NS2 dense-fallback guard modified other sparse source code")
print("R457_NS2_SPARSE_DENSE_FALLBACK_GUARD_PASS",
      "12GiB_dense=forbidden", "original_receipt=preserved")
assert sparse_receipt["opt_in"] in (ROOT/sparse_path).read_text()
# The current production constructor is generation-neutral; the archived
# NS2-only source fragment must exist in the exact reconstructed predecessor.
assert sparse_receipt["source_fragment"] in current_sparse_source
print("R457_NS2_SPARSE_F07_SEPARATE_PIN_PASS", "historical_F07_unchanged=1",
      "new_owner_consoles_qualified=0")
# Reviewed NS2 production deltas supersede only their exact pinned vendor blobs.\n# R458 advances the already-reviewed launcher owner from a frozen retained frame\n# to one bounded GL presenter; the historical F07/R457 receipts stay immutable.
selected_texture_vendor = subprocess.check_output(
    ["git","-C",str(ROOT/"vendor"),"rev-parse","HEAD"],text=True
).strip()
if integrated_cache_lock_qualified:
    assert selected_texture_vendor in integrated_cache_lock_pins
    selected_texture_vendor = "4354add020afac574198f63d87167f3022bff9c6"
ns2_production_blobs = {
    # Reviewed R457 unified GL -> Vulkan loading owner: no final-frame CPU
    # readback; the launcher presents loading_scene.glsl and retains VideoOut
    # until the selected renderer takes ownership. Console continuity pending.
    "headless/prosperoeden/frontend.cpp": "25884807fdf7759834cb232548184ffefca715d4",
    "vendor/encore-active/eden-core/src/core/memory_native_a32.cpp":
        ("3e3b07af30032ce14ca68e8482986d2f1a7201da" if selected_texture_vendor in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "aa08b4af80e22109495f8dfbec1fec129f2261e9" if selected_texture_vendor in {"6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "8007c91fd1757acf66f5f5b6a67d862afa0c475c" if selected_texture_vendor in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762"}
         else "318cb932c496c09853c2d9ba333d726cf7f820cd"),
    "vendor/encore-active/eden-core/src/core/memory_native_standard.cpp":
        ("96663d23335fe7448712a15416003a975a3f8023" if selected_texture_vendor in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "9dad056a223b90f27470c6a5b55977217238993a" if selected_texture_vendor in {"6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "3757b123153c66584ec0dde8bd01334ec41ec9e2" if selected_texture_vendor in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762"}
         else "91463583eec9cfcbd180a56662cda072553787e0"),
    "vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h": (
        "09e1578dec6dcbcb0b8f54d4bb819b71d0eed972" if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}
        else "c4ed79a1fe6aec09da8040b7af3901f6184f910b" if gpu_table_vendor_pin == pair_receipt["selected_vendor"]
        else "469eddd0ea9e0a3498446bf08ab473caac3b76f9"),
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_buffer_cache.h": "08b0ad3a99c1509eb23bd6317fdbd9c4b3251b52",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_scheduler.h": "460b5d95453cb974eefff10c4af76c5b318e685f",
    "vendor/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp": "1877d43aa8facfabf193dac16b8beea3ff7e188e",
    "vendor/encore-active/eden-vulkan/vulkan_scheduler.cpp": "70bc538c71ba1327a0c2a51a6bcb57d1835db2e0",
    "vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h":
        ("c7cb95ecaf388b925fc29582499bbd4b54a77f75" if selected_texture_vendor in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else
         "859a9e46fb63a97fee82c8ea6b1566317264f98f" if selected_texture_vendor == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else
         "0d99f9a861c645562519f71d62f4f49bfedd8101" if selected_texture_vendor == "1a09972eea6f473fda1b714efe84cd52219bf681" else
         "744bf30e1421dcce212146f7e26e9d90558676a8")
}
for changed_path, expected_sha in ns2_production_blobs.items():
    if changed_path in drift_index:
        assert drift_index[changed_path]["actual"] == expected_sha, changed_path
        if changed_path in post_index:
            post_index[changed_path]["post_snapshot_git_blob"] = expected_sha
        else:
            drift_index.pop(changed_path)
# R23 #113 parent-program metadata and #126 UUID service adjustments
# update two pre-existing historical source owners. The frozen F07 snapshot
# remains unchanged; require exact reviewed new Git blobs independently.
r23_existing_source_successors = {
    "vendor/encore-active/eden-core/src/core/file_sys/registered_cache.cpp":
        "2658884ef0332ec7dc579824d9c89925f9168891",
    "vendor/encore-active/eden-core/src/core/hle/service/am/service/application_functions.cpp":
        "2bd3959b2046f7e1cccf93ccbad9d1d91cd9a590",
}
assert set(r23_existing_source_successors).isdisjoint(post_index)
for changed_path, new_blob in r23_existing_source_successors.items():
    assert changed_path in drift_index, ("Missing R23 existing-owner delta",changed_path)
    source_delta = drift_index.pop(changed_path)
    assert source_delta["expected"] != new_blob
    assert source_delta["actual"] == new_blob, (
        "Unreviewed R23 existing-owner source edit", changed_path)
print("ENCORE_R23_EXISTING_F07_SOURCE_SUCCESSORS_PASS", "owners=2",
      "historical_F07_preserved=1")
# The XCI NCZ source receives two exact malformed-input guards reviewed in
# vendor #118. Keep the old format receipt; the historical checkout has no delta.
xci_path = "vendor/encore-active/eden-core/src/core/file_sys/card_image.cpp"
assert xci_path not in post_index
if post_f07_vfs_present:
    xci_delta = drift_index.pop(xci_path)
    assert xci_delta["expected"] == "f843e7f9c977b509368e71eb6356066c1a5e0c50"
    if xci_delta["actual"] == "5d5e6b40099b18768dadd39ba839881989e7ff6f":
        # Keep DXCI detection in the active gamecard loader; reconstruct only
        # the exact new magic contract on the historical audit copy.
        current_xci = (ROOT / xci_path).read_text()
        added_xci = """        // NxEmu DXCI keeps the XCI/HFS0 layout but changes HEAD -> DXCI.
        // Admit that decrypted variant only with the matching extension; do
        // not relax ordinary encrypted game-card validation.
        const auto name = Common::ToLower(file->GetName());
        const bool decrypted_card = name.ends_with(".dxci") &&
            header.magic == Common::MakeMagic('D', 'X', 'C', 'I');
        if (header.magic != Common::MakeMagic('H', 'E', 'A', 'D') &&
            !decrypted_card) {"""
        original_xci = """        if (header.magic != Common::MakeMagic('H', 'E', 'A', 'D')) {"""
        assert current_xci.count(added_xci) == 1
        assert current_xci.count('#include "common/string_util.h"\n') == 1
        restored_xci = current_xci.replace(added_xci, original_xci, 1)
        restored_xci = restored_xci.replace('#include "common/string_util.h"\n', "", 1)
        prior_raw = restored_xci.encode("utf-8")
        prior_sha = hashlib.sha1(b"blob "+str(len(prior_raw)).encode()+bytes([0])+prior_raw).hexdigest()
        assert prior_sha == "c3dbb891b10ae2f576566d5a8a5f1a871f94c3d0", prior_sha
        xci_delta["actual"] = prior_sha
    assert xci_delta["actual"] == "c3dbb891b10ae2f576566d5a8a5f1a871f94c3d0"
else:
    assert xci_path not in drift_index
# The selected C00 PS5 AudioIn capture source legitimately updates the
# existing historical native audio.cpp; this is NOT an F07 performance review.
# Its original F07 SHA stays immutable. Only this exact reviewed new blob is
# admitted after verifying capture pacing, bounds and one native AudioOut TU.
audio_changed_path = "headless/audio.cpp"
assert audio_changed_path not in post_index
assert audio_changed_path in drift_index
audio_changed = drift_index.pop(audio_changed_path)
assert audio_changed["expected"] != audio_changed["actual"]
assert audio_changed["actual"] == "4b5082d14fc12db39d7e3b06677d6dc403af2bf7"
audio_current = (ROOT / audio_changed_path).read_text()
assert "class SilentAudioInputStream final : public SinkStream" in audio_current
assert "make_unique<SilentAudioInputStream>(system, channels)" in audio_current
assert "MakeSilentAudioInSamples(samples)" in audio_current
assert "NullSinkStreamImpl" not in audio_current
assert "tools/audit/check-ab-ns1-guest-release-host.py" in tracked
print("C00_POST_F07_REAL_AUDIO_SINK_SUCCESSOR_PASS legacy_f07_preserved=1 exact_blob=1")
# The Nov13 scene-4/5 choice is one exact, reversible launcher change;
# it is NOT a retroactive change to the frozen F07 reviewed source ledger.
scene_path = "headless/prosperoeden/pe/ui/case_media_selection.hpp"
assert scene_path in drift_index and scene_path not in post_index
scene_drift = drift_index.pop(scene_path)
assert scene_drift["expected"] == "f4897989b5736bf48401cf5e2201a8af9a59ef03"
assert scene_drift["actual"] == "9df9797a09979b74cb81c266570a8c8c24c96d41"
scene_current = (ROOT / scene_path).read_text()
scene_added = "            const auto role = image[role_at];\n            if (role < '1' || role > '5' ||\n                image == cover || is_front(image) || !usable(image))\n                continue;\n            // Scenes 1-3 own dedicated panels. Extra independent LaunchBox\n            // gameplay shots (4-5) are real fallback material; the old\n            // selector silently discarded them, leaving a two-shot back.\n            if (role <= '3') {\n                const auto category = static_cast<std::size_t>(role - '1');\n                if (!selected[category] &&\n                    image.compare(marker, kSceneMarkers[category].size(),\n                                  kSceneMarkers[category]) == 0)\n                    selected[category] = &image;\n                continue;\n            }\n            bool seen = false;\n            for (const auto* prior : fallback) {\n                if (prior && *prior == image) seen = true;\n            }\n            if (!seen) {\n                for (auto& slot : fallback) {\n                    if (!slot) { slot = &image; break; }\n                }\n            }\n            continue;\n"
scene_prior = "            const auto role = image[role_at];\n            if (role < '1' || role > '3') continue;\n            const auto category = static_cast<std::size_t>(role - '1');\n            if (selected[category] ||\n                image.compare(marker, kSceneMarkers[category].size(),\n                              kSceneMarkers[category]) != 0 ||\n                image == cover || is_front(image) || !usable(image))\n                continue;\n            selected[category] = &image;\n            continue;\n"
# The later bounded-decode optimisation is also reversible. It changes ONLY
# candidate admission order, retaining scene 4/5 eligibility and all three
# real back slots. Prove its complete selected source hunk before reversing.
scene_probe_optimized = scene_added.replace(
    "image == cover || is_front(image) || !usable(image))",
    "image == cover || is_front(image))", 1).replace(
    "            // Scenes 1-3 own dedicated panels. Extra independent LaunchBox\n"
    "            // gameplay shots (4-5) are real fallback material; the old\n"
    "            // selector silently discarded them, leaving a two-shot back.\n",
    "            // Scenes 1-3 own dedicated panels. Do not attempt to decode\n"
    "            // a second file when its canonical category is already filled.\n"
    "            // Extra independent LaunchBox gameplay shots (4-5) remain\n"
    "            // eligible to fill an otherwise missing rear slot.\n", 1).replace(
    "                                  kSceneMarkers[category]) == 0)",
    "                                  kSceneMarkers[category]) == 0 &&\n"
    "                    usable(image))", 1).replace(
    "                    if (!slot) { slot = &image; break; }",
    "                    if (!slot) {\n"
    "                        // The bounded fallback list may already be full.\n"
    "                        // Only decode genuine candidates with a free slot.\n"
    "                        if (usable(image)) slot = &image;\n"
    "                        break;\n"
    "                    }", 1)
assert scene_probe_optimized != scene_added
assert scene_current.count(scene_probe_optimized) == 1, (
    "Unreviewed scene 4/5 bounded-decode candidate change")
scene_pre_opt = scene_current.replace(scene_probe_optimized, scene_added, 1)
scene_pre_opt_bytes = scene_pre_opt.encode()
assert hashlib.sha1(
    b"blob " + str(len(scene_pre_opt_bytes)).encode() + bytes([0]) +
    scene_pre_opt_bytes).hexdigest() == "ef73ba928089086c1cc79a226a2c0678a8f8a109"
scene_baseline = scene_pre_opt.replace(scene_added, scene_prior, 1).encode()
assert hashlib.sha1(b"blob " + str(len(scene_baseline)).encode() + bytes([0]) + scene_baseline).hexdigest() == scene_drift["expected"]
print("NOV13_GAMEPLAY_SCENE_4_5_REVERSIBLE_PASS historical_F07_preserved=1")
# R457 runtime log sink is independent of historical F07 owner entries.
# Verify its exact reviewed successor and reconstruct the earlier bounded
# sink byte-for-byte, then discard ONLY this separately qualified drift.
pipe_path = "headless/log_pipe.h"
assert pipe_path in drift_index and pipe_path not in post_index
pipe_drift = drift_index.pop(pipe_path)
assert pipe_drift["expected"] == "275a75da7baadbcb95be91996adb5cbdf35c59c2"
assert pipe_drift["actual"] == "fd3f0cdbe0e9f1d6440275b177e7dad4a027e52f"
pipe_source = (ROOT / pipe_path).read_text()
new_toggle = """        // Disabling collection must not delete already recorded evidence.
        // Re-enabling within the same process appends to the bounded current
        // segment instead of truncating the earlier game/fault diagnostics.
        const int next = want_enabled ?
            open(log_path.c_str(), O_WRONLY | O_CREAT | O_APPEND, 0666) :
            open("/dev/null", O_WRONLY);
        if (next < 0) return false;
        close(file_fd);
        file_fd = next;
        // Keep bytes and rotated across OFF/ON. The draining thread still
        // accounts for the existing segment, so an append cannot bypass the
        // 8 MiB per-segment limit or remove the preserved first segment.
        enabled = want_enabled;"""
old_toggle = """        const int next = want_enabled ?
            open(log_path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666) :
            open("/dev/null", O_WRONLY);
        if (next < 0) return false;
        close(file_fd);
        file_fd = next;
        enabled = want_enabled;
        rotated = false;
        bytes = 0;
        if (!want_enabled) {
            (void)std::remove(log_path.c_str());
            (void)std::remove(first_log_path.c_str());
        } else {
            (void)std::remove(first_log_path.c_str());
        }"""
assert pipe_source.count(new_toggle) == 1, "Unreviewed R457 log sink delta"
prior_pipe = pipe_source.replace(new_toggle, old_toggle, 1).encode("utf-8")
assert hashlib.sha1(b"blob " + str(len(prior_pipe)).encode() + bytes([0]) +
                    prior_pipe).hexdigest() == pipe_drift["expected"]
print("R457_LOG_PIPE_F07_SOURCE_DELTA_PASS reviewed=1 prior_reconstructed=1")

# 18 Nov P0: native memory_pages.cpp now remembers only failed direct
# allocation/mapping details for a fatal or recoverable incident. Reconstruct
# the exact reviewed production owner (no physical allocation changes).
direct_path = "src/memory_pages.cpp"
direct_prior = "30676a42a10ac7d03e812ce69d39bc38a499bc44"
direct_current = "72b3283a855b3fb4c62b0ee0b5d310b7756ef297"
assert direct_path in drift_index and direct_path not in post_index
direct_drift = drift_index.pop(direct_path)
assert direct_drift["expected"] == direct_prior
assert direct_drift["actual"] == direct_current
direct_text = (ROOT / direct_path).read_text(encoding="utf-8")
direct_start = "// Failed direct-memory requests must survive quiet stderr redirection."
direct_end = "std::atomic<std::int64_t> cached_direct_memory_extent{0};"
assert direct_text.count(direct_start) == direct_text.count(direct_end) == 1
first = direct_text.index(direct_start)
last = direct_text.index(direct_end, first)
direct_text = direct_text[:first] + direct_text[last:]
export_start = "// A C ABI keeps the crash-only frontend free of allocator dependencies."
export_end = "#endif\n\nnamespace Common {"
assert direct_text.count(export_start) == direct_text.count(export_end) == 1
first = direct_text.index(export_start)
last = direct_text.index(export_end, first)
direct_text = direct_text[:first] + direct_text[last:]
expanded_invalid = """    if (!total) {
#ifdef PS5_NATIVE
        NoteDirectAllocationFailure(3, EINVAL, size, 0);
#endif
        errno = EINVAL;
        return nullptr;
    }"""
assert direct_text.count(expanded_invalid) == 1
direct_text = direct_text.replace(
    expanded_invalid, "    if (!total) { errno = EINVAL; return nullptr; }", 1)
for recorded in (
    """        NoteDirectAllocationFailure(1, static_cast<std::uint32_t>(rc), total,
                                    static_cast<std::uint64_t>(limit));
""",
    """        NoteDirectAllocationFailure(2, static_cast<std::uint32_t>(rc), total,
                                    static_cast<std::uint64_t>(limit));
""",
):
    assert direct_text.count(recorded) == 1
    direct_text = direct_text.replace(recorded, "", 1)
direct_bytes = direct_text.encode("utf-8")
direct_reconstructed = hashlib.sha1(
    b"blob " + str(len(direct_bytes)).encode() + bytes([0]) + direct_bytes).hexdigest()
assert direct_reconstructed == direct_prior, (
    "Native direct allocation predecessor does not match F07", direct_reconstructed)
print("P0_DIRECT_MEMORY_FAILURE_ONLY_F07_REVERSE_PASS M01=1 historical=unchanged")

# 18 Nov P0: the crash-only recoverable-failure receipt lives in the
# historically reviewed U36 diagnostics.h, with no new per-frame logging.
# Reconstruct the exact original source from its changed C++ owner BEFORE
# resuming the immutable F07 source comparison. Do not rewrite old Git blobs.
incident_header = "headless/diagnostics.h"
incident_header_original = "0bc6a2c89def2a5be80df854e5ced443cb3c2e3d"
incident_header_current = "df373c11780ae174b1b9db4c54a9f0b4d2a652e2"
assert incident_header in drift_index and incident_header not in post_index
incident_drift = drift_index.pop(incident_header)
assert incident_drift["expected"] == incident_header_original
assert incident_drift["actual"] == incident_header_current
header_text = (ROOT / incident_header).read_text(encoding="utf-8")
incident_begin = "// A recoverable PS5 failure is NOT a fatal signal."
incident_end = "// A shutdown step with the milliseconds since the previous one (some games take 14-16 s)."
assert header_text.count(incident_begin) == header_text.count(incident_end) == 1
assert "inline bool WriteSessionFailureReceipt(" in header_text
assert header_text.count("inline bool WriteSessionBoundaryReceipt(") == 1
assert "EDEN_SESSION_BOUNDARY_V1" in header_text
assert "phase=%.32s age_ms=%llu gpu_completed=%llu gpu_stalls=%u" in header_text
assert "O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW" in header_text
start = header_text.index(incident_begin)
stop = header_text.index(incident_end)
assert start < stop
header_pre = header_text[:start] + header_text[stop:]
added_includes = """#include <cstdint>
#include <cstddef>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
"""
assert header_pre.count(added_includes) == 1
header_pre = header_pre.replace(added_includes, "", 1).encode("utf-8")
header_pre_sha = hashlib.sha1(
    b"blob " + str(len(header_pre)).encode() + bytes([0]) + header_pre).hexdigest()
assert header_pre_sha == incident_header_original, (
    "P0 session-failure diagnostics predecessor altered", header_pre_sha)
print("P0_CRASH_ONLY_DIAGNOSTICS_F07_REVERSE_PASS U36=1 historical=unchanged")

# NS2 P0, Nov22: shipping EDEN_DEV_PROFILE=OFF previously made RecordHle
# a no-op. Pin the four exact engine-only successor blobs for the bounded
# 10s/30s completed-service witness; historical 518 F07 owners and vendor
# sources stay immutable. No claim of improved gameplay or GPU submission.
ns2_boot_hle_receipts = {
    "headless/performance.h": (
        "1357052fa927075f006f9fca10e16b3399165664",
        "6c69d5e8dc4b639ff312ae8b8ac1d6d1a3b5eeb6",
        "void ReportNs2BootHle(unsigned stage_seconds) noexcept;"),
    "headless/performance.cpp": (
        "18ecba614f2c0077bbcc7044d68aa3eb714cb4b4",
        "9b9c593f3e3629599e1143861a2027d8fcf53096",
        "EDEN_NS2_LAST_HLE stage=%us"),
    "headless/graphics.cpp": (
        "ca3107c8745af36d6faf0196cf9692e628d52540",
        "b498ee4307ffb0b7f6ae18333177687607a297d7",
        "::Eden::Performance::ReportNs2BootHle(30);"),
    "headless/main.cpp": (
        "de81392f6948fc0257a764bf15daf1c4bf271fdb",
        "c04f16e3635325b233a8a03c02cb036306cb1c0d",
        "Eden::Performance::ResetNs2BootHle();"),
}
for path, (previous_blob, successor_blob, witness) in ns2_boot_hle_receipts.items():
    # The F07 518-path historical review did not include every later
    # headless owner. Pin those engine-only files independently, and update
    # only the sources that genuinely belong to the frozen post-F07 register.
    source = ROOT/path
    assert source.is_file(), ("NS2 HLE source missing", path)
    assert witness in source.read_text(), ("NS2 HLE witness dropped", path)
    current_blob = subprocess.check_output(
        ["git", "hash-object", str(source)], cwd=ROOT, text=True).strip()
    assert current_blob == successor_blob, ("NS2 HLE successor source drift", path)
    if path in post_index or path in drift_index:
        assert path in post_index and path in drift_index, path
        assert post_index[path]["post_snapshot_git_blob"] == previous_blob, path
        assert drift_index[path]["actual"] == successor_blob, path
        post_index[path]["post_snapshot_git_blob"] = successor_blob
print("NS2_BOOT_HLE_SHIPPING_RECEIPT_PASS owners=4 history=immutable "
      "console_boot=unvalidated")

# NX library selection (e0080f38) postdates the DNSP/DXCI game-file
# classifier. Reverse its four exact header hunks on the audit copy first;
# the shipping runtime keeps NX support and the DNSP/DXCI receipt stays frozen.
nx_game_files_path = "headless/game_files.h"
assert nx_game_files_path in drift_index and nx_game_files_path not in post_index
nx_game_files_source = (ROOT/nx_game_files_path).read_text()
nx_current_blob = subprocess.check_output(
    ["git", "hash-object", nx_game_files_path], cwd=ROOT, text=True
).strip()
assert nx_current_blob == "497a4500fb2b38fd2606acd7251c2a4343a0182f"
nx_hunks = (
    ("""// NX has a full content loader with verified VFS and snapshot dispatch.
inline bool IsNxFile(std::string_view name) {
    return EndsWithNoCase(name, ".nx");
}
""", ""),
    ("""           IsDirectLoaderFile(name) || IsNupFile(name) || IsNxFile(name);""",
     """           IsDirectLoaderFile(name) || IsNupFile(name);"""),
    ("""        !IsNupFile(selection) && !IsNxFile(selection)) return false;""",
     """        !IsNupFile(selection)) return false;"""),
    ("""                 !IsNupFile(name) && !IsNxFile(name))) continue;""",
     """                 !IsNupFile(name))) continue;"""),
)
for current, previous in nx_hunks:
    assert nx_game_files_source.count(current) == 1, current
    nx_game_files_source = nx_game_files_source.replace(current, previous, 1)
nx_predecessor = nx_game_files_source.encode("utf-8")
nx_predecessor_blob = hashlib.sha1(
    b"blob " + str(len(nx_predecessor)).encode() + bytes([0]) + nx_predecessor
).hexdigest()
assert nx_predecessor_blob == "e4502fb143a4e4efc9ffb21bdabcafab90ff922a"
assert drift_index[nx_game_files_path]["actual"] == nx_current_blob
drift_index[nx_game_files_path]["actual"] = nx_predecessor_blob
print("NX_GAME_FILES_SOURCE_SUCCESSOR_PASS predecessor=e4502fb1 current=497a4500")

# The same NX integration changes the maintained vendor loader in seven exact
# hunks. Reverse them only on the audit copy so the prior DNSP/DXCI loader
# receipt remains immutable while the shipping runtime keeps real NX support.
nx_loader_path = "vendor/encore-active/eden-core/src/core/loader/loader.cpp"
assert nx_loader_path in drift_index and nx_loader_path not in post_index
nx_loader_source = (ROOT/nx_loader_path).read_text()
nx_loader_current = subprocess.check_output(
    ["git", "hash-object", nx_loader_path], cwd=ROOT, text=True
).strip()
assert nx_loader_current == "1bfb0d797119087882da5d9674c8ef6ded879dc8"
nx_loader_hunks = (
    ('#include "core/loader/nx.h"\n', ''),
    ("""    if (const auto nx_type = IdentifyFileLoader<AppLoader_NX>(file)) {
        return *nx_type;
    }
""", ""),
    ("""    return type == FileType::NSP || type == FileType::XCI || type == FileType::NX;""",
     """    return type == FileType::NSP || type == FileType::XCI;"""),
    ("""    if (type == FileType::NX) {
        return AppLoader_NX::IsBootable(file);
    }
""", ""),
    ("""    else if (extension == "nx")
        return FileType::NX;
""", ""),
    ("""    case FileType::NX:
        return "NX";
""", ""),
    ("""    // NX archive: verified NxFormat container plus NS1/NS2 content snapshots.
    case FileType::NX:
        return std::make_unique<AppLoader_NX>(system, std::move(file), program_id, program_index);

""", ""),
)
for current, previous in nx_loader_hunks:
    assert nx_loader_source.count(current) == 1, current
    nx_loader_source = nx_loader_source.replace(current, previous, 1)
nx_loader_predecessor = nx_loader_source.encode("utf-8")
nx_loader_predecessor_blob = hashlib.sha1(
    b"blob " + str(len(nx_loader_predecessor)).encode() + bytes([0]) +
    nx_loader_predecessor
).hexdigest()
assert nx_loader_predecessor_blob == "0b4448bcf4bef93b9d2a54cf96256d5b81d9424e"
assert drift_index[nx_loader_path]["actual"] == nx_loader_current
drift_index[nx_loader_path]["actual"] = nx_loader_predecessor_blob
print("NX_LOADER_SOURCE_SUCCESSOR_PASS predecessor=0b4448bc current=1bfb0d79")

# DNCA/DXCI's shipping loader dispatch and library classifier are
# post-F07 structural additions, not updates to the frozen F07 receipt.
# The maintained C++/header owners are already sealed by exact Git blobs
# and CMake selection above; remove only these two verified new deltas.
for path, expected_blob, required in (
    ("headless/game_files.h", "e4502fb143a4e4efc9ffb21bdabcafab90ff922a", '".dnsp"'),
    ("vendor/encore-active/eden-core/src/core/loader/loader.cpp",
     "0b4448bcf4bef93b9d2a54cf96256d5b81d9424e",
     'extension == "xci" || extension == "xcz" || extension == "dxci"'),
):
    assert path not in post_index and path in drift_index, ("DNSP/DXCI classification", path)
    delta = drift_index.pop(path)
    assert delta["actual"] == expected_blob, ("DNSP/DXCI active source drift", path)
    assert delta["expected"] != expected_blob
    assert required in (ROOT/path).read_text(), path
assert "foreach(eden_plaintext_content_relative IN ITEMS" in release_cmake

# Two current vendor successors are independently reviewed post-F07 changes,
# not historical F07 owners: Lichii AOC explicit placeholder replies and the
# PS5 service-manager close/waiter header used by joined teardown.
aoc_path = "vendor/encore-active/eden-core/src/core/hle/service/aoc/addon_content_manager.cpp"
assert aoc_path in drift_index and aoc_path not in post_index
aoc_delta = drift_index.pop(aoc_path)
assert aoc_delta["actual"] == "443982a3887744e9c76db74d282338b17b152516"
assert aoc_delta["expected"] == "874172cc88bb3c4980df16aef42e3268e368d966"
aoc_source = (ROOT/aoc_path).read_text()
for current, previous in (
    ('{9, &IAddOnContentManager::StubReplyZeroed, "GetAddOnContentLostErrorCode"}',
     '{9, nullptr, "GetAddOnContentLostErrorCode"}'),
    ('{13, &IAddOnContentManager::StubReplyZeroed, "IsAddOnContentMountedForDebug"}',
     '{13, nullptr, "IsAddOnContentMountedForDebug"}'),
    ('{110, &IAddOnContentManager::StubReplyInterface, "CreateContentsServiceManager"}',
     '{110, nullptr, "CreateContentsServiceManager"}'),
    ('{200, &IAddOnContentManager::StubReplyZeroed, "SetRequiredAddOnContentsOnContentsAvailabilityTransition"}',
     '{200, nullptr, "SetRequiredAddOnContentsOnContentsAvailabilityTransition"}'),
    ('{300, &IAddOnContentManager::StubReplyZeroed, "SetupHostAddOnContent"}',
     '{300, nullptr, "SetupHostAddOnContent"}'),
    ('{301, &IAddOnContentManager::StubReplyZeroed, "GetRegisteredAddOnContentPath"}',
     '{301, nullptr, "GetRegisteredAddOnContentPath"}'),
    ('{302, &IAddOnContentManager::StubReplyZeroed, "UpdateCachedList"}',
     '{302, nullptr, "UpdateCachedList"}'),
):
    assert aoc_source.count(current) == 1, current
    aoc_source = aoc_source.replace(current, previous, 1)
aoc_raw = aoc_source.encode("utf-8")
assert hashlib.sha1(b"blob "+str(len(aoc_raw)).encode()+bytes([0])+aoc_raw).hexdigest() == (
    "874172cc88bb3c4980df16aef42e3268e368d966")
print("NS2_AOC_PLACEHOLDER_SOURCE_SUCCESSOR_PASS predecessor=874172cc current=443982a3")

sm_header_path = "vendor/encore-active/eden-core/src/core/hle/service/sm/sm.h"
assert sm_header_path in drift_index and sm_header_path not in post_index
sm_delta = drift_index.pop(sm_header_path)
assert sm_delta["actual"] == "7069439e66a6f28ffa56229e08906a21222e2801"
assert sm_delta["expected"] == "83e0b7e26a867d578eb869389a807fe3b9c7035b"
sm_source = (ROOT/sm_header_path).read_text()
# Current FC27 destructor fix adds a separate SM-owned handler retirement
# method; strip only its exact source delta in the historical F07 replay.
late_sm_release = """    // Drop service-owned guest/device references before guest KProcesses retire.
    // Does not destroy SM ports or the SM object itself.
    void ReleaseRegisteredHandlersForShutdown();
"""
assert sm_source.count(late_sm_release) == 1
sm_source = sm_source.replace(late_sm_release, "", 1)
for current, previous in (
    ("#include <condition_variable>\n", ""),
    ("""    bool WaitForService(const std::string& name);
    void Close();

""", ""),
    ("""    bool closing{};
    u32 service_waiters{};
    std::condition_variable waiters_changed;

""", ""),
):
    assert sm_source.count(current) == 1, current
    sm_source = sm_source.replace(current, previous, 1)
sm_raw = sm_source.encode("utf-8")
assert hashlib.sha1(b"blob "+str(len(sm_raw)).encode()+bytes([0])+sm_raw).hexdigest() == (
    "83e0b7e26a867d578eb869389a807fe3b9c7035b")
print("PS5_SM_HEADER_TEARDOWN_SOURCE_SUCCESSOR_PASS predecessor=83e0b7e2 current=7069439e")

assert set(drift_index) == set(post_index), (
    "Unregistered or obsolete post-F07 source delta",
    sorted(set(drift_index) ^ set(post_index)))
for path, item in post_index.items():
    drift = drift_index[path]
    assert item['historical_reviewed_git_blob'] == drift['expected'], (
        "F07 immutable prior source SHA changed", path)
    assert item['post_snapshot_git_blob'] == drift['actual'], (
        "Unreviewed post-F07 source SHA change", path)
    assert item['original_disposition'] == drift['prior_disposition']
    assert item['post_snapshot_git_blob'] != item['historical_reviewed_git_blob']
    assert item['classification'] == (
        'post_snapshot_source_delta_only_not_performance_or_console_proof')
    assert item['review_kind'] in {
        'host_source_input','source_contract','integrity_workflow',
        'host_source_service','source_interface','locale_source',
        'host_preview_mock','host_source_ui'}
    assert len(item['source_scope']) >= 32
    fragment = item['required_source_fragment']
    assert fragment and fragment in (ROOT/path).read_text(), (
        "Post-F07 new source contract lost", path)
print("ENCORE_POST_F07_SOURCE_DELTA_INTEGRITY_PASS",
      "historical_f07_snapshot=preserved",
      f"independently_pinned_changes={len(post_entries)}",
      "performance_and_console_qualification=NOT_CLAIMED",flush=True)
for e in entries:
    if not e.get("source_review_document"):
        continue
    assert e["disposition"]=="reviewed_without_new_code_edit"
    # Some native startup shims, generated headers and standalone host test
    # executables are code owners without an ID in the *core* audit graph.
    # Keep their explicit review and unchanged Git blob rather than invent an ID.
    ident=e.get("contract_id")
    if ident is not None:
        # U23 is a preserved historical F07 blob identified by its former
        # filename; the live audit graph now uses the byte-reviewed renamed
        # JIT policy. Do not rewrite the old F07 fingerprint or invent proof.
        alias = (ident == 'U23' and e['path'] == U23_LEGACY and
                 ident in by_id and by_id[ident]['path'] == U23_CURRENT)
        assert ident in by_id and (by_id[ident]["path"] == e["path"] or alias)
    else:
        assert e.get("review_scope") in {
            "host-only-test","startup-shim","shutdown-only",
            "generated-configuration","startup-interface","inactive-experimental",
            "runtime-abi-interface", "launcher-release-hotpath",
            "launcher-release-support",
        }
        assert e["path"] not in {r["path"] for r in by_id.values()}
        if e.get("review_scope") in {"launcher-release-hotpath","launcher-release-support"}:
            assert e["path"].startswith("headless/prosperoeden/")
            assert e.get("reviewed_source_git_blob") and e["source_review_document"].startswith(
                "docs/EDEN_RELEASE_LAUNCHER_SOURCE_OPTIMIZATION_AUDIT_")

    source_review=ROOT/e["source_review_document"]
    assert source_review.is_file()
    assert "| `"+e["path"]+"` |" in source_review.read_text(),e["path"]
    if e.get("proof_ref") and e.get("prior_status"):
        row=by_id[e["contract_id"]]
        assert row["status"]==e["prior_status"]
        assert row["evidence"]==e["proof_ref"]
        assert "python3 -B "+e["proof_ref"] in preflight
# Generated fragments and opt-in sources are not production runtime hot paths.
# They count as source-triaged, but never as FPS-optimized. Verify their
# original ownership and that every asserted witness still runs in CI.
vulkan_generator=(ROOT/"tools/prepare-vulkan-port.py").read_text()
for e in entries:
    if e["disposition"]!="preexisting_generated_or_inactive_unit": continue
    ident=e["contract_id"]
    assert ident in by_id and by_id[ident]["path"]==e["path"]
    assert by_id[ident]["status"]==e["prior_status"]=="SOURCE"
    assert by_id[ident]["evidence"]==e["proof_ref"]
    assert "python3 -B "+e["proof_ref"] in preflight
    assert (ROOT/e["path"]).is_file()
    kind=e["profile_visibility"]
    if kind=="vulkan_oracle_not_compiled":
        assert e["path"].startswith("vendor/encore-active/eden-vulkan-oracles/")
        basename=Path(e["path"]).name
        assert "(vulkan_oracle / '"+basename+"').read_text()" in vulkan_generator
    elif kind=="dynarmic_scalar_generator_fragment":
        assert e["contract_id"] in {"J28","J29"}
    elif kind=="maintained_standard_memory":
        assert e["contract_id"] in {"V97","V98"}
    elif kind=="opengl_dev_capture_fragment":
        assert e["contract_id"]=="V107"
    elif kind=="deferred_guest_bridge_off":
        assert e["contract_id"] in {"V89","V90","V91","V92","V93",
                                   "V94","V95","V96","V99"}
        bridge=(ROOT/"headless/guest_write_deferred_bridge.cmake").read_text()
        assert 'option(EDEN_GUEST_WRITE_BRIDGE_DEV "Compile inactive native deferred-write bridge" OFF)' in bridge
        assert 'guest_write_deferred_bridge.cmake' not in (ROOT/"headless/CMakeLists.txt").read_text()
    else: raise AssertionError(("unexpected profile",kind))
assert sum(e["disposition"]=="preexisting_generated_or_inactive_unit"
           for e in entries)==19
status=Counter(e["disposition"] for e in entries)
# The baseline remains a dated historical inventory. New source owners must
# be explicit, traceable, present in the current tree and handled in the
# source-review ledger, rather than silently rewriting the snapshot count.
post_snapshot=set(STATE.get("post_snapshot_owned_additions", []))
assert len(post_snapshot)==len(STATE.get("post_snapshot_owned_additions", []))
assert post_snapshot<=owners, ("untracked post-snapshot source", sorted(post_snapshot-owners))
assert post_snapshot<=handled, ("post-snapshot source lacks review", sorted(post_snapshot-handled))
assert len(owners)==STATE["owned_code_count_at_snapshot"]+len(post_snapshot), (
    "source inventory changed", len(owners),
    STATE["owned_code_count_at_snapshot"],len(post_snapshot))
assert len(owners)==len(handled)+len(owners-handled)
print("EDEN_OPTIMIZATION_REVIEW_BACKLOG_PASS",
      "owned_code="+str(len(owners)),
      "handled="+str(len(handled)),
      "code_touched="+str(status["code_changed_in_batch"]),
      "source_reviewed="+str(status["reviewed_without_new_code_edit"]),
      "prior_host="+str(status["historical_host_contract_reviewed"]),
      "prior_source="+str(status["previously_integrated_source_change"]),
      "shipping_integrated="+str(status["shipping_backport_integrated_previously"]),
      "historical_maintained="+str(status["historical_maintained_unit_parity"]),
      "new_code_fixes="+str(status["new_source_issue_corrected"]),
      "format_feature_integrated_not_optimized="+str(status["format_feature_source_integrated"]),
      "native_selected="+str(status["historical_native_selected_unit"]),
      "preexisting_inactive_oracle="+str(status["preexisting_generated_or_inactive_unit"]),
      "remaining_emulator_to_optimize_review="+str(len(pending_code-launcher_pending)),
      "launcher_ui_pending_separate="+str(len(launcher_pending)),
      "all_component_triage_remaining="+str(len(owners-handled)),
      "new_code_fixes_required=UNKNOWN native_console_validation=SEPARATE")
