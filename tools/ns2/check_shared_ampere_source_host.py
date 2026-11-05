#!/usr/bin/env python3
"""Verify P0.2 Ampere source selection without overriding the NS1 BufferCache ABI."""
from pathlib import Path
import os
import platform
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
section = cmake.split("# P0.2: Compile the same native Ampere-to-Maxwell frontend", 1)[1].split("# N3m: compile a renderer-callable", 1)[0]
assert "set(EDEN_SHARED_NS2_AMPERE_CORE OFF)" in section
assert "if(PS5_NATIVE AND EDEN_FINAL_RELEASE_PROFILE AND" in section
assert "EDEN_REVIEWED_DUAL_NPDM AND EDEN_PS5_VULKAN)" in section
assert "if(EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL OR EDEN_SHARED_NS2_AMPERE_CORE)" in section
research=section.split("if(EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL)",1)[1].split("    else()",1)[0]
shared=section.split("    else()",1)[1].split("    endif()",1)[0]
assert "EDEN_NS2_SHADER_RESOURCE_ROOT" in research
assert "PORT_BUILD_DIR" in shared
assert shared.count("target_include_directories(")==3
assert not re.search(r"target_include_directories\([^)]*EDEN_NS2_SHADER_RESOURCE_ROOT",shared)
assert "buffer_cache/buffer_cache_base.h" not in shared
assert "configure_file(" in shared

pinned=(ROOT/"vendor/sources/eden/src/shader_recompiler/frontend/ir/attribute.h").read_text()
reviewed=(ROOT/"vendor/encore-active/ns2-runtime/shader_resource/include/shader_recompiler/frontend/ir/attribute.h").read_text()
assert pinned.count("attribute <= Attribute::Generic31X") == 1
assert reviewed.count("attribute <= Attribute::Generic31W") == 1
assert reviewed.replace(
    "    // Generic31 is a complete vec4, not X only. Y/Z/W carry the final\n"
    "    // vertex/geometry varying and must be classified like slots 0..30.\n"
    "    return attribute >= Attribute::Generic0X && attribute <= Attribute::Generic31W;",
    "    return attribute >= Attribute::Generic0X && attribute <= Attribute::Generic31X;") == pinned
assert "NUM_STORAGE_BUFFERS = 16" in (ROOT/"vendor/sources/eden/src/video_core/buffer_cache/buffer_cache_base.h").read_text()
assert "NUM_STORAGE_BUFFERS = 32" in (ROOT/"vendor/encore-active/ns2-runtime/shader_resource/include/video_core/buffer_cache/buffer_cache_base.h").read_text()

selector=section[section.index("set(EDEN_SHARED_NS2_AMPERE_CORE OFF)"):section.index(
    "if(EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL OR EDEN_SHARED_NS2_AMPERE_CORE)")]
with tempfile.TemporaryDirectory(prefix="encore-ampere-selector-") as tmp:
    script=Path(tmp)/"select.cmake"
    for native,release,npdm,vulkan,expected in (
        (True,True,True,True,"ON"),
        (False,True,True,True,"OFF"),
        (True,False,True,True,"OFF"),
        (True,True,False,True,"OFF"),
        (True,True,True,False,"OFF"),
    ):
        vars=(("PS5_NATIVE",native),("EDEN_FINAL_RELEASE_PROFILE",release),
              ("EDEN_REVIEWED_DUAL_NPDM",npdm),("EDEN_PS5_VULKAN",vulkan))
        script.write_text("\n".join(
            f"set({name} {'ON' if val else 'OFF'})" for name,val in vars)
            + "\n" + selector +
            '\nmessage(STATUS "SHARED_AMPERE=${EDEN_SHARED_NS2_AMPERE_CORE}")\n')
        output=subprocess.run(["cmake","-P",str(script)],capture_output=True,text=True,timeout=10)
        assert output.returncode==0 and "SHARED_AMPERE="+expected in output.stdout, (output.stdout,output.stderr)
print("P0_2_SHARED_AMPERE_SELECTOR_PASS qualified=ON research=OFF desktop=OFF")

ampere=ROOT/"vendor/encore-active/ns2-runtime/ampere"
files=(
    "shader_recompiler/frontend/ampere/probe.cpp",
    "shader_recompiler/frontend/ampere/lower_bridge.cpp",
    "shader_recompiler/frontend/ampere/maxwell_image.cpp",
    "shader_recompiler/frontend/ampere/capture.cpp",
    "shader_recompiler/frontend/ampere/translation_cache.cpp",
    "shader_recompiler/frontend/ampere/maxwell_environment.cpp",
    "shader_recompiler/frontend/ampere/ir_bridge.cpp",
    "video_core/native_shader_capture.cpp",
)
compiler=shutil.which("clang++")
assert compiler
deps=ROOT/"vendor/sources/eden-cpm"
includes=[ROOT/"vendor/sources/eden/src",ampere,deps/"fmt/12.1.0/include"]
includes+=sorted((deps/"boost/boost-1.90.0/libs").glob("*/include"))
assert len(includes)>100
cmd=[compiler,"-std=c++20","-O0","-fsyntax-only","-DPS5_NATIVE=1",
     *["-I"+str(path) for path in includes]]
env=os.environ.copy()
if platform.system()=="Darwin":
    sdk=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
    assert (sdk/"usr/include/c++/v1/__thread/jthread.h").is_file()
    env["SDKROOT"]=str(sdk)
    cmd+=["-target","arm64-apple-macos15","-nostdinc++","-isystem",
          str(sdk/"usr/include/c++/v1")]
for name in files:
    assert (ampere/name).is_file()
    result=subprocess.run(cmd+[str(ampere/name)],capture_output=True,text=True,env=env,timeout=90)
    assert result.returncode==0,(name,result.stderr[-5000:])
    print("P0_2_REAL_AMPERE_OWNER_PASS",name)
print("P0_2_SHARED_AMPERE_COMPILE_ONLY_PASS units=8 ns1_cache_abi=PINNED ps5=NOT_TESTED")
