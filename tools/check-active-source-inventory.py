#!/usr/bin/env python3
"""Fail if the active C/C++ source catalogue drifts from tracked files.

This verifies file-level coverage and exact graph cross-links only.
It is not a function audit, compiler check or console-test certificate.
"""
from pathlib import Path
import json
import re
import runpy
import subprocess
import hashlib

root = Path(__file__).resolve().parents[1]
active = root / "vendor/encore-active"
# November 23 stabilization is a reviewed exact successor, not a new
# historical F07 baseline. Preserve prior classifications for unchanged owners.
shipping_vendor = subprocess.check_output(
    ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD"], text=True).strip()
stabilization_trees = {
    "9632ac089f8b2d89a6856a42e8fb55206cdba1fa": "51c9a38eba78d69893c48db6f3e48a169ea879e3",
    "b5c6f089a6aecd321d08a40238f3cd502f505b26": "668fb8effa6963be062d780e3bd145a5233d6b7e",
    "dc9f5f95b1f784bb358d6480e53de7247d61d777": "1660883553006cfca7e80465ad5521b4c2ca33b1",
    "a441295022b23834f8531c54d2b0965f84023278": "d53129478299aded8cb8d7432751b43fa74594b9",
    "7c5d5220dd4df4a531418458ab623ef86c41348c": "9ff41b47bfe30a9cef86a5ab7c584c0094f586bf",
    "44540549ee9a65eb8078e271f43ccded0e8e984f": "86d6068c438cc36ffd01513fc178d2590fb010cb",
    "d63d82dfb9c2afbacac4c9dc1491f743fb083d52": "290d8c51e8ab40dd56651d50483abe42e11fa404",
    "d634b381d85dae30492dd6291fc4e6e96143f363": "a51ee73257c13fce70cbaf5d3e26c62010abf2e9",
    "692e9819a7a1f1b818bf3739c72d8e5252cae661": "6743fed9174ee7e3451afbbad230dca6c2e4203c",
    "166e473e120a86a6edcd32a975ffe19b45ffdd42": "3a996079e9de76e0c3d8bd2e595e6c83dadd6ce0",
    "3522d8578fbcd7b46d2a439d5d718dfb570beb7b": "67917388ba3308bacfa3e8da6fff9d83c4efb713",
    "042204fde8e5b74aa5048c6213a8af4450d26fe5": "08ff1d3ef45b03cbe3396079bcb91fa5dce4f160",
    "294442004543aeecc5f3c61cc1b73b2feaff2f92": "50ba35725b57b59cae76a67c7c1d4ba6ad894e2f",
    "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb": "a21aa2b63cfb9cae4dd9ba386982c3bd57a7ef1f",
    "7e137d362f9679125726ef4876355a09d788795e": "6861e052a9824450c7eeaa91b53334c153ca9865",
    "973d45ae0da5d9612d30900e39118d67d039b31a": "1d991da378f711312faf34125f1d4cfe1378bcaa",
    "6b8fd06606f12be187f73e8809e56a49864794f9": "6ecf485d48b3c29c5e058de99a09c5c495cd537d",
    "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc": "57a6ef072ad018954d493cb9064b5c722a5af827",
    "38e19d4be0d99bbba35558af2c0620cd9b46f12e": "a27660a134453d2895e23d5c56ac64e6f12d9960",
    "4c51642038c4a3cc04c0f8f0b8267b17aafd4045": "77add4864dbadc2c2246c339b215c3d79b40a549",
    "881f6fb23c818ecfc387d2b134e1cd7328fc5995": "ba3ad593fb37ac3dc62f2c8b6064328c55cabb3b",
    "d8155325107dbbb1f8ef44f75553595fe4c8ec8c": "a6451d095d44e8b9968635320d3bba34d5722fa5",
    "101eae5edb76fefc40b039009eb35bbaaae99386": "8e42496a1f01a94cc6b17f57eee6ebdff2698ff6",
    "3abd88bc1a3c334f53f345998b72e9cf8ae87abf": "b82ce9bb3b543bf85d535bdfdfb6d725fe88be56",
    "cd5ce4dabef1d32e0441d22dccdee358ebf23287": "2a8d99c8a9912041a286c747c7dcebf5a8cc6f89",
    "a8f327c972bd2f84f6e6f9432c96c4a948963073": "747569d1bafefc23fb235e1929bda0f5c0d48de3",
    "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e": "af3fb89c9c6bb96c19bd2e099273019840536267",
}

# The strict native completion ABI adds only these reviewed blocks. Reconstruct
# the immutable predecessor on an audit copy, never on the compiled source.
def strict_completion_predecessor(relative, data):
    current = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
    changes = {
        "eden-vulkan/vulkan_rasterizer.cpp": ("e5baa7f438d8caf11327989087db38ed1ca053a4", "f67815618d25657dcf64a87944b0c0bc5c2d8993", "#ifdef PS5_NATIVE\nbool RasterizerVulkan::SignalNativeSyncPoint(u32 value) {\n    fence_manager.SignalNativeSyncPoint(value);\n    return true;\n}\n#endif\n\n".encode()),
        "eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h": ("8bd6f2a4e489aa608fc4420d2ff5847b7c12e165", "6e0bf7ab2a3a2147f9db0c630070db30d9b35d56", "#ifdef PS5_NATIVE\n    bool SignalNativeSyncPoint(u32 value) override;\n#endif\n".encode()),
        "ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h": ("74587c78870735bb23d2430415f3742b9e7cca68", "33b1b5475e68c8459f9666b1ae1a6e446221cb63", "#ifdef PS5_NATIVE\n    // Native Ampere completion must retire behind a real renderer fence.\n    // Non-Vulkan backends fail closed rather than publishing an early GSV\n    // counter; the production PS5 Vulkan rasterizer overrides this method.\n    virtual bool SignalNativeSyncPoint(u32) {\n        return false;\n    }\n#endif\n\n".encode()),
    }
    if relative not in changes:
        return data, current
    successor, predecessor, addition = changes[relative]
    if current != successor:
        return data, current
    assert data.count(addition) == 1, ("Strict completion ABI drift", relative)
    data = data.replace(addition, b"", 1)
    actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
    assert actual == predecessor, ("Strict completion predecessor drift", relative, actual)
    return data, actual

stabilization_selected = shipping_vendor in stabilization_trees
stabilization_new_headers = set()
if stabilization_selected:
    assert subprocess.check_output(
        ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD^{tree}"],
        text=True).strip() == stabilization_trees[shipping_vendor]
    # Both new headers are shipping Vulkan inputs, not historical F07 files.
    for relative, expected in {
        "eden-vulkan/include/video_core/renderer_vulkan/frame_pacer.h": "c3f6f99dd427fb9fd0acb84bb50ba88dc25d9a89",
        "eden-vulkan/include/video_core/renderer_vulkan/vk_swapchain.h": "c4df1ab813495b8014e0eda5ed4bcd8fb0be855c",
    }.items():
        raw = (active / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, relative
        stabilization_new_headers.add(relative)
if shipping_vendor == "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e":
    for relative, expected in {"eden-core/overrides/buffer-hotpath/common/range_sets.h":"1c90e08bc3c66731aa717e7b17b3249539848016","eden-core/overrides/buffer-hotpath/common/range_sets.inc":"742dc02b71ada75425fec7e126093634a22d2102","eden-core/overrides/buffer-hotpath/video_core/buffer_cache/word_manager.h":"0992d01d0b4e262dd4b4a79633affa8b02529795"}.items():
        raw = (active / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, relative
        stabilization_new_headers.add(relative)
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
assert len(research_paths) == len(set(research_paths)) == 121
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
    "ns2-runtime/process/core/hle/kernel/k_process.cpp",
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
assert 'set(EDEN_NS2_KPROCESS_SOURCE' in kernel_select
assert 'ns2-runtime/process/core/hle/kernel/k_process.cpp' in kernel_select
assert 'list(REMOVE_ITEM eden_ns2_process_sources "hle/kernel/k_process.cpp")' in kernel_select
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

# P1.3: eight shared kernel/address-space owners are release-selected only
# with the reviewed dual-NPDM GPU-access SVC. Keep the frozen 337-file
# source catalogue intact, with a separate verified post-F07 owner list.
shared_ns2_wait64_owners = {
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.cpp",
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.h",
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_process.h",
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_address_space_info.h",
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_page_table_base.h",
    "ns2-runtime/kernel_wait64/core/hle/kernel/k_process_page_table.h",
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

# Production-selected CPU6 scheduler/JIT and reviewed A64 v8.1-v8.5 owners
# live in the vendor submodule, not headless. Preserve the frozen F07
# catalogue; these are separately audited shipping owners, never research.
post_f07_cpu6_ldapr_owners = {
    "ns2-runtime/cpu6/maintained/core/hle/kernel/global_scheduler_context.cpp",
    "ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_32.cpp",
    "ns2-runtime/cpu6/maintained/core/arm/dynarmic/arm_dynarmic_64.cpp",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.h",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/decoder/a64.inc",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/impl.h",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/load_store_exclusive.cpp",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/a64_branch.cpp",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/load_store_atomic.cpp",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/memory_tagging.cpp",
    "ns2-runtime/ldapr/maintained/dynarmic/frontend/A64/translate/impl/pointer_authentication.cpp",
}
assert post_f07_cpu6_ldapr_owners <= set(physical_all), (
    "Missing vendor-maintained CPU6/A64-v8.1-v8.5 owners",
    sorted(post_f07_cpu6_ldapr_owners - set(physical_all)))
assert not post_f07_cpu6_ldapr_owners.intersection(research_paths), (
    "Shipping CPU6/A64-v8.1-v8.5 owners misclassified as research")
assert 'vendor/encore-active/ns2-runtime/cpu6/maintained/core' in (
    root/'headless/ns2_cpu6_source_bridge.cmake').read_text()
assert 'vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64' in (
    root/'headless/shared_a64_ldapr.cmake').read_text()
print("ENCORE_VENDOR_MAINTAINED_CPU6_A64_V81_V85_PASS owners=11")

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
# Vendor #156 adds a reviewed successor to the R437 native header. Verify
# its raw blob and reverse only the three exact added declaration blocks
# before applying the original R437 byte-for-byte proof.
def checked_guest_cache_lock_vendor(pin):
    if pin not in {"17253dc91e9fe1eb2d9980f261f59d227bfcd1a1", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd"}:
        return pin
    if pin in {"95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd"}:
        reviewed_tree = subprocess.check_output(
            ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
        assert reviewed_tree == {
            "95343060f948601930f2e62b919da0789f0830bb": "efa6548c57f7823d4e8b2c975944c6846b765ff3",
            "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af": "64179fcce4962f9b2b7c738504a6fa0e00b2b292",
            "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c": "3f7f1523cef730ad153bf658fbb3567222d6e956",
            "150a3a79ca103061f73a9a50ca8f463a3b4712f3": "39fb9a3efe65f67115dfcdebe39a55334a702f2d",
            "fcd62408fdbc33af01a4caebc8fd44c8500b628f": "8447712e2cecf661910fd1a32613f0b844ceaeb0",
            "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb": "067c72d30a71a79faefd1ad14876e2a46f02755c",
            "dbef23055897b1649f83c20cf7a0516e64f3d5cd": "9e28e5b83cf9c0f4086a33d6838904353a8fd541",
        }[pin], ("Vendor source tree drift", pin, reviewed_tree)
    # Only the two exact new C++ function call sites may differ from the
    # reviewed integrated renderer. Runtime C++ is never modified here.
    source=(active/"eden-vulkan/vulkan_rasterizer.cpp").read_text()
    raw=source.encode("utf-8")
    digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    assert digest=="f67815618d25657dcf64a87944b0c0bc5c2d8993"
    begin="VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea("
    end="\nvoid RasterizerVulkan::InvalidateRegion("
    assert source.count(begin)==source.count(end)==1
    i=source.index(begin)
    j=source.index(end,i)
    method=source[i:j]
    for newer,prior in (
        ("::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);",
         "::Eden::Performance::GuestCacheLock texture_wait(texture_cache.mutex, true);"),
        ("::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);",
         "::Eden::Performance::GuestCacheLock buffer_wait(buffer_cache.mutex, true);"),
    ):
        assert method.count(newer)==1 and prior not in method
        method=method.replace(newer,prior,1)
    previous=(source[:i]+method+source[j:]).encode("utf-8")
    old_blob=hashlib.sha1(b"blob "+str(len(previous)).encode()
                          +bytes([0])+previous).hexdigest()
    assert old_blob=="0633e3cf41c615f46791d3943ff40ac22399b047"
    return "4354add020afac574198f63d87167f3022bff9c6"

r437_vendor_pin = subprocess.check_output(
    ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD"], text=True).strip()
# The NS1/NS2 vendor merge extends only the GPU-owned DMA output ABI in
# the R437 BufferCacheBase header. Seal the integrated full blob, reverse
# that declaration on this audit copy, then replay every historical R437 test.
raw = r437_body.encode("utf-8")
merged_r437_blob = hashlib.sha1(
    b"blob " + str(len(raw)).encode() + bytes([0]) + raw
).hexdigest()
if merged_r437_blob == "fd9708571ef61c83c399042a5200c87b2e3784d6":
    actual = merged_r437_blob
    merged_dma = "    /// Optionally report whether the copied source contains GPU-owned buffer bytes.\n    /// gpu_written_dest names the exact destination subranges whose newest bytes stay GPU-owned.\n    bool DMACopy(\n        GPUVAddr src_address, GPUVAddr dest_address, u64 amount, bool* gpu_written = nullptr,\n        boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest = nullptr);\n"
    earlier_dma = "    /// Optionally report whether the copied source contains GPU-owned buffer bytes.\n    /// A caller must not re-upload the destination texture from stale guest memory.\n    bool DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,\n                 bool* gpu_written = nullptr);\n"
    assert r437_body.count(merged_dma) == 1
    r437_body = r437_body.replace(merged_dma, earlier_dma, 1)
    raw = r437_body.encode("utf-8")
    previous = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert previous == "716634290574ed4dfc8fd3be0d0ea0ad582980f8", ("Merged BufferCacheBase predecessor drift", previous)
    print("ENCORE_NS1_NS2_DMA_BUFFER_BASE_EXACT_REVERSE_PASS")

# FC27 P1 added PS5-only shared TickFrame budget and typed CPU-write claims.
# Reverse only these exact source hunks on this audit COPY, retaining the
# historical R437/NS2 source replay and never editing the shipping header.
r437_vendor_pin = checked_guest_cache_lock_vendor(r437_vendor_pin)
fc27_p1_applet_macro_fix = r437_vendor_pin == "b65d8d9673475433f0b6eac72eb304bf23141666"
# Selected BufferCacheBase did not change through later NS2-only vendor
# commits. Reverse the FC27 P1 additions only for the byte-exact active
# successor, then require its historical SHA before replaying the R437 gate.
fc27_p1_vendor = (
    hashlib.sha1(
        b"blob " + str(len(r437_body.encode("utf-8"))).encode() +
        bytes([0]) + r437_body.encode("utf-8")
    ).hexdigest() == "716634290574ed4dfc8fd3be0d0ea0ad582980f8"
)
if fc27_p1_vendor:
    raw = r437_body.encode("utf-8")
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "716634290574ed4dfc8fd3be0d0ea0ad582980f8", actual
    prewarm_tick = ("#ifdef PS5_NATIVE\n"
                    "    // Consume one native GPU-memory sample shared with TextureCache.\n"
                    "    // Other backends retain the original budget query fallback.\n"
                    "    void TickFrame(std::optional<u64> externally_sampled_usage = std::nullopt);\n"
                    "#else\n    void TickFrame();\n#endif")
    old_claim = "    void ClaimCpuWrites(std::span<const std::pair<DAddr, u64>> ranges);"
    new_claim = ("    // Both GPU-collected writes (size_t) and normal guest batches (u64)\n"
                 "    // must be claimed together before any stale GPU page readback begins.\n"
                 "    template <typename RangeSize>\n"
                 "    void ClaimCpuWrites(std::span<const std::pair<DAddr, RangeSize>> ranges);")
    assert r437_body.count(prewarm_tick) == r437_body.count(new_claim) == 1
    assert r437_body.count("#include <optional>\n") == 1
    r437_body = (r437_body.replace("#include <optional>\n", "", 1)
                 .replace(prewarm_tick, "    void TickFrame();", 1)
                 .replace(new_claim, old_claim, 1))
    old = r437_body.encode("utf-8")
    previous = hashlib.sha1(b"blob " + str(len(old)).encode() + bytes([0]) + old).hexdigest()
    assert previous == "7e1e2fb6a1a54571f3094d809e934312fbbd83b6", previous
    r437_vendor_pin = "eadc6e798def18417e50db6a03a291440429d795"
    print("ENCORE_FC27_P1_BUFFER_BASE_EXACT_REVERSE_PASS")

# This revert commit has the same complete vendor Git tree as the
# reviewed pre-rollback pin. Reject any different source tree, including
# newly added or removed files, before reusing its byte-exact source gates.
if r437_vendor_pin == "03b264ee3e5ac7d7bbf89d3a9c51a3aff93a4433":
    actual_tree = subprocess.check_output(
        ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD^{tree}"],
        text=True).strip()
    assert actual_tree == "301f91c2ee0eb4e5d86baba9b1036c57f6d5aa04", ("Vendor revert tree drift", actual_tree)
    r437_vendor_pin = "eadc6e798def18417e50db6a03a291440429d795"
# Keep the exact vendor source generation visible after historical R437 reversal.
current_fc27_raster_source = r437_vendor_pin == "eadc6e798def18417e50db6a03a291440429d795"
r437_vendor_pin = "ab417b59c5f7f4613ff27386be05c0644d0ed776" if r437_vendor_pin in {
    "ce25655b08751aa0c2f9efb10ff05fd8fcbf7a93", "7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285"
} else r437_vendor_pin
# Current BufferCacheBase adds two reviewed runtime changes after the
# 32-slot successor: GPU-owned DMA reporting and absolute bit iteration.
# Reverse only in the audit copy, with exact source seals at both ends.
if r437_vendor_pin in {
    "917ccdc1cf772b9312b19888eea181b8e114334b",
    "0c1bd95c896f6ddc7870a245ffca51b2ac7e2932",
    "eadc6e798def18417e50db6a03a291440429d795",
}:
    raw = r437_body.encode("utf-8")
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "7e1e2fb6a1a54571f3094d809e934312fbbd83b6", actual
    new_dma = """    /// Optionally report whether the copied source contains GPU-owned buffer bytes.
    /// A caller must not re-upload the destination texture from stale guest memory.
    bool DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,
                 bool* gpu_written = nullptr);
"""
    old_dma = "    bool DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount);\n"
    new_bits = """    static void ForEachEnabledBit(u32 enabled_mask, Func&& func) {
        // Iterate occupied binding slots directly; preserve the original
        // ascending indices without shifting a second time per enabled slot.
        while (enabled_mask != 0) {
            const u32 index = static_cast<u32>(std::countr_zero(enabled_mask));
            func(index);
            enabled_mask &= enabled_mask - 1;
        }
    }"""
    old_bits = """    static void ForEachEnabledBit(u32 enabled_mask, Func&& func) {
        for (u32 index = 0; enabled_mask != 0; ++index, enabled_mask >>= 1) {
            const int disabled_bits = std::countr_zero(enabled_mask);
            index += disabled_bits;
            enabled_mask >>= disabled_bits;
            func(index);
        }
    }"""
    assert r437_body.count(new_dma) == r437_body.count(new_bits) == 1
    r437_body = r437_body.replace(new_dma, old_dma, 1).replace(new_bits, old_bits, 1)
    raw = r437_body.encode("utf-8")
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "63ef9b07b37bdc4bc9588dd77639358010e545dc", actual
    r437_vendor_pin = "ab417b59c5f7f4613ff27386be05c0644d0ed776"
    print("ENCORE_R437_DMA_AND_MASK_EXACT_REVERSE_PASS")

fc27_deferred_selected = r437_vendor_pin in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200", "67759611edc13414c112ea9d2b6664d54827a200"}
fc27_deferred_owner = "eden-core/overrides/core/deferred_cached_updates.h"
fc27_deferred_present = {fc27_deferred_owner} & set(physical_all)
if fc27_deferred_selected:
    assert fc27_deferred_present == {fc27_deferred_owner}
    for relative, expected_blob in (
        (fc27_deferred_owner, "33262f511777cdd1b4a74ac0cd6dc39caa12c9d0"),
        ("eden-core/overrides/core/device_memory_manager.inc", "852a0272696c7ce182bc05aee92bc7cbb195446b"),
        ("eden-vulkan/vulkan_rasterizer.cpp", "38d5630570675088a0620ef533112bb314a40ae8"),
    ):
        raw = (active / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected_blob, ("FC27 new vendor owner drift", relative, actual)
    print("FC27_DEFERRED_HEADER_POST_F07_SOURCE_PASS exact=3")
else:
    assert not fc27_deferred_present
# Reuse the historic R437 invariants ONLY after exact new-source receipts.
if fc27_deferred_selected:
    r437_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
# Lichii 15dd980 / vendor 372a83d9 changes only the selected shared
# storage-buffer capacity in this class header. Seal that exact successor, then
# reverse only this reviewed hunk before replaying the historical R437 oracle.
if r437_vendor_pin in {"372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    raw = r437_body.encode("utf-8")
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "63ef9b07b37bdc4bc9588dd77639358010e545dc", ("Shared 32-slot BufferCacheBase drift", actual)
    storage32 = """constexpr u32 NUM_COMPUTE_UNIFORM_BUFFERS = 8;
// Lichii 15dd980: native Switch 2 compute shaders (including Bananza) bind
// slots 16/17. This maintained header is selected uniformly for the shared
// PS5 BufferCache, so widen the single ABI instead of using the stale NS2-only
// header with a different class layout.
constexpr u32 NUM_STORAGE_BUFFERS = 32;
constexpr u32 NUM_TEXTURE_BUFFERS = 32;
constexpr u32 NUM_STAGES = 5;

static_assert(NUM_GRAPHICS_UNIFORM_BUFFERS <= 32, "fast bitmask must fit u32");
static_assert(NUM_STORAGE_BUFFERS <= 32, "storage-buffer bitmasks must fit u32");"""
    storage16 = """constexpr u32 NUM_COMPUTE_UNIFORM_BUFFERS = 8;
constexpr u32 NUM_STORAGE_BUFFERS = 16;
constexpr u32 NUM_TEXTURE_BUFFERS = 32;
constexpr u32 NUM_STAGES = 5;

static_assert(NUM_GRAPHICS_UNIFORM_BUFFERS <= 32, "fast bitmask must fit u32");"""
    assert r437_body.count(storage32) == 1
    r437_body = r437_body.replace(storage32, storage16, 1)
    r437_vendor_pin = "0d75406e36a3676b45184670093f0ecf652aab2f"
    print("NS2_SHARED_STORAGE32_EXACT_REVERSE_PASS selected=32 historical=16")

# Reconstructed reviewed successor: same R437 GPU owners as d024,
# plus preserved RomFS index-0 source and full synchronous page protection.
if r437_vendor_pin in {"c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    for relative, blob in {
        "eden-core/overrides/core/device_memory_manager.inc":
            "daf493ce6e863397ec44bfae467c4f7533570477",
        "eden-vulkan/vulkan_rasterizer.cpp":
            ("71d097b9a83028dfad9370792c905bb3bfccfd5a" if fc27_p1_vendor else
             "f23ad861761d53b59b8c83ae6003c089ae688060"
             if current_fc27_raster_source
             else "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35"),
        "eden-core/src/core/file_sys/romfs_factory.cpp":
            "4775cf98c3bfbc587402928bad424dcb471047a0",
    }.items():
        source=(active/relative).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(source)).encode()+bytes([0])+source).hexdigest()
        source, actual = strict_completion_predecessor(relative, source)
        if (relative == "eden-vulkan/vulkan_rasterizer.cpp" and
            actual in {"0633e3cf41c615f46791d3943ff40ac22399b047", "f67815618d25657dcf64a87944b0c0bc5c2d8993"} and
            blob == "71d097b9a83028dfad9370792c905bb3bfccfd5a"):
            # The selected vendor's exact 16 reviewed NS1/NS2 GPU deltas
            # are reconstructed against the original FC27 rasterizer blob.
            # Borrow its strict source verifier; neither test alters C++.
            import sys
            sys.path.insert(0, str(root / "vendor" / "tests"))
            from native_msaa_handle_receipt import restore_integrated_rasterizer
            historical = restore_integrated_rasterizer(source.decode("utf-8")).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            print("NS1_NS2_GPU16_EXACT_REVERSE_PASS")
        assert actual==blob, ("FC27 sync rollback owner drift",relative,actual)
    if r437_vendor_pin in {"729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for relative, blob in {
            "ns2-helpers/include/core/loader/ns2_svc_trace.h":
                "86e8e7e96b5eda5b6b98ccd3c7e6ce76d4275c86",
            "ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp":
                "09ae2494b2b6f620a25ab549c06c69045a9fb73d",
        }.items():
            raw = (active / relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == blob, ("NS2 reviewed SVC boundary source drift", relative, actual)
    if r437_vendor_pin in {"1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        raw = (active / "ns2-astc/include/video_core/texture_cache/texture_cache.h").read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        if actual == "27ea4e0e665d3f94e173c1335cb19211efc03646":
            # Reverse the four reviewed HUD/cache hunks only on the audit copy.
            text = raw.decode("utf-8")
            for current, predecessor in (
                ("void TextureCache<P>::RemoveFramebuffers(std::span<const ImageViewId> removed_views) {\n#ifdef PS5_NATIVE\n    // No framebuffer can contain an absent view. Do not flush deferred\n    // clears belonging to other render targets or scan the framebuffer map.\n    if (removed_views.empty()) {\n        return;\n    }\n#endif\n    runtime.FlushDeferredClear();\n    auto it = framebuffers.begin();\n    while (it != framebuffers.end()) {\n        if (it->first.Contains(removed_views)) {\n            auto framebuffer_id = it->second;\n            ASSERT(framebuffer_id);\n            if (framebuffer_id == last_framebuffer_id) {\n                last_framebuffer_id = {};\n                last_framebuffer_serial = 0;\n            }\n            sentenced_framebuffers.Push(std::move(slot_framebuffers[framebuffer_id]));\n            it = framebuffers.erase(it);\n        } else {\n            ++it;\n        }\n    }\n}", "void TextureCache<P>::RemoveFramebuffers(std::span<const ImageViewId> removed_views) {\n    runtime.FlushDeferredClear();\n    auto it = framebuffers.begin();\n    while (it != framebuffers.end()) {\n        if (it->first.Contains(removed_views)) {\n            auto framebuffer_id = it->second;\n            ASSERT(framebuffer_id);\n            if (framebuffer_id == last_framebuffer_id) {\n                last_framebuffer_id = {};\n                last_framebuffer_serial = 0;\n            }\n            sentenced_framebuffers.Push(std::move(slot_framebuffers[framebuffer_id]));\n            it = framebuffers.erase(it);\n        } else {\n            ++it;\n        }\n    }\n}"),
                ("void TextureCache<P>::RemoveImageViewReferences(std::span<const ImageViewId> removed_views) {\n#ifdef PS5_NATIVE\n    // Images created and retired without any view cannot be in a channel's\n    // descriptor-to-view map. Avoid scanning every channel on that path.\n    if (removed_views.empty()) {\n        return;\n    }\n#endif\n    for (size_t c : active_channel_ids) {\n        auto& channel_info = channel_storage[c];\n        auto it = channel_info.image_views.begin();\n        while (it != channel_info.image_views.end()) {\n            const auto found = std::ranges::find(removed_views, it->second);\n            if (found != removed_views.end()) {\n                it = channel_info.image_views.erase(it);\n            } else {\n                ++it;\n            }\n        }\n    }\n}", "void TextureCache<P>::RemoveImageViewReferences(std::span<const ImageViewId> removed_views) {\n    for (size_t c : active_channel_ids) {\n        auto& channel_info = channel_storage[c];\n        auto it = channel_info.image_views.begin();\n        while (it != channel_info.image_views.end()) {\n            const auto found = std::ranges::find(removed_views, it->second);\n            if (found != removed_views.end()) {\n                it = channel_info.image_views.erase(it);\n            } else {\n                ++it;\n            }\n        }\n    }\n}"),
                ("        // Publish both valid->NULL and NULL->valid generation transitions.\n        // A failed reconstruction also retires the previously bound view.\n        if (pair->second != NULL_IMAGE_VIEW_ID || remapped_cached_view)\n            ++texture_bindings_serial;", "        // CheckFeedbackLoop caches barrier decisions by this serial. Reviving\n        // an image without rewriting its TIC must invalidate that decision.\n        if (pair->second != NULL_IMAGE_VIEW_ID)\n            ++texture_bindings_serial;"),
                ("#ifdef PS5_NATIVE\n    // A descriptor table can retain its bytes after a channel map entry\n    // is evicted/rebuilt. Never dereference a missing sampler mapping.\n    const auto it = channel_state->sampler_ids.find(map_index);\n    if (it == channel_state->sampler_ids.end()) {\n        const auto id = FindSampler(descriptor, compute);\n        channel_state->sampler_ids.insert_or_assign(map_index, id);\n        return id;\n    }\n    return it->second;\n#else\n    return channel_state->sampler_ids.find(map_index)->second;\n#endif\n}", "    return channel_state->sampler_ids.find(map_index)->second;\n}"),
            ):
                assert text.count(current) == 1, "HUD/cache parity owner drift"
                text = text.replace(current, predecessor, 1)
            raw = text.encode("utf-8")
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == "5c6d015cf207d63de31b577411972606145d9f2e"
        if actual == "5c6d015cf207d63de31b577411972606145d9f2e":
            # Reverse the reviewed failed render-target allocation successor
            # only in the audit copy, then replay the original source proof.
            current = """    if (!image_id) {
        // An allocation failure means no render target. NULL_IMAGE_VIEW_ID is
        // a valid descriptor-null sentinel and has no render-target VkImageView.
        return ImageViewId{};
    }"""
            predecessor = """    if (!image_id) {
        return NULL_IMAGE_VIEW_ID;
    }"""
            assert raw.decode("utf-8").count(current) == 1
            raw = raw.decode("utf-8").replace(current, predecessor, 1).encode("utf-8")
            actual = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + bytes([0]) + raw
            ).hexdigest()
            assert actual == "948960fad4d829ba874746acb6e353a8a2ed19f7"
            print("ENCORE_TEXTURECACHE_NULL_TARGET_EXACT_REVERSE_PASS")
        if actual == "948960fad4d829ba874746acb6e353a8a2ed19f7":
            # Performance-only successor: TRACE compiles these two high-frequency
            # invalid-descriptor diagnostics out of release builds. Restore DEBUG
            # in the audit copy before reversing the ten semantic TextureCache hunks.
            text = raw.decode("utf-8")
            sampler_trace = '        LOG_TRACE(HW_GPU, "Invalid sampler index={}", index);'
            image_trace = '        LOG_TRACE(HW_GPU, "Invalid image view index={}", index);'
            assert text.count(sampler_trace) == 1 and text.count(image_trace) == 1, (
                "Descriptor hot-path log owner drift"
            )
            text = text.replace(
                sampler_trace,
                '        LOG_DEBUG(HW_GPU, "Invalid sampler index={}", index);',
                1,
            ).replace(
                image_trace,
                '        LOG_DEBUG(HW_GPU, "Invalid image view index={}", index);',
                1,
            )
            raw = text.encode("utf-8")
            actual = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + bytes([0]) + raw
            ).hexdigest()
            assert actual == "5b3db278f70b560a098a2a479d3ee98e78b987f2"
            print("ENCORE_DESCRIPTOR_HOT_PATH_LOG_EXACT_REVERSE_PASS")
        if actual == "5b3db278f70b560a098a2a479d3ee98e78b987f2":
            # Integrated descriptor/DMA/layered-copy/volume/X8_D24 successor.
            # Reverse its exact ten reviewed source hunks only in this audit copy.
            lines = raw.decode("utf-8").split("\n")
            reverse = (
                (49, ["","inline std::vector<ImageCopy> SplitLayeredImageCopies(std::span<const ImageCopy> copies) {","    std::vector<ImageCopy> layer_copies;","    layer_copies.reserve(copies.size());","    for (const ImageCopy& copy : copies) {","        const s32 num_layers = copy.dst_subresource.num_layers;","        if (num_layers <= 1 || copy.src_subresource.num_layers != num_layers) {","            layer_copies.push_back(copy);","            continue;","        }","        for (s32 layer = 0; layer < num_layers; ++layer) {","            ImageCopy single = copy;","            single.dst_subresource.base_layer += layer;","            single.src_subresource.base_layer += layer;","            single.dst_subresource.num_layers = 1;","            single.src_subresource.num_layers = 1;","            layer_copies.push_back(single);","        }","    }","    return layer_copies;","}","","","using Tegra::Texture::TICEntry;","using Tegra::Texture::TSCEntry;","using VideoCore::Surface::GetFormatType;"], ["using Tegra::Texture::TICEntry;","using Tegra::Texture::TSCEntry;","using VideoCore::Surface::GetFormatType;"]),
                (449, ["    if (index > table.current_limit || index >= table.descriptors.size()) {","        LOG_DEBUG(HW_GPU, \"Invalid sampler index={}\", index);","        return NULL_SAMPLER_ID;","    }"], ["    if (index > table.current_limit) {","        LOG_DEBUG(HW_GPU, \"Invalid sampler index={}\", index);","        return NULL_SAMPLER_ID;","    }"]),
                (475, ["    // A guest-controlled TIC/TSC limit must never allocate an unbounded","    // descriptor array from inside DescriptorTable::Refresh() noexcept.","    // 21-bit table indices are the conservative upstream upper bound.","    constexpr u32 MaxDescriptorTableLimit = (1U << 21) - 1;","    if (compute) {","        const bool linked_tsc = kepler_compute->launch_description.linked_tsc;","        const u32 tic_limit = (std::min)(kepler_compute->regs.tic.limit, MaxDescriptorTableLimit);","        const u32 tsc_limit = linked_tsc ? tic_limit : (std::min)(kepler_compute->regs.tsc.limit, MaxDescriptorTableLimit);","        bool bindings_changed = false;"], ["    if (compute) {","        const bool linked_tsc = kepler_compute->launch_description.linked_tsc;","        const u32 tic_limit = kepler_compute->regs.tic.limit;","        const u32 tsc_limit = linked_tsc ? tic_limit : kepler_compute->regs.tsc.limit;","        bool bindings_changed = false;"]),
                (493, ["        const u32 tic_limit = (std::min)(maxwell3d->regs.tex_header.limit, MaxDescriptorTableLimit);","        const u32 tsc_limit = linked_tsc ? tic_limit : (std::min)(maxwell3d->regs.tex_sampler.limit, MaxDescriptorTableLimit);","        bool bindings_changed = false;","        if (channel_state->graphics_sampler_table.Synchronize(maxwell3d->regs.tex_sampler.Address(), tsc_limit))","            bindings_changed = true;"], ["        const u32 tic_limit = maxwell3d->regs.tex_header.limit;","        const u32 tsc_limit = linked_tsc ? tic_limit : maxwell3d->regs.tex_sampler.limit;","        bool bindings_changed = false;","        if (channel_state->graphics_sampler_table.Synchronize(maxwell3d->regs.tex_sampler.Address(), tsc_limit))","            bindings_changed = true;"]),
                (849, ["    if (index > table.current_limit || index >= table.descriptors.size()) {","        LOG_DEBUG(HW_GPU, \"Invalid image view index={}\", index);","        return NULL_IMAGE_VIEW_ID;","    }"], ["    if (index > table.current_limit) {","        LOG_DEBUG(HW_GPU, \"Invalid image view index={}\", index);","        return NULL_IMAGE_VIEW_ID;","    }"]),
                (985, ["void TextureCache<P>::WriteDmaCopy(","    GPUVAddr src_addr, GPUVAddr dest_addr, size_t size,","    std::span<const std::pair<DAddr, size_t>> gpu_written_dest) {","    if (size == 0) {","        return;","    }","    const std::optional<DAddr> src = gpu_memory->GpuToCpuAddress(src_addr);","    const std::optional<DAddr> dest = gpu_memory->GpuToCpuAddress(dest_addr);","    if (!src || !dest ||","        *src > (std::numeric_limits<DAddr>::max)() - size ||","        *dest > (std::numeric_limits<DAddr>::max)() - size) {","        return;","    }","    const DAddr src_end = *src + size;","    const DAddr dest_end = *dest + size;","","    // BufferCache reports destination bytes whose source was newer on the GPU.","    // Guest memory still contains older bytes there until a later download.","    boost::container::small_vector<std::pair<DAddr, size_t>, 8> unheld;","    unheld.reserve(gpu_written_dest.size() + 4);","    for (const auto& [begin, length] : gpu_written_dest) {","        if (length == 0 || begin < *dest || begin >= dest_end ||","            length > dest_end - begin) {","            return;","        }","        unheld.emplace_back(begin, length);","    }","","    // GPU-written source images have the same property: DMACopy moves their","    // host-GPU bytes, while the guest-memory mirror still holds older data.","    ForEachImageInRegion(*src, size, [&](ImageId, Image& image) {","        if (False(image.flags & ImageFlagBits::GpuModified)) {","            return;","        }","        const DAddr begin = (std::max)(static_cast<DAddr>(image.cpu_addr), *src);","        const DAddr end = (std::min)(static_cast<DAddr>(image.cpu_addr_end), src_end);","        if (begin < end) {","            unheld.emplace_back(*dest + (begin - *src), static_cast<size_t>(end - begin));","        }","    });","","    const auto overlaps_unheld = [&unheld](const Image& image) {","        return std::ranges::any_of(unheld, [&image](const auto& range) {","            const DAddr range_end = range.first + range.second;","            return range.first < image.cpu_addr_end && image.cpu_addr < range_end;","        });","    };","","    ForEachImageInRegion(*dest, size, [&](ImageId image_id, Image& image) {","        // Uploading this image would consume bytes that guest memory does not","        // hold yet, or discard GPU-owned texels outside the copied interval.","        const bool keeps_gpu_contents =","            True(image.flags & ImageFlagBits::GpuModified) &&","            (image.cpu_addr < *dest || image.cpu_addr_end > dest_end);","        if (overlaps_unheld(image) || keeps_gpu_contents) {","            return;","        }","#ifdef EDEN_NS2_ASTC_CACHE_BRIDGE","        if (image.ns2_astc_dirty) {","            if (image.ns2_astc_dirty->MarkWrite(*dest, size)) {","                image.flags |= ImageFlagBits::CpuModified;","                return;","            }","            image.ns2_astc_dirty.reset();","        }","#endif","        if (True(image.flags & ImageFlagBits::CpuModified)) {","            return;","        }","        image.flags |= ImageFlagBits::CpuModified;","        if (True(image.flags & ImageFlagBits::Tracked)) {","            UntrackImage(image, image_id);","        }","    });","}","","template <class P>","bool TextureCache<P>::IsGpuMemoryGpuModified(GPUVAddr gpu_addr, size_t size) {","    // GetSubmappedRange omits unmapped/reserved holes. A partial translation","    // must never make a DMA destination look safe for a guest-memory upload."], ["bool TextureCache<P>::IsGpuMemoryGpuModified(GPUVAddr gpu_addr, size_t size) {","    // GetSubmappedRange omits unmapped/reserved holes. A partial translation","    // must never make a DMA destination look safe for a guest-memory upload."]),
                (1409, ["#ifdef PS5_NATIVE","    // NS1 / Maxwell production path for Lichii #853 semantics. NS2 address","    // spaces enable native tiling after authenticated channel admission and","    // keep using the separately guarded native-volume path above.","    if constexpr (std::is_same_v<Runtime, Vulkan::TextureCacheRuntime>) {","        const auto copy_ns1_volume_slice = [&]() -> bool {","            using Fermi2D = Tegra::Engines::Fermi2D;","            if (!gpu_memory || gpu_memory->UsesNativeTiling() || !channel_state ||","                copy.operation != Fermi2D::Operation::SrcCopy ||","                copy.filter != Fermi2D::Filter::Point) {","                return false;","            }","            const auto is_volume = [](const Fermi2D::Surface& surface) {","                return surface.depth > 1 &&","                       surface.linear == Fermi2D::MemoryLayout::BlockLinear &&","                       surface.layer == 0 && surface.width != 0 && surface.height != 0;","            };","            if (src.width > static_cast<u32>(std::numeric_limits<s32>::max()) ||","                dst.width > static_cast<u32>(std::numeric_limits<s32>::max()) ||","                src.height > static_cast<u32>(std::numeric_limits<s32>::max()) ||","                dst.height > static_cast<u32>(std::numeric_limits<s32>::max())) {","                return false;","            }","            const bool whole_slice =","                copy.src_x0 == 0 && copy.src_y0 == 0 &&","                copy.dst_x0 == 0 && copy.dst_y0 == 0 &&","                copy.src_x1 == static_cast<s32>(src.width) &&","                copy.src_y1 == static_cast<s32>(src.height) &&","                copy.dst_x1 == static_cast<s32>(dst.width) &&","                copy.dst_y1 == static_cast<s32>(dst.height);","            if (!is_volume(src) || !is_volume(dst) || !whole_slice ||","                src.format != dst.format || src.width != dst.width ||","                src.height != dst.height) {","                return false;","            }","","            const auto format =","                VideoCore::Surface::PixelFormatFromRenderTargetFormat(src.format);","            struct Slice {","                ImageId id;","                s32 depth;","            };","            const auto find_slice = [&](const Fermi2D::Surface& surface)","                -> std::optional<Slice> {","                std::optional<Slice> found;","                bool ambiguous = false;","                const GPUVAddr address = surface.Address();","                ForEachImageInRegionGPU(channel_state->gpu_memory.GetID(), address, 1,","                                        [&](ImageId id, Image& image) {","                    if (image.info.type != ImageType::e3D ||","                        image.info.format != format ||","                        image.info.num_samples != 1 ||","                        image.info.size.width != surface.width ||","                        image.info.size.height != surface.height ||","                        image.info.size.depth != surface.depth ||","                        !image.aliased_images.empty() || !image.overlapping_images.empty() ||","                        True(image.flags & (ImageFlagBits::Remapped | ImageFlagBits::Sparse |","                                            ImageFlagBits::Rescaled | ImageFlagBits::IsDecoding)) ||","                        address < image.gpu_addr) {","                        return false;","                    }","                    const u64 relative = address - image.gpu_addr;","                    if (relative >= image.guest_size_bytes ||","                        relative > std::numeric_limits<u32>::max() ||","                        image.slice_offsets.size() != image.slice_subresources.size()) {","                        return false;","                    }","                    const auto it =","                        std::ranges::find(image.slice_offsets, static_cast<u32>(relative));","                    if (it == image.slice_offsets.end()) {","                        return false;","                    }","                    const auto index = static_cast<size_t>(","                        std::distance(image.slice_offsets.begin(), it));","                    const SubresourceBase base = image.slice_subresources[index];","                    if (base.level != 0 || base.layer < 0 ||","                        static_cast<u32>(base.layer) >= image.info.size.depth) {","                        return false;","                    }","                    if (found) {","                        ambiguous = true;","                        return false;","                    }","                    found = Slice{id, base.layer};","                    return false;","                });","                return ambiguous ? std::nullopt : found;","            };","","            const auto src_slice = find_slice(src);","            const auto dst_slice = find_slice(dst);","            if (!src_slice || !dst_slice || src_slice->id == dst_slice->id) {","                return false;","            }","","            struct PhysicalSpan {","                u64 address;","                u64 bytes;","            };","            const auto capture_physical = [&](ImageId id) -> std::optional<PhysicalSpan> {","                const Image& image = slot_images[id];","                const u64 bytes = image.guest_size_bytes;","                constexpr u64 MaxVolumeBytes = 256ULL * 1024 * 1024;","                if (!image.gpu_addr || !bytes || bytes > MaxVolumeBytes ||","                    image.gpu_addr > std::numeric_limits<u64>::max() - (bytes - 1) ||","                    !gpu_memory->IsContinuousRange(image.gpu_addr, bytes)) {","                    return std::nullopt;","                }","                const auto start = gpu_memory->GpuToCpuAddress(image.gpu_addr);","                const auto end = gpu_memory->GpuToCpuAddress(image.gpu_addr + bytes - 1);","                if (!start || !end || *start != image.cpu_addr ||","                    *start > std::numeric_limits<u64>::max() - (bytes - 1) ||","                    *end != *start + bytes - 1) {","                    return std::nullopt;","                }","                return PhysicalSpan{*start, bytes};","            };","            const auto overlaps = [](PhysicalSpan lhs, PhysicalSpan rhs) {","                return lhs.address <= rhs.address","                    ? rhs.address - lhs.address < lhs.bytes","                    : lhs.address - rhs.address < rhs.bytes;","            };","            const auto src_physical = capture_physical(src_slice->id);","            const auto dst_physical = capture_physical(dst_slice->id);","            if (!src_physical || !dst_physical ||","                overlaps(*src_physical, *dst_physical)) {","                return false;","            }","","            runtime.FlushDeferredClear();","            PrepareImage(src_slice->id, false, false);","            PrepareImage(dst_slice->id, false, false);","","            // RefreshContents/SynchronizeAliases may replace either cached","            // image. Resolve the exact slices again before publishing a write.","            const auto src_after = find_slice(src);","            const auto dst_after = find_slice(dst);","            if (!src_after || !dst_after ||","                src_after->id != src_slice->id || dst_after->id != dst_slice->id ||","                src_after->depth != src_slice->depth ||","                dst_after->depth != dst_slice->depth) {","                return false;","            }","            const auto src_physical_after = capture_physical(src_slice->id);","            const auto dst_physical_after = capture_physical(dst_slice->id);","            if (!src_physical_after || !dst_physical_after ||","                src_physical_after->address != src_physical->address ||","                dst_physical_after->address != dst_physical->address ||","                src_physical_after->bytes != src_physical->bytes ||","                dst_physical_after->bytes != dst_physical->bytes ||","                overlaps(*src_physical_after, *dst_physical_after)) {","                return false;","            }","","            MarkModification(slot_images[dst_slice->id]);","            const ImageCopy slice_copy{","                .src_subresource = {.base_level = 0, .base_layer = 0, .num_layers = 1},","                .dst_subresource = {.base_level = 0, .base_layer = 0, .num_layers = 1},","                .src_offset = {0, 0, src_slice->depth},","                .dst_offset = {0, 0, dst_slice->depth},","                .extent = {src.width, src.height, 1},","            };","            runtime.CopyImage(slot_images[dst_slice->id], slot_images[src_slice->id],","                              std::span{&slice_copy, 1});","            return true;","        };","        if (copy_ns1_volume_slice()) {","            return true;","        }","    }","#endif","    const auto result = GetBlitImages(dst, src, copy);","    if (!result) {","        return false;"], ["    const auto result = GetBlitImages(dst, src, copy);","    if (!result) {","        return false;"]),
                (4034, ["    for (const ImageCopy& copy : SplitLayeredImageCopies(copies)) {","        UNIMPLEMENTED_IF(copy.dst_subresource.num_layers != 1);","        UNIMPLEMENTED_IF(copy.src_subresource.num_layers != 1);","        UNIMPLEMENTED_IF(copy.src_offset != Offset3D{});"], ["    for (const ImageCopy& copy : copies) {","        UNIMPLEMENTED_IF(copy.dst_subresource.num_layers != 1);","        UNIMPLEMENTED_IF(copy.src_subresource.num_layers != 1);","        UNIMPLEMENTED_IF(copy.src_offset != Offset3D{});"]),
                (4052, ["        // X8_D24 aliases preserve raw 32-bit storage. When either side is depth-only","        // X8_D24, view every 4-byte colour alias as ABGR8 so the Vulkan conversion","        // shader sees the original low three depth bytes instead of colour semantics.","        const auto alias_conversion_format = [](PixelFormat format, PixelFormat other_format) {","            if (other_format == PixelFormat::X8_D24_UNORM &&","                GetFormatType(format) == SurfaceType::ColorTexture &&","                BytesPerBlock(format) == 4) {","                return PixelFormat::A8B8G8R8_UNORM;","            }","            return format;","        };","        PixelFormat dst_format = alias_conversion_format(dst.info.format, src.info.format);","        const PixelFormat src_format = alias_conversion_format(src.info.format, dst.info.format);","        if (GetFormatType(src.info.format) == SurfaceType::DepthStencil &&","            GetFormatType(dst_format) == SurfaceType::ColorTexture &&","            BytesPerBlock(dst_format) == 4) {"], ["        PixelFormat dst_format = dst.info.format;","        if (GetFormatType(src.info.format) == SurfaceType::DepthStencil &&","            GetFormatType(dst_format) == SurfaceType::ColorTexture &&","            BytesPerBlock(dst_format) == 4) {"]),
                (4071, ["        const ImageViewInfo src_view_info(ImageViewType::e2D, src_format, src_range);","        const auto [dst_framebuffer_id, dst_view_id] = RenderTargetFromImage(dst_id, dst_view_info);","        Framebuffer* const dst_framebuffer = &slot_framebuffers[dst_framebuffer_id];","        const ImageViewId src_view_id = FindOrEmplaceImageView(src_id, src_view_info);"], ["        const ImageViewInfo src_view_info(ImageViewType::e2D, src.info.format, src_range);","        const auto [dst_framebuffer_id, dst_view_id] = RenderTargetFromImage(dst_id, dst_view_info);","        Framebuffer* const dst_framebuffer = &slot_framebuffers[dst_framebuffer_id];","        const ImageViewId src_view_id = FindOrEmplaceImageView(src_id, src_view_info);"]),
            )
            for index, newer, earlier in reversed(reverse):
                assert lines[index:index + len(newer)] == newer, "Integrated TextureCache source drift"
                lines[index:index + len(newer)] = earlier
            historical = "\n".join(lines).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            assert actual == "c797eb9e3f4432b6ba19fe8a17a7289b23b75864"
            print("ENCORE_NS1_NS2_TEXTURECACHE10_EXACT_REVERSE_PASS")
        assert actual == ("c797eb9e3f4432b6ba19fe8a17a7289b23b75864" if fc27_p1_vendor else
                          "c7cb95ecaf388b925fc29582499bbd4b54a77f75" if r437_vendor_pin in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "859a9e46fb63a97fee82c8ea6b1566317264f98f" if r437_vendor_pin == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "0d99f9a861c645562519f71d62f4f49bfedd8101"), ("Selected F07 TextureCache drift", actual)
    assert fc27_deferred_present == set()
    r437_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"

if r437_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}:
    def current_r437_blob(source):
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert current_r437_blob(r437_body) == "bd424e728182500b573a4cc4cf07987ddc4cbdc3"
    sibling_decl = """    /// Preserve GPU-written bytes elsewhere on touched pages before a CPU write
    /// changes the page-granular ownership. Disable only when the mapping is going away.
    void WriteMemory(DAddr device_addr, u64 size, bool keep_page_gpu_data = true);
"""
    historical_decl = "    void WriteMemory(DAddr device_addr, u64 size);\n"
    assert r437_body.count(sibling_decl) == 1
    r437_body = r437_body.replace(sibling_decl, historical_decl, 1)
    assert current_r437_blob(r437_body) == "42f7b4287d9457b26113d10819bbe4ddaf065aaa"
    print("ENCORE_FC27_BUFFER_BASE_SIBLING_DECL_EXACT_REVERSE_PASS")
if r437_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or r437_vendor_pin in {"b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "affa3c761f70268c89e9f7c7de24eec958c7f889",
                         "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"}:
    def r437_blob(source):
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert r437_blob(r437_body) == "42f7b4287d9457b26113d10819bbe4ddaf065aaa"
    additions = (
        """    using PendingCpuWrites = std::function<void(const std::function<void(DAddr, size_t)>&)>;
    void SetPendingCpuWrites(PendingCpuWrites source) { pending_cpu_writes = std::move(source); }

    /// Remove all about-to-be-applied CPU writes from GPU-owned ranges before
    /// any one write can trigger a download of older bytes over another.
    void ClaimCpuWrites(std::span<const std::pair<DAddr, u64>> ranges);

""",
        """    [[nodiscard]] Common::RangeSet<DAddr> PendingCpuWriteRanges();
    void WriteDownloadedMemory(const Common::RangeSet<DAddr>& cpu_written,
                               DAddr device_addr, const u8* data, u64 size);

""",
        "    PendingCpuWrites pending_cpu_writes;\n",
    )
    for addition in additions:
        assert r437_body.count(addition) == 1
        r437_body = r437_body.replace(addition, "", 1)
    assert r437_blob(r437_body) == "b4b7480e6a3d52ef7ec8c597f8e81c9e2f9fe1d9"
    print("ENCORE_FC27_BUFFER_BASE_EXACT_REVERSE_PARITY_PASS")
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
assert 'set(eden_ns2_prior_eden_ns2_image_source_idx "${EDEN_NS1_IMAGE_DESCRIPTOR_SOURCE}")' in image_select
assert 'list(FIND eden_ns2_shader_sources' in image_select
assert 'list(REMOVE_ITEM eden_ns2_shader_sources "${eden_ns2_prior_eden_ns2_image_source_idx}")' in image_select
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

# P2.7: the three suspend/resume owners exist across the reviewed native
# GPFIFO vendor lineage. The NVK/M2MF channel-state override was added only
# by vendor 697159fd; historical pair gates intentionally checkout older
# vendors and must not pretend that later owner existed there.
post_f07_native_gpfifo_owners = {
    "ns2-runtime/gpu_dispatch/video_core/dma_pusher.h",
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp",
    "ns2-runtime/gpu_dispatch/video_core/control/scheduler.h",
}
native_m2mf_channel_state = "ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp"
native_gpfifo_vendor_pin = subprocess.check_output(
    ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD"], text=True).strip()
native_gpfifo_vendor_pin = "ab417b59c5f7f4613ff27386be05c0644d0ed776" if native_gpfifo_vendor_pin in {
    "ce25655b08751aa0c2f9efb10ff05fd8fcbf7a93", "7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285"
} else native_gpfifo_vendor_pin
if native_gpfifo_vendor_pin in {"01c942171fea39c1f7cf31d13ab36895aebb593a",
                              "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
    # Retain the exact production NS2 GPFIFO M2MF owner across the merged
    # FC27 P1 and GetInfo receipt-only vendor commits.
    current = (active / native_m2mf_channel_state).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(current)).encode() + bytes([0]) + current).hexdigest()
    assert actual == "dd30183f72a9a9dfc2a17700db263f85e4d77596", actual
    native_gpfifo_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if native_gpfifo_vendor_pin in {
    "c15cdfe96a3d836bf32ba21b8070088add81cdc9",
    "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776",
}:
    # The selected channel-state owner is unchanged by the SVC-only successor.
    raw = (active / native_m2mf_channel_state).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "dd30183f72a9a9dfc2a17700db263f85e4d77596", (
        "NS2 M2MF channel-state source drift", actual)
    native_gpfifo_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if native_gpfifo_vendor_pin in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200", "67759611edc13414c112ea9d2b6664d54827a200"}:
    native_gpfifo_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if native_gpfifo_vendor_pin in {"697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6","affa3c761f70268c89e9f7c7de24eec958c7f889"}:
    post_f07_native_gpfifo_owners.add(native_m2mf_channel_state)
# Later NS2-only vendor commits retain the byte-identical M2MF channel-state
# TU. Confirm the actual compiled CMake owner and source SHA, not vendor HEAD.
if native_m2mf_channel_state not in post_f07_native_gpfifo_owners:
    selected_channel = active / native_m2mf_channel_state
    selection_cmake = (root / "headless/CMakeLists.txt").read_text()
    raw = selected_channel.read_bytes()
    actual = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + bytes([0]) + raw
    ).hexdigest()
    if (actual == "dd30183f72a9a9dfc2a17700db263f85e4d77596" and
        'list(APPEND eden_ns2_sched_sources "${EDEN_NS2_GPFIFO_CHANNEL_STATE}")' in selection_cmake and
        'list(REMOVE_ITEM eden_ns2_sched_sources "control/channel_state.cpp")' in selection_cmake):
        post_f07_native_gpfifo_owners.add(native_m2mf_channel_state)
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
if native_m2mf_channel_state in post_f07_native_gpfifo_owners:
    assert 'list(REMOVE_ITEM eden_ns2_sched_sources "control/channel_state.cpp")' in native_gpfifo_cmake
    assert 'list(APPEND eden_ns2_sched_sources "${EDEN_NS2_GPFIFO_CHANNEL_STATE}")' in native_gpfifo_cmake
    native_channel_state = (active / native_m2mf_channel_state).read_text()
    assert "constexpr u32 NvkM2mfSubchannel = 2;" in native_channel_state
    assert "payload.kepler_memory, NvkM2mfSubchannel" in native_channel_state
    assert "Engines::EngineTypes::KeplerMemory" in native_channel_state
else:
    assert native_m2mf_channel_state not in set(physical_all)
print("ENCORE_POST_F07_NATIVE_GPFIFO_OWNER_PASS",
      f"owners={len(post_f07_native_gpfifo_owners)}",
      f"m2mf_default={int(native_m2mf_channel_state in post_f07_native_gpfifo_owners)}")

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
    "eden-core/overrides/native-tiling/video_core/textures/decoders.h",
    "eden-core/overrides/native-tiling/video_core/memory_manager.h",
    "eden-core/src/video_core/engines/engine_upload.cpp",
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

# Lichii #290 / PS5 0081: one maintained common ThreadWorker header is
# selected by the native CMake graph. It is post-F07 and must not rewrite
# the immutable 337-owner historical ledger.
post_f07_thread_worker_owners = {
    "eden-core/overrides/thread-worker/common/thread_worker.h",
}
assert post_f07_thread_worker_owners <= set(physical_all)
assert not post_f07_thread_worker_owners.intersection(research_paths)
thread_worker_recipe = (root / "headless/CMakeLists.txt").read_text()
for token in (
    'set(EDEN_MAINTAINED_THREAD_WORKER_ROOT',
    'eden-core/overrides/thread-worker',
    'target_include_directories(common BEFORE PUBLIC "${EDEN_MAINTAINED_THREAD_WORKER_ROOT}")',
    'target_include_directories(core BEFORE PUBLIC "${EDEN_MAINTAINED_THREAD_WORKER_ROOT}")',
    'target_include_directories(video_core BEFORE PRIVATE "${EDEN_MAINTAINED_THREAD_WORKER_ROOT}")',
):
    assert token in thread_worker_recipe, token
print("ENCORE_POST_F07_THREAD_WORKER_OWNER_PASS owners=1 historical_F07=337")

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

# A missing game loader follows an already-initialized kernel on PS5.
# All three maintained core variants must shut down before returning an error.
# See Lichii upstream #972; do not fork immutable sources/eden.
for loader_owner in (
    "encore-active/eden-core/src/core/core_native.cpp",
    "encore-active/eden-core/src/core/core_standard.cpp",
    "encore-active/ns2-runtime/process/core/core.cpp",
):
    selected = (root / "vendor" / loader_owner).read_text()
    block = selected.split("        if (!app_loader) {", 1)[1].split("\n        }", 1)[0]
    assert block.count("ShutdownMainProcess();") == 1, loader_owner
    assert block.index("ShutdownMainProcess();") < block.index(
        "return SystemResultStatus::ErrorGetLoader;"), loader_owner
print("ENCORE_NS1_NS2_MISSING_LOADER_TEARDOWN_PASS owners=3")


# R457 NS2 KPort sparse slab precommit is a separately reviewed post-F07
# production owner, not a retroactive member of the immutable 337 files.
post_f07_r457_slab_owners = {"ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp"}
assert post_f07_r457_slab_owners <= set(physical_all)
slab_source = (root / "vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp").read_bytes()
assert hashlib.sha1(b"blob " + str(len(slab_source)).encode() + bytes([0]) + slab_source).hexdigest() == "130eb7bd53e29b816bb81fec3fa053a584cd4b6e"
assert slab_source.decode().count("EdenNs2CommitGuestBacking(") == 3

# The Nov13 native fix adds two reviewed owners AFTER the immutable F07
# catalogue. They are not retroactively counted as historical F07 sources:
# both must exist and be selected in native CMake (single stb implementation).
# Nov14 PS5 Vulkan usage-tracker overlay is added AFTER the immutable
# 337-owner F07 catalog, and only when the exact vendor candidate is staged.
# The pinned original engine gitlink lacks this header by design. Never
# inflate the frozen 337 count, and never exclude any other new source.
post_f07_usage_tracker_owners = {
    "eden-core/overrides/usage-tracker/video_core/buffer_cache/usage_tracker.h",
}
usage_tracker_present = post_f07_usage_tracker_owners & set(physical_all)
if usage_tracker_present:
    assert usage_tracker_present == post_f07_usage_tracker_owners
    assert (root / "tools/check-ps5-usage-tracker-selection-host.py").is_file()
    assert "EDEN_PS5_USAGE_TRACKER_ROOT" in (
        root / "headless/CMakeLists.txt").read_text()
    print("ENCORE_POST_F07_USAGE_TRACKER_OWNER_PASS reviewed=1")

# Nov14 selected NVDEC FFmpeg source and ABI header are a reviewed
# optional pair postdating F07. Do not inflate the frozen 337-source ledger.
# Preserve the original pristine Eden codec tree and fail on half-candidates.
post_f07_nvdec_owners = {
    "eden-core/src/video_core/host1x/ffmpeg.cpp",
    "eden-core/overrides/video_core/host1x/ffmpeg.h",
}
post_f07_nvdec_present = post_f07_nvdec_owners & set(physical_all)
if post_f07_nvdec_present:
    assert post_f07_nvdec_present == post_f07_nvdec_owners, (
        "Half-selected NVDEC source/ABI header", sorted(post_f07_nvdec_present))
    assert (root / "tools/check-nvdec-eagain-owner-selection-host.py").is_file()
    assert "EDEN_NVDEC_MAINTAINED_SOURCE" in (
        root / "headless/CMakeLists.txt").read_text()
    print("ENCORE_POST_F07_NVDEC_OWNER_PAIR_PASS owners=2")

# R457 VIC diagnostics have one optional, explicitly reviewed new owner;
# the two FFmpeg ABI owners above retain their existing identity and count.
post_f07_vic_receipt = "eden-core/src/video_core/host1x/vic.cpp"
post_f07_vic_present = {post_f07_vic_receipt} & set(physical_all)
if post_f07_vic_present:
    assert post_f07_nvdec_present == post_f07_nvdec_owners
    raw_vic = (active / post_f07_vic_receipt).read_bytes()
    vic_sha = hashlib.sha1(
        b"blob " + str(len(raw_vic)).encode() + bytes([0]) + raw_vic
    ).hexdigest()
    if vic_sha == "178d361bc3b5e9a0bf6ca9fa579d49df7ab72935":
        # The selected VIC adds the reviewed bounds/overflow, unaligned SIMD
        # and worker-lifetime protections. Reuse its existing exact 29-hunk
        # source receipt instead of duplicating that reconstruction here.
        vic_receipt = root / "vendor/tests/fc27_nvdec_vic_witness_host.py"
        assert vic_receipt.is_file()
        subprocess.run(["python3", "-B", str(vic_receipt)], check=True, timeout=180)
        print("ENCORE_POST_F07_VIC29_EXACT_RECEIPT_PASS")
    else:
        assert vic_sha == "48008fc5f3b05c3e95432827c03e20b815cce21c", (
            "Unreviewed VIC source drift", vic_sha)
    raw_ffmpeg = (active / "eden-core/src/video_core/host1x/ffmpeg.cpp").read_bytes()
    assert hashlib.sha1(b"blob " + str(len(raw_ffmpeg)).encode() + bytes([0]) + raw_ffmpeg).hexdigest() == "2eadc437cec5559560e5aaf849dd3b6446782e99"
    vic_cmake = (root / "headless/CMakeLists.txt").read_text()
    assert 'list(REMOVE_ITEM eden_vic_video_sources "host1x/vic.cpp")' in vic_cmake
    assert 'list(APPEND eden_vic_video_sources "${EDEN_VIC_MAINTAINED_SOURCE}")' in vic_cmake
    assert (root / "tools/check-nvdec-eagain-owner-selection-host.py").is_file()
print("ENCORE_POST_F07_VIC_WITNESS_OWNER_PASS", f"owners={len(post_f07_vic_present)}")

nov13_native_owners = {
    "eden-core/src/common/stb_image_png.cpp",
    "ns2-runtime/sparse-residency/core/hle/kernel/k_shared_memory.cpp",
}
assert nov13_native_owners <= set(physical_all), (
    "Missing Nov13 native crash/PNG owners", sorted(nov13_native_owners - set(physical_all)))
nov13_cmake = (root / "headless/CMakeLists.txt").read_text()
assert 'list(REMOVE_ITEM eden_stb_common_sources "stb.cpp")' in nov13_cmake
assert 'list(APPEND eden_stb_common_sources "${EDEN_NATIVE_STB_CODECS}")' in nov13_cmake
assert 'list(REMOVE_ITEM eden_sparse_core_sources "hle/kernel/k_shared_memory.cpp")' in nov13_cmake
assert 'list(APPEND eden_sparse_core_sources "${EDEN_NS2_SHARED_MEMORY_SOURCE}")' in nov13_cmake
# The optional JXR source pair is reviewed post-F07 and must not alter the
# immutable source-owner count. Check actual source identities if present;
# historical vendor probes can still run without the later adapter.
post_f07_jxr_adapter_owners = {
    "ps5-jxr/jxr_decoder.c",
    "ps5-jxr/jxr_decoder.h",
}
post_f07_jxr_present = post_f07_jxr_adapter_owners & set(physical_all)
if post_f07_jxr_present:
    assert post_f07_jxr_present == post_f07_jxr_adapter_owners, "Incomplete JXR adapter"
    assert 'add_library(eden-ps5-jxr STATIC ${eden_jxr_library_sources}' in nov13_cmake
    assert '"${EDEN_JXR_ADAPTER}/jxr_decoder.c")' in nov13_cmake
    assert 'target_link_libraries(eden-headless PRIVATE eden-ps5-jxr)' in nov13_cmake
    for name, expected_blob in {
        "jxr_decoder.c": "e83e13a3a6e66b7e63fb9510215c1dff2d42dd14",
        "jxr_decoder.h": "d8bb62a86fa1226375ae09e70f39c58511a667f9",
    }.items():
        data = (root / "vendor/encore-active/ps5-jxr" / name).read_bytes()
        actual_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
        assert actual_blob == expected_blob, ("JXR selected source changed; review new blob", name, actual_blob)
# Lichii #957 exact source backport, post-F07; never alter frozen 337 count.
post_f07_gpu_table_owners = {"eden-core/src/common/multi_level_page_table.cpp"}
post_f07_gpu_table_present = post_f07_gpu_table_owners & set(physical_all)
# The tracker workflow also explicitly tests historical vendor 1ec7b42.
# Only that known historical checkout (not a missing production TU) may omit it.
gpu_table_vendor_pin = checked_guest_cache_lock_vendor(subprocess.check_output(["git","-C",str(root/"vendor"),"rev-parse","HEAD"],text=True).strip())
if stabilization_selected:
    gpu_table_vendor_pin = "9db97fb12db1a390d6b2410f0c18333aa31e37da"
gpu_table_vendor_pin = "ab417b59c5f7f4613ff27386be05c0644d0ed776" if gpu_table_vendor_pin in {
    "ce25655b08751aa0c2f9efb10ff05fd8fcbf7a93", "7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285"
} else gpu_table_vendor_pin
shared_storage32_selected = gpu_table_vendor_pin in {"372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}
ps5_vfs128_selected = gpu_table_vendor_pin in {"a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} or fc27_p1_vendor
ps5_ns2_ipc_selected = gpu_table_vendor_pin == "ab417b59c5f7f4613ff27386be05c0644d0ed776" or fc27_p1_vendor
if gpu_table_vendor_pin in {
    "c15cdfe96a3d836bf32ba21b8070088add81cdc9",
    "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776",
}:
    # Current vendor's production FC27/Vulkan/ROMFS source blobs and the
    # new SVC owners were already verified above; only replay historical
    # F07 classifications using their exact unchanged source profile.
    gpu_table_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if gpu_table_vendor_pin in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200", "67759611edc13414c112ea9d2b6664d54827a200"}:
    gpu_table_vendor_pin = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_gpu_table_present
else:
    assert post_f07_gpu_table_present == post_f07_gpu_table_owners
    page_table_bytes = (active / "eden-core/src/common/multi_level_page_table.cpp").read_bytes()
    assert hashlib.sha1(b"blob " + str(len(page_table_bytes)).encode() + bytes([0]) + page_table_bytes).hexdigest() == "c55a55498fe300458800b646bfc295db11283b4a"
    assert 'list(REMOVE_ITEM eden_page_table_sources "multi_level_page_table.cpp")' in nov13_cmake
    assert 'list(APPEND eden_page_table_sources "${EDEN_MAINTAINED_GPU_PAGE_TABLE}")' in nov13_cmake
print("ENCORE_POST_F07_GPU_PAGE_TABLE_OWNER_PASS", f"owners={len(post_f07_gpu_table_present)}")
# VFS/PFS #118 adds three real post-F07 owners; old explicit historical
# checkout must not have them. Fail on half-selected or changed blobs.
post_f07_vfs_receipts = {
    "eden-core/src/core/file_sys/vfs/vfs.cpp": "70926039977f56c87558270d7655f8de26d1e446",
    "eden-core/src/core/file_sys/vfs/vfs_vector.cpp": "5f9c99b7ed5227c403ceca1d2e04d6c8dafc26cb",
    "eden-core/src/core/file_sys/partition_filesystem.cpp": "350af05f831fe89a05158350f8c8aded988980dd"
}
post_f07_vfs_present = set(post_f07_vfs_receipts) & set(physical_all)
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_vfs_present
else:
    assert post_f07_vfs_present == set(post_f07_vfs_receipts)
    for relative, blob in post_f07_vfs_receipts.items():
        data = (active / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest() == blob
    assert 'list(REMOVE_ITEM core_sources "${eden_vfs_relative}")' in nov13_cmake
    assert 'list(APPEND core_sources "${eden_vfs_maintained}")' in nov13_cmake
# Native PS5 PS5 VFS descriptor-budget owner (EglantinePS5 47b54bb)
# remains outside the 337-file frozen historical F07 audit.
ps5_vfs128_owner = "eden-core/src/core/file_sys/vfs/vfs_real.cpp"
ps5_vfs128_present = {ps5_vfs128_owner} & set(physical_all)
if ps5_vfs128_selected:
    assert ps5_vfs128_present == {ps5_vfs128_owner}
    raw = (active / ps5_vfs128_owner).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "097335e42a0f569a51f58417f0cfd6239f474136", ("Selected PS5 VFS descriptor owner drift", actual)
    assert '"file_sys/vfs/vfs_real.cpp"' in nov13_cmake
    assert 'setenv("MESA_DISK_CACHE_DATABASE_NUM_PARTS", "4", 0)' in (
        root / "headless/main.cpp").read_text()
else:
    assert not ps5_vfs128_present
# One native-only HLE peer source, outside frozen F07 337 owners.
ns2_ipc_owner = "eden-threading/src/core/hle/kernel/k_server_session.cpp"
ns2_ipc_present = {ns2_ipc_owner} & set(physical_all)
if ps5_ns2_ipc_selected:
    assert ns2_ipc_present == {ns2_ipc_owner}
    for relative, expected in ((ns2_ipc_owner, "5bd8cd81c2bf8d32f0d65406881b8286a06ca771"),
        ("eden-threading/native-hle-overrides.cmake", "0ed9f8520019c07874c157c97ded3864c07a8a32")):
        raw = (active / relative).read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert digest == expected, ("Selected IPC source drift", relative, digest)
else:
    assert not ns2_ipc_present
print("ENCORE_PS5_NS2_IPC_PEER_OWNER_PASS", f"owners={len(ns2_ipc_present)}")
print("ENCORE_PS5_VFS128_FD_BUDGET_OWNER_PASS", f"owners={len(ps5_vfs128_present)}")

print("ENCORE_POST_F07_VFS_BOUNDS_OWNER_PASS", f"owners={len(post_f07_vfs_present)}")
# NCA #119: two additional exact post-F07 source owners.
post_f07_nca_receipts = {
    "eden-core/src/core/file_sys/fssystem/fssystem_integrity_verification_storage.cpp": "5afc754433f6276ffd80bc0af418d31cf5cf496c",
    "eden-core/src/core/file_sys/fssystem/fssystem_nca_file_system_driver.cpp": "f6ceeb8d18b88b850c19b86cc3823e40ce5b9afa"
}
post_f07_nca_present = set(post_f07_nca_receipts) & set(physical_all)
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_nca_present
else:
    assert post_f07_nca_present == set(post_f07_nca_receipts)
    for relative, blob in post_f07_nca_receipts.items():
        raw = (active / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == blob
    assert 'list(REMOVE_ITEM core_sources "${eden_vfs_relative}")' in nov13_cmake
    assert all('"' + relative.removeprefix("eden-core/src/core/") + '"' in nov13_cmake
               for relative in post_f07_nca_receipts)
print("ENCORE_POST_F07_NCA_OWNER_PASS", f"owners={len(post_f07_nca_present)}")
post_f07_romfs_receipt = "eden-core/src/core/file_sys/romfs.cpp"
post_f07_romfs_present = {post_f07_romfs_receipt} & set(physical_all)
if gpu_table_vendor_pin == "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864":
    assert not post_f07_romfs_present
else:
    assert post_f07_romfs_present == {post_f07_romfs_receipt}
    raw_romfs = (active / post_f07_romfs_receipt).read_bytes()
    assert hashlib.sha1(b"blob " + str(len(raw_romfs)).encode() + bytes([0]) + raw_romfs).hexdigest() == "51eb401e5f2e3a0deefc5fc0e4cc30b0f4b8e4a3"
    assert '"file_sys/romfs.cpp"' in nov13_cmake
print("ENCORE_POST_F07_ROMFS_OWNER_PASS", f"owners={len(post_f07_romfs_present)}")
# FC27 compiler owners are post-F07 maintained overrides, not additions to
# the immutable 337-path historical catalogue. Keep exact blobs and engine
# selection receipts so a new path cannot be hidden by merely changing count.
fc27_ssa_receipts = {
    "eden-shader/include/shader_recompiler/frontend/ir/basic_block.h":
        "0a23d1ce0f43524e6195bd8219349ef632cfb719",
    "eden-shader/src/shader_recompiler/ir_opt/ssa_rewrite_pass.cpp":
        "26c42a9900256e5573735394753c1d5264611664",
}
fc27_ssa_present = set(fc27_ssa_receipts) & set(physical_all)
fc27_compiler_pins = {
    "b9f6052a65ef01e23ca4a46ba1654ed3a58cf181",
    "76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3",
    "6f4bb38594b273fe7cc4fba960dfe62cdb9f508e",
    "4572e581d011c444fd59428d5c042098f05dcfca",
    "f7ee793f1ee1bb1c2b1a35f68073844163658262",
    "3f019c64c2907ac3e84baa9b6200de8898f30636",
    "f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6",
}
if gpu_table_vendor_pin in fc27_compiler_pins or gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or fc27_p1_vendor:
    assert fc27_ssa_present == set(fc27_ssa_receipts)
    for relative, blob in fc27_ssa_receipts.items():
        raw = (active / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == blob
    assert 'set(EDEN_FC27_SSA_HEADER' in nov13_cmake
    assert 'set(EDEN_FC27_SSA_SOURCE' in nov13_cmake
    assert 'list(REMOVE_ITEM eden_fc27_ssa_sources "ir_opt/ssa_rewrite_pass.cpp")' in nov13_cmake
else:
    assert not fc27_ssa_present, ("Unexpected FC27 SSA owners", sorted(fc27_ssa_present))
print("ENCORE_FC27_SSA_OWNER_PASS", f"owners={len(fc27_ssa_present)}")

# The failed-search-pruning graph adds one further maintained source only at
# vendor 76c5efe. The BFS header path predates it and is already catalogued.
fc27_ssbo_receipts = {
    "eden-shader/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp":
        "41ad0f5cef1e070e552b43ea49648d5e74f10bad",
}
fc27_ssbo_present = set(fc27_ssbo_receipts) & set(physical_all)
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3", "6f4bb38594b273fe7cc4fba960dfe62cdb9f508e", "4572e581d011c444fd59428d5c042098f05dcfca", "f7ee793f1ee1bb1c2b1a35f68073844163658262", "3f019c64c2907ac3e84baa9b6200de8898f30636", "f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} or fc27_p1_vendor:
    assert fc27_ssbo_present == set(fc27_ssbo_receipts)
    for relative, blob in fc27_ssbo_receipts.items():
        raw = (active / relative).read_bytes()
        actual = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw
        ).hexdigest()
        if (relative.endswith("global_memory_to_storage_buffer_pass.cpp") and
            actual == "602d45b4d2ad872b138d62ce05f379b5e1103602"):
            selected = raw.decode("utf-8")
            newer = "    case IR::Opcode::GlobalAtomicExchange32:\n    case IR::Opcode::GlobalAtomicCompareExchange32:\n    case IR::Opcode::GlobalAtomicIAdd64:\n"
            earlier = "    case IR::Opcode::GlobalAtomicExchange32:\n    case IR::Opcode::GlobalAtomicIAdd64:\n"
            assert newer in selected
            historical = selected.replace(newer, earlier, 1).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            print("ENCORE_FC27_SSBO_CAS32_EXACT_REVERSE_PASS")
        assert actual == blob, ("FC27 SSBO source drift", relative, actual, blob)
    assert 'set(EDEN_FC27_SSBO_SOURCE' in nov13_cmake
    assert 'list(REMOVE_ITEM eden_fc27_ssbo_sources "ir_opt/global_memory_to_storage_buffer_pass.cpp")' in nov13_cmake
else:
    assert not fc27_ssbo_present, ("Unexpected FC27 SSBO owner", sorted(fc27_ssbo_present))
print("ENCORE_FC27_SSBO_OWNER_PASS", f"owners={len(fc27_ssbo_present)}")

# Eglantine #374 / vendor #147 adds one maintained descriptor-table header
# after the frozen F07 inventory. It is selected by EDEN_SMALL_VECTOR_ROOT's
# eden-core/src include overlay and must be classified explicitly.
fc27_descriptor_receipts = {
    "eden-core/src/video_core/texture_cache/descriptor_table.h":
        "be14d3396ff3871ceed46cb8499e9cfb546719de",
}
fc27_descriptor_present = set(fc27_descriptor_receipts) & set(physical_all)
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"6f4bb38594b273fe7cc4fba960dfe62cdb9f508e", "4572e581d011c444fd59428d5c042098f05dcfca", "f7ee793f1ee1bb1c2b1a35f68073844163658262", "3f019c64c2907ac3e84baa9b6200de8898f30636", "f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} or fc27_p1_vendor:
    assert fc27_descriptor_present == set(fc27_descriptor_receipts)
    for relative, blob in fc27_descriptor_receipts.items():
        raw = (active / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == blob
    assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_SMALL_VECTOR_ROOT}")' in nov13_cmake
else:
    assert not fc27_descriptor_present, ("Unexpected FC27 descriptor owner", sorted(fc27_descriptor_present))
print("ENCORE_FC27_DESCRIPTOR_OWNER_PASS", f"owners={len(fc27_descriptor_present)}")

# Vendor scalar-cache qualification also carries a standalone include-tree
# copy. Encore selects the richer src/ Task/Mesh-compatible header instead;
# classify this exact duplicate as unselected rather than rewriting F07 counts.
fc27_scalar_unselected_receipts = {
    "eden-shader/include/shader_recompiler/backend/spirv/spirv_emit_context.h":
        "68e14b3a0c4ae990933652baa51183a51eee4f81",
}
fc27_scalar_unselected_present = set(fc27_scalar_unselected_receipts) & set(physical_all)
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"6f4bb38594b273fe7cc4fba960dfe62cdb9f508e", "4572e581d011c444fd59428d5c042098f05dcfca", "f7ee793f1ee1bb1c2b1a35f68073844163658262", "3f019c64c2907ac3e84baa9b6200de8898f30636", "f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1", "b1bb49abea63b6664e0945df8431e10aac128c2f", "89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} or fc27_p1_vendor:
    assert fc27_scalar_unselected_present == set(fc27_scalar_unselected_receipts)
    for relative, blob in fc27_scalar_unselected_receipts.items():
        raw = (active / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == blob
    assert "eden-shader/include/shader_recompiler/backend/spirv/spirv_emit_context.h" not in nov13_cmake
    scalar_gate = (root / ".github/workflows/spirv-scalar-engine-host.yml").read_text()
    assert "vendor/encore-active/eden-shader/src/shader_recompiler/backend/spirv/spirv_emit_context.h" in scalar_gate
    assert "844a118358c874b0666aebda116c1d6a0c9a8ceb" in scalar_gate
else:
    assert not fc27_scalar_unselected_present
print("ENCORE_FC27_SCALAR_DUPLICATE_UNSELECTED_PASS",
      f"owners={len(fc27_scalar_unselected_present)}", "selected_src_header=1")

# Exact post-F07 receipt for the combined vendor candidates. Earlier vendor
# checkouts remain historically strict; do not count new ABI owners as F07.
pair_receipt = json.loads((root / "docs/audits/NOV15_FC27_NS2_VENDOR_PAIR_SOURCE_RECEIPT.json").read_text())
assert pair_receipt["schema_version"] == 1 and pair_receipt["hardware_qualified"] is False
pair_new_owners = set(pair_receipt["new_owners"])
assert len(pair_new_owners) == 2 and len(pair_receipt["files"]) == 14
pair_present = pair_new_owners & set(physical_all)
# Preserve all 14 exact source blobs for the merged FC27 runtime owner
# graph. The updated BufferCache/TextureCache/Vulkan ABIs are qualified as a
# complete set here, not inferred from their parent's commit SHA.
merged_fc27_pair_receipts = dict(pair_receipt["files"])
merged_fc27_pair_receipts.update({
    "eden-core/src/video_core/buffer_cache/buffer_cache.h": "41239f19b9e16741d49e31145c504e0086b1095e",
    "eden-core/src/video_core/buffer_cache/buffer_cache_base.h": "716634290574ed4dfc8fd3be0d0ea0ad582980f8",
    "eden-core/src/video_core/gpu_gl_native.cpp": "8abd4f3652b4a10f27281a2fd43a3764bd6d5c6e",
    "eden-core/src/video_core/gpu_gl_native_dev.cpp": "091431333f6f05e7e81c691051d64771cab4a5dd",
    "eden-core/src/video_core/gpu_vulkan.cpp": "842a0289f75bc2a0763285173e4616060348ec22",
    "eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h": "6467fd4d704de6b77deb7e6cba4b8e33f70f5a08",
    "eden-vulkan/vulkan_rasterizer.cpp": "71d097b9a83028dfad9370792c905bb3bfccfd5a",
    "ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "3397cd39a3d35c1255802c4c3862584530f15cfe",
})
if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    # Keep the frozen Nov15 receipt immutable; only the selected runtime
    # successor carries the reviewed Ampere lowering from vendor af32/bfdf.
    merged_fc27_pair_receipts["ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h"] = "9169e95ec14559aa6466c68b7d1e1cd3f9e69557"
current_pair_successor_blobs = {
    "eden-core/src/video_core/buffer_cache/buffer_cache.h": "09e1578dec6dcbcb0b8f54d4bb819b71d0eed972",
    "eden-core/src/video_core/buffer_cache/buffer_cache_base.h": "bd424e728182500b573a4cc4cf07987ddc4cbdc3",
    "eden-core/src/video_core/gpu_gl_native.cpp": "8abd4f3652b4a10f27281a2fd43a3764bd6d5c6e",
    "eden-core/src/video_core/gpu_gl_native_dev.cpp": "091431333f6f05e7e81c691051d64771cab4a5dd",
    "eden-core/src/video_core/gpu_vulkan.cpp": "842a0289f75bc2a0763285173e4616060348ec22",
    "eden-vulkan/vulkan_rasterizer.cpp": "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35",
    "ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "3397cd39a3d35c1255802c4c3862584530f15cfe"
}
if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    current_pair_successor_blobs["ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h"] = "9169e95ec14559aa6466c68b7d1e1cd3f9e69557"
latest_pair_successor_blobs = dict(current_pair_successor_blobs)
latest_pair_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache.h"] = (
    "505ee80a37d5991b7925019282e71926c1648e02"
)
# Vendor #189 changes ONLY the selected BufferCache source query API. Preserve
# prior file receipts; pin the new exact blob without accepting unknown drift.
native_range_api_pair_successor_blobs = dict(latest_pair_successor_blobs)
native_range_api_pair_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache.h"] = (
    "c6bab56cbd4e58458d010e423d74df9f933a8f8d"
)
shared_storage32_pair_successor_blobs = dict(native_range_api_pair_successor_blobs)
shared_storage32_pair_successor_blobs["eden-core/src/video_core/buffer_cache/buffer_cache_base.h"] = (
    "63ef9b07b37bdc4bc9588dd77639358010e545dc"
)
if fc27_deferred_selected:
    native_range_api_pair_successor_blobs["eden-vulkan/vulkan_rasterizer.cpp"] = "38d5630570675088a0620ef533112bb314a40ae8"
if gpu_table_vendor_pin in {pair_receipt["selected_vendor"], "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or fc27_p1_vendor:
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
        source_path = active / path
        raw = source_path.read_bytes()
        if fc27_p1_vendor:
            # Compare all fourteen merged native owners against immutable blobs.
            # Known post-merge successors are reversed only on this audit copy,
            # each behind an exact full-source SHA and byte-identical predecessor.
            data = (active / path).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
            data, actual = strict_completion_predecessor(path, data)
            stabilization_pair_blobs = {
                "eden-core/overrides/core/gpu_dirty_memory_manager.h": "7769e314fbefeb8393e6d11b115c88bc0a8a0e58",
                "eden-core/src/video_core/buffer_cache/buffer_cache.h": ("4ce33d21debc33c9625129cbd545bf9b1c084272" if shipping_vendor == "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e" else "7f07e392ea0cc828d862da29d32ada1ebc3966aa"),
                "eden-core/src/video_core/gpu_vulkan.cpp": "f083c985451563dcfe387d1bc61f54bd02ed762e",
            }
            if stabilization_selected and path in stabilization_pair_blobs:
                assert actual == stabilization_pair_blobs[path], ("Stabilization pair owner drift", path, actual)
                continue
            if path == "eden-core/src/video_core/buffer_cache/buffer_cache.h" and actual == "6aa9754506ee82b4d25a4e36d4f3be646a62456b":
                successor = "    if (!IsRegionGpuModified(aligned_start, aligned_end - aligned_start)) {\n        // WriteMemory's clean-page branch does exactly this mark. Re-entering\n        // it would scan the same GPU-modified ranges again under the buffer\n        // cache mutex, even though this full-page query already proved that\n        // no GPU-owned sibling bytes need a download.\n        memory_tracker.MarkRegionAsCpuModified(device_addr, size);\n        return;\n    }"
                predecessor = "    if (!IsRegionGpuModified(aligned_start, aligned_end - aligned_start)) {\n        WriteMemory(device_addr, size);\n        return;\n    }"
                text = data.decode("utf-8")
                assert text.count(successor) == 1, "Unexpected clean-page BufferCache change"
                data = text.replace(successor, predecessor, 1).encode("utf-8")
                actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
                assert actual == "6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b", ("Clean-page inventory predecessor drift", actual)
            if path == "eden-core/src/video_core/buffer_cache/buffer_cache.h" and actual == "6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b":
                lines = data.decode("utf-8").split("\n")
                reverse = (
                    (294, ["bool BufferCache<P>::DMACopy(","    GPUVAddr src_address, GPUVAddr dest_address, u64 amount, bool* gpu_written,","    boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest) {","    if (gpu_written_dest) {","        gpu_written_dest->clear();","    }","    // FindBuffer and SynchronizeBuffer accept u32 byte spans. Never truncate","    // a wider DMA request: the caller can take its ordinary software path.","    // Reject empty copies before dirty-range bookkeeping as well."], ["bool BufferCache<P>::DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,","                             bool* gpu_written) {","    // FindBuffer and SynchronizeBuffer accept u32 byte spans. Never truncate","    // a wider DMA request: the caller can take its ordinary software path.","    // Reject empty copies before dirty-range bookkeeping as well."]),
                    (325, ["    // vkCmdCopyBuffer forbids overlapping source and destination DEVICE","    // memory (VUID-vkCmdCopyBuffer-pRegions-00117). Distinct GMMU virtual","    // addresses can alias one physical allocation, and different VkBuffer","    // handles do not make those overlapping memory accesses legal.","    // Reject BEFORE dirty-range bookkeeping, ClearDownload, or GPU commands:","    // MaxwellDMA will read the authoritative source and snapshot the alias.","    // Compare distances rather than forming a potentially overflowing end.","    const DAddr source = *cpu_src_address;","    const DAddr destination = *cpu_dest_address;","    if ((source <= destination && destination - source < amount) ||","        (destination < source && source - destination < amount)) {","        return false;","    }","    const bool source_dirty = IsRegionRegistered(*cpu_src_address, amount);","    const bool dest_dirty = IsRegionRegistered(*cpu_dest_address, amount);","    if (!source_dirty && !dest_dirty) {"], ["    const bool source_dirty = IsRegionRegistered(*cpu_src_address, amount);","    const bool dest_dirty = IsRegionRegistered(*cpu_dest_address, amount);","    if (!source_dirty && !dest_dirty) {"]),
                    (378, ["    if (gpu_written_dest) {","        *gpu_written_dest = tmp_intervals;","    }","    for (const auto& pair : tmp_intervals) {","        gpu_modified_ranges.Add(pair.first, pair.second);","    }"], ["    for (const auto& pair : tmp_intervals) {","        gpu_modified_ranges.Add(pair.first, pair.second);","    }"]),
                    (1849, ["        // A stream near the start of physical memory may begin before","        // min_page. Subtraction in the original test then wraps around and","        // turns an ordinary backward leap into a huge invalid GPU buffer.","        // Never move begin forwards past the range we already own.","        if (begin <= min_page || add_value > begin - min_page) {","            begin = (std::min)(begin, min_page);","            device_addr = Core::DEVICE_PAGESIZE;","            return;","        }"], ["        if (add_value > begin - min_page) {","            begin = min_page;","            device_addr = Core::DEVICE_PAGESIZE;","            return;","        }"]),
                )
                for index, newer, earlier in reversed(reverse):
                    assert lines[index:index + len(newer)] == newer, ("Merged owner hunk drift", path)
                    lines[index:index + len(newer)] = earlier
                historical = "\n".join(lines).encode()
                actual = hashlib.sha1(
                    b"blob " + str(len(historical)).encode() + bytes([0]) + historical
                ).hexdigest()
                assert actual == "41239f19b9e16741d49e31145c504e0086b1095e", ("Merged owner predecessor drift", path, actual)
                print("ENCORE_MERGED_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
            if path == "eden-core/src/video_core/buffer_cache/buffer_cache_base.h" and actual == "fd9708571ef61c83c399042a5200c87b2e3784d6":
                lines = data.decode("utf-8").split("\n")
                reverse = (
                    (326, ["    /// gpu_written_dest names the exact destination subranges whose newest bytes stay GPU-owned.","    bool DMACopy(","        GPUVAddr src_address, GPUVAddr dest_address, u64 amount, bool* gpu_written = nullptr,","        boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest = nullptr);","","    bool DMAClear(GPUVAddr src_address, u64 amount, u32 value);",""], ["    /// A caller must not re-upload the destination texture from stale guest memory.","    bool DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,","                 bool* gpu_written = nullptr);","","    bool DMAClear(GPUVAddr src_address, u64 amount, u32 value);",""]),
                )
                for index, newer, earlier in reversed(reverse):
                    assert lines[index:index + len(newer)] == newer, ("Merged owner hunk drift", path)
                    lines[index:index + len(newer)] = earlier
                historical = "\n".join(lines).encode()
                actual = hashlib.sha1(
                    b"blob " + str(len(historical)).encode() + bytes([0]) + historical
                ).hexdigest()
                assert actual == "716634290574ed4dfc8fd3be0d0ea0ad582980f8", ("Merged owner predecessor drift", path, actual)
                print("ENCORE_MERGED_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
            if path == "eden-core/src/video_core/gpu_vulkan.cpp" and actual == "90b8f8c99878b21558b3996e8b1e95a5fc6ad9a6":
                lines = data.decode("utf-8").split("\n")
                reverse = (
                    (116, ["#if defined(PS5_NATIVE)","        // Queue retirement on the existing GPU worker. Only the worker","        // reads/mutates the channels map: the NVDRV service thread must not","        // race GPU::BindChannel while looking up a channel on FD close.","        // The caller keeps to_release alive until this synchronous barrier","        // completes. Verify the exact owner epoch on the worker side.","        const s32 channel_id = to_release.bind_id;","        const auto* expected = &to_release;","        const u64 fence = RequestSyncOperation([this, channel_id, expected] {","            const auto it = channels.find(channel_id);","            if (it == channels.end() || it->second.get() != expected)","                return; // An old FD cannot retire a reused channel ID.","            const auto owner = it->second;","            scheduler.RetireChannel(owner.get());","            if (current_channel == owner.get()) {","                current_channel = nullptr;","                bound_channel = -1;","            }","            if (owner->initialized)","                renderer->ReadRasterizer()->ReleaseChannel(owner->bind_id);","            channels.erase(it);","        });","        gpu_thread.TickGPU(is_async);","        WaitForSyncOperation(fence);","#else","        // Host/non-PS5 scheduler has no native epoch-retirement API.","        // Preserve its original behavior; no platform-wide ABI change.","        UNIMPLEMENTED();","#endif","    }",""], ["        UNIMPLEMENTED();","    }",""]),
                    (182, ["        // Publish a fence only AFTER the queue owns its callback. If","        // allocating this node throws, no fence is skipped: subsequent waits","        // must still be reachable by TickWork's completed-request counter.","        sync_requests.emplace_back(std::forward<Func>(action));","        return ++last_sync_fence;","    }",""], ["        const u64 fence = ++last_sync_fence;","        sync_requests.emplace_back(std::forward<Func>(action));","        return fence;","    }",""]),
                    (196, ["        while (!shutting_down.load(std::memory_order_relaxed) &&","               CurrentSyncRequestFence() < fence) {","            // A failed GPU worker cannot advance this fence. Preserve the","            // published exception for every waiter instead of hanging the","            // launcher/guest-stop path indefinitely.","            if (auto failure = ::Eden::PeekGpuFailure()) {","                std::rethrow_exception(failure);","            }","            sync_request_cv.wait_for(lck, std::chrono::milliseconds(100));","        }","        if (auto failure = ::Eden::PeekGpuFailure()) {","            std::rethrow_exception(failure);","        }","    }","","    void WaitForIdle() {"], ["        sync_request_cv.wait(lck, [this, fence] { return CurrentSyncRequestFence() >= fence; });","    }","","    void WaitForIdle() {"]),
                    (223, ["            // Keep the RAII lock's ownership state consistent if a GPU","            // callback throws. Unlocking the raw mutex left lck owning an","            // already-unlocked mutex during exception unwinding.","            lck.unlock();","            request();","            current_sync_fence.fetch_add(1, std::memory_order_release);","            lck.lock();","            sync_request_cv.notify_all();"], ["            sync_request_mutex.unlock();","            request();","            current_sync_fence.fetch_add(1, std::memory_order_release);","            sync_request_mutex.lock();","            sync_request_cv.notify_all();"]),
                    (298, ["        const u64 fence = RequestSyncOperation([this, raster_area]() {","            renderer->ReadRasterizer()->FlushRegion(raster_area.start_address, raster_area.end_address - raster_area.start_address);","        });","        gpu_thread.TickGPU(is_async);"], ["        const u64 fence = RequestSyncOperation([this, &raster_area]() {","            renderer->ReadRasterizer()->FlushRegion(raster_area.start_address, raster_area.end_address - raster_area.start_address);","        });","        gpu_thread.TickGPU(is_async);"]),
                    (416, ["    // A guest may close an NVDRV GPU FD before its first successful bind.","    // ReleaseChannel compares this pointer even for an uninitialized owner.","    Tegra::Control::ChannelState* current_channel{};","    s32 bound_channel{-1};","","    std::deque<size_t> free_swap_counters;"], ["    Tegra::Control::ChannelState* current_channel;","    s32 bound_channel{-1};","","    std::deque<size_t> free_swap_counters;"]),
                )
                for index, newer, earlier in reversed(reverse):
                    assert lines[index:index + len(newer)] == newer, ("Merged owner hunk drift", path)
                    lines[index:index + len(newer)] = earlier
                historical = "\n".join(lines).encode()
                actual = hashlib.sha1(
                    b"blob " + str(len(historical)).encode() + bytes([0]) + historical
                ).hexdigest()
                assert actual == "842a0289f75bc2a0763285173e4616060348ec22", ("Merged owner predecessor drift", path, actual)
                print("ENCORE_MERGED_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
            if path == "eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h" and actual == "6e0bf7ab2a3a2147f9db0c630070db30d9b35d56":
                lines = data.decode("utf-8").split("\n")
                reverse = (
                    (65, ["                           Scheduler& scheduler, Tegra::MemoryManager* const& gpu_memory);","","    bool BufferCopy(GPUVAddr start_address, GPUVAddr end_address, u64 amount) override;",""], ["                           Scheduler& scheduler);","","    bool BufferCopy(GPUVAddr start_address, GPUVAddr end_address, u64 amount) override;",""]),
                    (86, ["    // The GPU address space changes on channel binds. Reference the","    // rasterizer's active pointer, not a stale construction-time channel.","    Tegra::MemoryManager* const& gpu_memory;","};","","class RasterizerVulkan final : public VideoCore::RasterizerInterface,"], ["};","","class RasterizerVulkan final : public VideoCore::RasterizerInterface,"]),
                    (222, ["    void UpdateBlending(Tegra::Engines::Maxwell3D::Regs& regs,","                        const GraphicsPipeline* pipeline);","    void UpdateColorWriteEnable(Tegra::Engines::Maxwell3D::Regs& regs);","","    void UpdateVertexInput(Tegra::Engines::Maxwell3D::Regs& regs);"], ["    void UpdateBlending(Tegra::Engines::Maxwell3D::Regs& regs);","    void UpdateColorWriteEnable(Tegra::Engines::Maxwell3D::Regs& regs);","","    void UpdateVertexInput(Tegra::Engines::Maxwell3D::Regs& regs);"]),
                    (269, ["","#ifdef PS5_NATIVE","    // Cached once per native rasterizer, never queried on each hot-path QMD."], ["    vk::Event wfi_event;","","#ifdef PS5_NATIVE","    // Cached once per native rasterizer, never queried on each hot-path QMD."]),
                    (280, ["    u32 last_color_output_mask{};","    bool mesh_draw{}; ///< the draw being prepared uses a task/mesh pipeline","};",""], ["    bool mesh_draw{}; ///< the draw being prepared uses a task/mesh pipeline","};",""]),
                )
                for index, newer, earlier in reversed(reverse):
                    assert lines[index:index + len(newer)] == newer, ("Merged owner hunk drift", path)
                    lines[index:index + len(newer)] = earlier
                historical = "\n".join(lines).encode()
                actual = hashlib.sha1(
                    b"blob " + str(len(historical)).encode() + bytes([0]) + historical
                ).hexdigest()
                assert actual == "6467fd4d704de6b77deb7e6cba4b8e33f70f5a08", ("Merged owner predecessor drift", path, actual)
                print("ENCORE_MERGED_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
            if (path == "eden-vulkan/vulkan_rasterizer.cpp" and
                actual in {"0633e3cf41c615f46791d3943ff40ac22399b047", "f67815618d25657dcf64a87944b0c0bc5c2d8993"}):
                import sys
                sys.path.insert(0, str(root / "vendor" / "tests"))
                from native_msaa_handle_receipt import restore_integrated_rasterizer
                historical = restore_integrated_rasterizer(data.decode("utf-8")).encode()
                actual = hashlib.sha1(
                    b"blob " + str(len(historical)).encode() + bytes([0]) + historical
                ).hexdigest()
                assert actual == "71d097b9a83028dfad9370792c905bb3bfccfd5a"
                print("ENCORE_MERGED_EXACT_REVERSE_PASS", path, "hunks=16")
            assert actual == merged_fc27_pair_receipts[path], (path, actual)
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
                native_range_api_pair_successor_blobs if gpu_table_vendor_pin in {"2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}
                else latest_pair_successor_blobs if gpu_table_vendor_pin in {"945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"}
                else current_pair_successor_blobs
            ).get(path, blob)
            assert actual == expected_blob, (path, actual, expected_blob)
            continue
        if gpu_table_vendor_pin in gpu_dirty_include_successors and path in gpu_dirty_include_owners:
            # Vendor #175 changes only compile ownership here. Reconstruct the
            # exact pre-#175 blob in memory before applying the frozen Nov15
            # source receipt; unknown/duplicate include drift fails closed.
            assert raw.count(gpu_dirty_include) == 1, path
            historical = raw.replace(gpu_dirty_include, b"", 1)
            header = b"blob " + str(len(historical)).encode() + b"\0"
            actual = hashlib.sha1(header + historical).hexdigest()
        else:
            actual = subprocess.check_output(
                ["git", "hash-object", str(source_path)], text=True).strip()
        if (gpu_table_vendor_pin in {"42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} and
                path == "eden-vulkan/vulkan_rasterizer.cpp"):
            assert actual == "aa3ff8baf97f075d1adf44a9d19335c89403c8e1", path
        else:
            assert actual == blob, path
else:
    assert not pair_present
print("ENCORE_NOV15_VENDOR_PAIR_OWNER_RECEIPT_PASS", f"new_owners={len(pair_present)}", "hardware=unverified")

drawtexture_receipts = {
    "eden-vulkan/blit_image.cpp": "bbde031a184b93745fa0449aef74f351355fb70d",
    "eden-vulkan/include/video_core/renderer_vulkan/blit_image.h":
        "81eda086f50e04d3e1537aebff404a6097a07069",
}
drawtexture_present = set(drawtexture_receipts) & set(physical_all)
if gpu_table_vendor_pin in {"42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6", "edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or fc27_p1_vendor:
    assert drawtexture_present == set(drawtexture_receipts)
    for path, blob in drawtexture_receipts.items():
        raw = (active / path).read_bytes()
        actual = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw
        ).hexdigest()
        if path == "eden-vulkan/blit_image.cpp" and actual == "4ba93afb6594213d5bde82be2693f0e08cb1cd63":
            lines = raw.decode("utf-8").split("\n")
            reverse = (
                (18, ["#include \"video_core/host_shaders/convert_abgr8_to_x8d24_frag_spv.h\"","#include \"video_core/host_shaders/convert_x8d24_to_abgr8_frag_spv.h\"","#include \"video_core/host_shaders/convert_abgr8_to_d32f_frag_spv.h\"","#include \"video_core/host_shaders/convert_d24s8_to_abgr8_frag_spv.h\"","#include \"video_core/host_shaders/convert_d32f_to_abgr8_frag_spv.h\""], ["#include \"video_core/host_shaders/convert_abgr8_to_d32f_frag_spv.h\"","#include \"video_core/host_shaders/convert_d24s8_to_abgr8_frag_spv.h\"","#include \"video_core/host_shaders/convert_d32f_to_abgr8_frag_spv.h\""]),
                (631, ["      convert_abgr8_to_x8d24_frag(BuildShader(device, CONVERT_ABGR8_TO_X8D24_FRAG_SPV)),","      convert_x8d24_to_abgr8_frag(BuildShader(device, CONVERT_X8D24_TO_ABGR8_FRAG_SPV)),","      convert_abgr8_to_d32f_frag(BuildShader(device, CONVERT_ABGR8_TO_D32F_FRAG_SPV)),","      convert_d32f_to_abgr8_frag(BuildShader(device, CONVERT_D32F_TO_ABGR8_FRAG_SPV)),","      convert_d24s8_to_abgr8_frag(BuildShader(device, CONVERT_D24S8_TO_ABGR8_FRAG_SPV)),"], ["      convert_abgr8_to_d32f_frag(BuildShader(device, CONVERT_ABGR8_TO_D32F_FRAG_SPV)),","      convert_d32f_to_abgr8_frag(BuildShader(device, CONVERT_D32F_TO_ABGR8_FRAG_SPV)),","      convert_d24s8_to_abgr8_frag(BuildShader(device, CONVERT_D24S8_TO_ABGR8_FRAG_SPV)),"]),
                (871, ["void BlitImageHelper::ConvertABGR8ToX8D24(const Framebuffer* dst_framebuffer,","                                          const ImageView& src_image_view) {","    ConvertPipelineDepthTargetEx(convert_abgr8_to_x8d24_pipeline, dst_framebuffer->RenderPass(),","                                 convert_abgr8_to_x8d24_frag);","    Convert(*convert_abgr8_to_x8d24_pipeline, dst_framebuffer, src_image_view);","}","","void BlitImageHelper::ConvertX8D24ToABGR8(const Framebuffer* dst_framebuffer,","                                          const ImageView& src_image_view) {","    ConvertPipelineEx(convert_x8d24_to_abgr8_pipeline, dst_framebuffer->RenderPass(),","                      convert_x8d24_to_abgr8_frag, true, false);","    Convert(*convert_x8d24_to_abgr8_pipeline, dst_framebuffer, src_image_view);","}","","void BlitImageHelper::ConvertABGR8ToD24S8(const Framebuffer* dst_framebuffer,","                                          const ImageView& src_image_view) {","    if (!device.IsExtShaderStencilExportSupported()) {"], ["void BlitImageHelper::ConvertABGR8ToD24S8(const Framebuffer* dst_framebuffer,","                                          const ImageView& src_image_view) {","    if (!device.IsExtShaderStencilExportSupported()) {"]),
            )
            for index, newer, earlier in reversed(reverse):
                assert lines[index:index + len(newer)] == newer, ("X8D24 receipt hunk drift", path)
                lines[index:index + len(newer)] = earlier
            historical = "\n".join(lines).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            assert actual == "bbde031a184b93745fa0449aef74f351355fb70d", ("X8D24 receipt predecessor drift", path, actual)
            print("ENCORE_X8D24_DRAW_RECEIPT_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
        if path == "eden-vulkan/include/video_core/renderer_vulkan/blit_image.h" and actual == "a38cfcf655adcb8ceebfce955b39a2312a239768":
            lines = raw.decode("utf-8").split("\n")
            reverse = (
                (115, ["    void ConvertABGR8ToX8D24(const Framebuffer* dst_framebuffer, const ImageView& src_image_view);","","    void ConvertX8D24ToABGR8(const Framebuffer* dst_framebuffer, const ImageView& src_image_view);","","    void ConvertABGR8ToD32F(const Framebuffer* dst_framebuffer, const ImageView& src_image_view);","","    void ConvertD32FToABGR8(const Framebuffer* dst_framebuffer, ImageView& src_image_view);"], ["    void ConvertABGR8ToD32F(const Framebuffer* dst_framebuffer, const ImageView& src_image_view);","","    void ConvertD32FToABGR8(const Framebuffer* dst_framebuffer, ImageView& src_image_view);"]),
                (237, ["    vk::ShaderModule convert_abgr8_to_x8d24_frag;","    vk::ShaderModule convert_x8d24_to_abgr8_frag;","    vk::ShaderModule convert_abgr8_to_d32f_frag;","    vk::ShaderModule convert_d32f_to_abgr8_frag;","    vk::ShaderModule convert_d24s8_to_abgr8_frag;"], ["    vk::ShaderModule convert_abgr8_to_d32f_frag;","    vk::ShaderModule convert_d32f_to_abgr8_frag;","    vk::ShaderModule convert_d24s8_to_abgr8_frag;"]),
                (294, ["    vk::Pipeline convert_abgr8_to_x8d24_pipeline;","    vk::Pipeline convert_x8d24_to_abgr8_pipeline;","    vk::Pipeline convert_abgr8_to_d32f_pipeline;","    vk::Pipeline convert_d32f_to_abgr8_pipeline;","    vk::Pipeline convert_d24s8_to_abgr8_pipeline;"], ["    vk::Pipeline convert_abgr8_to_d32f_pipeline;","    vk::Pipeline convert_d32f_to_abgr8_pipeline;","    vk::Pipeline convert_d24s8_to_abgr8_pipeline;"]),
            )
            for index, newer, earlier in reversed(reverse):
                assert lines[index:index + len(newer)] == newer, ("X8D24 receipt hunk drift", path)
                lines[index:index + len(newer)] = earlier
            historical = "\n".join(lines).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            assert actual == "81eda086f50e04d3e1537aebff404a6097a07069", ("X8D24 receipt predecessor drift", path, actual)
            print("ENCORE_X8D24_DRAW_RECEIPT_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
        assert actual == blob, (path, actual, blob)
else:
    assert not drawtexture_present
print("ENCORE_EDEN4559_POST_F07_OWNER_PASS", f"owners={len(drawtexture_present)}")

ns2_early_hle_receipts = {
    "ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "df3edaf42d0596c69eaa6fea18b33fc02c6bff3c",
    "ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "903190e43dc10a0ca5067ca563d6d944e84ae5d2",
    "ns2-runtime/hle/core/hle/service/am/service/graphics_scaling_parameters_functions.h": "bded1f902ac1a0995d71ffc3f425f33ba781b198",
    "ns2-runtime/hle/core/hle/service/hid/hid_server.cpp": "c00ec7de86402abdd6693092f3e57917e80ab7ec",
    "ns2-runtime/hle/core/hle/service/hid/hid_server.h": "cdc83734e27d5478f1981126950dd1f3f7a91227",
}
# The native Switch 2 appletOE command-10 owner was added after the
# frozen 337-source inventory; classify and seal it with the early AM/HID
# overlays rather than silently inflating the historical source total.
native_applet_proxy_path = "ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp"
if native_applet_proxy_path in set(physical_all):
    assert '"hle/service/am/service/application_proxy_service.cpp"' in kernel_select
    ns2_early_hle_receipts[native_applet_proxy_path] = (
        "1e6f2592e34845d9b9b3aa3d152c78c4fed66639"
    )
if fc27_p1_vendor:
    # Current production appletOE inherits two approved C++ owners and ships
    # its two extension headers. Seal each exact Git blob before subtracting
    # these additions from the frozen 337-source native review.
    ns2_early_hle_receipts.update({
        "ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "d6b14213485b56aefbd9736c8f0e6a2a2b4fa38c",
        "ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "03cf286dd642a3e517c7fa4950850603038c6d6b",
        native_applet_proxy_path: ("b1acd90a74bceb03c900a505e217f484f6ecd18f" if fc27_p1_applet_macro_fix else "849baf7bfe243734ee49c9e7617462665746d5f1"),
        "ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "e534f8da6c4b88fe042cff8098dd386dcc29a8e4",
        "ns2-runtime/hle/core/hle/service/am/service/performance_functions.h": "be4ce2bee44ac77e4f8b8bbe9e18cad11ab47b19",
    })
# Post-F07 Lichii NS2 AM table synchronization: preserve previous owners
# and qualify only source files that actually changed at this exact gitlink.
if subprocess.check_output(
    ["git", "-C", str(root/"vendor"), "rev-parse", "HEAD"], text=True
).strip() in {"f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634", "ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3"}:
    ns2_early_hle_receipts.update({
        "ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp":
            "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912",
        "ns2-runtime/hle/core/hle/service/am/service/application_proxy.h":
            "ed88acba848071d6c9e2c0b080c3234925003b50",
        "ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp":
            "0d2ed417d23f11a97f91cf18e733fad6515d0756",
        "ns2-runtime/hle/core/hle/service/nx2_stub_interface.h":
            "68c087899680b8a3a764d6cd3c362b0e98237ae0",
    })
# Exact Lichii AM additional direct source owners are selected once by CMake.
if subprocess.check_output(
    ["git", "-C", str(root/"vendor"), "rev-parse", "HEAD"], text=True
).strip() in {"d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634", "ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3"}:
    ns2_early_hle_receipts.update({
        "ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
        "ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
        "ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
        "ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
        "ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
        "ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
        "ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
        "ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
    })
if gpu_table_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    ns2_early_hle_receipts[native_applet_proxy_path] = "a07dae606312e673bdbff5110fbf81d4ce307776"
    ns2_early_hle_receipts["ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h"] = "7aab2ba6235b33b91819ea78a006129183194194"
ns2_early_hle_present = set(ns2_early_hle_receipts) & set(physical_all)
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} or fc27_p1_vendor:
    assert ns2_early_hle_present == set(ns2_early_hle_receipts)
    for path, blob in ns2_early_hle_receipts.items():
        raw = (active / path).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        if (path == "ns2-runtime/hle/core/hle/service/hid/hid_server.cpp"
                and actual == "27182c310b7e26ed4ffa57d3ece919d1c88a12f9"):
            # Lichii NX2 HID 213/214 and command-table placeholders:
            # reverse only reviewed hunks in a copy, preserve current runtime.
            _hid_source = raw.decode("utf-8")
            _nx2_hid_reverse = (
                ("#include <fmt/ranges.h>\n#include <mutex>\n#include <cstring>\n#include <cmath>\n#include <algorithm>\n", ""),
                ("        {73, &IHidServer::StubReplyZeroed, \"SetAccelerometerParameters\"},\n        {74, &IHidServer::StubReplyZeroed, \"GetAccelerometerParameters\"},\n        {75, &IHidServer::StubReplyZeroed, \"ResetAccelerometerParameters\"},\n        {76, &IHidServer::StubReplyZeroed, \"SetAccelerometerPlayMode\"},\n        {77, &IHidServer::StubReplyZeroed, \"GetAccelerometerPlayMode\"},\n        {78, &IHidServer::StubReplyZeroed, \"ResetAccelerometerPlayMode\"},\n", "        {73, nullptr, \"SetAccelerometerParameters\"},\n        {74, nullptr, \"GetAccelerometerParameters\"},\n        {75, nullptr, \"ResetAccelerometerParameters\"},\n        {76, nullptr, \"SetAccelerometerPlayMode\"},\n        {77, nullptr, \"GetAccelerometerPlayMode\"},\n        {78, nullptr, \"ResetAccelerometerPlayMode\"},\n"),
                ("        {86, &IHidServer::StubReplyZeroed, \"StoreSixAxisSensorCalibrationParameter\"},\n", "        {86, nullptr, \"StoreSixAxisSensorCalibrationParameter\"},\n"),
                ("        {308, &IHidServer::StubReplyZeroed, \"SetSevenSixAxisSensorFusionStrength\"},\n        {309, &IHidServer::StubReplyZeroed, \"GetSevenSixAxisSensorFusionStrength\"},\n", "        {308, nullptr, \"SetSevenSixAxisSensorFusionStrength\"},\n        {309, nullptr, \"GetSevenSixAxisSensorFusionStrength\"},\n"),
                ("        {320, &IHidServer::StubReplyZeroed, \"EnableNpadImu\"}, //21.0.0+\n        {321, &IHidServer::StubReplyZeroed, \"DisableNpadImu\"}, //21.0.0+\n", "        {320, nullptr, \"EnableNpadImu\"}, //21.0.0+\n        {321, nullptr, \"DisableNpadImu\"}, //21.0.0+\n"),
                ("        {401, &IHidServer::StubReplyZeroed, \"EnableUsbFullKeyController\"},\n        {402, &IHidServer::StubReplyZeroed, \"IsUsbFullKeyControllerConnected\"},\n        {403, &IHidServer::StubReplyZeroed, \"HasBattery\"},\n        {404, &IHidServer::StubReplyZeroed, \"HasLeftRightBattery\"},\n        {405, &IHidServer::StubReplyZeroed, \"GetNpadInterfaceType\"},\n        {406, &IHidServer::StubReplyZeroed, \"GetNpadLeftRightInterfaceType\"},\n        {407, &IHidServer::StubReplyZeroed, \"GetNpadOfHighestBatteryLevel\"},\n", "        {401, nullptr, \"EnableUsbFullKeyController\"},\n        {402, nullptr, \"IsUsbFullKeyControllerConnected\"},\n        {403, nullptr, \"HasBattery\"},\n        {404, nullptr, \"HasLeftRightBattery\"},\n        {405, nullptr, \"GetNpadInterfaceType\"},\n        {406, nullptr, \"GetNpadLeftRightInterfaceType\"},\n        {407, nullptr, \"GetNpadOfHighestBatteryLevel\"},\n"),
                ("        {3000, &IHidServer::StubReplyZeroed, \"GetDebugPadGenericPadMap\"},\n        {3001, &IHidServer::StubReplyZeroed, \"SetDebugPadGenericPadMap\"},\n        {3002, &IHidServer::StubReplyZeroed, \"ResetDebugPadGenericPadMap\"},\n        {3003, &IHidServer::StubReplyZeroed, \"GetDebugPadKeyboardMap\"},\n        {3004, &IHidServer::StubReplyZeroed, \"SetDebugPadKeyboardMap\"},\n        {3005, &IHidServer::StubReplyZeroed, \"ResetDebugPadKeyboardMap\"},\n        {3006, &IHidServer::StubReplyZeroed, \"GetFullKeyGenericPadMap\"},\n        {3007, &IHidServer::StubReplyZeroed, \"SetFullKeyGenericPadMap\"},\n        {3008, &IHidServer::StubReplyZeroed, \"ResetFullKeyGenericPadMap\"},\n        {3009, &IHidServer::StubReplyZeroed, \"GetFullKeyKeyboardMap\"},\n        {3010, &IHidServer::StubReplyZeroed, \"SetFullKeyKeyboardMap\"},\n        {3011, &IHidServer::StubReplyZeroed, \"ResetFullKeyKeyboardMap\"},\n        {3012, &IHidServer::StubReplyZeroed, \"GetDebugPadGenericPadMap\"}, //21.0.0+\n        {3013, &IHidServer::StubReplyZeroed, \"SetDebugPadGenericPadMap\"}, //21.0.0+\n        {3014, &IHidServer::StubReplyZeroed, \"GetDebugPadKeyboardMap\"}, //21.0.0+\n        {3015, &IHidServer::StubReplyZeroed, \"SetDebugPadKeyboardMap\"}, //21.0.0+\n", "        {3000, nullptr, \"GetDebugPadGenericPadMap\"},\n        {3001, nullptr, \"SetDebugPadGenericPadMap\"},\n        {3002, nullptr, \"ResetDebugPadGenericPadMap\"},\n        {3003, nullptr, \"GetDebugPadKeyboardMap\"},\n        {3004, nullptr, \"SetDebugPadKeyboardMap\"},\n        {3005, nullptr, \"ResetDebugPadKeyboardMap\"},\n        {3006, nullptr, \"GetFullKeyGenericPadMap\"},\n        {3007, nullptr, \"SetFullKeyGenericPadMap\"},\n        {3008, nullptr, \"ResetFullKeyGenericPadMap\"},\n        {3009, nullptr, \"GetFullKeyKeyboardMap\"},\n        {3010, nullptr, \"SetFullKeyKeyboardMap\"},\n        {3011, nullptr, \"ResetFullKeyKeyboardMap\"},\n        {3012, nullptr, \"GetDebugPadGenericPadMap\"}, //21.0.0+\n        {3013, nullptr, \"SetDebugPadGenericPadMap\"}, //21.0.0+\n        {3014, nullptr, \"GetDebugPadKeyboardMap\"}, //21.0.0+\n        {3015, nullptr, \"SetDebugPadKeyboardMap\"}, //21.0.0+\n"),
                ("        {137, &IHidServer::StubReplyZeroed, \"Unknown137\"},\n        {140, &IHidServer::StubReplyZeroed, \"Unknown140\"},\n        {150, &IHidServer::StubReplyZeroed, \"Unknown150\"},\n        {151, &IHidServer::StubReplyZeroed, \"Unknown151\"},\n        {160, &IHidServer::StubReplyZeroed, \"Unknown160\"},\n        {213, C<&IHidServer::SendVibrationValueInMode>, \"SendVibrationValueInMode\"},\n        {214, C<&IHidServer::SendNx2VibrationValues>, \"SendVibrationValuesInMode\"},\n        {311, &IHidServer::StubReplyZeroed, \"Unknown311\"},\n        {312, &IHidServer::StubReplyZeroed, \"Unknown312\"},\n        {322, &IHidServer::StubReplyZeroed, \"Unknown322\"},\n        {323, &IHidServer::StubReplyZeroed, \"Unknown323\"},\n        {324, &IHidServer::StubReplyZeroed, \"Unknown324\"},\n        {550, &IHidServer::StubReplyZeroed, \"Unknown550\"},\n        {1005, &IHidServer::StubReplyZeroed, \"Unknown1005\"},\n        {3114, &IHidServer::StubReplyZeroed, \"Unknown3114\"},\n        {3134, &IHidServer::StubReplyZeroed, \"Unknown3134\"},\n        {3135, &IHidServer::StubReplyZeroed, \"Unknown3135\"},\n        {3136, &IHidServer::StubReplyZeroed, \"Unknown3136\"},\n        {3137, &IHidServer::StubReplyZeroed, \"Unknown3137\"},\n        {3140, &IHidServer::StubReplyZeroed, \"Unknown3140\"},\n        {3141, &IHidServer::StubReplyZeroed, \"Unknown3141\"},\n        {3142, &IHidServer::StubReplyZeroed, \"Unknown3142\"},\n        {3143, &IHidServer::StubReplyZeroed, \"Unknown3143\"},\n        {3144, &IHidServer::StubReplyZeroed, \"Unknown3144\"},\n        {3145, &IHidServer::StubReplyZeroed, \"Unknown3145\"},\n        {3146, &IHidServer::StubReplyZeroed, \"Unknown3146\"},\n        {3147, &IHidServer::StubReplyZeroed, \"Unknown3147\"},\n        {3148, &IHidServer::StubReplyZeroed, \"Unknown3148\"},\n        {3149, &IHidServer::StubReplyZeroed, \"Unknown3149\"},\n        {5000, &IHidServer::StubReplyZeroed, \"Unknown5000\"},\n", ""),
                ("Result IHidServer::SendNx2VibrationValues(\n    u64 unknown, AppletResourceUserId aruid,\n    InArray<Core::HID::VibrationDeviceHandle, BufferAttr_HipcPointer> vibration_handles,\n    InArray<Core::HID::VibrationValue, BufferAttr_HipcPointer> vibration_values) {\n    LOG_DEBUG(Service_HID, \"called, unknown={}, applet_resource_user_id={}\", unknown, aruid.pid);\n\n    // Unlike 206 this never fails: rumble is best effort and the command is only known from\n    // captures, so an unexpected handle or layout shouldn't return an error a game may treat as\n    // fatal.\n    const auto count = (std::min)(vibration_handles.size(), vibration_values.size());\n    for (std::size_t i = 0; i < count; i++) {\n        const auto result = GetResourceManager()->SendVibrationValue(\n            aruid.pid, vibration_handles[i], vibration_values[i]);\n        if (result.IsError()) {\n            LOG_DEBUG(Service_HID, \"failed to send vibration {}, result={:#x}\", i, result.raw);\n        }\n    }\n\n    R_SUCCEED();\n}\n\nResult IHidServer::SendVibrationValueInMode(std::array<u8, 0x18> raw,\n                                            ClientAppletResourceUserId aruid) {\n    // Two layouts are proposed for the 0x18 bytes before the aruid, both with the value at 0x08:\n    // a mode at 0x00 and the handle at 0x04 (most decoders), or the handle at 0x00 and a u32 mode\n    // at 0x04. A handle's first byte is its npad style, which the modes seen in 214 (0 and 2)\n    // can't pass for, so the first offset holding a valid handle wins. Requests that fit neither\n    // are dropped, as 213 was before.\n    Core::HID::VibrationDeviceHandle handle{};\n    Core::HID::VibrationValue value{};\n    std::memcpy(&value, raw.data() + 0x08, sizeof(value));\n    const bool is_value_valid = std::isfinite(value.low_amplitude) &&\n                                std::isfinite(value.high_amplitude) &&\n                                std::isfinite(value.low_frequency) &&\n                                std::isfinite(value.high_frequency);\n    constexpr std::array<std::size_t, 2> handle_offsets{0x04, 0x00};\n    const bool has_handle = std::ranges::any_of(handle_offsets, [&](std::size_t offset) {\n        std::memcpy(&handle, raw.data() + offset, sizeof(handle));\n        return IsVibrationHandleValid(handle).IsSuccess();\n    });\n\n    static std::once_flag logged;\n    std::call_once(logged, [&raw] {\n        LOG_INFO(Service_HID, \"first request: {:02x}\", fmt::join(raw, \"\"));\n    });\n\n    if (!is_value_valid || !has_handle) {\n        R_SUCCEED();\n    }\n\n    const auto result = GetResourceManager()->SendVibrationValue(aruid.pid, handle, value);\n    if (result.IsError()) {\n        LOG_DEBUG(Service_HID, \"failed to send vibration, result={:#x}\", result.raw);\n    }\n    R_SUCCEED();\n}\n\n", ""),
            )
            for _current, _previous in _nx2_hid_reverse:
                assert _hid_source.count(_current) == 1, (
                    "NX2 HID runtime hunk drift", _current[:72])
                _hid_source = _hid_source.replace(_current, _previous, 1)
            _hid_raw = _hid_source.encode("utf-8")
            _hid_previous = hashlib.sha1(
                b"blob " + str(len(_hid_raw)).encode() + b"\0" + _hid_raw
            ).hexdigest()
            assert _hid_previous == "b83f519fef3905eabb0bef65cab4d989033b5287", (
                "NX2 HID predecessor drift", _hid_previous)
            raw = _hid_raw
            actual = _hid_previous
        if path == "ns2-runtime/hle/core/hle/service/hid/hid_server.cpp" and actual == "b83f519fef3905eabb0bef65cab4d989033b5287":
            # Switch 2 scene/vibration/Nmouse additions are source-sealed here;
            # the historical early-HLE receipt remains immutable.
            lines = raw.decode("utf-8").split("\n")
            reverse = (
                (14, ["#include \"core/hle/kernel/svc_results.h\"","#include <new>","#include \"core/hle/service/cmif_serialization.h\"","#include \"core/hle/service/hid/active_vibration_device_list.h\"","#include \"core/hle/service/hid/applet_resource.h\""], ["#include \"core/hle/service/cmif_serialization.h\"","#include \"core/hle/service/hid/active_vibration_device_list.h\"","#include \"core/hle/service/hid/applet_resource.h\""]),
                (123, ["        {138, C<&IHidServer::SetSceneIdForPrivateApp>, \"SetSceneIdForPrivateApp\"},","        {139, C<&IHidServer::GetSceneIdForPrivateApp>, \"GetSceneIdForPrivateApp\"},","        {200, C<&IHidServer::GetVibrationDeviceInfo>, \"GetVibrationDeviceInfo\"},","        {201, C<&IHidServer::SendVibrationValue>, \"SendVibrationValue\"},","        {202, C<&IHidServer::GetActualVibrationValue>, \"GetActualVibrationValue\"},"], ["        {200, C<&IHidServer::GetVibrationDeviceInfo>, \"GetVibrationDeviceInfo\"},","        {201, C<&IHidServer::SendVibrationValue>, \"SendVibrationValue\"},","        {202, C<&IHidServer::GetActualVibrationValue>, \"GetActualVibrationValue\"},"]),
                (138, ["        {220, C<&IHidServer::IsOunceVibrationDeviceMounted>, \"IsOunceVibrationDeviceMounted\"},","        {300, C<&IHidServer::ActivateConsoleSixAxisSensor>, \"ActivateConsoleSixAxisSensor\"},","        {301, C<&IHidServer::StartConsoleSixAxisSensor>, \"StartConsoleSixAxisSensor\"},","        {302, C<&IHidServer::StopConsoleSixAxisSensor>, \"StopConsoleSixAxisSensor\"},"], ["        {300, C<&IHidServer::ActivateConsoleSixAxisSensor>, \"ActivateConsoleSixAxisSensor\"},","        {301, C<&IHidServer::StartConsoleSixAxisSensor>, \"StartConsoleSixAxisSensor\"},","        {302, C<&IHidServer::StopConsoleSixAxisSensor>, \"StopConsoleSixAxisSensor\"},"]),
                (248, ["        // Documented Nmouse lifecycle and pointer ABI; do not invent sensor samples.","        {3130, C<&IHidServer::InitializeNmouse>, \"InitializeNmouse\"},","        {3131, C<&IHidServer::FinalizeNmouse>, \"FinalizeNmouse\"},","        {3132, C<&IHidServer::SetNmousePointerRanges>, \"SetNmousePointerRanges\"},","        {3133, C<&IHidServer::GetNmousePointerRanges>, \"GetNmousePointerRanges\"},","        {3138, C<&IHidServer::SetMergedNmouseSourceTypes>, \"SetMergedNmouseSourceTypes\"},","        {3139, C<&IHidServer::InitializeNmouse2>, \"InitializeNmouse2\"},","        {3150, C<&IHidServer::SetMouseLibraryVersion>, \"SetMouseLibraryVersion\"}, //21.0.0+","        // What? -- {12010, nullptr, \"SetButtonConfigLeft\"},","    };"], ["        {3150, C<&IHidServer::SetMouseLibraryVersion>, \"SetMouseLibraryVersion\"}, //21.0.0+","        // What? -- {12010, nullptr, \"SetButtonConfigLeft\"},","    };"]),
                (1093, ["Result IHidServer::SetSceneIdForPrivateApp(ClientAppletResourceUserId aruid, u64 scene_id) {","    const std::scoped_lock lock{m_ns2_state_mutex};","    try {","        m_ns2_scene_ids[aruid.pid] = scene_id;","    } catch (const std::bad_alloc&) {","        R_THROW(Kernel::ResultOutOfResource);","    }","    R_SUCCEED();","}","","Result IHidServer::GetSceneIdForPrivateApp(Out<u64> out_scene_id,","                                           ClientAppletResourceUserId aruid) {","    const std::scoped_lock lock{m_ns2_state_mutex};","    const auto it = m_ns2_scene_ids.find(aruid.pid);","    *out_scene_id = it != m_ns2_scene_ids.end() ? it->second : 0;","    R_SUCCEED();","}","","Result IHidServer::IsOunceVibrationDeviceMounted(","    Out<bool> out_is_mounted, Core::HID::VibrationDeviceHandle vibration_device_handle,","    ClientAppletResourceUserId aruid) {","    *out_is_mounted = false;","    if (IsVibrationHandleValid(vibration_device_handle).IsSuccess()) {","        const auto* device = GetResourceManager()->GetVibrationDevice(vibration_device_handle);","        if (device != nullptr) {","            *out_is_mounted = device->IsVibrationMounted();","        }","    }","    R_SUCCEED();","}","","Result IHidServer::SendVibrationValueInBool(","    bool is_vibrating, Core::HID::VibrationDeviceHandle vibration_device_handle,","    ClientAppletResourceUserId aruid) {"], ["Result IHidServer::SendVibrationValueInBool(","    bool is_vibrating, Core::HID::VibrationDeviceHandle vibration_device_handle,","    ClientAppletResourceUserId aruid) {"]),
                (1526, ["Result IHidServer::InitializeNmouse(u8 pointer_type, s32 width, s32 height,","                                     ClientAppletResourceUserId aruid, u64 t_mem_size,","                                     InCopyHandle<Kernel::KTransferMemory> t_mem) {","    // Horizon 20+ Nmouse initialization: a copied, read-only TransferMemory,","    // pointer-type byte, state-range dimensions and the process ARUID.","    // With no emulated Joy-Con 2 sensor, the guest buffer has no samples.","    static_cast<void>(pointer_type);","    static_cast<void>(t_mem_size);","    static_cast<void>(t_mem);","    R_RETURN(SetNmousePointerRanges(width, height, aruid));","}","","Result IHidServer::FinalizeNmouse(ClientAppletResourceUserId aruid) {","    const std::scoped_lock lock{m_ns2_state_mutex};","    m_ns2_nmouse_ranges.erase(aruid.pid);","    m_ns2_merged_mouse_sources.erase(aruid.pid);","    R_SUCCEED();","}","","Result IHidServer::SetMergedNmouseSourceTypes(u32 source_types,","                                               ClientAppletResourceUserId aruid) {","    // Horizon S2 accepts a BitFlagSet of NmouseType. The documented","    // SDK masks this to 0x6; preserve only supported types, per ARUID.","    const std::scoped_lock lock{m_ns2_state_mutex};","    try {","        m_ns2_merged_mouse_sources[aruid.pid] = source_types & 0x6U;","    } catch (const std::bad_alloc&) {","        R_THROW(Kernel::ResultOutOfResource);","    }","    R_SUCCEED();","}","","Result IHidServer::InitializeNmouse2(u32 pointer_type, s32 width, s32 height,","                                      u32 unknown, ClientAppletResourceUserId aruid,","                                      u64 t_mem_size, InCopyHandle<Kernel::KTransferMemory> t_mem) {","    // CMIF decodes the guest COPY TransferMemory descriptor. No Nmouse sensor","    // is exposed: keep its user-space buffer untouched and report no samples.","    static_cast<void>(pointer_type);","    static_cast<void>(unknown);","    static_cast<void>(t_mem_size);","    static_cast<void>(t_mem);","    const std::scoped_lock lock{m_ns2_state_mutex};","    try {","        m_ns2_nmouse_ranges[aruid.pid] = {width, height};","    } catch (const std::bad_alloc&) {","        R_THROW(Kernel::ResultOutOfResource);","    }","    R_SUCCEED();","}","","Result IHidServer::SetNmousePointerRanges(s32 width, s32 height,","                                          ClientAppletResourceUserId aruid) {","    const std::scoped_lock lock{m_ns2_state_mutex};","    try {","        m_ns2_nmouse_ranges[aruid.pid] = {width, height};","    } catch (const std::bad_alloc&) {","        R_THROW(Kernel::ResultOutOfResource);","    }","    R_SUCCEED();","}","","Result IHidServer::GetNmousePointerRanges(Out<s32> out_width, Out<s32> out_height,","                                          ClientAppletResourceUserId aruid) {","    const std::scoped_lock lock{m_ns2_state_mutex};","    const auto it = m_ns2_nmouse_ranges.find(aruid.pid);","    *out_width = it != m_ns2_nmouse_ranges.end() ? it->second.width : 0;","    *out_height = it != m_ns2_nmouse_ranges.end() ? it->second.height : 0;","    R_SUCCEED();","}","","Result IHidServer::SetMouseLibraryVersion(ClientAppletResourceUserId aruid) {","    LOG_INFO(Service_HID, \"(STUBBED) called, applet_resource_user_id={}\", aruid.pid);",""], ["Result IHidServer::SetMouseLibraryVersion(ClientAppletResourceUserId aruid) {","    LOG_INFO(Service_HID, \"(STUBBED) called, applet_resource_user_id={}\", aruid.pid);",""]),
            )
            for index, newer, earlier in reversed(reverse):
                assert lines[index:index + len(newer)] == newer, ("NS2 HID successor drift", path)
                lines[index:index + len(newer)] = earlier
            historical = "\n".join(lines).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            assert actual == "c00ec7de86402abdd6693092f3e57917e80ab7ec", ("NS2 HID predecessor drift", path, actual)
            print("ENCORE_NS2_HID_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
        if (path == "ns2-runtime/hle/core/hle/service/hid/hid_server.h"
                and actual == "6c93ae9a04b121903f3ae3211b705b91e3675942"):
            # Current Lichii NX2 HID vibration extension: immutable
            # predecessor contract, exact source-only reverse.
            _hid_header = raw.decode("utf-8")
            for _current, _previous in (
                ("    // Switch 2 sends vibration every frame with 214: pointer buffers of device handles and values\n    // like 206, but the aruid is raw data after an unknown u64 instead of a sent process id.\n    Result SendNx2VibrationValues(\n        u64 unknown, AppletResourceUserId aruid,\n        InArray<Core::HID::VibrationDeviceHandle, BufferAttr_HipcPointer> vibration_handles,\n        InArray<Core::HID::VibrationValue, BufferAttr_HipcPointer> vibration_values);\n    // 213: one handle and value with a mode, sent per controller every frame by Kirby Air Riders.\n    // Its layout is only known from guesses, so the raw bytes are decoded in the handler.\n    Result SendVibrationValueInMode(std::array<u8, 0x18> raw, ClientAppletResourceUserId aruid);\n", ""),
            ):
                assert _hid_header.count(_current) == 1, (
                    "NX2 HID header hunk drift", _current[:72])
                _hid_header = _hid_header.replace(_current, _previous, 1)
            _hid_header_raw = _hid_header.encode("utf-8")
            _hid_header_previous = hashlib.sha1(
                b"blob " + str(len(_hid_header_raw)).encode() + b"\0" + _hid_header_raw
            ).hexdigest()
            assert _hid_header_previous == "1f3b144324b9014d4e5db64f796019f0e9f4c9a6", (
                "NX2 HID header predecessor drift", _hid_header_previous)
            raw = _hid_header_raw
            actual = _hid_header_previous
        if path == "ns2-runtime/hle/core/hle/service/hid/hid_server.h" and actual == "1f3b144324b9014d4e5db64f796019f0e9f4c9a6":
            # Switch 2 scene/vibration/Nmouse additions are source-sealed here;
            # the historical early-HLE receipt remains immutable.
            lines = raw.decode("utf-8").split("\n")
            reverse = (
                (8, ["#include <mutex>","#include <unordered_map>","","#include \"core/hle/service/cmif_types.h\"","#include \"core/hle/service/service.h\"","#include \"hid_core/hid_types.h\""], ["#include \"core/hle/service/cmif_types.h\"","#include \"core/hle/service/service.h\"","#include \"hid_core/hid_types.h\""]),
                (41, ["    // Switch 2 HID: process-scoped scene state, vibration and disconnected Nmouse.","    Result SetSceneIdForPrivateApp(ClientAppletResourceUserId aruid, u64 scene_id);","    Result GetSceneIdForPrivateApp(Out<u64> out_scene_id, ClientAppletResourceUserId aruid);","    Result IsOunceVibrationDeviceMounted(Out<bool> out_is_mounted,","                                         Core::HID::VibrationDeviceHandle vibration_device_handle,","                                         ClientAppletResourceUserId aruid);","    Result InitializeNmouse(u8 pointer_type, s32 width, s32 height,","                            ClientAppletResourceUserId aruid, u64 t_mem_size,","                            InCopyHandle<Kernel::KTransferMemory> t_mem);","    Result FinalizeNmouse(ClientAppletResourceUserId aruid);","    Result SetMergedNmouseSourceTypes(u32 source_types, ClientAppletResourceUserId aruid);","    Result InitializeNmouse2(u32 pointer_type, s32 width, s32 height, u32 unknown,","                             ClientAppletResourceUserId aruid, u64 t_mem_size,","                             InCopyHandle<Kernel::KTransferMemory> t_mem);","    Result SetNmousePointerRanges(s32 width, s32 height, ClientAppletResourceUserId aruid);","    Result GetNmousePointerRanges(Out<s32> out_width, Out<s32> out_height,","                                  ClientAppletResourceUserId aruid);","    Result CreateAppletResource(OutInterface<IAppletResource> out_applet_resource,","                                ClientAppletResourceUserId aruid);","    Result ActivateDebugPad(ClientAppletResourceUserId aruid);"], ["    Result CreateAppletResource(OutInterface<IAppletResource> out_applet_resource,","                                ClientAppletResourceUserId aruid);","    Result ActivateDebugPad(ClientAppletResourceUserId aruid);"]),
                (290, ["    struct NmousePointerRanges {","        s32 width{};","        s32 height{};","    };","    // Per-applet state; guest service sessions may run concurrently.","    std::mutex m_ns2_state_mutex;","    std::unordered_map<u64, u64> m_ns2_scene_ids;","    std::unordered_map<u64, NmousePointerRanges> m_ns2_nmouse_ranges;","    std::unordered_map<u64, u32> m_ns2_merged_mouse_sources;","};","","} // namespace Service::HID"], ["};","","} // namespace Service::HID"]),
            )
            for index, newer, earlier in reversed(reverse):
                assert lines[index:index + len(newer)] == newer, ("NS2 HID successor drift", path)
                lines[index:index + len(newer)] = earlier
            historical = "\n".join(lines).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            assert actual == "cdc83734e27d5478f1981126950dd1f3f7a91227", ("NS2 HID predecessor drift", path, actual)
            print("ENCORE_NS2_HID_EXACT_REVERSE_PASS", path, f"hunks={len(reverse)}")
        if (path == "ns2-runtime/hle/core/hle/service/am/service/application_proxy.h"
                and actual == "ed88acba848071d6c9e2c0b080c3234925003b50"
                and blob == "03cf286dd642a3e517c7fa4950850603038c6d6b"):
            # Lichii NX2 adds a typed getter only; preserve the exact
            # preceding header ABI by reversing its one new declaration.
            _h = raw.decode("utf-8")
            _method = "    void GetNx2Interface(HLERequestContext& ctx);\n"
            assert _h.count(_method) == 1
            _old = _h.replace(_method, "", 1).encode("utf-8")
            actual = hashlib.sha1(
                b"blob " + str(len(_old)).encode() + b"\0" + _old
            ).hexdigest()
            assert actual == blob, ("NX2 applet proxy header drift", actual)
        if (path == "ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp" and (
            actual == "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912"
            and blob == "d6b14213485b56aefbd9736c8f0e6a2a2b4fa38c"
        )):
            # Reviewed NX2 extra typed interface getters (50/70/80/90).
            # Reverse only these exact bytes in the receipt copy.
            _proxy = raw.decode("utf-8")
            _proxy_includes = '#include "core/hle/service/nx2_stub_interface.h"\n'
            assert _proxy.count(_proxy_includes) == 1
            _proxy = _proxy.replace(_proxy_includes, "", 1)
            for _cmd in (50, 70, 80, 90):
                _line = f'        {{{_cmd}, &IApplicationProxy::GetNx2Interface, "Nx2Getter{_cmd}"}},\n'
                assert _proxy.count(_line) == 1, _cmd
                _proxy = _proxy.replace(_line, "", 1)
            _method = ('   \nvoid IApplicationProxy::GetNx2Interface(HLERequestContext& ctx) {\n'
                       '    ReturnNx2StubInterface(system, ctx, "IApplicationProxy");\n'
                       '}\n')
            assert _proxy.count(_method) == 1
            _proxy = _proxy.replace(_method + "\n", "", 1)
            _raw = _proxy.encode("utf-8")
            actual = hashlib.sha1(
                b"blob " + str(len(_raw)).encode() + b"\0" + _raw
            ).hexdigest()
            assert actual == blob, ("NX2 applet proxy reverse drift", actual)
            print("ENCORE_NS2_APPLET_NX2_INTERFACE_EXACT_REVERSE_PASS")
        if (path == native_applet_proxy_path and
            actual == "0d2ed417d23f11a97f91cf18e733fad6515d0756"
            and blob == "849baf7bfe243734ee49c9e7617462665746d5f1"):
            # Lichii NX2 added a typed appletOE ID 2000. Reverse this
            # single declared row on the audit copy to the exact prior
            # merged appletOE blob; the active C++ keeps the extra handler.
            selected = raw.decode("utf-8")
            added = '        {2000, &IApplicationProxyService::StubReplyInterface, "Unknown2000"},\n'
            assert selected.count(added) == 1
            previous = selected.replace(added, "", 1).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(previous)).encode() + bytes([0]) + previous
            ).hexdigest()
            assert actual == "b1acd90a74bceb03c900a505e217f484f6ecd18f", (
                "AppletOE ID 2000 predecessor drift", actual)
            raw = previous
        if (path == native_applet_proxy_path and
            actual == "b1acd90a74bceb03c900a505e217f484f6ecd18f" and
            blob == "849baf7bfe243734ee49c9e7617462665746d5f1"):
            selected = raw.decode("utf-8")
            newer = "        R_THROW(Result(ErrorModule::AM, 201));"
            earlier = "        R_THROW(Result{ErrorModule::AM, 201});"
            assert selected.count(newer) == 1 and earlier not in selected
            historical = selected.replace(newer, earlier, 1).encode()
            actual = hashlib.sha1(
                b"blob " + str(len(historical)).encode() + bytes([0]) + historical
            ).hexdigest()
            assert actual == blob, ("Applet proxy macro predecessor drift", actual, blob)
            print("ENCORE_NS2_APPLET_RESULT_MACRO_EXACT_REVERSE_PASS")
        assert actual == blob, (path, actual)
else:
    assert not ns2_early_hle_present
print("ENCORE_NS2_EARLY_HLE_OWNER_RECEIPT_PASS",
      f"owners={len(ns2_early_hle_present)}", "blanket_autostub=0")

# Lichii-derived NS2 built-in-font implementation is a reviewed post-F07
# shipping overlay. Keep the four files outside the frozen 337-owner snapshot,
# while proving exact bytes and the one-owner CMake replacement.
ns2_font_service_receipts = {
    "ns2-runtime/font_service/core/hle/service/ns/font_merge.cpp":
        "015ff25ee80bb2197b18e96a6c39fe4271db5f5b",
    "ns2-runtime/font_service/core/hle/service/ns/font_merge.h":
        "4380ec17e9d602e26839f6c8a4dddddb916a0f02",
    "ns2-runtime/font_service/core/hle/service/ns/platform_service_manager.cpp":
        "87994714900728c1c7acabfc94fc5cfa6d2028ca",
    "ns2-runtime/font_service/core/hle/service/ns/platform_service_manager.h":
        "ed0bb0a17d01d10339bb8263f690aa52666158ad",
}
ns2_font_service_present = set(ns2_font_service_receipts) & set(physical_all)
assert ns2_font_service_present == set(ns2_font_service_receipts)
for path, blob in ns2_font_service_receipts.items():
    raw = (active / path).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == blob, (path, actual, blob)
assert not ns2_font_service_present.intersection(research_paths)
for token in (
    'set(EDEN_NS2_FONT_SERVICE_ROOT',
    'list(REMOVE_ITEM eden_ns2_font_sources',
    '"hle/service/ns/platform_service_manager.cpp")',
    'core/hle/service/ns/platform_service_manager.cpp',
    'core/hle/service/ns/font_merge.cpp',
    'target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_FONT_SERVICE_ROOT}")',
):
    assert token in kernel_select, ("NS2 font service is not release-selected", token)
print("ENCORE_NS2_FONT_SERVICE_SELECTED_PASS",
      f"owners={len(ns2_font_service_present)}", "shipping=1 legacy_cmds=0-6")

# Vendor #178 adds the diagnostics HTTPS declaration after the frozen F07
# source graph. Keep it explicit and byte-pinned rather than inflating the
# historical 337-owner baseline.
post_f07_diagnostics_net_owners = {"eden-backports/src/common/net/net.h"}
post_f07_diagnostics_net_present = post_f07_diagnostics_net_owners & set(physical_all)
if gpu_table_vendor_pin in {"edcc311c09eed3a33e5acc373c63a436f662cb5b", "945385cb96f539a5b2ab2edf269683dd1e9ebad9", "2acf67ac8c6b8b1973ba29043206782a13ac8f41", "ab38816078a53b81d4c59152ec660fcb653d4e7f", "3cac7130d6626dced483d038cbf034274a0463d8", "ec3757b3f17d974577b304faa0d54279e01d0a5a", "2a8d841c4c7e34e89254e532fc75fd23e16f01fe", "3b3a26afd70fbfbfb706e5b9964e3303c07a944c", "49070af1bfee1ef67ed8037221345baf71d02373", "388f0bda53806cd89d9c2f85139ec0491f212654", "c92ce9a8b90808869be76d02e73d35636857a0d4", "1e51d1f3383f149a599e36052aba7d887d4b1f77", "b79c774d5d976b7d374b7f851354a652f6aa69c4", "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"} or gpu_table_vendor_pin in {"ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","a0e17271e94342c32b02acdc3199c3f258a8aecf","772f06c8f5b12fdc81066e61f3db2dedfe3eed81","568ae541c07691518e9663aa0fc5f3b017a98d53","dcfe3d2384bd800c6139ede672518ea2c66922a6"} or fc27_p1_vendor:
    assert post_f07_diagnostics_net_present == post_f07_diagnostics_net_owners
    diagnostics_net = active / "eden-backports/src/common/net/net.h"
    raw = diagnostics_net.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == "f8244b366d591ce10342f110d282c295f835474f", actual
else:
    assert not post_f07_diagnostics_net_present
print("ENCORE_DIAGNOSTICS_NET_POST_F07_OWNER_PASS",
      f"owners={len(post_f07_diagnostics_net_present)}")

# Exact NS1/NS2 integration cohort: these 33 maintained C++/header owners
# arrived after the historical 337-path F07 ledger. Review each source
# through its pinned vendor tree; never re-date it as an F07 source.
merged_ns1_ns2_owner_blobs = {
    "eden-core/include/video_core/engines/maxwell_dma.h": "457361bc15a68aed231111e66e5617d6f9585d82",
    "eden-core/overrides/video_core/cdma_pusher.h": "72338d9e2c07f2ebe019450c8b608df802738449",
    "eden-core/overrides/video_core/host1x/control.h": "fc1c4e3d47bdcf8ef282da02410940432051fcca",
    "eden-core/overrides/video_core/host1x/host1x.h": "d716ee97dd8be807d2f29219c4b0c7072ed6b028",
    "eden-core/overrides/video_core/host1x/syncpoint_manager.h": "4f45e7ca10bef7fadf94b4d08a310dea953e7315",
    "eden-core/src/core/hle/kernel/svc/svc_cache.cpp": "e891c2512eb6b7da9a7493af29f6623fc22adc40",
    "eden-core/src/video_core/cdma_pusher.cpp": "91ace41154430a718cd163ceacd45b9607b63d43",
    "eden-core/src/video_core/host1x/control.cpp": "fcbf4e092f054724b9fd4731c8dfec9917cea27a",
    "eden-core/src/video_core/host1x/host1x.cpp": "1815363b19282be07bb4217dd01f369a38e53272",
    "eden-core/src/video_core/host1x/nvdec.cpp": "c83ac98215fcf196ec8b2927ec9a421ddf95c9f7",
    "eden-core/src/video_core/texture_cache/format_lookup_table.cpp": "a3b26a963dddab598610003563fde95d2472058e",
    "eden-shader/src/shader_recompiler/backend/glasm/emit_glasm_context_get_set.cpp": "eed2bdd4df5e5512098adfe262339ad8616b6c4c",
    "eden-shader/src/shader_recompiler/backend/glasm/emit_glasm_memory.cpp": "86b9c091674da72d085d9b3128827705e6a8de9b",
    "eden-shader/src/shader_recompiler/backend/glsl/emit_glsl_atomic.cpp": "761a11801d03335d588b9f5758a9728e042a888b",
    "eden-shader/src/shader_recompiler/backend/glsl/emit_glsl_context_get_set.cpp": "65bd22b3821acfadddf8b1ac4f1bf31cb399940c",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_atomic.cpp": "fc5a7314c680be851c2eb6ae0dee6d27e51c7f38",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp": "98afe1f9f09c0a1da45bfbfa0b0c7646e3067235",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_floating_point.cpp": "276d7f9f9e26b24b01e7afa3e9ea60dc189740f3",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_image.cpp": "ce9c143a794294bdfa3db9997a4dd44798cafd49",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_image_atomic.cpp": "a24136b8f088f6c2c2a46661214e420d25423a7a",
    "eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp": "6e6994343df4a1e3930495f8fd575c4329bfa8c4",
    "eden-shader/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp": "b28be237b6b0b15daa6a0ffdbcabbe2c498c309f",
    "eden-shader/src/shader_recompiler/frontend/maxwell/control_flow.cpp": "ea26c7464a02ce95af8709d8388e0899fe2c1425",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/atomic_operations_global_memory.cpp": "ee938cd456ca3f10cdece6eaf93c4024fd587a9b",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/atomic_operations_shared_memory.cpp": "5ab0cf6d097436d16f32f71b20fb00cca0305e80",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/double_add.cpp": "7d4d49dfe8978c659ec3bee04d15ca38b47a2d08",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/double_fused_multiply_add.cpp": "94c55722641216e5474954b87ca3760b4974ed48",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/double_multiply.cpp": "4986be75ce991e9758066746a73841b78031c50a",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/floating_point_add.cpp": "00d0eb71220ed43abc2b8c006a69ed8fd175164f",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/floating_point_fused_multiply_add.cpp": "f56ece313ee619e02d317b9948ac9f091d13907c",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/floating_point_min_max.cpp": "903e783f593b3be94e2e6611610f6fe8b11a781c",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/floating_point_multiply.cpp": "315c3c7c821016f23af7d2c6ffc8d7ca3a4ebe09",
    "eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/pixel_load.cpp": "e112f14eed85a6ac974a1d81a92d6952dfe57df3",
}
if shipping_vendor in {"166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf", "cd5ce4dabef1d32e0441d22dccdee358ebf23287", "a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e"}:
    merged_ns1_ns2_owner_blobs["eden-core/overrides/video_core/host1x/syncpoint_manager.h"] = "a62b9a9e8019c2df085fc9d393fcbd4207cd78d7"
merged_owner_present = set(merged_ns1_ns2_owner_blobs) & set(physical_all)
assert not (merged_owner_present & set(research_paths))
if gpu_table_vendor_pin == "4354add020afac574198f63d87167f3022bff9c6":
    assert merged_owner_present == set(merged_ns1_ns2_owner_blobs), (
        'Missing integrated source owner', sorted(set(merged_ns1_ns2_owner_blobs) - merged_owner_present))
    for relative, expected_blob in merged_ns1_ns2_owner_blobs.items():
        data = (active / relative).read_bytes()
        actual_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + bytes([0]) + data).hexdigest()
        assert actual_blob == expected_blob, ('Integrated source blob drift', relative, actual_blob)

# Distinct DNSP/DXCI plaintext NCA owners are present only after F07.
# Seal exact active blobs and the single native CMake selection.
post_f07_plaintext_nca_present = {
    "eden-core/src/core/file_sys/content_archive.cpp",
    "eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp",
} & set(physical_all)
actual_vendor = subprocess.check_output(
    ["git", "-C", str(root/"vendor"), "rev-parse", "HEAD"], text=True).strip()
if stabilization_selected:
    actual_vendor = "9db97fb12db1a390d6b2410f0c18333aa31e37da"

# Current vendor source additions postdate the immutable 337-path F07
# catalogue. One exact ledger serves both source inventories.
current_vendor_post_f07_owner_blobs = {
    "eden-core/src/core/hle/service/services.cpp": "19e8b023fe6467557766c71cd45e0ce2ba6d3cea",
    "eden-core/src/core/hle/service/services.h": "08593584bdcdc51f8ab96e2487fb26fad03193d1",
    "eden-core/src/core/hle/service/sm/sm.cpp": "494ee50d2880a491b07c2b981193df1a686c696a",
    "eden-core/src/core/hle/service/vi/vi.cpp": "42d3bad664e92ebf7be3650446e492306c6ff912",
    "ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
    "ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
    "ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
    "ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
    "ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
    "ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
    "ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
    "ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
    "ns2-runtime/hle/core/hle/service/acc/acc.cpp": "bda184c54aa81a037f7ff064554fe9557fff47bb",
    "ns2-runtime/hle/core/hle/service/acc/acc.h": "829c70a3afe5c7bf495bf10d66a75f7b0baff9be",
    "ns2-runtime/hle/core/hle/service/audio/audio_device.cpp": "59d2a5e65ba69fb4a8962c360f34b7695c81a214",
    "ns2-runtime/hle/core/hle/service/audio/audio_device.h": "d0dfca6406e2b427849aac541055916240da0ccc",
    "ns2-runtime/hle/core/hle/service/audio/audio_renderer_manager.cpp": "5b369d46170d1e92c2daa30ebc47deb6d8af7de7",
    "ns2-runtime/hle/core/hle/service/caps/caps_su.cpp": "b19e6b7a2775b89595b96c21275f0c777d69a120",
    "ns2-runtime/hle/core/hle/service/caps/caps_u.cpp": "1590265957c5e37d77edc1116ccc66dd934e534f",
    "ns2-runtime/hle/core/hle/service/lm/lm.cpp": "83d9b178459c33321a6fe388dae93bb3cb8b6f75",
    "ns2-runtime/hle/core/hle/service/mii/mii.cpp": "ffdb17fd145f032283ee9eda22a472d7a037cce6",
    "ns2-runtime/hle/core/hle/service/nifm/nifm.cpp": "342d00bc470e309f1027aeaa7f4abf5239ef9b77",
    "ns2-runtime/hle/core/hle/service/nx2_stub_interface.h": "68c087899680b8a3a764d6cd3c362b0e98237ae0",
    "ns2-runtime/hle/core/hle/service/set/settings_server.cpp": "297bd5ac2eadeb7b501b50f2655a43183e84e1df",
    "ns2-runtime/nx/core/file_sys/decrypted_nca.h": "623f142cfffea3194b9a39842750c3b715e1fdf8",
    "ns2-runtime/nx/core/file_sys/nx_content.cpp": "c374fab2fa5dbc6174099db309a2f6ebbf9e849c",
    "ns2-runtime/nx/core/loader/loader.h": "9efa7b4e54790942f5699c63b1286e6023873a65",
    "ns2-runtime/nx/core/loader/nx.cpp": "8a64df9a95675c1c9655f838efd6328645915d71",
    "ns2-runtime/nx/core/loader/nx.h": "508939fbd0d6eadafe488a19eb18dde5404919fd",
    "ns2-runtime/nx/nxformat/nx_reader.hpp": "7deff5cb5a4fbe5f9a04edf359ccd0504568b657",
    "ns2-runtime/nx/nxformat/nx_session.hpp": "1b12f29c85cb02cea79fa9a08f401c88182c8c6e",
    "ns2-runtime/sparse-residency/core/hle/kernel/k_page_heap.cpp": "574c88dc2add018094c3e6db9047881709da6659",
}
if shipping_vendor in {"692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf", "cd5ce4dabef1d32e0441d22dccdee358ebf23287", "a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e"}:
    current_vendor_post_f07_owner_blobs["ns2-runtime/nx/core/loader/nx.cpp"] = "5d999ca68668133ea3f151669ecd6ac6a17ae1c5"
# Post-F07 registry includes old SM while the latest exact successor
# changes ONLY SM handler retirement in that owner. Preserve exact pin and
# verify all other reviewed owners byte for byte.
if actual_vendor in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    # Exact bfdf delta over b099: reviewed Ampere lowering + appletOE cmd10 ABI.
    for relative, digest in {
        "encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "9169e95ec14559aa6466c68b7d1e1cd3f9e69557",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "a07dae606312e673bdbff5110fbf81d4ce307776",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "7aab2ba6235b33b91819ea78a006129183194194",
        "tests/ns2_early_hle_services_source.py": "a8885d094315e22f9bf0a3c41c969f31463815cb",
    }.items():
        raw = (root/"vendor"/relative).read_bytes()
        got = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert got == digest, ("bfdf reviewed successor drift", relative, got)
if actual_vendor in {"0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    current_vendor_post_f07_owner_blobs = {
        **current_vendor_post_f07_owner_blobs,
        "eden-core/src/core/hle/service/sm/sm.cpp": "34c7c85f1476a3ba819ad20b8a4f8150cca86e16",
        # Same exact SM teardown successor; only LM C++ changed for the new pin.
        "ns2-runtime/hle/core/hle/service/lm/lm.cpp": (
            "9136cf19b1176e96fb17609fd401e4592028d1e2"
            if actual_vendor in {"273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"} else
            "83d9b178459c33321a6fe388dae93bb3cb8b6f75"
        ),
    }
    # These changed C++ owners are not all in the post-F07 path table.
    for relative, digest in {
        "eden-core/src/core/hle/service/sm/sm.h": "7069439e66a6f28ffa56229e08906a21222e2801",
        "ns2-runtime/process/core/core.cpp": ("0e0aadb72c8de5bb2c66ce9105b1dd2d381b5f98" if stabilization_selected else "83fc9a903b05ed9fd096c35102db54a966d736c2"),
        "ns2-runtime/am/core/hle/service/am/service/application_functions.cpp": "9bfaa26664361994902d5b7f73d6a41ff0eadb07",
    }.items():
        raw=(active/relative).read_bytes()
        got=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert got==digest,("Post-F07 latest vendor source drift",relative,got)
    if actual_vendor in {"273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
        # Changed source-list owners are not part of frozen 337-path F07 receipt.
        # Preserve the verified old NS1 overlay and compile-only AM guard delta.
        for relative,digest in {
            "encore-active/eden-core/src/core/hle/service/am/window_system.cpp":
                "bbacbc9b8dde82c29b72a2272776d631f3e95fef",
            "sources/eden/src/core/hle/service/am/window_system.h":
                "d29e37adff7b62e790b26c4b5eba0d9ac667ad92",
        }.items():
            raw=(root/"vendor"/relative).read_bytes()
            got=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert got==digest,("NS1/NS2 AM one-shot exact owner drift",relative,got)
if actual_vendor in {"b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    # MME DMA read successor changes only the selected native GPU-dispatch pair.
    for relative,digest in {
        "ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp": "02e406d9209de6029bcc526bf800428268b81ed4",
        "ns2-runtime/gpu_dispatch/video_core/native_ampere_macro_state.h": "1f60c4cda2a7d5206082434945f40a1cf2bb546c",
    }.items():
        raw=(active/relative).read_bytes()
        got=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert got==digest,("Native MME DMA owner drift",relative,got)
current_vendor_post_f07_present = set(current_vendor_post_f07_owner_blobs) & set(physical_all)
if actual_vendor in {"593bc9ee6ddfcf38e488325ccf318f1a0a109d8e",
                     "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    assert current_vendor_post_f07_present == set(current_vendor_post_f07_owner_blobs)
    for relative, expected_blob in current_vendor_post_f07_owner_blobs.items():
        raw = (active / relative).read_bytes()
        actual_blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual_blob == expected_blob, ("Current post-F07 owner drift", relative, actual_blob)
    cmake_text = (root / "headless/CMakeLists.txt").read_text()
    for token in ("EDEN_NS2_AM_STRUCTURE_ROOT", "EDEN_NS2_SERVICE_PARITY_ROOT",
                  "EDEN_NS2_NX_ARCHIVE_ROOT", "EDEN_R457_SPARSE_PAGE_HEAP_SRC"):
        assert token in cmake_text, ("Current native selector missing", token)
else:
    assert not current_vendor_post_f07_present
if post_f07_plaintext_nca_present:
    # The decrypted NCA readers are source-identical in the later vendor
    # gitlink; verify both complete blobs and the active CMake selection.
    assert post_f07_plaintext_nca_present == {
        "eden-core/src/core/file_sys/content_archive.cpp",
        "eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp",
    }
    for relative, expected_blob in {
        "eden-core/src/core/file_sys/content_archive.cpp":
            "d31f75bf354f3ce5af1ac2f1ac170586503b1877",
        "eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp":
            "49841fbbde5bd086f23aba601c80b19176ed8ae4",
    }.items():
        raw = (active/relative).read_bytes()
        actual_blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual_blob == expected_blob, ("Decrypted NCA source drift", relative)
    assert "foreach(eden_plaintext_content_relative IN ITEMS" in (
        root/"headless/CMakeLists.txt").read_text()
else:
    assert not post_f07_plaintext_nca_present

physical = [p for p in physical_all
            if p not in stabilization_new_headers | post_f07_r23_added_owners | post_f07_c03_radv_meta_owners | merged_owner_present | ns2_production_added_owners | set(research_paths) | shared_ns2_kernel_owners | shared_ns2_audio_owners |
            shared_ns2_gpu_access_owners | post_f07_native_vulkan_owners |
            shared_compute_owners | native_typed_texture_owners |
            shared_gpu_scalar_owners | shared_gpu_remap_owners |
            post_f07_native_atomic_owners | post_f07_native_gpfifo_fetch_owners |
            shared_ns2_wait64_owners | post_f07_unified_rasterizer_owners |
            post_f07_cpu6_ldapr_owners | post_f07_shared_nvdrv_owners |
            post_f07_video_decoder_owners | post_f07_native_global_atomic_owners |
            post_f07_native_stage_buffer_owners | post_f07_task_mesh_source_owners |
            post_f07_r437_buffer_base_owners | fc27_deferred_present | post_f07_image_array_owners |
            post_f07_ampere_semaphore_owners | post_f07_native_opcode_owners |
             post_f07_native_gpfifo_owners | post_f07_feature_vendor_owners |
             post_f07_r09_vendor_owners | post_f07_h05_syncpoint_owners |
             post_f07_h01_fs_owners | post_f07_thread_worker_owners | r457_native_audio_owners | post_f07_r457_slab_owners | nov13_native_owners |
             usage_tracker_present | post_f07_nvdec_present | post_f07_vic_present | post_f07_jxr_present | post_f07_gpu_table_present | post_f07_vfs_present | ps5_vfs128_present | ns2_ipc_present | post_f07_nca_present | post_f07_romfs_present | fc27_ssa_present | fc27_ssbo_present | fc27_descriptor_present | fc27_scalar_unselected_present | pair_present | drawtexture_present | ns2_early_hle_present | ns2_font_service_present | post_f07_diagnostics_net_present | post_f07_plaintext_nca_present | current_vendor_post_f07_present]
# These two versioned headers preserve the immutable upstream Eden snapshot.
# They must be present in the real source catalogue, not excluded as NS2 fixtures.
warning_hygiene = {
    "eden-header-hygiene/include/common/page_table.h",
    "eden-header-hygiene/include/video_core/macro.h",
}
assert {p for p in physical if p.startswith("eden-header-hygiene/")} == warning_hygiene, (
    "Warning-hygiene active owner drift")
# Preserve the immutable 337-path F07 receipt. On a failed integration,
# identify every unclassified path so it can be assigned a real source owner
# rather than treating an arbitrary new count as historical coverage.
catalog_paths = set(re.findall(r"^\| `([^`]+)` \|", section, re.MULTILINE))
assert len(catalog_paths) == 337, ("Historical F07 catalog drift",len(catalog_paths))
assert len(physical) == 337, ("Shipping source catalogue changed",len(physical),
    "unclassified=" + repr(sorted(set(physical) - catalog_paths)),
    "missing=" + repr(sorted(catalog_paths - set(physical))))
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
    "Vendor-maintained CPU6/A64-v8.1-v8.5 owners missing exact audit rows",
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
diagnostics_rows = [line for line in document.split(post_begin)[1].split(post_end)[0].splitlines()
                    if line.startswith("| `eden-backports/src/common/net/net.h`")]
assert diagnostics_rows == (
    ["| `eden-backports/src/common/net/net.h` | U98 |"]
    if post_f07_diagnostics_net_present else []
), ("Diagnostics net owner catalogue drift", diagnostics_rows)
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
shipping_cpp |= {"src/" + p.removeprefix("eden-backports/src/")
                 for p in post_f07_diagnostics_net_present}
build_recipes = {"src/common/CMakeLists.txt", "src/core/CMakeLists.txt"}
assert shipping == shipping_cpp | build_recipes, (
    "Shipping backport source/build manifest coverage drift",
    sorted(shipping ^ (shipping_cpp | build_recipes)),
)
# Keep the expected count tied to the reviewed manifest revision: every
# additional shipping patch requires an explicit inventory review.
assert len(shipping) == (84 if post_f07_diagnostics_net_present else 83) and len(manifest["shipping_receipts"]) == 50
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
# R23 final BCAT/F2I/audren/channel-state/self-controller additions are
# post-F07 native owners, never part of the frozen 193 historical file table.
post_f07_r23_final_headless_owners = {
    "headless/r23_audren_debug_ns1_ps5.cpp",
    "headless/r23_audren_debug_ps5.cpp",
    "headless/r23_bcat_delivery_cache_file_ps5.cpp",
    "headless/r23_channel_state_cache_ps5.h",
    "headless/r23_f2i_conversion_ps5.cpp",
    "headless/r23_self_controller_240_ps5.h",
}
assert len(post_f07_r23_final_headless_owners) == 6
assert all((root / p).is_file() for p in post_f07_r23_final_headless_owners)
assert not post_f07_r23_final_headless_owners & (
    post_f07_feature_headless_owners | post_f07_r09_headless_owners |
    post_f07_p5_headless_owners | post_f07_r457_owners |
    post_f07_ns1_am_headless_owners | post_f07_ns1_audio_headless_owners)
for p in post_f07_r23_final_headless_owners:
    assert p.removeprefix("headless/") in native_cmake, ("R23 owner selection", p)
print("ENCORE_R23_FINAL_POST_F07_HEADLESS_PASS added=6 historic=193")

# Isolated post-F07 diagnostic queue prototype; never change historical counts.
post_f07_diagnostics_receipts = {
    "headless/diagnostics_sharing_policy.h": "2515badbeb070d0f22b02e0ec8dde8a30afdeef4",
    "headless/diagnostics_report_queue.h": "2a000792ac99ec40532b97f2e2645c1473039d5f",
    "headless/diagnostics_native_client.cpp": "358e3d675f44d4a1bf664f14697b074af7f666db",
    "headless/diagnostics_native_client.h": "cd843218b18d581599940f44e93003d84f19598c",
}
post_f07_diagnostics_owners = set(post_f07_diagnostics_receipts)
for path, blob in post_f07_diagnostics_receipts.items():
    assert subprocess.check_output(["git","hash-object",path], cwd=root, text=True).strip() == blob, path
print("ENCORE_DIAGNOSTICS_POST_F07_PASS", "owners=4 native_transport=https_idle_client")

# P1 typography adds two launcher-owned Unicode quick-menu sources after the
# frozen 193-file F07 headless catalogue. Pin them exactly and keep them out
# of historical counts; their runtime behavior is qualified separately.
post_f07_typography_receipts = {
    "headless/quick_overlay_font.cpp": "834b4b97602cb1d098944fb687123862bdf0e5e8",
    "headless/quick_overlay_font.h": "28fd15ac08a2744588a90dd6de0d9228e417719c",
}
post_f07_typography_owners = set(post_f07_typography_receipts)
for path, blob in post_f07_typography_receipts.items():
    assert subprocess.check_output(["git","hash-object",path], cwd=root, text=True).strip() == blob, path
assert "quick_overlay_font.cpp" in native_cmake
print("ENCORE_TYPOGRAPHY_POST_F07_PASS", "owners=2 unicode_quick_menu=1")

# The title-aware loading correction adds two independently reviewed
# headers; neither belongs to the immutable F07 baseline.
post_f07_loading_artwork_receipts = {
    "headless/loading_artwork_transfer.hpp": "2594c4ea8c3d08ec1c04e9c08de717f61ffb7df1",
    "headless/loading_artwork_gl.hpp": "945753fbd9f95f2a45d8fa16504f0bd98534b678",
}
post_f07_loading_artwork_owners = set(post_f07_loading_artwork_receipts)
for path, blob in post_f07_loading_artwork_receipts.items():
    actual = subprocess.check_output(["git","hash-object",path], cwd=root, text=True).strip()
    # Exact alternate-artwork successor from launcher commit 2b8c715.
    if path == "headless/loading_artwork_gl.hpp" and actual == "b08c16fa6650e89dbbd6b8f1b73d26f66a1f441e":
        blob = "b08c16fa6650e89dbbd6b8f1b73d26f66a1f441e"
    assert actual == blob, path
print("ENCORE_LOADING_ARTWORK_POST_F07_PASS owners=2 historical_headless_catalog_preserved=193")

# Newly selected native PS5 guest-fault sink is post-F07; retain the
# historical 193-file catalogue unchanged and prove its exact source blob.
post_f07_ns2_fault_receipts = {
    "headless/ns2_fault_receipt.cpp": "a5338f48aca155f5862a3eb40cade12b6f99a7d8",
}
post_f07_ns2_fault_owners = set(post_f07_ns2_fault_receipts)
for path, blob in post_f07_ns2_fault_receipts.items():
    assert subprocess.check_output(["git", "hash-object", path], cwd=root, text=True).strip() == blob
assert '"${EDEN_PORT_DIR}/ns2_fault_receipt.cpp"' in native_cmake
print("ENCORE_NS2_QUIET_FAULT_POST_F07_PASS", "owners=1")

# A bounded, read-only, 10s/30s NS2 SVC loading witness arrived after F07.
# It is included by the shipping PS5 Vulkan owner and must stay byte-sealed;
# it is not an addition to the immutable 193-file historical table.
post_f07_ns2_loading_svc_receipts = {
    "headless/ns2_loading_svc_snapshot.h": "ec3e66533c231877ab3066db51ec15a940bdc21a",
}
post_f07_ns2_loading_svc_owners = set(post_f07_ns2_loading_svc_receipts)
for path, blob in post_f07_ns2_loading_svc_receipts.items():
    assert subprocess.check_output(["git", "hash-object", path], cwd=root,
                                   text=True).strip() == blob, path
assert '#include "ns2_loading_svc_snapshot.h"' in (root / "headless/graphics.cpp").read_text()
assert '::Eden::NS2::LoadingSvcSnapshot::Report(10);' in (root / "headless/graphics.cpp").read_text()
assert '::Eden::NS2::LoadingSvcSnapshot::Report(30);' in (root / "headless/graphics.cpp").read_text()
print("ENCORE_NS2_LOADING_SVC_POST_F07_PASS owners=1 diagnostics_only=1")

# Selected post-snapshot GPU wait/scheduler/present owners. Do not rewrite
# the immutable 193-file catalogue or qualify console performance by inventory.
post_f07_gpu_wait_receipts = {
    "headless/vulkan_master_semaphore_ps5.cpp": "bf6016b68299fb0f494e725aacca2deae5c6a309",
    "headless/fence_manager_ps5.h": "e41f90553fd934629b608ab524c0188270ac3e5a",
    "headless/vk_fence_manager_ps5.h": "022cfc99c30a54e95095313289bdb7006ed014df",
    "headless/vulkan_scheduler_ps5.cpp": "6e94c5af099773a196f36fd91f3907a2e17f1e5b",
    "headless/vk_scheduler_ps5.h": "e920772e5f4127b14f3a3ffb1c0c2d1880c516b8",
    "headless/vulkan_present_manager_ps5.cpp": "32bee8ceea4d05de1be5a4acc89e594f72805e43",
    "headless/vk_rasterizer_shutdown_ps5.h": "e0d1657f9051736a5595b97dfae4843cbf886130",
    "headless/vk_buffer_cache_shutdown_ps5.cpp": "141826498b2b89bb5273468a8a3c9dde9c3b543f",
}
post_f07_gpu_wait_owners = set(post_f07_gpu_wait_receipts)
for path, blob in post_f07_gpu_wait_receipts.items():
    assert subprocess.check_output(["git", "hash-object", path], cwd=root,
                                   text=True).strip() == blob, path
    assert Path(path).name in (root/"headless/vulkan.cmake").read_text(), path
print("ENCORE_NATIVE_GPU_WAIT_RECEIPT_PASS", "owners=8 historical_headless_catalog_preserved=193")

headless_actual = sorted(
    p.relative_to(root).as_posix()
    for p in (root / "headless").rglob("*")
    if p.is_file() and p.suffix in headless_exts
    and p.relative_to(root).as_posix() not in (
        post_f07_feature_headless_owners | post_f07_r09_headless_owners |
        post_f07_p5_headless_owners | post_f07_r457_owners | post_f07_ns1_am_headless_owners | post_f07_ns1_audio_headless_owners | post_f07_r23_final_headless_owners |
        post_f07_diagnostics_owners | post_f07_typography_owners | post_f07_loading_artwork_owners | post_f07_ns2_fault_owners | post_f07_ns2_loading_svc_owners | post_f07_gpu_wait_owners)
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
        '"${EDEN_PORT_DIR}/stop_limit.cpp"',
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
