#!/usr/bin/env python3
"""Parallel, SHA-pinned NS1/NS2 host qualification. Never launches PS5 builds.

A focused P4.1 batch covering selected source, ABI, GPU and HLE witnesses.
Not a claim that every P0-P4 test has passed or that any PS5 frame exists.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TESTS = {
    "source_owner": "tools/check-ns2-source-selection.py",
    "release_profile": "tools/check-ns2-production-flags-host.py",
    "research_selector": "tools/ns2/check_native_research_selector.py",
    "shared_a64_ldapr": "tools/ns2/check_shared_a64_ldapr_host.py",
    "cpu6_scheduler_tick": "tools/ns2/check_cpu6_scheduler_tick_host.py",
    "native_gpu_owners_syntax": "tools/ns2/check_native_gpu_boot_source_tus_host.py",
    "qmd_state_allocation": "tools/ns2/check_native_qmd_allocation_host.py",
    "gpu_registration_alloc": "tools/ns2/check_native_gpu_registration_alloc_host.py",
    "gpu_worker_session_oom": "tools/ns2/check_native_worker_session_oom_host.py",
    "spirv_patch_output": "tools/ns2/check_native_spirv_patch_output_host.py",
    "process_handoff_transaction": "tools/ns2/check_native_process_handoff_transaction_host.py",
    "gpu_kernel_session_rollback": "tools/ns2/check_gpu_session_kernel_rollback_host.py",
    "gpu_ipc_event_partition_oom": "tools/ns2/check_native_gpu_session_ipc_oom_host.py",
    "gpu_acquire_worker_move_oom": "tools/ns2/check_native_gpu_acquire_worker_oom_host.py",
    "gpu_channel_alloc_owner": "tools/ns2/check_native_gpu_channel_allocation_host.py",
    "gpu_shader_cache_alloc": "tools/ns2/check_native_gpu_cache_allocation_host.py",
    "shared_ampere": "tools/ns2/check_shared_ampere_source_host.py",
    "native_stage_buffer": "tools/ns2/check_native_stage_buffer_host.py",
    "task_mesh_vulkan_tus": "tools/ns2/check_task_mesh_vulkan_tus_host.py",
    "hle_condvar_access": "tools/verify/hle/check-native-hle-condvar-access-host.py",
    "hle_condvar_key": "tools/verify/hle/check-native-hle-condvar-key-host.py",
    "hle_arbiter_access": "tools/verify/hle/check-native-hle-arbiter-access-host.py",
    "hle_arbiter_wrap": "tools/verify/hle/check-native-hle-arbiter-wrap-host.py",
    "hle_address_wake": "tools/verify/hle/check-native-hle-address-wake-host.py",
    "hle_overlay_layout": "tools/verify/hle/check-hle-overlay-layout.py",
    "hle_cmake_selector": "tools/verify/hle/check-hle-cmake-select-host.py",
    "hle_sync_unlink": "tools/verify/hle/check-native-hle-sync-unlink-host.py",
    "hle_wait_timeout": "tools/verify/hle/check-native-hle-wait-timeout-host.py",
    "hle_sleep_timeout": "tools/verify/hle/check-native-hle-sleep-timeout-host.py",
    "hle_ipc_timeout": "tools/verify/hle/check-native-hle-ipc-timeout-host.py",
    "hle_ipc_receive_index": "tools/verify/hle/check-native-hle-ipc-receive-index-host.py",
    "shared_spirv_compiler": "tools/ns2/check_shared_ns2_spirv_compiler_host.py",
    "spirv_descriptor_array_bounds": "tools/ns2/check_native_spirv_descriptor_array_bounds_host.py",
    "atomic_qmd3": "tools/ns2/check_native_qmd_atomic_span_host.py",
    "cbuf_qmd3": "tools/ns2/check_native_qmd_direct_cbuf_host.py",
    "qmd32_real_staging": "tools/ns2/check_native_qmd_32_slots_host.py",
    "nvdrv_4k_lifetime": "tools/ns2/check_native_nvdrv_allocation_range_host.py",
    "nvcore_session_close": "tools/ns2/check_native_nvcore_session_close_host.py",
    "nvdrv_fd_session_owners": "tools/ns2/check_nvdrv_fd_session_owners_host.py",
    "nvdrv_smmu_reclaim": "tools/ns2/check_native_nvmap_smmu_reclaim_host.py",
    "nvdrv_pin_refcounts": "tools/ns2/check_native_nvmap_pin_refs_host.py",
    "nvdrv_pin_failure_propagation": "tools/ns2/check_nvdrv_pin_failure_propagation_host.py",
    "native_vi2_output_ipc": "tools/ns2/check_native_vi2_output_ipc_host.py",
    "native_video_decoder_backend": "tools/ns2/check_native_video_decoder_backend_host.py",
    "native_video_decoder_ipc": "tools/ns2/check_native_video_decoder_ipc_host.py",
    "native_video_eos": "tools/ns2/check_native_video_eos_host.py",
    "native_video_work_buffer": "tools/ns2/check_native_video_work_buffer_host.py",
    "native_video_ready_event": "tools/ns2/check_native_video_ready_event_host.py",
    "native_video_rgb_tiling": "tools/ns2/check_native_video_tiling_roundtrip_host.py",
    "gp_fifo_preinit": "tools/ns2/check_native_gpfifo_preinit_host.py",
    "native_gpfifo_spans": "tools/ns2/check_native_gpfifo_command_spans_host.py",
    "native_gpfifo_fetch": "tools/ns2/check_native_gpu_fetch_admission_host.py",
    "dma_unbound_guard": "tools/ns2/check_native_dma_unbound_subchannel_host.py",
    "native_semaphore_shutdown": "tools/ns2/check_native_puller_semaphore_shutdown_host.py",
    "native_ampere_sem_execute": "tools/ns2/check_native_ampere_semaphore_host.py",
    "native_gpu_channel_reuse": "tools/ns2/check_native_gpu_channel_reuse_host.py",
    "native_invalid_bind": "tools/ns2/check_native_gpu_invalid_bind_owner_host.py",
    "kernel_wait64": "tools/ns2/check_shared_kernel_wait64_host.py",
    "ampere_scalar_alu": "tools/ns2/check_ampere_scalar_alu_sources_host.py",
    "sparse_page_types": "tools/check-sparse-slot-reuse-host.py",
    "spirv_cbuf": "tools/ns2/check_native_spirv_cbuf_span_host.py",
    "sysmix_registry": "tools/ns2/check_native_sysmix_registry_host.py",
    "sysmix_pcm": "tools/ns2/check_native_sysmix_pcm_ring_host.py",
    "audio_virtual": "tools/ns2/check_native_audio_virtual_device_host.py",
    "vulkan_real_tu": "tools/check-ps5-vulkan-texture-tu-syntax-host.py",
    "vulkan_regions": "tools/check-ps5-f07-reinterpret-stencil-regions-host.py",
    "vulkan_layout": "tools/check-ps5-f07-reinterpret-vulkan-layout-host.py",
    "vulkan_generator_fork": "tools/check-vendored-vulkan-fork.py",
    "final_engine_owners": "tools/ci/check-final-engine-owner-contracts.py",
    "deferred_dma_parity": "tools/check-deferred-native-bridge-contract.py",
    "audit_verification_matrix": "tools/check-eden-audit-verification-matrix.py",
    "vendor_source_parity": "tools/check-vendor-consolidation-debt.py",
    "native_package_contract": "tools/check-ps5-all-on-contract.py",
    "physical_core_atomic": "tools/check-native-physical-core-atomic-host.py",
    "vulkan_deferred_copy": "tools/check-vulkan-deferred-copy-ownership-host.py",
    "single_native_package_profile": "tools/ci/check-final-one-profile-source.py",
    "gpu_active_wait": "tools/check-ps5-gpu-active-wait-host.py",
    "quiet_cpu_io_clocks": "tools/check-ps5-quiet-cpu-io-clocks.py",
    "a64_native_interface_owner": "tools/check-maintained-a64-interface.py",
    "native_emitter_owner": "tools/check-maintained-emitters.py",
    "f07_shader_cold_stalls": "tools/check-ps5-f07-cold-stalls-host.py",
    "unified_jit_performance_policy": "tools/check-experimental-performance.py",
    "native_opengl_rasterizer_owner": "tools/check-maintained-opengl-rasterizer.py",
    "native_server_manager_owner": "tools/check-maintained-server-manager.py",
    "live_gpfifo_command_owner": "tools/ns2/check_native_gpu_command_fetch_owner.py",
    "f07_msaa_upload_retirement": "tools/check-ps5-f07-msaa-upload-retire-host.py",
    "f07_reinterpret_image_budget": "tools/check-ps5-f07-reinterpret-image-budget-host.py",
    "manual_native_build_isolation": "tools/check-native-manual-run-isolation.py",
    "loader_build_policy": "tools/check-ps5-vulkan-loading-stages-host.py",
    "native_renderer_selector": "tools/check-ns2-renderer-selector-host.py",
    "native_astc_cache_parity": "tools/ns2/check_egl_astc_texture_cache.py",
    "native_texture_format": "tools/ns2/check_native_texture_format_mapping.py",
    "active_sources": "tools/check-active-source-inventory.py",
    "f07_review": "tools/check-eden-optimization-coverage.py",
    "repo_hygiene": "tools/ci/check-repo-hygiene.py",
    "p1_p2_finite_exit_audit": "tools/ns2/check_p1_p2_exit_gate.py",
    "python_syntax": "tools/check-python-source-syntax.py",
}
SMOKE = ("source_owner", "release_profile", "shared_ampere",
         "vulkan_generator_fork", "repo_hygiene", "active_sources", "python_syntax")

def git(*args: str, cwd: Path = ROOT) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True,
                          capture_output=True, timeout=30)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout.strip()

def checked_revisions() -> tuple[str, str]:
    main = git("rev-parse", "HEAD")
    vendor = git("rev-parse", "HEAD", cwd=ROOT/"vendor")
    pinned = git("ls-tree", "HEAD", "vendor").split()
    if len(pinned) < 3 or pinned[0] != "160000" or pinned[2] != vendor:
        raise RuntimeError("Vendor checkout does not match the main SHA gitlink")
    if git("status", "--porcelain", "--untracked-files=no") or git(
        "status", "--porcelain", "--untracked-files=no", cwd=ROOT/"vendor"):
        raise RuntimeError("Dirty tracked source; cannot claim same-SHA qualification")
    return main, vendor

def run_one(name: str, path: str, env: dict[str, str]) -> dict:
    t0 = time.perf_counter()
    command = [sys.executable, "-B", path]
    try:
        proc = subprocess.run(command, cwd=ROOT, env=env, text=True,
                              capture_output=True, timeout=240)
        return {"name": name, "script": path, "passed": proc.returncode == 0,
                "returncode": proc.returncode, "seconds": round(time.perf_counter()-t0, 2),
                "stdout": proc.stdout[-12000:], "stderr": proc.stderr[-12000:]}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"name":name, "script":path, "passed":False, "returncode":None,
                "seconds":round(time.perf_counter()-t0,2),
                "stdout":"", "stderr":str(e)}

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("core","smoke"), default="core")
    parser.add_argument("--jobs", type=int, choices=range(1,5), default=3,
                        metavar="{1,2,3,4}")
    parser.add_argument("--shard", default="0/1",
                        help="Zero-based shard/count, e.g. 1/4")
    args=parser.parse_args()
    try:
        shard_index, shard_count = map(int, args.shard.split("/", 1))
    except ValueError:
        parser.error("--shard requires INDEX/COUNT")
    if not 1 <= shard_count <= 8 or not 0 <= shard_index < shard_count:
        parser.error("--shard requires 0 <= INDEX < COUNT <= 8")
    all_names = tuple(TESTS) if args.scope=="core" else SMOKE
    names = tuple(name for index, name in enumerate(all_names)
                  if index % shard_count == shard_index)
    for name in names:
        if not (ROOT/TESTS[name]).is_file():
            raise RuntimeError("Missing pinned host witness: "+TESTS[name])
    main_sha, vendor_sha=checked_revisions()
    print(f"P4_HOST_BATCH_START main={main_sha} vendor={vendor_sha} "
          f"scope={args.scope} jobs={args.jobs} shard={shard_index}/{shard_count} "
          f"count={len(names)}",flush=True)
    env=os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"]="1"
    # A newer CLT SDK can contain .tbd formats that the installed Apple
    # linker cannot parse. Pin only the HOST test subprocesses to a
    # compatible SDK; individual syntax-only witnesses may explicitly
    # select newer libc++ headers when they need C++20 jthread/stop_token.
    if sys.platform=="darwin":
        host_sdk=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
        if host_sdk.is_dir():
            env["SDKROOT"]=str(host_sdk)
    started=datetime.now(timezone.utc)
    results=[]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures={pool.submit(run_one,name,TESTS[name],env):name for name in names}
        for future in as_completed(futures):
            result=future.result()
            results.append(result)
            status="PASS" if result["passed"] else "FAIL"
            print(f"P4_HOST_BATCH_{status} {result['name']} "
                  f"{result['seconds']:.2f}s",flush=True)
            if not result["passed"]:
                print((result["stdout"]+"\n"+result["stderr"])[-2200:],flush=True)
    if checked_revisions()!=(main_sha,vendor_sha):
        raise RuntimeError("Source SHA drifted during host batch; results not qualified")
    results.sort(key=lambda r: names.index(r["name"]))
    output=ROOT/".build-local"/f"p4-host-batch-{main_sha[:8]}-s{shard_index}of{shard_count}.json"
    output.parent.mkdir(exist_ok=True)
    payload={"main_sha":main_sha,"vendor_sha":vendor_sha,
             "utc":started.isoformat(),"scope":args.scope,"jobs":args.jobs,
             "shard_index":shard_index,"shard_count":shard_count,
             "host_only":True,"ps5_build":False,"console_frame":False,
             "passed":sum(r["passed"] for r in results),
             "total":len(results),"results":results}
    output.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print(f"P4_HOST_BATCH_RESULT passed={payload['passed']}/{payload['total']} "
          f"receipt={output.relative_to(ROOT)}",flush=True)
    return 0 if payload["passed"]==payload["total"] else 1

if __name__=="__main__":
    raise SystemExit(main())
