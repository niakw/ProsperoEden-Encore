#!/usr/bin/env python3
"""Final engine/vendor source qualification for FC27 + P0 additions.

Host/source only. This proves the engine selects the exact reviewed vendor
graph and replays the vendor's own focused contracts. It is not a PS5 build,
FC27 visual pass, Bananza boot proof, or performance measurement.
"""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
# Vendor #190 touches only NS2 SVC/trace and source tests; the FC27 GPU
# owners remain byte-sealed by the focused tests below.
REVIEWED_PINS={"2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "435d49bd2a37439340b640443190d87893052347"}
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert selected==checked and selected in REVIEWED_PINS,(selected,checked)

cmake=(ROOT/"headless/CMakeLists.txt").read_text()
for needle in (
    'set(EDEN_R23_ATTRIBUTE_TEXTURE_PASS',
    'ir_opt/texture_pass.cpp',
    'foreach(eden_r23_subgroup_relative IN ITEMS',
    '"ir_opt/constant_propagation_pass.cpp"',
    'set(EDEN_FC27_SSA_SOURCE',
    'set(EDEN_FC27_SSBO_SOURCE',
    'set(EDEN_G11_PROFILE normal)',
    'arm_dynarmic_${bits}_${EDEN_G11_PLATFORM}_${EDEN_G11_PROFILE}.cpp',
    'target_include_directories(video_core BEFORE PRIVATE "${EDEN_SMALL_VECTOR_ROOT}")',
    'set(EDEN_MAINTAINED_THREAD_WORKER_ROOT',
    'eden-core/overrides/thread-worker',
):
    assert needle in cmake,needle

tests=(
    "fc27_xmad_pointer_fold_host.py",
    "fc27_dynamic_texture_static_sampler_host.py",
    "fc27_descriptor_page_fastpath_host.py",
    "fc27_storage_offset_current_host.py",
    "p0_bananza_low_write_current_source.py",
    "ps5_spirv_scalar_constant_cache_host.py",
    "fc27_maxwell_prmt_operand_forms_source.py",
    "shader_bitfield_uextract_fold_host.py",
    "ns2_getinfo_page_size_source.py",
    "ns2_getinfo_vamm_region_source.py",
    "ps5-late-upstream-fixes-source.py",
    "ps5-full-clear-skip-upload-source.py",
    "vulkan_static_pipeline_cache_source.py",
    "shutdown_teardown_lifetime_source.py",
    "shutdown_general_channel_lifetime_source.py",
    "ns2_ampere_imad_negated_addend_host.py",
    "ns2_dynamic_texture_found_bit_limit_host.py",
    "ns2_duskbloods_tld4_imad_host.py",
    "fc27_gpu_page_sibling_preservation_host.py",
    "ns2_ampere_hsetp2_cbuf_host.py",
    "ns2-kprocess-memory-budget-source.py",
    "ns2_alias_128g_no_kprocess_layout_host.py",
    "fc27_waited_pipeline_inline_source.py",
    "fc27_pipeline_teardown_and_syncwait_source.py",
    "ps5_host1x_wait_notification_host.py",
    "ns2_gpu_partition_new_sdk_source.py",
    "ns2_syncpt_bootstrap_source.py",
    "ns2_recent_svc_fault_trace_host.py",
    "ns2_ipc_started_thread_handoff_source.py",
    "ns2_gpu_access_svc_info_types_source.py",
    "ns2_gpu_identity_mapping_source.py",
    "ns2_nvhost_unknown_node_fallback_source.py",
    "ns2_smmu_34bit_capacity_source.py",
    "ns2_syncpoint_shim_source.py",
    "ns2_font_service_source.py",
    "ns2_backport_manifest_preserved_source.py",
    "ns2_sw_blitter_native_tiling_source.py",
    "ns2_native_tiling_activation_source.py",
    "fc27_release_npad_detailed_source.py",
)
for name in tests:
    subprocess.run(["python3","-B",str(V/"tests"/name)],check=True,timeout=240)

print("ENCORE_FINAL_VENDOR_FC27_P0_PASS pin=exact xmad=1 dynamic_sampler=1 descriptor_fastpath=1 storage_audit=1 bananza_low_write=1 scalar_cache=1 bitfield_uextract=1 ns2_getinfo_page_size=1 ns2_getinfo_vamm=1 alpha_ref=1 worker_lost_wake=1 full_clear_upload_elision=1 dynamic_texture_limit=1 duskbloods_shader=1 fc27_sibling_preservation=1 hsetp2_cbuf=1 alias128=1 kprocess_abi=1 fc27_pipeline=1 ns2_gpu_memory=1 native_tiling=auth+blitter host1x_wait=1 ipc_handoff=1 ps5=unverified")
