#!/usr/bin/env python3
"""Qualify the production A64 owners selected directly from encore-active."""
from pathlib import Path
import os, shutil, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[2]
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
SCRIPT = ROOT / "headless/shared_a64_ldapr.cmake"
ACTIVE_ROOT = ROOT / "vendor/encore-active/eden/src/dynarmic/src"
BASE_ROOT = ROOT / "vendor/sources/eden/src/dynarmic/src"
REL = Path("dynarmic/frontend/A64")
ACTIVE = ACTIVE_ROOT / REL
SELECTED_TRANSLATOR = ACTIVE / "translate/a64_translate.cpp"
FILES = (
    "decoder/a64.h", "decoder/a64.inc", "translate/impl/impl.h",
    "translate/impl/load_store_exclusive.cpp", "translate/impl/a64_branch.cpp",
    "translate/impl/load_store_atomic.cpp", "translate/impl/memory_tagging.cpp",
    "translate/impl/pointer_authentication.cpp",
)
assert 'set(EDEN_A64_V81_V85_ACTIVE_ROOT' in CMAKE
assert 'vendor/encore-active/eden/src/dynarmic/src' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE' in CMAKE
assert "EDEN_A64_V81_V85_OUTPUT_ROOT" not in CMAKE
assert "encore-active/eden/ldapr" not in CMAKE
assert all((ACTIVE / f).is_file() for f in FILES)
validated = subprocess.run(
    ["cmake", f"-DEDEN_A64_V81_V85_ACTIVE_ROOT={ACTIVE_ROOT}", "-P", str(SCRIPT)],
    capture_output=True, text=True, timeout=30)
assert validated.returncode == 0, validated.stderr
provenance = subprocess.run(
    [sys.executable, "-B", str(ROOT / "vendor/tests/ns2_a64_v81_v85_source.py")],
    cwd=ROOT, capture_output=True, text=True, timeout=30)
assert provenance.returncode == 0, provenance.stderr[-5000:]

decoder=(ACTIVE/"decoder/a64.inc").read_text()
for marker in (
    'INST(LDAPR_sz, "LDAPRB, LDAPRH, LDAPR"',
    'INST(AtomicMemOp, "LDADD/LDCLR/LDEOR/LDSET/LDSMAX/LDSMIN/LDUMAX/LDUMIN/SWP"',
    'INST(CompareAndSwapPair, "CASP"', 'INST(PACGA, "PACGA"',
    'INST(RETA, "RETAA, RETAB"', 'INST(STG_family, "STG/STZG/ST2G/STZ2G/LDG"',
):
    assert decoder.count(marker) == 1, marker
translator=SELECTED_TRANSLATOR.read_text()
guard="#if defined(EDEN_NS2_A64_V81_V85)"
assert translator.count(guard)==1
guarded=translator.split(guard,1)[1].split("#endif",1)[0]
for unit in ("load_store_atomic.cpp","memory_tagging.cpp","pointer_authentication.cpp"):
    assert guarded.count(unit)==1

compiler=(shutil.which("g++") if sys.platform=="linux" else shutil.which("clang++"))
compiler=compiler or shutil.which("clang++") or shutil.which("g++")
assert compiler
flags=[]; env=os.environ.copy()
if sys.platform=="darwin":
    sdk15=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    sdk26=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
    if sdk15.is_dir(): env["SDKROOT"]=str(sdk15)
    if sdk26.is_dir(): flags += ["-target","arm64-apple-macos15","-nostdinc++","-isystem",str(sdk26/"usr/include/c++/v1")]
deps=ROOT/"vendor/sources/eden-cpm"
roots=[ACTIVE_ROOT,BASE_ROOT,ROOT/"vendor/sources/eden/src",deps/"fmt/12.1.0/include"]+list((deps/"boost/boost-1.90.0/libs").glob("*/include"))
incs=["-I"+str(p) for p in roots if p.is_dir()]
syntax=subprocess.run([compiler,"-std=c++20","-O0","-fsyntax-only","-Wno-unused-parameter","-DFMT_HEADER_ONLY","-DEDEN_NS2_A64_V81_V85=1",*flags,*incs,str(SELECTED_TRANSLATOR)],capture_output=True,text=True,env=env,timeout=120)
assert syntax.returncode==0, syntax.stderr[-7000:]
print("P0_2_SHARED_A64_V81_V85_PASS files=8 canonical_owner=1 PS5_runtime=unverified")
