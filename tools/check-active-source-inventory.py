#!/usr/bin/env python3
"""Fail if the active C/C++ source catalogue drifts from tracked files.

This verifies file-level coverage and exact graph cross-links only.
It is not a function audit, compiler check or console-test certificate.
"""
from pathlib import Path
import json
import re
import runpy

root = Path(__file__).resolve().parents[1]
active = root / "vendor/encore-active"
document = (root / "docs/EDEN_ACTIVE_SOURCE_CATALOG.md").read_text()
audit = (root / "docs/EDEN_CORE_AUDIT_DEPENDENCIES.md").read_text()
begin, end = "<!-- ACTIVE_SOURCE_CATALOG_START -->", "<!-- ACTIVE_SOURCE_CATALOG_END -->"
assert document.count(begin) == document.count(end) == 1
section = document.split(begin, 1)[1].split(end, 1)[0]
suffixes = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".inc", ".inl", ".s", ".S", ".asm", ".cl"}
physical_all = sorted(
    p.relative_to(active).as_posix()
    for p in active.rglob("*")
    if p.is_file() and p.suffix in suffixes
)
# Exactly pinned third-party sources are in vendor/sources/, not in the
# maintained/active F07 production graph. Reject stale original-source trees
# in encore-active while still auditing *every* maintained override here.
pinned_upstream_source_counts = {
    "ps5-mihawkgen": 632,
    "ps5-fsr3-optical-flow": 41,
    "libwebp": 245,
}
for name, expected in pinned_upstream_source_counts.items():
    upstream = root / "vendor/sources" / name
    assert upstream.is_dir() and not (upstream / ".git").exists(), name
    actual = sum(p.is_file() and p.suffix in suffixes
                 for p in upstream.rglob("*"))
    assert actual == expected, ("Pinned upstream inventory drift", name, actual, expected)
for stale in ("PS5_MihawkGen", "PS5_FSR3OpticalFlow", "libwebp"):
    assert not (active / stale).exists(), ("Sources belong in sources/", stale)
print("ENCORE_PINNED_UPSTREAM_SOURCES_PASS",
      f"sources={sum(pinned_upstream_source_counts.values())}",
      f"trees={len(pinned_upstream_source_counts)}", "excluded_from_f07=1")
# Preserve the audited production source catalogue. The NS2 research sources
# are tracked separately and explicitly; they are not F07 shipping proofs.
research_manifest = json.loads(
    (root / "docs/NS2_RESEARCH_ADDED_SOURCE_OWNERS.json").read_text()
)
research_paths = research_manifest["paths"]
assert research_manifest["schema_version"] == 1
assert len(research_paths) == len(set(research_paths)) == 120
assert research_paths == sorted(research_paths)
retired_am = {
    "ns2-runtime/am/core/hle/service/am/service/application_proxy.cpp",
    "ns2-runtime/am/core/hle/service/am/service/application_proxy.h",
    "ns2-runtime/am/core/hle/service/am/service/graphics_scaling_parameters_functions.cpp",
    "ns2-runtime/am/core/hle/service/am/service/graphics_scaling_parameters_functions.h",
}
assert not retired_am & set(physical_all), "Retired false-success AM sources were restored"
assert not retired_am & set(research_paths), "Retired AM sources remain in research inventory"
assert set(research_paths) <= set(physical_all), (
    "Missing pinned NS2 research source owners", sorted(set(research_paths) - set(physical_all))
)
assert all(p.startswith(("ns2-", "eden-core/include/", "eden-vulkan/include/"))
           for p in research_paths), "Unreviewed NS2 source category"
# Four extracted AOC translation/header owners arrived with the mainline
# installation integration. They are shipping additions, not historical F07
# owners and not opt-in NS2 research files. Keep the historical F07 review
# immutable for optimization triage while cataloguing AOC in shipping ownership.
extracted_aoc_owners = {
    "eden-core/src/core/file_sys/extracted_aoc.h",
    "eden-core/src/core/file_sys/extracted_aoc_paths.h",
    "eden-core/src/core/file_sys/romfs_factory.cpp",
    "eden-core/src/core/hle/service/aoc/addon_content_manager.cpp",
}
assert extracted_aoc_owners <= set(physical_all), (
    "Missing maintained extracted AOC owners", sorted(extracted_aoc_owners - set(physical_all))
)
assert not extracted_aoc_owners.intersection(research_paths), (
    "Extracted AOC production owners misclassified as NS2 research"
)
aoc_recipe = (root / "headless/CMakeLists.txt").read_text()
assert "foreach(eden_aoc_relative IN ITEMS" in aoc_recipe
assert '"file_sys/romfs_factory.cpp"' in aoc_recipe
assert '"hle/service/aoc/addon_content_manager.cpp"' in aoc_recipe
assert 'list(REMOVE_ITEM core_sources "${eden_aoc_relative}")' in aoc_recipe
assert 'list(APPEND core_sources "${eden_aoc_maintained}")' in aoc_recipe
print("ENCORE_EXTRACTED_AOC_OWNER_PASS", f"new_shipping={len(extracted_aoc_owners)}")
# Shared NS2 heap overlays are newly reviewed, release-selected kernel owners.
# They are neither experimental research nor part of the frozen F07 historical
# optimization catalogue. Track them separately and retain the existing
# 337-owner F07 graph (and its original audit receipts) byte-for-byte.
shared_ns2_kernel_owners = {
    "ns2-runtime/kernel/core/hle/kernel/k_address_space_info.cpp",
    "ns2-runtime/kernel/core/hle/kernel/svc/svc_physical_memory.cpp",
    "ns2-runtime/process/core/core.cpp",
}
assert shared_ns2_kernel_owners <= set(physical_all), (
    "Missing shipping NS2 kernel overlays", sorted(shared_ns2_kernel_owners - set(physical_all))
)
assert not shared_ns2_kernel_owners.intersection(research_paths)
kernel_select = (root / "headless/CMakeLists.txt").read_text()
assert 'set(EDEN_SHARED_NS2_KERNEL_HEAP ON)' in kernel_select
assert 'PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM' in kernel_select
for relative in shared_ns2_kernel_owners:
    if relative.startswith("ns2-runtime/kernel/core/"):
        assert relative.removeprefix("ns2-runtime/kernel/core/") in kernel_select
assert 'ns2-runtime/process/core/core.cpp' in kernel_select
print("ENCORE_SHARED_NS2_KERNEL_SOURCE_PASS", f"new_shipping={len(shared_ns2_kernel_owners)}")
shared_ns2_audio_owners = {
    "ns2-runtime/audio/core/hle/service/audio/audio.cpp",
    "ns2-runtime/audio/core/hle/service/audio/nx2_audio_user_client.h",
    "ns2-runtime/audio/core/hle/service/audio/nx2_sysmix.cpp",
    "ns2-runtime/audio/core/hle/service/audio/nx2_sysmix.h",
    "ns2-runtime/audio/core/hle/service/audio/nx2_sysmix_user_service.h",
    "ns2-runtime/audio/core/hle/service/nx2_streamplay.h",
}
assert shared_ns2_audio_owners <= set(physical_all), (
    "Missing NS2 audio service owners", sorted(shared_ns2_audio_owners - set(physical_all))
)
assert not shared_ns2_audio_owners.intersection(set(research_paths) | shared_ns2_kernel_owners)
assert 'set(EDEN_SHARED_NS2_AUDIO ON)' in kernel_select
assert 'list(APPEND eden_ns2_audio_sources' in kernel_select
assert 'core/hle/service/audio/nx2_sysmix.cpp' in kernel_select
assert "python3 -B tools/ns2/check_native_sysmix_pcm_ring_host.py" in (
    root / ".github/workflows/encore-core-preflight.yml").read_text()
print("ENCORE_SHARED_NS2_AUDIO_SOURCE_PASS", f"owners={len(shared_ns2_audio_owners)}")
shared_ns2_gpu_access_owners = {
    "ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp",
    "ns2-runtime/gpu_access_svc/core/hle/kernel/ns2_gpu_memory_attribute.h",
    "ns2-runtime/gpu_access_svc/core/hle/kernel/svc_types.h",
    "ns2-runtime/gpu_access_svc/core/hle/kernel/k_memory_block.h",
}
assert shared_ns2_gpu_access_owners <= set(physical_all), sorted(shared_ns2_gpu_access_owners - set(physical_all))
assert not shared_ns2_gpu_access_owners.intersection(set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners)
assert 'set(EDEN_SHARED_NS2_GPU_ACCESS_SVC ON)' in kernel_select
print("ENCORE_SHARED_NS2_GPU_ACCESS_SOURCE_PASS", f"owners={len(shared_ns2_gpu_access_owners)}")
# Added after the frozen 337-owner source graph: the NS2 native Vulkan
# rasterizer ABI declaration. It is part of the PS5-only experimental bridge,
# not evidence of a historical F07 optimization or a Switch 1 code change.
post_f07_native_vulkan_owners = {
    "eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h",
}
assert post_f07_native_vulkan_owners <= set(physical_all), (
    "Missing experimental Vulkan ABI owner",
    sorted(post_f07_native_vulkan_owners - set(physical_all)),
)
assert not post_f07_native_vulkan_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners
)
native_rasterizer_header = (active / next(iter(post_f07_native_vulkan_owners))).read_text()
assert native_rasterizer_header.count("DispatchNativeCompute(") == 1
assert "#ifdef PS5_NATIVE" in native_rasterizer_header
assert "[[nodiscard]] bool DispatchNativeCompute(const Tegra::NativeComputeLaunch& launch) override;" in native_rasterizer_header
assert 'file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")' in (
    root / "headless/vulkan.cmake"
).read_text()
print("ENCORE_POST_F07_NATIVE_VULKAN_ABI_PASS", f"owners={len(post_f07_native_vulkan_owners)}")
# Common Maxwell/Ampere Compute reflection is maintained after the frozen
# 337-source audit. Do not silently classify it as NS2-only research.
shared_compute_owners = {
    "eden-vulkan/include/video_core/renderer_vulkan/vk_compute_storage_layout.h",
}
assert shared_compute_owners <= set(physical_all), (
    "Missing maintained shared Compute owner", sorted(shared_compute_owners-set(physical_all)))
assert not shared_compute_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners
)
shared_compute_header = (active / next(iter(shared_compute_owners))).read_text()
assert "namespace Vulkan::ComputeStorageLayout {" in shared_compute_header
assert "count > max_bindings - flattened" in shared_compute_header
assert "std::numeric_limits<std::uint32_t>::max()" in shared_compute_header
shared_compute_cpp = (active / "eden-vulkan/vk_compute_pipeline_cost.cpp").read_text()
assert '#include "video_core/renderer_vulkan/vk_compute_storage_layout.h"' in shared_compute_cpp
assert shared_compute_cpp.count("ComputeStorageLayout::ForEach(") == 3
print("ENCORE_SHARED_COMPUTE_SOURCE_PASS", f"owners={len(shared_compute_owners)}")
# New native-only cache ABI owner, after the locked 337-file history.
# It is generated from the already-reviewed shipping source, not a new Eden
# backport and not evidence of completion of the NS2 Vulkan image path.
native_typed_texture_owners = {
    "eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache_base.h",
}
assert native_typed_texture_owners <= set(physical_all), (
    "Native TIC/TSC cache interface missing",
    sorted(native_typed_texture_owners - set(physical_all)))
assert not native_typed_texture_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners | shared_compute_owners
)
typed_cache_header = (active / next(iter(native_typed_texture_owners))).read_text()
assert "#ifdef PS5_NATIVE" in typed_cache_header
assert "AcquireNativeImageView(" in typed_cache_header
assert "NativeChannelMatches(" in typed_cache_header
assert "AcquireNativeSampler(" in typed_cache_header
assert 'target_include_directories(video_core BEFORE PUBLIC "${PORT_BUILD_DIR}/vulkan-cache")' in (
    root / "headless/vulkan.cmake").read_text()
