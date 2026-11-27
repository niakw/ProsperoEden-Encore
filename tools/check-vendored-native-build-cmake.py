#!/usr/bin/env python3
"""Guard complete, tracked native CMake fork against generated/unreviewed changes.

This is one migrated build-configuration translation unit, not a certificate
that remaining CMake write_derived code paths have been consolidated.
"""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
original = (root/"vendor/sources/eden/src/CMakeLists.txt").read_text()
active = (root/"vendor/encore-active/eden/src/CMakeLists.txt").read_text()
installer = (root/"tools/install-vendored-eden-build-flags.py").read_text()
stager = (root/"tools/prepare-build.sh").read_text()
builder = (root/"tools/build-headless-native.sh").read_text()

old = '$<$<COMPILE_LANGUAGE:C,CXX>:-Wno-error-all>'
new = '$<$<COMPILE_LANGUAGE:C,CXX>:-Wno-error=all>'
assert original.count(old) == 1
assert old not in active
assert active == original.replace(old, new), "active native CMake has unreviewed drift"
assert '("src/CMakeLists.txt",b"-Wno-error-all>",b"-Wno-error=all>")' in installer
assert '("src/common/scm_rev.cpp.in"' in installer
assert 'assert current==old' in installer
assert 'python3 -B tools/install-vendored-eden-build-flags.py "$eden"' in stager
assert 'CMAKE_PROJECT_yuzu_INCLUDE="$root/headless/inject.cmake"' in builder
# Native platform identity is inherited before target creation. Host builds
# do not load the PS5 toolchain; never define PS5_NATIVE=0 because #ifdef
# guards treat zero as enabled.
toolchain = (root/"headless/ps5.cmake").read_text()
inject = (root/"headless/inject.cmake").read_text()
assert 'set(PS5_NATIVE 1 CACHE BOOL "Encore PS5 native platform")' in toolchain
assert 'if(NOT PS5_NATIVE)' in toolchain
native_block = inject.split("if(PS5_NATIVE)\n", 1)[1]
assert native_block.count("add_compile_definitions(PS5_NATIVE=1)") == 1
assert native_block.index("add_compile_definitions(PS5_NATIVE=1)") < native_block.index("add_subdirectory(")
assert "ENCORE_NATIVE_PLATFORM_GRAPH_PASS" in builder
assert builder.index("PY_NATIVE_PLATFORM") < builder.index('if [[ ${EDEN_SKIP_PREBUILD_SOURCE_CHECKS:-0} != 1 ]]')
clang = shutil.which("clang++-18") or shutil.which("clang++")
if clang:
    run = subprocess.run([clang, "-Wno-error=all", "-x", "c++", "-fsyntax-only", "-"],
                         input="int main(){return 0;}\n",
                         text=True, capture_output=True, timeout=10)
    assert run.returncode == 0, run.stderr
    assert "unknown" not in run.stderr.casefold(), run.stderr
print("PASS: complete tracked native CMake fork matches upstream except one supported Clang flag")
print("PASS: existing native stage installs tracked CMake and SCM forks with drift rejection")
