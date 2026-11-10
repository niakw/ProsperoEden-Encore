#!/usr/bin/env python3
"""Count Encore-owned files not yet handled in the optimization work pass.

Fast-skip previously maintained sources with a specific historical proof, but
never confuse code triage with host or console performance validation.
"""
import json
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
assert research["schema_version"] == 1 and len(research_owners) == 120
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
}
assert ns2_shared_release_owners <= all_owners, sorted(ns2_shared_release_owners-all_owners)
assert not ns2_shared_release_owners & (research_owners | hygiene_owners | extracted_aoc_owners)
release_cmake = (ROOT / "headless/CMakeLists.txt").read_text()
assert 'set(EDEN_SHARED_NS2_KERNEL_HEAP ON)' in release_cmake
assert 'ns2-runtime/process/core/core.cpp' in release_cmake
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

# P1.3: the five shared WaitIfEqual64 kernel source/ABI owners were
# introduced after the frozen F07 inventory. Qualify them with the real
# kernel/SVC/selector host witness; never inflate the historical 518 count.
post_f07_shared_wait64_owners = {
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.cpp",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.h",
    "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_process.h",
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

# Seven reviewed static CPU6/LDAPR units were moved from headless into
# vendor AFTER the frozen 518-owner F07 historical review. They are verified
# by exact pinned-source parity/UBSan, never retroactively counted as F07.
post_f07_static_engine_owners = {
    "vendor/encore-active/ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_32.cpp",
    "vendor/encore-active/ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_64.cpp",
    "vendor/encore-active/ns2-runtime/cpu6/maintained/core/hle/kernel/global_scheduler_context.cpp",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.h",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.inc",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/impl.h",
    "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/load_store_exclusive.cpp",
}
assert len(post_f07_static_engine_owners) == 7
assert post_f07_static_engine_owners <= all_owners, (
    "Missing post-F07 maintained native source owner",
    sorted(post_f07_static_engine_owners - all_owners))
assert not post_f07_static_engine_owners & research_owners
assert 'vendor/encore-active/ns2-runtime/cpu6/maintained' in (
    ROOT/'headless/ns2_cpu6_source_bridge.cmake').read_text()
assert 'vendor/encore-active/ns2-runtime/ldapr/maintained' in (
    ROOT/'headless/shared_a64_ldapr.cmake').read_text()
print("ENCORE_POST_F07_NATIVE_SOURCE_ISOLATION_PASS owners=7")

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

# Shared NS1/NS2 compiled targets use a native GPFIFO header, scheduler
# header and scheduler source added after F07. Resolve only the exact
# literal inventory set; never adjust the immutable 518-owner count.
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
assert post_f07_native_gpfifo_owners <= all_owners
assert not post_f07_native_gpfifo_owners & research_owners
assert post_f07_native_gpfifo_owners.isdisjoint(post_f07_ampere_semaphore_owners)
assert "EDEN_NS2_GPFIFO_SCHEDULER" in release_cmake
assert (ROOT / "tools/ns2/check_native_ampere_semaphore_host.py").is_file()
print("ENCORE_POST_F07_NATIVE_GPFIFO_ISOLATION_PASS", "owners=3")

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

# C00 AudioIn fix has an independently tested maintained source helper.
# Keep the immutable 518-source F07 review untouched while admitting it.
post_f07_c00_audioin_owners = {"headless/audio_in_silence.h",
                                "headless/audio_device_session_ps5.cpp"}
assert post_f07_c00_audioin_owners <= all_owners
assert '#include "audio_in_silence.h"' in (ROOT / "headless/audio.cpp").read_text()
assert 'audio_input_device_id = "ps5"' in (ROOT / "headless/main.cpp").read_text()
assert not post_f07_c00_audioin_owners.intersection(
    research_owners | post_f07_p5_astc_scope_bridge_owners |
    post_f07_feature_stack_owners | post_f07_r09_overlay_owners)
assert 'IsValidVirtualAddressRange' in (ROOT / "headless/audio_device_session_ps5.cpp").read_text()
print("ENCORE_POST_F07_C00_AUDIOIN_OWNER_PASS", "shipping_sources=2 historical_F07=518")
post_f07_r23_fixed_source_owners = {
    "headless/r23_f2i_conversion_ps5.cpp",
    "headless/r23_bcat_delivery_cache_file_ps5.cpp",
}
assert post_f07_r23_fixed_source_owners <= all_owners
assert post_f07_r23_fixed_source_owners.isdisjoint(
    research_owners | post_f07_c00_audioin_owners | post_f07_feature_stack_owners |
    post_f07_r09_overlay_owners | post_f07_p5_astc_scope_bridge_owners)
r23_cmake = (ROOT / "headless/CMakeLists.txt").read_text()
assert all(p.rsplit("/", 1)[-1] in r23_cmake for p in post_f07_r23_fixed_source_owners)
print("ENCORE_POST_F07_R23_TWO_SELECTED_OWNERS_PASS", "owners=2 historical_F07=518")


owners=all_owners-research_owners-hygiene_owners-ns2_shared_release_owners-ns2_shared_audio_owners-ns2_shared_gpu_access_owners-post_f07_native_vulkan_owners-post_f07_shared_compute_owners-post_f07_launcher_handoff_owners-post_f07_ns2_typed_cache_owners-post_f07_shared_gpu_scalar_owners-post_f07_shared_gpu_remap_owners-post_f07_nup_vfs_owners-post_f07_native_atomic_span_owners-post_f07_native_gpfifo_fetch_owners-post_f07_shared_wait64_owners-post_f07_unified_rasterizer_owners-post_f07_static_engine_owners-post_f07_shared_nvdrv_owners-post_f07_video_decoder_owners-post_f07_native_global_atomic_owners-post_f07_native_stage_buffer_owners-post_f07_task_mesh_owners-post_f07_r437_buffer_base_owners-post_f07_image_array_owners-post_f07_ampere_semaphore_owners-post_f07_native_opcode_owners-post_f07_native_gpfifo_owners-post_f07_feature_stack_owners-post_f07_r09_overlay_owners-post_f07_h05_syncpoint_owners-h01_fs_paths-post_f07_p5_astc_scope_bridge_owners-post_f07_c00_audioin_owners-post_f07_r23_fixed_source_owners
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
assert len(shipping["entries"])==83
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
    assert e["shipping_active_sha256"]==record["active"]
    assert e["shipping_upstream_sha256"]==record["upstream"]
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
assert len(post_entries) == 33
post_index = {item['path']: item for item in post_entries}
assert len(post_index) == len(post_entries)
drift_index = {item['path']: item for item in reviewed_blob_drifts}
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