print("ENCORE_POST_F07_NS2_TYPED_TEXTURE_CACHE_OWNER_PASS",
      f"owners={len(native_typed_texture_owners)}")
# P1.2: one common native GPU scalar seam helper is selected by the already
# maintained PS5 memory manager for BOTH NS1 and NS2. It was introduced after
# the frozen F07 source audit and must carry independent source/host proof.
shared_gpu_scalar_owners = {"eden-core/src/video_core/native_paged_scalar.h"}
assert shared_gpu_scalar_owners <= set(physical_all), (
    "Missing shared native GPU scalar owner",
    sorted(shared_gpu_scalar_owners - set(physical_all)))
assert not shared_gpu_scalar_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners |
    shared_compute_owners | native_typed_texture_owners
)
gpu_owner = (active / "eden-core/src/video_core/memory_manager.cpp").read_text()
assert '#include "native_paged_scalar.h"' in gpu_owner
assert "Eden::GpuScalar::Read(addr, value," in gpu_owner
assert "Eden::GpuScalar::Write(addr, data," in gpu_owner
assert "memory.GetSpan(dev_addr_base, copy_amount)" in gpu_owner
assert "python3 -B tools/ns2/check_paged_gpu_scalar_host.py" in (
    root / ".github/workflows/encore-core-preflight.yml").read_text()
print("ENCORE_POST_F07_SHARED_GPU_SCALAR_OWNER_PASS",
      f"owners={len(shared_gpu_scalar_owners)}")
# P1.2 post-F07 common source: a Mapped->Mapped physical rebind must
# invalidate the old rasterizer backing on both NS1 and NS2. This is
# neither an opt-in NS2 owner nor part of the frozen 337-source graph.
shared_gpu_remap_owners = {"eden-core/src/video_core/native_gpu_page_remap.h"}
assert shared_gpu_remap_owners <= set(physical_all)
assert not shared_gpu_remap_owners.intersection(
    set(research_paths) | shared_gpu_scalar_owners |
    shared_ns2_kernel_owners | shared_ns2_audio_owners | shared_ns2_gpu_access_owners)
remap_source = (active / "eden-core/src/video_core/memory_manager.cpp").read_text()
assert '#include "native_gpu_page_remap.h"' in remap_source
assert remap_source.count("Eden::GpuMemory::NeedsRasterizerUnmap(") == 2
assert "tools/ns2/check_native_gpu_pte_remap_host.py" in (
    root / ".github/workflows/ns2-research-host.yml").read_text()
print("ENCORE_POST_F07_SHARED_GPU_REMAP_OWNER_PASS",
      f"owners={len(shared_gpu_remap_owners)}")
# P2.3 opt-in native Compute atomic-span policy was added AFTER the frozen
# historical 337-source graph. Preserve that baseline without misclassifying
# this new NS2-only header as a shipping/performance source.
post_f07_native_atomic_owners = {
    "ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_atomic_span.h",
}
assert post_f07_native_atomic_owners <= set(physical_all), (
    "Missing native QMD3 atomic span owner",
    sorted(post_f07_native_atomic_owners - set(physical_all)))
assert not post_f07_native_atomic_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners |
    shared_compute_owners | native_typed_texture_owners |
    shared_gpu_scalar_owners | shared_gpu_remap_owners)
atomic_owner=(active/next(iter(post_f07_native_atomic_owners))).read_text()
assert "CollectNativeQmdAtomicSpans(" in atomic_owner
assert "NativeQmdAtomicSpansFitBindings(" in atomic_owner
assert 'native_atomic_span.h' in (
    active/"ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.h"
).read_text()
assert "python3 -B tools/ns2/check_native_qmd_atomic_span_host.py" in (
    root/".github/workflows/ns2-research-host.yml").read_text()
print("ENCORE_POST_F07_NATIVE_ATOMIC_SPAN_OWNER_PASS",
      f"owners={len(post_f07_native_atomic_owners)}")

# P2.3: canonical QMD3 global atomic-to-SSBO conversion is a separate,
# release-selected native source owner, not a retroactive F07 optimization.
post_f07_native_global_atomic_owners = {
    "ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_global_atomic_binding.h",
}
assert post_f07_native_global_atomic_owners <= set(physical_all), (
    "Missing native QMD3 global atomic binding owner",
    sorted(post_f07_native_global_atomic_owners - set(physical_all)))
assert not post_f07_native_global_atomic_owners.intersection(research_paths)
atomic_binding=(active/next(iter(post_f07_native_global_atomic_owners))).read_text()
shader_bridge=(active/"ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp").read_text()
assert "NativeAtomic::Rewrite(ir)" in shader_bridge
assert "native_global_atomic_binding.h" in shader_bridge
assert "Opcode::PackUint2x32" in atomic_binding
assert "Opcode::CompositeConstructU32x2" in atomic_binding
assert "left_pointer == right_pointer" in atomic_binding
assert "Opcode::GlobalAtomicAddF32" in atomic_binding
assert "Opcode::GlobalAtomicMaxF16x2" in atomic_binding
assert "Opcode::GlobalAtomicMaxF32x2" in atomic_binding
assert "rec.cbuf_offset == address->descriptor" in atomic_binding
assert "python3 -B tools/ns2/check_native_qmd_direct_cbuf_host.py" in (
    root/".github/workflows/ns2-research-host.yml").read_text()
print("ENCORE_POST_F07_NATIVE_GLOBAL_ATOMIC_BINDING_PASS", "owners=1")

# P2.7 native command-fetch recheck was introduced after the 337-source
# historical F07 graph. It is a conditional research header, NOT a new
# shipping optimization proof. Require a real normal/DEV owner and a host
# execution test rather than silently increasing the frozen catalogue.
post_f07_native_gpfifo_fetch_owners = {
    "ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h",
}
assert post_f07_native_gpfifo_fetch_owners <= set(physical_all), (
    "Missing native GPFIFO live fetch helper",
    sorted(post_f07_native_gpfifo_fetch_owners - set(physical_all)))
assert not post_f07_native_gpfifo_fetch_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners |
    shared_compute_owners | native_typed_texture_owners |
    shared_gpu_scalar_owners | shared_gpu_remap_owners |
    post_f07_native_atomic_owners)
fetch_header=(active/next(iter(post_f07_native_gpfifo_fetch_owners))).read_text()
assert 'NativeGpfifoFetchMapped(' in fetch_header
assert 'words > (native_limit - address) / bytes_per_word' in fetch_header
for dma in ('dma_pusher.cpp','dma_pusher_dev.cpp'):
    owner=(active/'eden-core/src/video_core'/dma).read_text()
    assert '#include "core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h"' in owner
    assert 'NativeGpfifoFetchMapped(' in owner
assert 'python3 -B tools/ns2/check_native_gpu_fetch_admission_host.py' in (
    root/'.github/workflows/encore-core-preflight.yml').read_text()
print('ENCORE_POST_F07_NATIVE_GPFIFO_FETCH_OWNER_PASS',
      f'owners={len(post_f07_native_gpfifo_fetch_owners)}')

# P1.3: five new shared kernel arbiter owners are release-selected only
# with the reviewed dual-NPDM GPU-access SVC. Keep the frozen 337-file
# source catalogue intact, with a separate verified post-F07 owner list.
shared_ns2_wait64_owners = {
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.cpp",
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.h",
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_process.h",
    "ns2-runtime/kernel_wait64/core/hle/kernel/svc.h",
    "ns2-runtime/kernel_wait64/core/hle/kernel/svc/svc_address_arbiter.cpp",
}
assert shared_ns2_wait64_owners <= set(physical_all), sorted(
    shared_ns2_wait64_owners - set(physical_all))
assert not shared_ns2_wait64_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners |
    shared_compute_owners | native_typed_texture_owners |
    shared_gpu_scalar_owners | shared_gpu_remap_owners |
    post_f07_native_atomic_owners)
assert 'if(EDEN_SHARED_NS2_GPU_ACCESS_SVC)' in kernel_select
assert 'set(EDEN_SHARED_NS2_WAIT64 ON)' in kernel_select
assert 'set_property(TARGET core PROPERTY SOURCES "${eden_wait64_sources}")' in kernel_select
assert (root/'tools/ns2/check_shared_kernel_wait64_host.py').is_file()
print("ENCORE_SHARED_NS2_WAIT64_SOURCE_PASS", f"post_f07_owners={len(shared_ns2_wait64_owners)}")

# The unified PS5 RasterizerInterface was introduced after the historical
# F07 snapshot, replacing a per-mode vtable guard. Preserve historical
# provenance without hiding or counting this new production owner as F07.
post_f07_unified_rasterizer_owners = {
    "ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h",
}
assert post_f07_unified_rasterizer_owners <= set(physical_all)
assert not post_f07_unified_rasterizer_owners.intersection(
    set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
    shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners)
unified_rasterizer = (active / next(iter(post_f07_unified_rasterizer_owners))).read_text()
assert 'virtual bool DispatchNativeCompute(const Tegra::NativeComputeLaunch&)' in unified_rasterizer
assert '#ifdef PS5_NATIVE' in unified_rasterizer
assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' not in unified_rasterizer
assert 'vulkan_abi/video_core/rasterizer_interface.h' in kernel_select
print('ENCORE_POST_F07_UNIFIED_RASTERIZER_ABI_OWNER_PASS owners=1')

# Production-selected CPU6 scheduler/JIT and A64 LDAPR owners live in the
# vendor submodule, not headless. Preserve the frozen F07 catalogue; these
# are separately audited shipping owners, never the opt-in research ledger.
post_f07_cpu6_ldapr_owners = {
    "ns2-runtime/cpu6/maintained/core/hle/kernel/global_scheduler_context.cpp",
    "ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_32.cpp",
    "ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_64.cpp",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.h",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.inc",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/impl.h",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/load_store_exclusive.cpp",
}
assert post_f07_cpu6_ldapr_owners <= set(physical_all), (
    "Missing vendor-maintained CPU6/LDAPR owners",
    sorted(post_f07_cpu6_ldapr_owners - set(physical_all)))
assert not post_f07_cpu6_ldapr_owners.intersection(research_paths), (
    "Shipping CPU6/LDAPR owners misclassified as research")
assert 'vendor/encore-active/ns2-runtime/cpu6/maintained/core' in (
    root/'headless/ns2_cpu6_source_bridge.cmake').read_text()
assert 'vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64' in (
    root/'headless/shared_a64_ldapr.cmake').read_text()
print("ENCORE_VENDOR_MAINTAINED_CPU6_LDAPR_PASS owners=7")

# P1.3 post-F07 live NVDRV owners. These two complete C++ translation
# units are shipped by the single shared core; neither alters the original
# 337-owner F07 performance audit nor replaces pinned sources in-place.
post_f07_shared_nvdrv_owners = {
    "eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp",
    "eden-core/src/core/hle/service/nvdrv/devices/nvmap.cpp",
    "eden-core/src/core/hle/service/nvdrv/devices/nvhost_nvdec_common.cpp",
}
assert post_f07_shared_nvdrv_owners <= set(physical_all), (
    "Missing complete maintained NVDRV NVMap owners",
    sorted(post_f07_shared_nvdrv_owners - set(physical_all)))
assert not post_f07_shared_nvdrv_owners.intersection(research_paths)
nvmap_recipe = (root / "headless/CMakeLists.txt").read_text()
assert "EDEN_MAINTAINED_NVDRV_NVMAP_CORE" in nvmap_recipe
assert "EDEN_MAINTAINED_NVDRV_NVMAP_DEVICE" in nvmap_recipe
assert "EDEN_MAINTAINED_NVDRV_NVDEC" in nvmap_recipe
assert "python3 -B tools/ns2/check_nvdrv_fd_session_owners_host.py" in (
    root / ".github/workflows/encore-core-preflight.yml").read_text()
print("ENCORE_POST_F07_SHARED_NVDRV_OWNER_PASS", f"owners={len(post_f07_shared_nvdrv_owners)}")

