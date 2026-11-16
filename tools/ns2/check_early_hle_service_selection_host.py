#!/usr/bin/env python3
"""Compile the selected bounded NS2 AM/HID early-service owners on a host compiler."""
from pathlib import Path
import os, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
DEPS=ROOT/"vendor/sources/eden-cpm"
V=ROOT/"vendor"
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert selected==checked=="ffa519db0f68fb0d5d2acf791e381c898a34a175",(selected,checked)
subprocess.run(["python3","-B",str(V/"tests/ns2_early_hle_services_source.py")],
               cwd=ROOT,check=True,timeout=60)
subprocess.run(["python3","-B",str(V/"tests/ns2_getinfo_page_size_source.py")],
               cwd=ROOT,check=True,timeout=60)
subprocess.run(["python3","-B",str(V/"tests/ns2_getinfo_vamm_region_source.py")],
               cwd=ROOT,check=True,timeout=60)
cm=(ROOT/"headless/CMakeLists.txt").read_text()
for marker in (
    "EDEN_NS2_EARLY_HLE_ROOT",
    '"hle/service/am/service/application_proxy.cpp"',
    '"hle/service/hid/hid_server.cpp"',
    "target_include_directories(core BEFORE PRIVATE",
):
    assert marker in cm,marker
assert "global auto-stub fallback" in cm
inc=[
    ROOT/"vendor/encore-active/ns2-runtime/hle",
    ROOT/"vendor/sources/eden/src",
    ROOT/"vendor/sources/eden/src/dynarmic/src",
    ROOT/"vendor/sources/fmt/include",
]
inc += sorted((DEPS/"boost/boost-1.90.0/libs").glob("*/include"))
compiler=(shutil.which("g++") if sys.platform=="linux" else None) or shutil.which("clang++") or shutil.which("g++")
assert compiler
flags=[compiler,"-std=c++20","-fsyntax-only","-Wno-unused-parameter","-DFMT_HEADER_ONLY","-DPS5_NATIVE=1"]
flags += ["-I"+str(p) for p in inc if p.is_dir()]
owners=[
    V/"encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp",
    V/"encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.cpp",
]
for owner in owners:
    assert owner.is_file(),owner
    run=subprocess.run(flags+[str(owner)],cwd=ROOT,capture_output=True,text=True,
                       env=os.environ.copy(),timeout=120)
    if run.returncode:
        print(run.stderr[-7000:],file=sys.stderr)
    assert run.returncode==0,(owner,run.returncode)
    print("NS2_EARLY_HLE_TU_SYNTAX_PASS",owner.relative_to(ROOT))
print("NS2_EARLY_HLE_ENGINE_SELECTION_PASS owners=2 blanket_autostub=0 ps5_build=OFF")
