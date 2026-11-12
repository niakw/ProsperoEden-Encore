#!/usr/bin/env python3
"""Offline source closure: one vendor Gitlink, three exact upstream Git trees."""
from pathlib import Path
import hashlib, subprocess
root=Path(__file__).resolve().parents[2]
vendor=root/"vendor"
def git(c,*args): return subprocess.check_output(["git","-C",str(c),*args],text=True).strip()
modules=[s.split()[-1] for s in git(root,"ls-tree","-r","HEAD").splitlines() if s.startswith("160000 commit ")]
assert modules==["vendor"],modules
assert (root/".gitmodules").read_text().count('[submodule "')==1
assert not (vendor/".gitmodules").exists()
assert git(root,"rev-parse","HEAD:vendor")==git(vendor,"rev-parse","HEAD")
pins={"ps5-mihawkgen":("aad67f4bd28c040db7aa0d78cfd3d0de85cfba7a","c57232a9f16bcb6df5fe07c9bb631518f2b1cc0e"),
"ps5-fsr3-optical-flow":("85e34d638cd9e8b211e08fb19d1a57a588bb8d76","64362101757cdd6f7df9eeb984cb53f03f1fbfca"),
"libwebp":("3a7830b9713d9187cf1211862d4571ff58b0d507","4fa21912338357f89e4fd51cf2368325b59e9bd9")}
provenance=(vendor/"docs/PS5_INTERNAL_DEPENDENCY_ORIGINS_2026-11-10.md").read_text()
for name,(tree,sha) in pins.items():
    path=vendor/"sources"/name
    assert path.is_dir() and not (path/".git").exists(),name
    assert git(vendor,"rev-parse","HEAD:sources/"+name)==tree,name
    assert sha in provenance,name
# Preserve exact upstream provenance for the sole security-necessary
# MihawkGen training requirements update; never silently admit other changes.
historical_vendor="a800f08eb13fd9b6aac84f1ec21f9ac917f57330"
train="sources/ps5-mihawkgen/train/requirements.txt"
changed=git(vendor,"diff","--name-only",historical_vendor,"HEAD","--","sources/ps5-mihawkgen").splitlines()
assert changed==[train], ("Unexpected PS5 renderer source changes", changed)
previous=git(vendor,"show",f"{historical_vendor}:{train}")
assert previous.count("pillow==12.3.0")==1
assert (vendor/train).read_text().strip()==previous.replace("pillow==12.3.0","pillow==13.0.0")
for stale in ("PS5_MihawkGen", "PS5_FSR3OpticalFlow", "libwebp"):
    assert not (vendor/"encore-active"/stale).exists(), stale
net=vendor/"sources/ps5-mihawkgen/framegen/models/network.fgw"
assert net.stat().st_size==1757240
assert hashlib.sha256(net.read_bytes()).hexdigest()=="31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b"
for p in ["ps5-mihawkgen/LICENSE.md","ps5-mihawkgen/THIRD_PARTY_NOTICES.txt","ps5-fsr3-optical-flow/COPYING","ps5-fsr3-optical-flow/shaders/LICENSE.txt","libwebp/COPYING","libwebp/PATENTS"]:
    assert (vendor/"sources"/p).is_file(),p
assert "version 1.6.0" in (vendor/"sources/libwebp/NEWS").read_text()
print("PS5_INTERNAL_DEPENDENCIES_PASS gitlinks=1 sources=3 trees=byte_exact_except_reviewed_mihawk_training_patch model=sha256 libwebp=1.6.0 no_ps5_build=1")