# Shared FFmpeg-backed native decoder added after the frozen 337-owner F07
# catalogue; it is selected by the unified native engine, not experimental.
post_f07_video_decoder_owners = {
    "ns2-runtime/video_decoder/video_core/host1x/h264_packet.h",
    "ns2-runtime/video_decoder/video_core/host1x/nx2_video_decoder.h",
    "ns2-runtime/video_decoder/video_core/host1x/nx2_video_decoder.cpp",
    "ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.h",
    "ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp",
    "ns2-runtime/video_decoder/core/hle/service/am/service/native_video_eos.h",
    "ns2-runtime/video_decoder/core/hle/service/am/service/native_video_work_buffer.h",
    "ns2-runtime/video_decoder/core/hle/service/am/service/native_video_ready_state.h",
}
assert post_f07_video_decoder_owners <= set(physical_all), (
    "Missing maintained native FFmpeg owner",
    sorted(post_f07_video_decoder_owners - set(physical_all)))
assert not post_f07_video_decoder_owners.intersection(research_paths)
assert "EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT" in (
    root / "headless/CMakeLists.txt").read_text()
assert (root / "tools/ns2/check_native_video_decoder_ipc_host.py").is_file()
print("ENCORE_POST_F07_NATIVE_VIDEO_CODEC_OWNER_PASS", f"owners={len(post_f07_video_decoder_owners)}")

# R437: the native BufferCacheBase declarations arrived after the frozen
# 337-source F07 register. Audit this exact added owner, not the F07 snapshot.
post_f07_r437_buffer_base_owners = {
    "eden-core/src/video_core/buffer_cache/buffer_cache_base.h",
}
assert post_f07_r437_buffer_base_owners <= set(physical_all)
assert not post_f07_r437_buffer_base_owners.intersection(research_paths)
r437_path = next(iter(post_f07_r437_buffer_base_owners))
r437_body = (active / r437_path).read_text()
pinned_base = (root / "vendor/sources/eden/src/video_core/buffer_cache/buffer_cache_base.h").read_text()
old_mark = "    void MarkWrittenBuffer(BufferId buffer_id, DAddr device_addr, u32 size);"
new_mark = """    // R437: preserve the legacy three-argument call while exposing explicit
    // write-tick ownership to the maintained native BufferCache implementation.
    void MarkWrittenBuffer(BufferId buffer_id, DAddr device_addr, u32 size,
                           bool needs_sync = true);"""
old_wait = "    void WaitForGpuFenceIfNeeded(Buffer& buffer);"
new_wait = """    // Same fence-wait member as the maintained R437 BufferCache body.
    void SynchronizeBufferWrites(Buffer& buffer);"""
assert r437_body.count(new_mark) == r437_body.count(new_wait) == 1
assert r437_body.replace(new_mark, old_mark).replace(new_wait, old_wait) == pinned_base, (
    "Unreviewed R437 BufferCache base-source drift")
r437_select = (root / "headless/CMakeLists.txt").read_text()
assert "set(EDEN_MAINTAINED_BUFFER_BASE" in r437_select
assert "buffer-pages/video_core/buffer_cache/buffer_cache_base.h" in r437_select
print("ENCORE_POST_F07_R437_BUFFER_BASE_PASS", f"owners={len(post_f07_r437_buffer_base_owners)}")

# P2.4: the maintained Ampere Task/Mesh stage-buffer decoder was introduced
# after the frozen F07 337-source review. It is an active shader header, not
# a historical optimization. Keep its exact owner and CMake selection guarded.
post_f07_native_stage_buffer_owners = {
    "ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_stage_buffer.h",
}
assert post_f07_native_stage_buffer_owners <= set(physical_all), (
    "Missing native stage-buffer decoder owner",
    sorted(post_f07_native_stage_buffer_owners - set(physical_all)))
assert not post_f07_native_stage_buffer_owners.intersection(research_paths)
stage_buffer_source = (active / next(iter(post_f07_native_stage_buffer_owners))).read_text()
stage_lowerer = (active / "ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h").read_text()
assert "DecodeNativeStageBufferAccess(" in stage_buffer_source
assert "DecodeNativeStageBufferAccess(insn)" in stage_lowerer
assert "native_stage_buffer.h" in (root / "headless/CMakeLists.txt").read_text()
print("ENCORE_POST_F07_STAGE_BUFFER_OWNER_PASS", f"owners={len(post_f07_native_stage_buffer_owners)}")

# P2.4 Task/Mesh maintained source ports are post-F07 sources in the
# vendor feature branch. They are NOT F07 historical optimization receipts
# and cannot be called shipping until the full shader/Vulkan graph is selected
# and the host compiler/spirv-val qualification passes.
post_f07_task_mesh_source_owners = {
    "eden-shader/src/shader_recompiler/backend/glasm/emit_glasm.cpp",
    "eden-shader/src/shader_recompiler/backend/glasm/emit_glasm_instructions.h",
    "eden-shader/src/shader_recompiler/backend/glasm/emit_glasm_not_implemented.cpp",
    "eden-shader/src/shader_recompiler/backend/glasm/glasm_emit_context.cpp",
    "eden-shader/src/shader_recompiler/backend/glsl/emit_glsl_instructions.h",
    "eden-shader/src/shader_recompiler/backend/glsl/emit_glsl_not_implemented.cpp",
    "eden-shader/src/shader_recompiler/backend/glsl/glsl_emit_context.cpp",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv.cpp",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_instructions.h",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_mesh.cpp",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_special.cpp",
    "eden-shader/src/shader_recompiler/backend/spirv/spirv_emit_context.h",
    "eden-shader/src/shader_recompiler/environment.h",
    "eden-shader/src/shader_recompiler/frontend/ir/ir_emitter.cpp",
    "eden-shader/src/shader_recompiler/frontend/ir/ir_emitter.h",
    "eden-shader/src/shader_recompiler/frontend/ir/microinstruction.cpp",
    "eden-shader/src/shader_recompiler/frontend/ir/opcodes.cpp",
    "eden-shader/src/shader_recompiler/frontend/ir/opcodes.h",
    "eden-shader/src/shader_recompiler/frontend/ir/opcodes.inc",
    "eden-shader/src/shader_recompiler/frontend/ir/program.h",
    "eden-shader/src/shader_recompiler/frontend/maxwell/maxwell.inc",
    "eden-shader/src/shader_recompiler/frontend/maxwell/structured_control_flow.cpp",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/internal_stage_buffer_entry_read.cpp",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate_program.cpp",
    "eden-shader/src/shader_recompiler/ir_opt/collect_shader_info_pass.cpp",
    "eden-shader/src/shader_recompiler/runtime_info.h",
    "eden-shader/src/shader_recompiler/shader_info.h",
    "eden-shader/src/shader_recompiler/stage.h",
    "eden-vulkan/include/video_core/vulkan_common/vulkan_device.h",
}
assert post_f07_task_mesh_source_owners <= set(physical_all), (
    "Missing maintained Task/Mesh source", sorted(post_f07_task_mesh_source_owners - set(physical_all)))
assert not post_f07_task_mesh_source_owners.intersection(research_paths)
assert len(post_f07_task_mesh_source_owners) == 29
assert "EDEN_NATIVE_TASK_MESH_ROOT" in (root / "headless/CMakeLists.txt").read_text()
print("ENCORE_P24_TASK_MESH_STAGED_SOURCE_PASS", f"owners={len(post_f07_task_mesh_source_owners)}")

# Track the three unified Maxwell/NS2 opcode owners added after F07.
# These are one ABI (decode / enum / name table), not F07 optimizations.
post_f07_native_opcode_owners = {
    "eden-shader/src/shader_recompiler/frontend/maxwell/decode.cpp",
    "eden-shader/src/shader_recompiler/frontend/maxwell/opcodes.cpp",
    "eden-shader/src/shader_recompiler/frontend/maxwell/opcodes.h",
}
assert post_f07_native_opcode_owners <= set(physical_all)
assert not post_f07_native_opcode_owners.intersection(research_paths)
opcode_root = active / "eden-shader/src/shader_recompiler/frontend/maxwell"
assert "INST(ISBE_nx2" in (opcode_root / "maxwell.inc").read_text()
assert '#include "maxwell.inc"' in (opcode_root / "opcodes.h").read_text()
for name in ("decode.cpp", "opcodes.cpp"):
    assert '#include "shader_recompiler/frontend/maxwell/maxwell.inc"' in (
        opcode_root / name).read_text()
recipe = (root / "headless/CMakeLists.txt").read_text()
assert "frontend/maxwell/decode.cpp" in recipe and "frontend/maxwell/opcodes.cpp" in recipe
print("ENCORE_POST_F07_NATIVE_OPCODE_OWNER_PASS", "owners=3")

# P2.2c's maintained SPIR-V image emitter is a new post-F07 production
# source, not a historical F07 optimization or an unselected experiment.
# Keep the immutable 337-file source audit exact and independently prove the
# new source is selected once by the native shared shader graph.
post_f07_image_array_owners = {
    "ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_image.cpp",
}
assert post_f07_image_array_owners <= set(physical_all), (
    "Missing maintained native descriptor array source",
    sorted(post_f07_image_array_owners - set(physical_all)))
assert not post_f07_image_array_owners.intersection(research_paths)
image_select = (root / "headless/CMakeLists.txt").read_text()
assert 'list(REMOVE_ITEM eden_ns2_shader_sources "backend/spirv/emit_spirv_image.cpp")' in image_select
assert 'list(APPEND eden_ns2_shader_sources "${EDEN_NS2_SPIRV_IMAGE_ARRAY}")' in image_select
print("ENCORE_P22C_SPIRV_DESCRIPTOR_ARRAY_OWNER_PASS",
      f"owners={len(post_f07_image_array_owners)}")

# P2.7: the native Ampere semaphore method decoder was created after the
# immutable 337-file F07 audit. Keep its exact new owner in the supplemental
# manifest, not in the frozen performance snapshot (nor research paths).
post_f07_ampere_semaphore_owners = {
    "ns2-runtime/gpu_dispatch/video_core/engines/native_ampere_semaphore.h",
}
assert post_f07_ampere_semaphore_owners <= set(physical_all), (
    "Missing maintained Ampere semaphore decoder",
    sorted(post_f07_ampere_semaphore_owners - set(physical_all)))
assert not post_f07_ampere_semaphore_owners.intersection(research_paths)
native_puller = (root / "vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp").read_text()
assert '#include "native_ampere_semaphore.h"' in native_puller
assert 'ProcessNativeSemaphoreExecute(dma_pusher, method_call.argument)' in native_puller
assert (root / "tools/ns2/check_native_ampere_semaphore_host.py").is_file()
print("ENCORE_POST_F07_AMPERE_SEMAPHORE_OWNER_PASS",
      f"owners={len(post_f07_ampere_semaphore_owners)}")

# P2.7: these three isolated native GPFIFO ownership files were added
# after the frozen F07 source audit. The legacy NS1 DMA and scheduler
# source remains immutable. Verify the production source selector rather
# than quietly counting new NS2 files as historical F07 work.
post_f07_native_gpfifo_owners = {
    "ns2-runtime/gpu_dispatch/video_core/dma_pusher.h",
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp",
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.h",
}
assert post_f07_native_gpfifo_owners <= set(physical_all), (
    "Missing native GPFIFO suspend/resume owner",
    sorted(post_f07_native_gpfifo_owners - set(physical_all)))
assert not post_f07_native_gpfifo_owners.intersection(research_paths)
native_gpfifo_cmake = (root / "headless/CMakeLists.txt").read_text()
assert "EDEN_NS2_GPFIFO_SCHEDULER" in native_gpfifo_cmake
assert 'list(REMOVE_ITEM eden_ns2_sched_sources "control/scheduler.cpp")' in native_gpfifo_cmake
assert 'list(APPEND eden_ns2_sched_sources "${EDEN_NS2_GPFIFO_SCHEDULER}")' in native_gpfifo_cmake
native_dma_header = (active / "ns2-runtime/gpu_dispatch/video_core/dma_pusher.h").read_text()
assert "command_resume_offset" in native_dma_header
assert "#ifdef PS5_NATIVE" not in native_dma_header
assert "ResumePendingNative" in (
    active / "ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp").read_text()
