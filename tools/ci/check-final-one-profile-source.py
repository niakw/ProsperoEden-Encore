#!/usr/bin/env python3
"""Verify one native PS5 app and independently chosen package/release policy.

The CMake graph must never depend on a P5, DEV or final-release profile.
Building a native app is distinct from publishing a release. This checks
source/build configuration only; no SDK, package, PS5 execution or pixels.
"""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
pkg=(root/'tools/build-package.sh').read_text()
build=(root/'tools/build-headless-native.sh').read_text()
cm=(root/'headless/CMakeLists.txt').read_text()
validator=(root/'tools/ci/check-release-experiments.py').read_text()
main=(root/'headless/main.cpp').read_text()
nup=(root/'headless/nup_v1_runtime.cmake').read_text()
workflow=(root/'.github/workflows/build-040-zbic.yml').read_text()

assert pkg.count('release|release-stage)')==1
assert 'export EDEN_PACKAGE_DIR="$root/build/release/PPSA99008"' in pkg
assert 'export EDEN_PS5_VULKAN=ON EDEN_VULKAN_DRIVER=RADV' in pkg
assert 'bash tools/build-headless-native.sh --graphics' in pkg
assert 'bash tools/package-headless-native.sh --integration' in pkg
assert 'if [[ $mode == release ]]; then' in pkg
assert 'elif [[ $mode == release-stage ]]; then' in pkg
assert 'python3 -B headless/check_package.py --check' in pkg
assert 'bash tools/build-package.sh release-stage' in workflow
assert 'EDEN_STAGE_DIR: build/release/PPSA99008' in workflow
assert 'build/dev/PPSA99008' not in workflow
assert "if: >-\n      ${{ github.event_name == 'workflow_dispatch' ||" in workflow
assert "contains(github.event.head_commit.message || '', '[full-build]')" in workflow
assert "(github.event_name == 'workflow_dispatch' && inputs.publish)" in workflow
assert "needs.build.result == 'success'" in workflow
assert 'if: ${{ false }}' not in workflow
assert 'EDEN_FINAL_RELEASE_PROFILE=ON' not in pkg
assert 'EDEN_DEV_PROFILE=ON' not in pkg

assert build.count('-DPS5_NATIVE=ON')==1
assert build.count('-DEDEN_PS5_VULKAN=ON')==1
assert build.count('-DEDEN_VULKAN_DRIVER=RADV')==1
assert '-DENABLE_OPENGL="$graphics" -DEDEN_PS5_OPENGL="$graphics"' in build
assert 'graphics=ON' in build and 'graphics=OFF' not in build
for forbidden in ('EDEN_FINAL_RELEASE_PROFILE','EDEN_DEV_PROFILE',
                  'EDEN_NS2_NATIVE_GPU_DISPATCH=1', 'EDEN_NS2_EXEFS_EXPERIMENTAL',
                  'EDEN_GUEST_WRITE_BRIDGE_DEV=ON'):
    assert forbidden not in build, forbidden
    assert forbidden not in cm, forbidden

assert 'set(EDEN_G11_PROFILE normal)' in cm
assert 'a64_interface_standard.cpp' in cm
assert 'a64_interface_shared.cpp' not in cm
assert 'EDEN_SHARED_JIT_AVAILABLE=0' in cm
assert 'EDEN_JIT_COMPILE_BATCH_AVAILABLE=0' in cm
assert 'if(PS5_NATIVE AND (NOT EDEN_PS5_VULKAN OR NOT EDEN_PS5_OPENGL OR' in cm
assert 'NOT EDEN_VULKAN_DRIVER STREQUAL "RADV"' in cm
assert cm.count('include("${CMAKE_CURRENT_LIST_DIR}/nup_v1_runtime.cmake")')==1
assert 'option(EDEN_NUP_V1_RUNTIME' not in nup
assert 'EDEN_FINAL_RELEASE_PROFILE' not in nup
for symbol in ('nup_v1_native_loader.cpp','nup_v1_aoc_service.cpp',
               'target_compile_definitions(eden-headless PRIVATE EDEN_NUP_V1_RUNTIME=1)',
               'target_compile_definitions(eden-metadata PRIVATE EDEN_NUP_V1_RUNTIME=1)'):
    assert symbol in nup,symbol
assert 'experimental_sparse_jit = true;' in main
assert 'if (!Common::ProbeSparseJitAlias())' in main
assert 'throw std::runtime_error("PS5 sparse JIT alias preflight failed")' in main
for flag in ('"PS5_NATIVE"', '"EDEN_PS5_VULKAN:BOOL": "ON"',
             '"EDEN_VULKAN_DRIVER:STRING": "RADV"'):
    assert flag in validator, flag
assert '"EDEN_FINAL_RELEASE_PROFILE:BOOL"' not in validator
assert '"EDEN_NUP_V1_RUNTIME:BOOL": "OFF"' not in validator
assert 'EDEN_JIT_SPARSE_TRIM' in validator
assert 'DISALLOWED_ACTIVE' in validator
subprocess.run([sys.executable,'-B',str(root/'tools/ci/check-release-experiments.py'),
                '--self-test'],check=True,timeout=15)
print('ENCORE_SINGLE_NATIVE_PROFILE_SOURCE_PASS build_profile=1 packaging=operator release=independent nup=always jit=normal GPU=RADV')
