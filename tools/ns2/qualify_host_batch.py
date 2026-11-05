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
    "shared_ampere": "tools/ns2/check_shared_ampere_source_host.py",
    "shared_spirv_compiler": "tools/ns2/check_shared_ns2_spirv_compiler_host.py",
    "atomic_qmd3": "tools/ns2/check_native_qmd_atomic_span_host.py",
    "cbuf_qmd3": "tools/ns2/check_native_qmd_direct_cbuf_host.py",
    "qmd32_real_staging": "tools/ns2/check_native_qmd_32_slots_host.py",
    "nvdrv_4k_lifetime": "tools/ns2/check_native_nvdrv_allocation_range_host.py",
    "gp_fifo_preinit": "tools/ns2/check_native_gpfifo_preinit_host.py",
    "dma_unbound_guard": "tools/ns2/check_native_dma_unbound_subchannel_host.py",
    "native_semaphore_shutdown": "tools/ns2/check_native_puller_semaphore_shutdown_host.py",
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
    "active_sources": "tools/check-active-source-inventory.py",
    "f07_review": "tools/check-eden-optimization-coverage.py",
    "repo_hygiene": "tools/ci/check-repo-hygiene.py",
    "python_syntax": "tools/check-python-source-syntax.py",
}
SMOKE = ("source_owner", "release_profile", "shared_ampere",
         "repo_hygiene", "active_sources", "python_syntax")

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
    args=parser.parse_args()
    names = tuple(TESTS) if args.scope=="core" else SMOKE
    for name in names:
        if not (ROOT/TESTS[name]).is_file():
            raise RuntimeError("Missing pinned host witness: "+TESTS[name])
    main_sha, vendor_sha=checked_revisions()
    print(f"P4_HOST_BATCH_START main={main_sha} vendor={vendor_sha} "
          f"scope={args.scope} jobs={args.jobs} count={len(names)}",flush=True)
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
    output=ROOT/".build-local"/f"p4-host-batch-{main_sha[:8]}.json"
    output.parent.mkdir(exist_ok=True)
    payload={"main_sha":main_sha,"vendor_sha":vendor_sha,
             "utc":started.isoformat(),"scope":args.scope,"jobs":args.jobs,
             "host_only":True,"ps5_build":False,"console_frame":False,
             "passed":sum(r["passed"] for r in results),
             "total":len(results),"results":results}
    output.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print(f"P4_HOST_BATCH_RESULT passed={payload['passed']}/{payload['total']} "
          f"receipt={output.relative_to(ROOT)}",flush=True)
    return 0 if payload["passed"]==payload["total"] else 1

if __name__=="__main__":
    raise SystemExit(main())