print("ENCORE_POST_F07_NATIVE_GPFIFO_OWNER_PASS", "owners=3")

# The four merged feature PRs added sources after the frozen F07 snapshot.
# They remain visible in a separate exact file ledger, not retroactively
# counted as 337 historically audited vendor sources or as console proofs.
feature_stack = json.loads((root / "docs/ENCORE_POST_F07_FEATURE_STACK_OWNERS.json").read_text())
assert feature_stack["schema_version"] == 1
assert feature_stack["counts"] == {"headless": 54, "vendor_active": 155, "total": 209}
post_f07_feature_vendor_owners = set(feature_stack["vendor_active"])
post_f07_feature_headless_owners = set(feature_stack["headless"])
assert len(post_f07_feature_vendor_owners) == 155
assert len(post_f07_feature_headless_owners) == 54
assert feature_stack["vendor_active"] == sorted(post_f07_feature_vendor_owners)
assert feature_stack["headless"] == sorted(post_f07_feature_headless_owners)
assert post_f07_feature_vendor_owners <= set(physical_all), (
    "Missing merged native graphics owners",
    sorted(post_f07_feature_vendor_owners - set(physical_all)))
assert not post_f07_feature_vendor_owners.intersection(research_paths)
assert all(p.startswith(("amd-fsr31/", "eden-vulkan/"))
           for p in post_f07_feature_vendor_owners)
assert all(p.startswith("headless/") and (root / p).is_file()
           for p in post_f07_feature_headless_owners)
print("ENCORE_MERGED_FEATURE_STACK_POST_F07_PASS",
      "headless=54", "vendor=155", "historical_F07_unchanged=1")

# The R09 GPU owners and private DLL loader arrived after the immutable
# historical 337-source F07 audit. The separate versioned manifest has
# nine headless owners and exactly 58 new vendor owners.
r09_receipt = json.loads(
    (root / "docs/ENCORE_POST_F07_R09_OVERLAY_OWNERS.json").read_text())
assert r09_receipt["schema_version"] == 1
assert r09_receipt["historical_f07_reviewed_owners"] == 518
assert r09_receipt["post_f07_new_unqualified_owners"] == 67
assert r09_receipt["ps5_console_qualified"] is False
assert r09_receipt["dlss_nr_complete_inference_validated"] is False
assert r09_receipt["paths"] == sorted(set(r09_receipt["paths"]))
post_f07_r09_vendor_owners = {
    path.removeprefix("vendor/encore-active/")
    for path in r09_receipt["paths"]
    if path.startswith("vendor/encore-active/")
}
assert len(post_f07_r09_vendor_owners) == 58
assert post_f07_r09_vendor_owners <= set(physical_all), (
    "Missing maintained R09 GPU source owner",
    sorted(post_f07_r09_vendor_owners - set(physical_all)))
assert not post_f07_r09_vendor_owners & (
    set(research_paths) | post_f07_feature_vendor_owners)
post_f07_r09_headless_owners = {
    p for p in r09_receipt["paths"] if p.startswith("headless/")
}
assert len(post_f07_r09_headless_owners) == 9
assert all((root / p).is_file() for p in post_f07_r09_headless_owners), (
    "Missing reviewed R09 local header owner")
assert post_f07_r09_headless_owners.isdisjoint(post_f07_feature_headless_owners)
print("ENCORE_R09_POST_F07_VENDOR_CATALOG_PASS",
      "vendor=58", "headless=9", "historical_F07_unchanged=1")

# P1/P2 H05 added two maintained NVDEC syncpoint allocator owners after
# the historical F07 source snapshot. These are real Encore-active overrides,
# NOT pristine upstream dependency trees and NOT retroactive F07 proofs.
# Keep them explicitly inventoried and separately host-qualified.
post_f07_h05_syncpoint_owners = {
    "eden-sync/overrides/h05-syncpoint/core/hle/service/nvdrv/core/syncpoint_manager.h",
    "eden-sync/src/core/hle/service/nvdrv/core/syncpoint_manager.cpp",
}
assert post_f07_h05_syncpoint_owners <= set(physical_all), (
    "Missing maintained H05 syncpoint override", sorted(
        post_f07_h05_syncpoint_owners - set(physical_all)))
assert not post_f07_h05_syncpoint_owners.intersection(research_paths)
h05_header = (active / "eden-sync/overrides/h05-syncpoint/core/hle/service/nvdrv/core/syncpoint_manager.h").read_text()
h05_source = (active / "eden-sync/src/core/hle/service/nvdrv/core/syncpoint_manager.cpp").read_text()
assert "[[nodiscard]] u32 TryAllocateSyncpoint(bool client_managed);" in h05_header
assert "u32 SyncpointManager::TryAllocateSyncpoint(bool client_managed)" in h05_source
assert "std::lock_guard lock(reservation_lock);" in h05_source
print("ENCORE_POST_F07_H05_SYNCPOINT_OWNER_PASS", "owners=2",
      "source_only=1 historical_F07_unchanged=1")

# H01 adds a native-only filesystem-controller ABI override after the
# frozen F07 inventory. Keep it distinct from pristine sources/eden and
# verify its real executable owner, not a retroactive shipping claim.
post_f07_h01_fs_owners = {
    "eden-core/overrides/h01-filesystem/core/hle/service/filesystem/filesystem.h",
}
assert post_f07_h01_fs_owners <= set(physical_all), (
    "Missing H01 native filesystem rollback header",
    sorted(post_f07_h01_fs_owners - set(physical_all)))
assert not post_f07_h01_fs_owners.intersection(research_paths)
h01_header = (active / next(iter(post_f07_h01_fs_owners))).read_text()
h01_source = (
    active / "eden-core/src/core/hle/service/filesystem/filesystem.cpp"
).read_text()
h01_process = (
    active / "ns2-runtime/process/core/hle/service/os/process.cpp"
).read_text()
assert "void UnregisterProcessIfPresent(ProcessId process_id);" in h01_header
assert "void FileSystemController::UnregisterProcessIfPresent(" in h01_source
assert "UnregisterProcessIfPresent(" in h01_process
print("ENCORE_POST_F07_H01_FS_ROLLBACK_OWNER_PASS", "owners=1",
      "historical_F07_unchanged=1")

# New native NS2 production source owners are separately verified; the
# historical 337-file F07 catalogue remains immutable and independently audited.
ns2_production_added_owners = {
    "eden-vulkan/include/rdna2_nr_vit_min_pool_policy.h",
    "eden-vulkan/include/rdna2_nr_fswin_scratch_pool_policy.h",
    "eden-vulkan/include/video_core/renderer_vulkan/nr_rdna2_readback_dimensions.h",
    "eden-core/src/video_core/textures/decoders.cpp",
    "eden-core/tests/test_ns2_gob16_decoder_public_api.cpp",
    "eden-vulkan/include/video_core/renderer_vulkan/ns2_gpu_retirement_hold.h",
    "eden-vulkan/include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h",
    "eden-vulkan/include/video_core/renderer_vulkan/ns2_verified_upload_batch.h",
    "eden-vulkan/include/video_core/renderer_vulkan/vk_staging_buffer_pool.h",
    "eden-vulkan/tests/test_ns2_cache_shutdown_order.cpp",
    "eden-vulkan/tests/test_ns2_gpu_retirement_hold.cpp",
    "eden-vulkan/tests/test_ns2_verified_upload_batch.cpp",
    "eden-vulkan/vk_staging_buffer_pool.cpp",
    "ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp",
}
assert ns2_production_added_owners <= set(physical_all), (
    "NS2 production source missing", sorted(ns2_production_added_owners - set(physical_all)))
assert not ns2_production_added_owners.intersection(research_paths)

# C03 adds two maintained RADV meta translation units after the frozen
# 337-path shipping ledger. They remain real native compiler inputs and
# must never be retroactively added to historical F07 review.
post_f07_c03_radv_meta_owners = {
    "ps5-mesa/src/amd/vulkan/meta/radv_meta_buffer.c",
    "ps5-mesa/src/amd/vulkan/meta/radv_meta_copy.c",
}
assert post_f07_c03_radv_meta_owners <= set(physical_all)
assert post_f07_c03_radv_meta_owners.isdisjoint(
    ns2_production_added_owners | set(research_paths))
print("NS1_C03_POST_F07_NATIVE_OWNER_PASS", "meta_units=2 historical_F07=337")

# R23 adds 45 selected source owners after the frozen 337-file F07 ledger.
# Keep exact paths, require all to exist, and exclude them from historical F07
# rather than silently re-dating the audited source snapshot.
post_f07_r23_added_owners = {
    "eden-core/include/common/uuid.h",
    "eden-core/include/core/file_sys/patch_manager.h",
    "eden-core/include/core/file_sys/registered_cache.h",
    "eden-core/include/core/file_sys/savedata_factory.h",
    "eden-core/include/core/hle/service/acc/profile_manager.h",
    "eden-core/include/core/hle/service/filesystem/fsp/fs_i_storage.h",
    "eden-core/include/core/hle/service/ipc_helpers.h",
    "eden-core/include/core/hle/service/service.h",
    "eden-core/include/core/memory/cheat_engine.h",
    "eden-core/include/dynarmic/backend/x64/constant_pool.h",
    "eden-core/include/hid_core/frontend/emulated_controller.h",
    "eden-core/include/hid_core/hid_core.h",
    "eden-core/src/audio_core/opus/decoder.cpp",
    "eden-core/src/audio_core/opus/hardware_opus.cpp",
    "eden-core/src/audio_core/opus/hardware_opus.h",
    "eden-core/src/common/uuid.cpp",
    "eden-core/src/core/hle/service/am/window_system.cpp",
    "eden-core/src/core/hle/service/audio/errors.h",
    "eden-core/src/core/hle/service/nvnflinger/hardware_composer.cpp",
    "eden-core/src/core/hle/service/ssl/ssl.cpp",
    "eden-core/src/core/hle/service/ssl/ssl_backend.h",
    "eden-core/src/core/hle/service/ssl/ssl_backend_openssl.cpp",
    "eden-core/src/core/memory/cheat_engine.cpp",
    "eden-core/src/dynarmic/backend/x64/emit_x64_floating_point.cpp",
    "eden-core/src/dynarmic/backend/x64/emit_x64_sm4.cpp",
    "eden-core/src/dynarmic/backend/x64/emit_x64_vector_floating_point.cpp",
    "eden-core/src/dynarmic/frontend/A32/decoder/asimd.inc",
    "eden-core/src/dynarmic/frontend/A32/translate/impl/a32_translate_impl.h",
    "eden-core/src/dynarmic/frontend/A32/translate/impl/asimd_three_regs.cpp",
    "eden-core/src/dynarmic/frontend/A32/translate/impl/asimd_two_regs_misc.cpp",
    "eden-core/src/hid_core/hid_core.cpp",
    "eden-core/src/video_core/host1x/codec_types.h",
    "eden-core/src/video_core/host1x/codecs/vp9.cpp",
    "eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_warp.cpp",
    "eden-shader/src/shader_recompiler/host_translate_info.h",
    "eden-shader/src/shader_recompiler/ir_opt/constant_propagation_pass.cpp",
    "eden-shader/src/shader_recompiler/ir_opt/geometry_compaction_pass.cpp",
    "eden-shader/src/shader_recompiler/ir_opt/passes.h",
    "eden-shader/src/shader_recompiler/ir_opt/texture_pass.cpp",
    "eden-shader/src/shader_recompiler/ir_opt/vendor_workaround_pass.cpp",
    "eden-shader/src/shader_recompiler/profile.h",
    "eden-vulkan/fixed_pipeline_state.cpp",
    "eden-vulkan/include/video_core/renderer_vulkan/fixed_pipeline_state.h",
    "eden-vulkan/include/video_core/renderer_vulkan/vk_texture_cache.h",
}
assert len(post_f07_r23_added_owners) == 45
assert post_f07_r23_added_owners <= set(physical_all), (
    "Missing post-F07 R23 maintained sources",
    sorted(post_f07_r23_added_owners - set(physical_all)))
