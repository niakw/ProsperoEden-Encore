#!/usr/bin/env python3
"""G08 real Ampere instruction CFG handoff: execute maintained C++ owners.

Compiles the genuine Ampere-to-Maxwell image/bridge and Eden Maxwell CFG
against the maintained reviewed BRX and branch/exit fixtures. Both success
and invalid-stage/unknown-target refusals are checked by the linked binary.
This certifies the bounded reviewed ISA/CFG contract, not unknown instruction
families, a Vulkan render, or PS5 gameplay.
"""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
V=ROOT/"vendor"
SOURCE=ROOT/"tools/ns2/test_ampere_maxwell_cfg.cpp"
source=SOURCE.read_text()
for necessary in (
    "Shader::Maxwell::Flow::CFG",
    "branch_cfg.Functions().front().blocks.empty()",
    "NativeIndirectBranchPlan indirect_plan{}",
    "TranslateNativeAddress(8*16)",
    "unknown_image",
    "Compute stage rejected before GPU IR bridge",
    "NS2 actual Maxwell CFG and IR handoff ABI: PASS",
):
    assert necessary in source, f"real CFG witness missing: {necessary}"
shader=V/"encore-active/ns2-runtime/ampere"
eden=V/"sources/eden/src"
srcs=[SOURCE,*[
    shader/("shader_recompiler/frontend/ampere/"+name)
    for name in ("ir_bridge.cpp","probe.cpp","lower_bridge.cpp",
                 "maxwell_image.cpp","maxwell_environment.cpp")],
    *[eden/("shader_recompiler/frontend/maxwell/"+name)
      for name in ("control_flow.cpp","decode.cpp","opcodes.cpp",
                   "indirect_branch_table_track.cpp")],
    eden/"shader_recompiler/frontend/ir/condition.cpp"]
assert all(x.is_file() for x in srcs)
fmt=V/"sources/eden-cpm/fmt/12.1.0/include"
if not fmt.is_dir():
    fmt=V/"sources/fmt/include"
assert fmt.is_dir(),"vendored fmt source required, no network fallback"
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Clang/GCC required"
env=os.environ.copy()
if platform.system()=="Darwin":
    sdk=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    if sdk.is_dir():env["SDKROOT"]=str(sdk)
with tempfile.TemporaryDirectory(prefix="eden-g08-native-cfg-") as tmp:
    for cxx in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(tmp)/(Path(cxx).name+opt)
            argv=[cxx,"-std=c++20",opt,"-DFMT_HEADER_ONLY",
                  "-Werror","-Wno-unused-parameter",
                  "-pthread",
                  "-I"+str(fmt),"-I"+str(shader),"-I"+str(eden),
                  *map(str,srcs),"-o",str(exe)]
            proc=subprocess.run(argv,capture_output=True,text=True,
                                timeout=130,env=env)
            assert proc.returncode==0,proc.stderr[-6000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,
                               timeout=35,env=env)
            assert run.returncode==0,(run.stdout[-3000:],run.stderr[-5000:])
            assert "NS2 actual Maxwell CFG and IR handoff ABI: PASS" in run.stdout,run.stdout
            print("G08_REAL_AMPERE_MAXWELL_CFG_OWNER_PASS",Path(cxx).name,opt,
                  "reviewed_brx=lowered native_pc_relocated=checked"
                  " invalid_stage=refused cfg=nonempty",flush=True)
