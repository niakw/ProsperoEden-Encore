#!/usr/bin/env python3
"""Final engine/vendor source qualification for FC27 + P0 additions.

Host/source only. This proves the engine selects the exact reviewed vendor
graph and replays the vendor's own focused contracts. It is not a PS5 build,
FC27 visual pass, Bananza boot proof, or performance measurement.
"""
from pathlib import Path
import hashlib
import subprocess

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
# Vendor #192/#193 touch only reviewed NS2 A64/kernel owners and their tests.
# The FC27 GPU owners remain byte-sealed by the focused tests below.
REVIEWED_PINS={"1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc", "8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200", "c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "2558d69f4668cdf150dcde42a940848ccf342e0a"}
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert selected==checked and selected in REVIEWED_PINS,(selected,checked)
if selected == "2558d69f4668cdf150dcde42a940848ccf342e0a":
    for path, expected in (
        ("encore-active/ns2-runtime/gamechat/core/hle/service/friend/friend.cpp", "ceb8b4afa7c0f19af3fe209fd8ca8d848a66d2cb"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", "64b34b1028a3c0b6683db1a179fb31f1cd868bfd"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h", "be4d6eaaa43ee247b61d835a7b280fe26aa8eb63"),
    ):
        raw=(V/path).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected, ("NS2 GameChat owner drift", path, actual)
    selected = "ab417b59c5f7f4613ff27386be05c0644d0ed776"
if selected in {"372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    raw=(V/"encore-active/eden-core/src/video_core/buffer_cache/buffer_cache_base.h").read_bytes()
    actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    assert actual == "63ef9b07b37bdc4bc9588dd77639358010e545dc", ("Shared 32-slot BufferCacheBase drift",actual)
if selected in {"a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    raw=(V/"encore-active/eden-core/src/core/file_sys/vfs/vfs_real.cpp").read_bytes()
    actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    assert actual == "097335e42a0f569a51f58417f0cfd6239f474136", ("PS5 VFS128 owner drift",actual)
if selected == "ab417b59c5f7f4613ff27386be05c0644d0ed776":
    for path, expected in (("encore-active/eden-threading/src/core/hle/kernel/k_server_session.cpp", "5bd8cd81c2bf8d32f0d65406881b8286a06ca771"),
                           ("encore-active/eden-threading/native-hle-overrides.cmake", "0ed9f8520019c07874c157c97ded3864c07a8a32")):
        raw=(V/path).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected, ("NS2 IPC peer owner drift", path, actual)
if selected == "67759611edc13414c112ea9d2b6664d54827a200":
    # Confirm the new release modifies only its reviewed RomFS owner/test;
    # actual GitHub commit comparison is documented in the incident register.
    for relative, expected in {
        "encore-active/eden-core/src/core/file_sys/romfs_factory.cpp":
            "4775cf98c3bfbc587402928bad424dcb471047a0",
        "tests/ns2_romfs_program_index_fallback_host.py":
            "abac08b40623febec02c58d2703b4ec3676b88f0",
        "encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp":
            "dd30183f72a9a9dfc2a17700db263f85e4d77596",
    }.items():
        raw = (V/relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("RomFS-only successor drift",relative,actual)

if selected in {"c15cdfe96a3d836bf32ba21b8070088add81cdc9",
                "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    # PR #194 is rolled back only in production GPU cache protection.
    # Preserve newly reviewed NS2 RomFS and A64 uniform 16MiB ABI.
    for relative, expected in {
        "encore-active/eden-core/overrides/core/device_memory_manager.inc":
            "daf493ce6e863397ec44bfae467c4f7533570477",
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp":
            "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35",
        "encore-active/eden-core/src/core/file_sys/romfs_factory.cpp":
            "4775cf98c3bfbc587402928bad424dcb471047a0",
        "tests/fc27_deferred_page_protection_host.py":
            ("ae967badcfef7e098ac2620b789a1138fad79058" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "876ebf0f43ffc3999d7ed6d983160d3447bc15f0" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "cb821c1aaab3f968ce25d7ac92d489e01ba3b8f6" if selected == "1a09972eea6f473fda1b714efe84cd52219bf681" else "7051e22341bf7a5374221700834917fc74e4f746"),
    }.items():
        raw = (V/relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("Sync rollback source drift",relative,actual)
    if selected in {"729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for relative, expected in {
            "encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h":
                "86e8e7e96b5eda5b6b98ccd3c7e6ce76d4275c86",
            "encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp":
                "09ae2494b2b6f620a25ab549c06c69045a9fb73d",
            "tests/ns2_recent_svc_fault_trace_host.py":
                "79d8d7294e37e141d6c669d9b55fa5a02d94287e",
        }.items():
            raw = (V/relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == expected, ("Quiet NS2 SVC witness drift",relative,actual)
    if selected in {"1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for relative, expected in {
            "encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h": ("c7cb95ecaf388b925fc29582499bbd4b54a77f75" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "859a9e46fb63a97fee82c8ea6b1566317264f98f" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "0d99f9a861c645562519f71d62f4f49bfedd8101"),
            "tests/ns1_r23_18_tir_host.py": ("753df3ca146cba983057801df36dcf9db0b5fc6b" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "7c225ac2065a1721eb53cc034ea3bc4e3b581770" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "520c5eb05f23c5fc6ad4438c9f6df774533644e1"),
            "tests/fc27_deferred_page_protection_host.py": ("ae967badcfef7e098ac2620b789a1138fad79058" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "876ebf0f43ffc3999d7ed6d983160d3447bc15f0" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "cb821c1aaab3f968ce25d7ac92d489e01ba3b8f6"),
        }.items():
            raw = (V/relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == expected, ("Selected PS5 F07 TextureCache source drift", relative, actual)
    assert not (V/"encore-active/eden-core/overrides/core/deferred_cached_updates.h").exists()
    subprocess.run(["python3", "-B", str(V/"tests/fc27_deferred_page_protection_host.py")],
                   check=True, timeout=240)
    print("FC27_SYNCHRONOUS_PROTECTION_RESTORED source=exact test=host ps5=unverified")

if selected in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
    reviewed_fc27_owners = {
        "encore-active/eden-core/overrides/core/deferred_cached_updates.h": "33262f511777cdd1b4a74ac0cd6dc39caa12c9d0",
        "encore-active/eden-core/overrides/core/device_memory_manager.inc": "852a0272696c7ce182bc05aee92bc7cbb195446b",
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp": "38d5630570675088a0620ef533112bb314a40ae8",
    }
    for relative, expected_blob in reviewed_fc27_owners.items():
        body = (V/relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
        assert actual == expected_blob, ("FC27 reviewed source changed", relative, actual)
    if selected == "6c38328fbef33de747f5c31ea30d13541a513a4a":
        # One reviewed PS5-only A64 table capacity delta; the FC27 source
        # seal above still requires exact unchanged Vulkan/guest-write blobs.
        reviewed_dispatch = (V/"encore-active/eden-core/src/dynarmic/backend/x64/"
                             "a64_emit_x64_standard.h").read_bytes()
        dispatch_blob = hashlib.sha1(b"blob " + str(len(reviewed_dispatch)).encode()
                                     + bytes([0]) + reviewed_dispatch).hexdigest()
        assert dispatch_blob == "633dceaf5e7adf2b17a6b97af3862e9c7ecd1147", dispatch_blob
    elif selected in {"8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
        # Source-exact P0 rollback: stable A64 class has no PS5_NATIVE-dependent member size.
        repaired_dispatch = (V/"encore-active/eden-core/src/dynarmic/backend/x64/"
                             "a64_emit_x64_standard.h").read_bytes()
        dispatch_blob = hashlib.sha1(b"blob " + str(len(repaired_dispatch)).encode()
                                     + bytes([0]) + repaired_dispatch).hexdigest()
        assert dispatch_blob == "205e73772861ce5036370bbe114d60275daf186e", dispatch_blob
    subprocess.run(["python3", "-B", str(V/"tests/fc27_deferred_page_protection_host.py")],
                   check=True, timeout=240)
    print("FC27_DEFERRED_PAGE_PROTECTION_REVIEWED_SOURCE_PASS source=exact host=pass ps5=unverified")

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
    "ns2_alias_64g_upstream_parity_host.py",
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

print("ENCORE_FINAL_VENDOR_FC27_P0_PASS pin=exact xmad=1 dynamic_sampler=1 descriptor_fastpath=1 storage_audit=1 bananza_low_write=1 scalar_cache=1 bitfield_uextract=1 ns2_getinfo_page_size=1 ns2_getinfo_vamm=1 alpha_ref=1 worker_lost_wake=1 full_clear_upload_elision=1 dynamic_texture_limit=1 duskbloods_shader=1 fc27_sibling_preservation=1 hsetp2_cbuf=1 alias64_vamm32=1 kprocess_abi=1 fc27_pipeline=1 ns2_gpu_memory=1 native_tiling=auth+blitter host1x_wait=1 ipc_handoff=1 ps5=unverified")