assert post_f07_r23_added_owners.isdisjoint(post_f07_c03_radv_meta_owners)
print("NS1_R23_POST_F07_SOURCE_OWNER_PASS", "added=45", "historical_F07=337")

# R457/C00: two new maintained native AudioIn/Out assets; this does not
# rewrite the exact 337-file historical F07 shipping source inventory.
r457_native_audio_owners = {
    "eden-core/overrides/core/memory.h",
    "eden-core/src/audio_core/device/device_session.cpp",
}
assert r457_native_audio_owners <= set(physical_all), (
    "R457 native audio assets absent", sorted(r457_native_audio_owners - set(physical_all)))
audio_r457_owner = (root / "vendor/encore-active/eden-core/src/audio_core/device/device_session.cpp").read_text()
assert "ReadyForAudioRead()" in audio_r457_owner
assert "IsValidAudioInBufferShape(buffer.size, channel_count)" in audio_r457_owner
assert "ReadyForAudioRead() const noexcept;" in (
    root / "vendor/encore-active/eden-core/overrides/core/memory.h").read_text()
print("R457_C00_POST_F07_NATIVE_AUDIO_OWNER_PASS owners=2")

physical = [p for p in physical_all
            if p not in post_f07_r23_added_owners | post_f07_c03_radv_meta_owners | ns2_production_added_owners | set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
            shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners |
            shared_compute_owners | native_typed_texture_owners |
            shared_gpu_scalar_owners | shared_gpu_remap_owners |
            post_f07_native_atomic_owners | post_f07_native_gpfifo_fetch_owners |
            shared_ns2_wait64_owners | post_f07_unified_rasterizer_owners |
            post_f07_cpu6_ldapr_owners | post_f07_shared_nvdrv_owners |
            post_f07_video_decoder_owners | post_f07_native_global_atomic_owners |
            post_f07_native_stage_buffer_owners | post_f07_task_mesh_source_owners |
            post_f07_r437_buffer_base_owners | post_f07_image_array_owners |
            post_f07_ampere_semaphore_owners | post_f07_native_opcode_owners |
             post_f07_native_gpfifo_owners | post_f07_feature_vendor_owners |
             post_f07_r09_vendor_owners | post_f07_h05_syncpoint_owners |
             post_f07_h01_fs_owners | r457_native_audio_owners]
# These two versioned headers preserve the immutable upstream Eden snapshot.
# They must be present in the real source catalogue, not excluded as NS2 fixtures.
warning_hygiene = {
    "eden-header-hygiene/include/common/page_table.h",
    "eden-header-hygiene/include/video_core/macro.h",
}
assert {p for p in physical if p.startswith("eden-header-hygiene/")} == warning_hygiene, (
    "Warning-hygiene active owner drift")
assert len(physical) == 337, ("Shipping source catalogue changed", len(physical))
print("NS2_RESEARCH_SOURCE_LEDGER_PASS",
      f"unqualified={len(research_paths)}", f"historical={len(physical)}")
graph = {}
for line in audit.splitlines():
    if not re.match(r"^\| [A-Z][0-9]{2,3} \|", line):
        continue
    fields = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(fields) < 4 or not fields[3].startswith("vendor/encore-active/"):
        continue
    relative = fields[3].removeprefix("vendor/encore-active/")
    graph.setdefault(relative, []).append(fields[0])
assert all(path in graph for path in post_f07_cpu6_ldapr_owners), (
    "Vendor-maintained CPU6/LDAPR owners missing exact audit rows",
    sorted(path for path in post_f07_cpu6_ldapr_owners if path not in graph))
# A separate supplemental catalog keeps new runtime sources explicitly owned,
# without re-dating or silently increasing the immutable 337-path F07 snapshot.
post_begin, post_end = ("<!-- POST_F07_MAINTAINED_OWNER_START -->",
                        "<!-- POST_F07_MAINTAINED_OWNER_END -->")
assert document.count(post_begin) == document.count(post_end) == 1
post_rows = [line for line in document.split(post_begin)[1].split(post_end)[0].splitlines()
             if line.startswith("| `ns2-runtime/")]
post_expected = [
    f"| `{path}` | {','.join(graph[path])} |"
    for path in sorted(post_f07_cpu6_ldapr_owners)]
assert post_rows == post_expected, ("post-F07 vendor source owner drift",
                                   post_rows, post_expected)
r437_rows = [line for line in document.split(post_begin)[1].split(post_end)[0].splitlines()
             if line.startswith("| `eden-core/src/video_core/buffer_cache/buffer_cache_base.h`")]
assert r437_rows == [
    "| `eden-core/src/video_core/buffer_cache/buffer_cache_base.h` | R437 |",
], ("Missing reviewed R437 BufferCache base owner catalogue", r437_rows)
print("ENCORE_POST_F07_VENDOR_CATALOG_PASS", f"maintained={len(post_rows)}")
def role(path):
    if path.startswith("eden-backports/"):
        return "shipping-backport"
    if path.startswith("ps5-mesa/"):
        return "driver-fork"
    # Test-only historical generator snippets are NOT shipping overrides.
    if path.startswith("eden-vulkan-oracles/"):
        return "oracle-only"
    return "maintained-override"
expected = [
    f"| `{path}` | `{role(path)}` | {','.join(graph[path]) if path in graph else '—'} |"
    for path in physical
]
present = [line for line in section.splitlines() if line.startswith("| `")]
assert present == expected, (
    "Active source catalogue stale or exact graph linkage changed",
    len(present), len(expected),
    next(((a, b) for a, b in zip(present, expected) if a != b), None),
)
# The shipping backport manifest also carries two build recipes that are not
# C/C++ source files; track them explicitly rather than silently omitting them.
manifest = json.loads((active / "eden-backports/manifest.json").read_text())
shipping = set(manifest["entries"])
shipping_cpp = {"src/" + p.removeprefix("eden-backports/src/")
                for p in physical if p.startswith("eden-backports/src/")}
build_recipes = {"src/common/CMakeLists.txt", "src/core/CMakeLists.txt"}
assert shipping == shipping_cpp | build_recipes, (
    "Shipping backport source/build manifest coverage drift",
    sorted(shipping ^ (shipping_cpp | build_recipes)),
)
# Keep the expected count tied to the reviewed manifest revision: every
# additional shipping patch requires an explicit inventory review.
assert len(shipping) == 83 and len(manifest["shipping_receipts"]) == 50
assert all(re.fullmatch(r"[0-9a-f]{64}", digest)
           for digest in manifest["shipping_receipts"].values()), (
    "invalid shipping patch SHA256 receipt",
)
assert manifest["excluded_experimental"] == ["EDEN_EXPERIMENTAL_DUMMY_THREAD_WAITS"]
# All nine selected Vulkan cost translation units have exact graph owners.
# This is source-ownership coverage, not evidence of GPU progress.
vulkan_recipe = (root/"headless/vulkan.cmake").read_text()
cost_modules = ("vk_fence_manager", "vk_buffer_cache", "vk_texture_cache",
                "vk_descriptor_buffer", "vk_multi_range_buffer", "vk_compute_pass",
                "vk_graphics_pipeline", "vk_compute_pipeline", "vk_pipeline_cache")
assert "foreach(name " + " ".join(cost_modules) + ")" in vulkan_recipe
assert 'list(APPEND video_sources "${PORT_BUILD_DIR}/${name}_cost.cpp")' in vulkan_recipe
for module in cost_modules:
    relative = "eden-vulkan/" + module + "_cost.cpp"
    assert (active/relative).is_file(), ("missing selected Vulkan cost source", relative)
    assert relative in graph, ("missing indexed Vulkan cost source", relative)
print("ENCORE_VULKAN_COST_OWNER_PASS", f"selected={len(cost_modules)}")

# Keep the native GPU/guest memory header overrides distinguishable from
# the pinned and materialized backport copies. Selection is native-only.
native_cmake = (root/"headless/CMakeLists.txt").read_text()
assert 'set(EDEN_NATIVE_DIRTY_HEADER_ROOT' in native_cmake
assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")' in native_cmake
assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")' in native_cmake
native_mem = ("device_memory_manager.inc", "gpu_dirty_memory_manager.h", "guest_memory.h")
for name in native_mem:
    rel = "eden-core/overrides/core/" + name
    assert (active/rel).is_file(), ("missing native memory override", rel)
    assert rel in graph, ("native memory override lacks active function owner", rel)
    assert '${EDEN_NATIVE_DIRTY_HEADER_ROOT}/core/' + name in native_cmake
print("ENCORE_NATIVE_MEMORY_OWNER_PASS", f"headers={len(native_mem)}")

# Maintained core code and headers must never be silently omitted from the
# function-owner register. Do not confuse an indexed path with a HOST proof.
maintained_core_paths = [path for path in physical if path.startswith("eden-core/")]
assert len(maintained_core_paths) == 167, ("maintained core source set changed", len(maintained_core_paths))
assert all(path in graph for path in maintained_core_paths), (
    "uncatalogued maintained core source paths",
    [path for path in maintained_core_paths if path not in graph],
)
print("ENCORE_MAINTAINED_CORE_OWNER_PASS", f"files={len(maintained_core_paths)}")

# A maintained native draw manager must replace (not join) the pinned
# engine source. Tracking its file and V108 graph row alone is insufficient
# if CMake silently compiles the old function body instead.
draw_owner = "eden-core/src/video_core/engines/draw_manager.cpp"
draw_sel = native_cmake.split("set(EDEN_MAINTAINED_DRAW_MANAGER", 1)
assert len(draw_sel) == 2, "native selected draw owner missing"
draw_block = draw_sel[1].split("# A guest span must be rejected BEFORE", 1)[0]
assert 'list(REMOVE_ITEM video_sources engines/draw_manager.cpp)' in draw_block
assert 'list(APPEND video_sources "${EDEN_MAINTAINED_DRAW_MANAGER}")' in draw_block
assert '"${PORT_ROOT}/vendor/encore-active/"' not in draw_block
assert '"${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/engines/draw_manager.cpp"' in draw_block
assert draw_owner in graph and graph[draw_owner] == ["V108"]
assert (active / draw_owner).is_file()
print("ENCORE_INDEXED_DRAW_OWNER_PASS", "source=maintained", "single_CMake_target=video_core")

# GPU variants and the coordinated HLE header overlays are not optional
# catalogue blind spots, even if selected only by a native build flag.
for family, size in (("eden-gpu/", 4), ("eden-threading/", 12)):
    members = [path for path in physical if path.startswith(family)]
    assert len(members) == size, ("maintained family footprint changed", family, len(members))
    assert all(path in graph for path in members), (
        "uncatalogued maintained family file", family,
        [path for path in members if path not in graph],
    )
print("ENCORE_GPU_THREADING_OWNER_PASS", "gpu=4", "threading=12")

# The surface lifecycle and bounded local-memory shader are already
# maintained sources; require their REAL source selection, not a second copy.
shader_rel = "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/load_store_local_shared.cpp"
surface_rel = "eden-surface-lifecycle/src/core/hle/service/nvnflinger/surface_flinger.cpp"
composer_rel = "eden-surface-lifecycle/src/core/hle/service/nvnflinger/hardware_composer.cpp"
for rel in (shader_rel, surface_rel, composer_rel):
    assert rel in graph and (active / rel).is_file(), ("missing active owner", rel)
shader_recipe = (root / "headless/CMakeLists.txt").read_text()
assert 'list(APPEND eden_shader_sources "${EDEN_MAINTAINED_SHADER_LOCAL}")' in shader_recipe
assert 'set_property(TARGET shader_recompiler PROPERTY SOURCES "${eden_shader_sources}")' in shader_recipe
surface_installer = (root / "tools/install-vendored-surface-lifecycle.py").read_text()
surface_prepare = (root / "tools/prepare-build.sh").read_text()
assert 'ORIGINAL_GIT_BLOB = "a6136c111d96d2660c28b27c6881e3b671e7eed8"' in surface_installer
assert 'WaitForComposite();' in surface_installer and 'm_composer.RemoveLayerLocked(' in surface_installer
assert 'tools/install-vendored-surface-lifecycle.py "$eden"' in surface_prepare
# Installer verifies BOTH pinned originals and rejects unknown staged
# translations before replacing either one. This avoids mixing mismatched
# SurfaceFlinger/HardwareComposer lifetimes in a single native app.
assert 'COMPOSER_ORIGINAL_GIT_BLOB = "5decb791e1bb1ab2420f386e3fdbdd2b8628a324"' in surface_installer
assert 'if existing not in (original, maintained)' in surface_installer
assert 'check_composer()' in surface_installer
assert 'for rel, source, original, maintained, previous, label in sources:' in surface_installer
assert 'COMPOSER_PATH, COMPOSER_ACTIVE' in surface_installer
print("ENCORE_SHADER_SURFACE_SOURCE_OWNER_PASS sources=3")

# Core native Vulkan device, query and presentation implementation units
# are versioned sources selected into the disposable build tree by the Vulkan
# recipe. Exact source ownership is not a successful native GPU execution.
native_vk_sources = (
    "vulkan_device.cpp", "vulkan_memory_allocator.cpp", "vulkan_query_cache.cpp",
    "vulkan_wrapper.cpp",
)
for unit in native_vk_sources:
    rel = "eden-vulkan/" + unit
    assert rel in graph and (active / rel).is_file(), ("uncatalogued Vulkan unit", rel)
    assert '"${PORT_BUILD_DIR}/' + unit + '"' in vulkan_recipe, ("source selection lost", unit)
# The blit unit is a reviewed vendor reference but the ACTUAL PS5-native
# CMake selects the R08 adapter, not the vendor copy. Do not falsely claim
# the vendor .cpp is compiled: verify the explicit build selection and
# the adapter's real source before counting this presentation owner.
blit_ref = "eden-vulkan/vulkan_blit_screen.cpp"
assert blit_ref in graph and (active / blit_ref).is_file()
assert '"${EDEN_PORT_DIR}/vulkan_blit_screen_r08.cpp"' in vulkan_recipe
assert (root / "headless/vulkan_blit_screen_r08.cpp").is_file()
assert '"${PORT_BUILD_DIR}/vulkan_blit_screen.cpp"' not in vulkan_recipe
# The window-adaptation path likewise selects the R08 native adapter, not
# its reviewed but unused vendor reference. Verify both CMake and the real
# maintained adapter file, preserving its catalog/audit membership.
window_ref = "eden-vulkan/vulkan_window_adapt_pass.cpp"
assert window_ref in graph and (active / window_ref).is_file()
assert '"${EDEN_PORT_DIR}/vulkan_window_adapt_r08.cpp"' in vulkan_recipe
assert (root / "headless/vulkan_window_adapt_r08.cpp").is_file()
assert '"${PORT_BUILD_DIR}/vulkan_window_adapt_pass.cpp"' not in vulkan_recipe
print("ENCORE_VULKAN_DEVICE_PRESENT_OWNER_PASS",
      f"maintained_selected={len(native_vk_sources)}",
      "ps5_blit_adapter=1", "ps5_window_adapter=1",
      "vendor_reference_units_not_selected=2")

# Vulkan headers are shipped as an ABI-consistent set with the selected
# maintained translation units; do not let include-root owners disappear.
assert 'file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")' in vulkan_recipe
assert 'target_include_directories(video_core BEFORE PUBLIC "${PORT_BUILD_DIR}/include")' in vulkan_recipe
abi_headers = ("vk_scheduler.h", "vk_present_manager.h", "vk_descriptor_buffer.h",
               "vk_blit_screen.h", "vk_buffer_cache.h", "renderer_vulkan.h")
for header in abi_headers:
    rel = "eden-vulkan/include/video_core/renderer_vulkan/" + header
    assert (active/rel).is_file() and rel in graph, ("missing selected Vulkan ABI owner", rel)
print("ENCORE_VULKAN_SHARED_ABI_OWNER_PASS", f"headers={len(abi_headers)}")

# Summary prose is itself an audit contract, not a manually stale count.
linked_count = sum(path in graph for path in physical)
assert f"**{len(physical)} fichiers** de code" in document
source_truth = (root / "docs/EDEN_OVERRIDE_SOURCE_OF_TRUTH.md").read_text()
assert f"**{len(physical)} sources et en-têtes suivis**" in source_truth, (
    "stale single-source summary", len(physical)
)
assert f"**{linked_count} fichiers** possèdent" in document
if linked_count == len(physical):
    assert "**0 fichier** reste sans correspondance" in document
else:
    assert f"**{len(physical)-linked_count} fichiers** n'ont" in document
root_cmake = (root / "headless/CMakeLists.txt").read_text()
root_generator_count = len(re.findall(r'write_derived\(\s*"', root_cmake))
if root_generator_count == 1:
    assert "L'inventaire du générateur CMake principal G23" in document
else:
    assert f"L'inventaire des {root_generator_count} générateurs CMake" in document
# The CMake debt summary must count actual call sites, not an obsolete snapshot.
override_inventory = (root / "docs/EDEN_OVERRIDE_MIGRATION_INVENTORY.md").read_text()
root_call = "appel générateur" if root_generator_count == 1 else "appels générateurs"
assert f"**{root_generator_count} {root_call}**" in override_inventory
# Source comments describing retired rewrites must not be counted as CMake calls.
active_reads = len(re.findall(r'^\s*file\(READ', root_cmake, re.M))
active_replacements = len(re.findall(r'^\s*string\(REPLACE', root_cmake, re.M))
assert f"**{active_reads} lectures `file(READ`**" in override_inventory
assert f"**{active_replacements} remplacements" in override_inventory

# Separate headless C/C++ footprint: active Encore sources are not the only
# potential implementation units. Track ALL paths without inventing
# native compile coverage or marking launcher work as validated.
headless_doc = (root / "docs/EDEN_HEADLESS_SOURCE_CATALOG.md").read_text()
headless_start = "<!-- HEADLESS_SOURCE_CATALOG_START -->"
headless_end = "<!-- HEADLESS_SOURCE_CATALOG_END -->"
assert headless_doc.count(headless_start) == headless_doc.count(headless_end) == 1
headless_exts = {".c", ".cc", ".cpp", ".h", ".hpp", ".inc", ".cl"}
# P5: the first compiler-error repairs add one include-only native header
# after the immutable 193-entry historical headless source catalogue.
# Enforce its exact existence/selection separately; do not retroactively
# rewrite the F07 table or classify it as an audited optimization.
post_f07_p5_headless_owners = {"headless/ns2_astc_texture_cache_scope_bridge.h"}
assert all((root / p).is_file() for p in post_f07_p5_headless_owners)
assert not post_f07_p5_headless_owners & (
    post_f07_feature_headless_owners | post_f07_r09_headless_owners)
assert 'ns2_astc_texture_cache_scope_bridge.h' in (
    root / "headless/vulkan.cmake").read_text()
print("ENCORE_POST_F07_P5_NATIVE_HEADER_SOURCE_PASS", "owners=1 historical_headless=193")
# R457 console diagnostic owners were created after the immutable F07
# 193-source snapshot. The ABI probe is selected in the native PS5 CMake
# graph; the NS2 planner is research-only and must NOT be in HostMemory.
post_f07_r457_owners = {
    "headless/ps5_cpu6_abi_probe.cpp",
    "headless/ps5_ns2_guest_backing_plan.h",
}
assert all((root / p).is_file() for p in post_f07_r457_owners)
assert not post_f07_r457_owners & (
    post_f07_feature_headless_owners | post_f07_r09_headless_owners |
    post_f07_p5_headless_owners)
assert 'ps5_cpu6_abi_probe.cpp' in native_cmake
assert 'ps5_ns2_guest_backing_plan.h' not in (root / "src/host_memory.cpp").read_text()
print("ENCORE_POST_F07_R457_RESEARCH_SOURCE_PASS", "owners=2 historical_headless=193")
# The R23 AM frontend prototype is a post-F07 native overlay, not an
# additional item in the frozen 193-file historical headless catalogue.
post_f07_ns1_audio_headless_owners = {"headless/audio_in_silence.h"}
assert all((root / p).is_file() for p in post_f07_ns1_audio_headless_owners)
assert "SilentAudioInputStream" in (root / "headless/audio.cpp").read_text()
assert "audio_in_silence.h" in native_cmake
print("ENCORE_C00_POST_F07_HEADLESS_OWNER_PASS new=1 historical=193")

post_f07_ns1_am_headless_owners = {"headless/r23_am_frontend_applets_ps5.cpp"}
assert all((root / p).is_file() for p in post_f07_ns1_am_headless_owners)
assert "r23_am_frontend_applets_ps5.cpp" in native_cmake
assert not post_f07_ns1_am_headless_owners & (
    post_f07_feature_headless_owners | post_f07_r09_headless_owners |
    post_f07_p5_headless_owners | post_f07_r457_owners)
print("ENCORE_NS1_AM_POST_F07_HEADLESS_PASS", "new=1 historical=193")
headless_actual = sorted(
    p.relative_to(root).as_posix()
    for p in (root / "headless").rglob("*")
    if p.is_file() and p.suffix in headless_exts
    and p.relative_to(root).as_posix() not in (
        post_f07_feature_headless_owners | post_f07_r09_headless_owners |
        post_f07_p5_headless_owners | post_f07_r457_owners | post_f07_ns1_am_headless_owners | post_f07_ns1_audio_headless_owners)
)
print("ENCORE_POST_F07_R09_HEADLESS_OWNER_PASS", "r09=9",
      "historical_headless_catalog_preserved=193")
headless_rows = []
for entry in headless_doc.split(headless_start, 1)[1].split(headless_end, 1)[0].splitlines():
    if not entry.startswith("| `headless/"):
        continue
    cells = [cell.strip() for cell in entry.strip().strip("|").split("|")]
    assert len(cells) == 4 and cells[0].startswith("`headless/"), ("malformed headless row", entry)
    headless_rows.append((cells[0].strip("`"), cells[1], cells[2], cells[3]))
assert [r[0] for r in headless_rows] == headless_actual, (
    "headless source path catalog drift", len(headless_rows), len(headless_actual))
# The vendor-active graph above intentionally stores vendor-relative keys.
# Headless paths use repository-relative keys and need an independent map.
headless_graph = {}
for entry in audit.splitlines():
    if not entry.startswith("| "):
        continue
    cells = [cell.strip() for cell in entry.strip().strip("|").split("|")]
    if len(cells) == 9 and re.fullmatch("[A-Z][0-9]{2,3}", cells[0]) and cells[3].startswith("headless/"):
        # U23 was renamed without removing its owner; its CPU6 JIT fallback
        # changed after the frozen F07 snapshot and is retested separately.
        current_path = (
            'headless/jit_memory_policy.h'
            if cells[3] == 'headless/experimental_performance.h' else cells[3]
        )
        if current_path == 'headless/jit_memory_policy.h':
            assert cells[0] == 'U23'
            assert (root/'tools/ns2/check_unified_jit_cpu6_baseline_host.py').is_file()
        headless_graph.setdefault(current_path, []).append(cells[0])
# These three headless runtime translation units are application-owned,
# not third-party dependency overrides. They must remain indexed and selected
# by their actual CMake targets; moving them into vendor would be misleading.
runtime_headless = {
    "headless/metadata_bridge.cpp":
        'add_library(eden-metadata STATIC "${EDEN_PORT_DIR}/metadata_bridge.cpp")',
    "headless/stop_limit.cpp":
        '"${EDEN_PORT_DIR}/crash_report.cpp" "${EDEN_PORT_DIR}/stop_limit.cpp"',
    "headless/zbic_compression.cpp":
        'target_sources(common PRIVATE "${EDEN_PORT_DIR}/zbic_compression.cpp")',
}
for path, selection in runtime_headless.items():
    assert path in headless_graph, ("runtime source lacks functional audit entry", path)
    assert selection in native_cmake, ("tracked runtime unit lost compile selection", path)
for path in ("headless/metadata_bridge.h", "headless/stop_limit.h",
             "headless/zbic_compression.h", "headless/graphics.h",
             "headless/gpu_failure.h", "headless/gpu_deferred_write_queue.h"):
    assert path in headless_graph, ("runtime interface lacks graph owner", path)
print("ENCORE_HEADLESS_RUNTIME_OWNERS_PASS",
      f"compiled={len(runtime_headless)}", "headers=6")

headless_linked = sum(p in headless_graph for p in headless_actual)
for p, family, owner, state in headless_rows:
    if p in headless_graph:
        assert owner == ",".join(headless_graph[p]) and state.strip().startswith("Chemin indexé"), (
            "headless graph owner stale", p)
    else:
        assert owner == "—" and state.strip() == "À qualifier", ("headless owner stale", p)
# Separate intentionally unlinked application/UI and test roles from
# vendor-source overrides. Count from actual catalog/graph, not a guessed
# TODO total or a second manually maintained ownership register.
from collections import Counter
unlinked_by_role = Counter(role for path, role, _, _ in headless_rows
                           if path not in headless_graph)
assert sum(unlinked_by_role.values()) == len(headless_actual)-headless_linked
assert set(unlinked_by_role) == {
    "launcher/UI", "harness/test", "outil auxiliaire",
    "données générées"}
assert unlinked_by_role.get("en-tête/fragment", 0) == 0, (
    "new unowned headless header or fragment", unlinked_by_role)
# The launcher/Vulkan frame mailbox is a true shared UI boundary, not a
# vendor override. It lives at headless root because both renderers include it.
assert all(path.startswith("headless/prosperoeden/") or
           path == "headless/launch_handoff.hpp"
           for path, role, _, _ in headless_rows if role == "launcher/UI")
assert all(path in headless_graph for path, role, _, _ in headless_rows
           if role == "runtime/bridge")
for role, count in unlinked_by_role.items():
    assert f"| `{role}` | **{count}** |" in headless_doc, (
        "unlinked headless role summary stale", role, count)
assert f"| **Total non indexé** | **{sum(unlinked_by_role.values())}** |" in headless_doc

assert f"**{len(headless_actual)}** chemins" in headless_doc
assert f"**{headless_linked}** chemins déjà présents" in headless_doc
assert f"**{len(headless_actual)-headless_linked}** chemins sans propriétaire exact" in headless_doc
print("ENCORE_HEADLESS_SOURCE_CATALOG_PASS",
      f"paths={len(headless_actual)}", f"graph_exact={headless_linked}",
      f"unlinked={len(headless_actual)-headless_linked}")

print("ENCORE_ACTIVE_CATALOG_SUMMARY_PASS",
      f"files={len(physical)}", f"covered={linked_count}",
      f"cmake_primary_generators={root_generator_count}")

# Every versioned Vulkan source and ABI header selected through the fork's
# configure-time copy has an exact source ownership record. This guards
# coverage, not GPU forward progress or successful native device tests.
vulkan_family = [p for p in physical if p.startswith("eden-vulkan/")]
assert len(vulkan_family) == 43, ("Vulkan maintained footprint changed", len(vulkan_family))
assert all(p in graph for p in vulkan_family), (
    "Vulkan maintained source lacks owner", [p for p in vulkan_family if p not in graph],
)
assert 'file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")' in vulkan_recipe
print("ENCORE_VULKAN_WHOLE_FAMILY_OWNER_PASS", f"files={len(vulkan_family)}")

# The immutable guest-network shipping header is disabled by a native-only
# include-root override. Guest BSD, DNS and NIFM must all consult this policy.
native_offline = "eden-core/overrides/core/hle/service/sockets/encore_guest_network_policy.h"
shipping_online = "eden-backports/src/core/hle/service/sockets/encore_guest_network_policy.h"
assert native_offline in graph and shipping_online in graph
assert (active / shipping_online).read_text().count(
    "inline constexpr bool kGuestNetworkOffline = false;") == 1
assert (active / native_offline).read_text().count(
    "inline constexpr bool kGuestNetworkOffline = true;") == 1
assert '${EDEN_NATIVE_DIRTY_HEADER_ROOT}/core/hle/service/sockets/encore_guest_network_policy.h' in native_cmake
assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")' in native_cmake
for consumer in ("sockets/bsd.cpp", "sockets/sfdnsres.cpp", "nifm/nifm.cpp"):
    body = (active / "eden-backports/src/core/hle/service" / consumer).read_text()
    assert 'Eden::Encore::kGuestNetworkOffline' in body, ("guest network policy not used", consumer)
print("ENCORE_NATIVE_GUEST_NETWORK_POLICY_PASS consumers=3")

# Native RADV is installed from exactly fourteen versioned inputs,
# including an OpenCL geometry shader that the C/C++ scanner once omitted.
installer_inputs = runpy.run_path(str(root / "tools/install-vendored-radv.py"))["PATHS"]
mesa_inputs = {"ps5-mesa/" + path for path in installer_inputs}
mesa_physical = {path for path in physical_all if path.startswith("ps5-mesa/")}
assert len(mesa_inputs) == 14 and mesa_inputs == mesa_physical
# All legacy inputs retain their exact historic audit rows. The two
# research-only C03 sources are separately pinned, byte-attested and selected;
# do not mint fake historical Rxx audit identifiers for their new files.
assert all(path in graph or path in post_f07_c03_radv_meta_owners for path in mesa_inputs), (
    "missing RADV source owner",
    sorted(path for path in mesa_inputs
           if path not in graph and path not in post_f07_c03_radv_meta_owners))
assert "ps5-mesa/src/amd/vulkan/cl/radv_gs_compute.cl" in mesa_inputs
print("ENCORE_DRIVER_INPUT_COVERAGE_PASS", f"inputs={len(mesa_inputs)}", "opencl=1")

# Patch-hunk owners in the versioned production backports; this checks
# known modified code sites, not the final runtime branch or GPU correctness.
modified_shipping = (
    ("eden-backports/src/core/device_memory_manager.h", ["std::shared_lock registry_lk(process_registry_guard);","AtomicLoadPhysical"]),
    ("eden-backports/src/core/device_memory_manager.inc", ["std::unique_lock lk(mapping_guard);","AtomicStoreReverse"]),
    ("eden-backports/src/core/memory.cpp", ["IsDirectBackingAlias","AddressSpaceContains"]),
    ("eden-backports/src/core/hle/kernel/k_scheduler.cpp", ["m_context_guard.try_lock()"]),
    ("eden-backports/src/core/hle/kernel/k_thread.h", ["std::mutex m_context_guard{};"]),
    ("eden-backports/src/core/hle/service/nvdrv/devices/nvmap.cpp", ["EDEN_NVMAP_REJECT_ZERO_ADDRESS","LockForMapDeviceAddressSpace"]),
    ("eden-backports/src/core/hle/service/nvnflinger/buffer_queue_core.cpp", ["dequeue_epoch.fetch_add","dequeue_epoch.load"]),
    ("eden-backports/src/core/hle/service/nvnflinger/buffer_queue_core.h", ["dequeue_epoch"]),
    ("eden-backports/src/core/hle/service/sockets/sfdnsres.cpp", ["kGuestNetworkOffline"]),
    ("eden-backports/src/video_core/renderer_vulkan/vk_buffer_cache.cpp", ["return scheduler.CurrentTick();"]),
    ("eden-backports/src/video_core/buffer_cache/buffer_cache.h", ["SynchronizeBufferWrites","gpu_modified_ranges"]),
    ("eden-backports/src/video_core/texture_cache/texture_cache.h", ["NULL_IMAGE_VIEW_ID","modification_tick == modification_tick"]),
)
for relative, anchors in modified_shipping:
    assert relative in graph and (active / relative).is_file(), (
        "missing function owner in production backport", relative)
    body = (active / relative).read_text()
    for anchor in anchors:
        assert anchor in body, ("shipping patch hunk moved", relative, anchor)
print("ENCORE_SHIPPING_BACKPORT_HOTPATH_OWNER_PASS", f"paths={len(modified_shipping)}")

# Source-owner proofs for eight additional production cache/fence/compute
# backports: changed marker appears once in shipping and not in pinned Eden.
gpu_shipping_diffs = (
    ("src/video_core/buffer_cache/buffer_cache_base.h", "void SynchronizeBufferWrites(Buffer& buffer);"),
    ("src/video_core/texture_cache/texture_cache_base.h", "std::vector<ImageViewId> last_feedback_view_ids;"),
    ("src/video_core/query_cache/query_cache.h", "!Settings::IsGPUFenceBehaviorBalanced() && !Settings::IsGPUFenceBehaviorAccurate()) && is_fence;"),
    ("src/video_core/fence_manager.h", "Settings::IsGPUFenceBehaviorBalanced() || Settings::IsGPUFenceBehaviorAccurate();"),
    ("src/video_core/control/channel_state_cache.h", "P* channel_state = nullptr;"),
    ("src/video_core/engines/kepler_compute.cpp", "if (data.was_dirty || source_dirty) {"),
    ("src/video_core/engines/kepler_compute.h", "bool upload_dirty{};"),
    ("src/video_core/dma_pusher.cpp", "const bool kepler_payload = engine == Engines::EngineTypes::KeplerCompute"),
)
for rel, marker in gpu_shipping_diffs:
    shipping = "eden-backports/" + rel
    assert shipping in graph, ("missing backport graph row", shipping)
    patched = (active / shipping).read_text()
    pinned = (root / "vendor/sources/eden" / rel).read_text()
    assert patched.count(marker) == 1 and marker not in pinned, (
        "production GPU backport drift", shipping, marker)
print("ENCORE_GPU_SHIPPING_PATCH_OWNER_PASS", f"sources={len(gpu_shipping_diffs)}")

# Indexed shipping sources have stable code anchors from their real
# patches, not simply a filename in the compiled-source inventory.
shipping_followups = (
    ("eden-backports/src/audio_core/audio_render_manager.cpp", ["ASSERT(session_count <= session_ids.size());","s32 Manager::GetSessionId()"]),
    ("eden-backports/src/core/hle/service/sockets/bsd.cpp", ["void BSD_USA::Ioctl(","Eden::Encore::kGuestNetworkOffline","write_buffer.size() < guest_addrin.len"]),
    ("eden-backports/src/core/hle/service/sockets/bsd.h", ["void Ioctl(HLERequestContext& ctx);"]),
    ("eden-backports/src/core/hle/service/nifm/nifm.cpp", ["Eden::Encore::kGuestNetworkOffline","void IGeneralService::SetWirelessCommunicationEnabled(","void IGeneralService::IsAnyInternetRequestAccepted("]),
    ("eden-backports/src/hid_core/resources/npad/npad.cpp", ["fullkey_lifo.ReadCurrentEntry().state.sampling_number","eden_watchdog_updates","EDEN_HID_NPAD"]),
    ("eden-backports/src/video_core/texture_cache/util.cpp", ["config.format == static_cast<Tegra::Texture::TextureFormat>(0)","if (config.is_sparse == 0)"]),
)
for relative, anchors in shipping_followups:
    assert relative in graph and (active / relative).is_file(), ("unindexed shipping source", relative)
    body = (active / relative).read_text()
    for anchor in anchors:
        assert anchor in body, ("shipping implementation changed", relative, anchor)
print("ENCORE_SHIPPING_NET_AUDIO_HID_TEXTURE_OWNER_PASS", f"files={len(shipping_followups)}")

# Modified shipping firmware, filesystem, applet and display contracts.
# Passing here asserts exact owner/hunk presence, not device runtime behavior.
shipping_hle_followups = (
    ("eden-backports/src/core/file_sys/system_archive/system_version.cpp", ["VirtualDir SystemVersion()","HLE::ApiVersion::VERSION_DIGEST[0]"]),
    ("eden-backports/src/core/hle/service/filesystem/filesystem.cpp", ["RegisterNamedService(\"fsp-srv\", std::move(FileSystemProxyFactory), 61);"]),
    ("eden-backports/src/core/hle/service/filesystem/fsp/fsp_srv.cpp", ["Result FSP_SRV::OpenDataFileSystemByCurrentProcess(","FileSys::ExtractRomFS(romfs)"]),
    ("eden-backports/src/core/hle/service/am/service/application_creator.cpp", ["IApplicationCreator::CreateSystemApplication(","HLE::ApiVersion::HOS_VERSION_MAJOR"]),
    ("eden-backports/src/core/hle/service/ns/application_manager_interface.cpp", ["IApplicationManagerInterface::Unknown936(","IApplicationManagerInterface::Unknown4042(","IApplicationManagerInterface::Unknown4105("]),
    ("eden-backports/src/core/hle/service/set/settings.cpp", ["RegisterNamedService(\"set:sys\", std::make_shared<ISystemSettingsServer>(system), 60);"]),
    ("eden-backports/src/core/frontend/applets/controller.cpp", ["DefaultControllerApplet::ReconfigureControllers(","keep_connected","max_supported_players"]),
    ("eden-backports/src/core/hle/service/am/display_layer_manager.cpp", ["DisplayLayerManager::CreateManagedDisplayLayer(","SetLayerStackMask(","SetLayerZIndex(Overlay"]),
)
for rel, anchors in shipping_hle_followups:
    assert rel in graph and (active / rel).is_file(), ("uncatalogued HLE source", rel)
    text = (active / rel).read_text()
    for anchor in anchors:
        assert anchor in text, ("firmware/HLE backport source drift", rel, anchor)
print("ENCORE_SHIPPING_FIRMWARE_HLE_OWNER_PASS", f"files={len(shipping_hle_followups)}")


# Strict ownership of shipping firmware, account, kernel, filesystem and
# Vulkan hunks. Pinned comparisons show a real shipped delta, not a new
# override to copy into CMake; this is not native hardware validation.
shipping_structural_diffs = (
    ("src/core/hle/api_version.h", "constexpr u8 HOS_VERSION_MAJOR = 23;"),
    ("src/core/hle/kernel/k_slab_heap.h", "std::mutex m_lock;"),
    ("src/core/hle/kernel/svc/svc_info.cpp", "case InfoType::Unknown37:"),
    ("src/core/hle/kernel/svc_types.h", "TransferMemoryHint = 34,"),
    ("src/core/hle/service/acc/acc.cpp", "void Module::Interface::LoadOpenContext(HLERequestContext& ctx) {"),
    ("src/core/hle/service/acc/acc.h", "void LoadOpenContext(HLERequestContext& ctx);"),
    ("src/core/hle/service/am/lifecycle_manager.h", "void RequestFocusStateChangedNotification(Kernel::KernelCore& kernel) {"),
    ("src/core/hle/service/filesystem/fsp/fsp_srv.h", "Result OpenDataFileSystemByCurrentProcess(OutInterface<IFileSystem> out_interface);"),
    ("src/core/hle/service/ns/application_manager_interface.h", "Result Unknown4042(OutInterface<IAsyncResult> out_interface,"),
    ("src/video_core/renderer_vulkan/vk_buffer_cache.h", "bool IsFree(u64 tick);"),
)
for rel, marker in shipping_structural_diffs:
    shipping_path = active / "eden-backports" / rel
    pinned_path = root / "vendor/sources/eden" / rel
    assert ("eden-backports/" + rel) in graph
    assert shipping_path.is_file() and pinned_path.is_file(), ("missing pinned comparison", rel)
    assert shipping_path.read_text().count(marker) == 1, ("shipping hunk drift", rel, marker)
    assert marker not in pinned_path.read_text(), ("hunk not distinct from pinned source", rel, marker)
print("ENCORE_SHIPPING_STRUCTURAL_OWNER_PASS", f"paths={len(shipping_structural_diffs)}")

shipping_new_ns = (
    ("src/core/hle/service/ns/i_async_result.cpp", "Result IAsyncResult::Cancel() {"),
    ("src/core/hle/service/ns/i_async_result.h", "class IAsyncResult final : public ServiceFramework<IAsyncResult> {"),
)
for rel, marker in shipping_new_ns:
    assert ("eden-backports/" + rel) in graph
    assert (active / "eden-backports" / rel).read_text().count(marker) == 1
    assert not (root / "vendor/sources/eden" / rel).exists(), ("new NS source exists upstream", rel)
print("ENCORE_SHIPPING_NEW_NS_OWNER_PASS", f"paths={len(shipping_new_ns)}")


# Previously unowned shipping backports: confirm a real delta against the
# pinned core, not merely an exact filename in a catalogue. Runtime behavior
# and selected build targets still require independent validation.
shipping_remaining_diffs = (
    ("src/common/logging.cpp", "extern \"C\" bool eden_native_detailed_logging() noexcept;", True),
    ("src/common/net/net.cpp", "const std::size_t timeout_seconds = url == \"https://api.nlib.cc\" ? 3 : 5;", True),
    ("src/common/settings.cpp", "bool IsGPUFenceBehaviorStrict() {", False),
    ("src/common/settings.h", "GpuFenceBehavior::Accurate,", True),
    ("src/common/settings_enums.h", "ENUM(GpuFenceBehavior, Default, Immediate, Balanced, Accurate);", True),
    ("src/core/hle/service/audio/audio.cpp", "server_manager->RegisterNamedService(\"aud:a\", std::make_shared<IAudioSystemManagerForApplet>(system), 30);", True),
    ("src/video_core/engines/sw_blitter/blitter.cpp", "(static_cast<size_t>(in_y) * src_width + static_cast<size_t>(in_x)) *", True),
    ("src/core/hle/service/am/frontend/applets.cpp", "std::erase(caller_applet->child_applets, applet_);", True),
    ("src/core/hle/service/am/service/library_applet_accessor.cpp", "else if (is_front_app) caller_applet->lifecycle_manager.RequestFocusStateChangedNotification(system.Kernel());", True),
    ("src/core/hle/service/am/service/library_applet_creator.cpp", "auto process = CreateProcess(system, program_id, 1, HLE::ApiVersion::HOS_VERSION_MAJOR);", True),
    ("src/core/hle/service/am/service/self_controller.cpp", "Result ISelfController::Unknown240(u32 in_val) {", True),
    ("src/core/hle/service/am/service/self_controller.h", "Result Unknown240(u32 in_val);", True),
    ("src/core/hle/service/bcat/bcat.cpp", "server_manager->RegisterNamedService(\"bcat:a\", std::make_shared<IServiceCreator>(system, \"bcat:a\"), 32);", True),
    ("src/core/hle/service/bpc/bpc.cpp", "server_manager->RegisterNamedService(\"bpc:ams\", std::make_shared<BPC_AMS>(system), 4);", True),
    ("src/core/hle/service/glue/arp.cpp", "LOG_ERROR(Service_ARP, \"Attempted to issue registrar, but registrar is already issued!\");", True),
    ("src/core/hle/service/glue/glue.cpp", "server_manager->RegisterNamedService(\"arp:r\", std::make_shared<ARP_R>(system, system.GetARPManager()), 16);", True),
    ("src/core/hle/service/grc/grc.cpp", "server_manager->RegisterNamedService(\"grc:c\", std::make_shared<GRC>(system), 4);", True),
    ("src/core/hle/service/hid/hid_system_server.cpp", '{551, &IHidSystemServer::GetRegisteredDevices, "GetRegisteredDevicesForControllerSupport"}', True),
    ("src/core/hle/service/ldr/ldr.cpp", "server_manager->RegisterNamedService(\"ldr:dmnt\", std::make_shared<DebugMonitor>(system), 3);", True),
    ("src/core/hle/service/nfp/nfp.cpp", "{25, &IUser::StartDetection, \"StartDetectionWithFilter\"},", True),
    ("src/core/hle/service/ngc/ngc.cpp", "server_manager->RegisterNamedService(\"ngct:u\", std::make_shared<IService>(system), 4);", True),
    ("src/core/hle/service/ns/ns.cpp", "server_manager->RegisterNamedService(\"ns:am2\", std::make_shared<IServiceGetterInterface>(system, \"ns:am2\"), 5);", True),
    ("src/core/hle/service/ns/read_only_application_control_data_interface.cpp", '{23, D<&IReadOnlyApplicationControlDataInterface::GetApplicationControlData3>, "GetApplicationControlData"}', True),
    ("src/core/hle/service/olsc/transfer_task_list_controller.cpp", "Result ITransferTaskListController::GetTransferTaskProgress() {", True),
    ("src/core/hle/service/olsc/transfer_task_list_controller.h", "Result GetTransferTaskProgress();", True),
    ("src/core/hle/service/pctl/parental_control_service.cpp", "Result IParentalControlService::Unknown1460(u8 in_unk, Out<PlayTimerRemainingTimeDisplayInfo> out_display_info) {", True),
    ("src/core/hle/service/pctl/parental_control_service.h", "Result Unknown1460(u8 in_unk, Out<PlayTimerRemainingTimeDisplayInfo> out_display_info);", True),
    ("src/core/hle/service/pctl/pctl_types.h", "struct PlayTimerRemainingTimeDisplayInfo {", True),
    ("src/core/hle/service/pm/pm.cpp", "server_manager->RegisterNamedService(\"pm:bm\", std::make_shared<BootMode>(system), 4);", True),
    ("src/core/hle/service/ro/ro.cpp", "server_manager->RegisterNamedService(\"ro:1\", std::make_shared<RoInterface>(system, \"ro:1\", ro, NrrKind::JitPlugin), 2);", True),
    ("src/core/hle/service/sm/sm.cpp", "Result ServiceManager::RegisterService(Kernel::KServerPort** out_server_port, std::string name, u32 max_sessions, SessionRequestHandlerFactory handler) {", True),
    ("src/core/hle/service/sockets/sockets.cpp", "server_manager->RegisterNamedService(\"bsd:s\", std::make_shared<BSD_USA>(system, \"bsd:s\", false), 0x7E);", True),
    ("src/core/hle/service/usb/usb.cpp", "server_manager->RegisterNamedService(\"usb:pd\", std::make_shared<IPdManager>(system), 6);", True),
    ("src/core/hle/service/wlan/wlan.cpp", "server_manager->RegisterNamedService(\"wlan:lcl\", std::make_shared<ILocalManager>(system), 10);", True),
)
for relative, marker, positive in shipping_remaining_diffs:
    relative_active = "eden-backports/" + relative
    shipping_path = active / relative_active
    pinned_path = root / "vendor/sources/eden" / relative
    assert relative_active in graph and shipping_path.is_file() and pinned_path.is_file()
    shipping_body, pinned_body = shipping_path.read_text(), pinned_path.read_text()
    if positive:
        assert shipping_body.count(marker) == 1 and marker not in pinned_body, (
            "shipping marker drifted", relative_active, marker)
    else:
        assert marker not in shipping_body and pinned_body.count(marker) == 1, (
            "removed shipping marker drifted", relative_active, marker)
print("ENCORE_SHIPPING_COMPLETE_OWNER_PASS", f"paths={len(shipping_remaining_diffs)}")

assert len(physical) == len(set(physical))
print("ENCORE_ACTIVE_SOURCE_CATALOG_PASS",
      f"files={len(physical)}",
      f"graph_exact={sum(path in graph for path in physical)}",
      f"unlinked={sum(path not in graph for path in physical)}",
      f"shipping_sources={len(shipping_cpp)}",
      f"shipping_build_recipes={len(build_recipes)}")
