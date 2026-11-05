#!/usr/bin/env python3
"""P0 compile graph owner proof for the single unified PS5 native product.

The original research-selector assertions are obsolete. Refuse their return;
configure the real native source-owner CMake segment instead of inspecting
legacy OFF flags or accepting mocked guest frames.
"""
from pathlib import Path
import os
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
cmake=(root/'headless/CMakeLists.txt').read_text()
assert 'EDEN_FINAL_RELEASE_PROFILE' not in cmake
assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' not in cmake
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in cmake
assert 'if(EDEN_SHARED_NS2_AMPERE_CORE)' in cmake
assert 'if(EDEN_SHARED_NS2_SPIRV_COMPILER)' in cmake
assert 'if(NOT eden_ns2_match_count EQUAL 1)' in cmake or 'EQUAL -1' in cmake
assert 'configure_file("${EDEN_NS2_RASTERIZER_INTERFACE}"' in cmake
# Run the independently maintained, exact CMake source-graph configure proof.
source=root/'tools/ns2/check_unified_native_gpu_graph_host.py'
assert source.is_file()
env=os.environ.copy()
if sys.platform=='darwin':
    sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if sdk.is_dir():env['SDKROOT']=str(sdk)
run=subprocess.run([sys.executable,'-B',str(source)],cwd=root,env=env,
                   capture_output=True,text=True,timeout=85)
assert run.returncode==0,run.stdout[-2500:]+run.stderr[-2500:]
assert 'UNIFIED_NATIVE_GPU_SOURCE_GRAPH_PASS' in run.stdout,run.stdout
build_workflow=(root/'.github/workflows/build-040-zbic.yml').read_text()
assert "if: >-\n      ${{ github.event_name == 'workflow_dispatch' ||" in build_workflow
assert "contains(github.event.head_commit.message || '', '[full-build]')" in build_workflow
assert "(github.event_name == 'workflow_dispatch' && inputs.publish)" in build_workflow
assert "needs.build.result == 'success'" in build_workflow
assert 'if: ${{ false }}' not in build_workflow
# An archived alternate workflow remains unselected; only the single real
# native app/package workflow can be invoked deliberately by its operator.
legacy=(root/'.github/workflows/ns2-native-ps5-research.yml').read_text()
assert 'if: ${{ false }}' in legacy
print('P0_SINGLE_NATIVE_GPU_CMAKE_GRAPH_PASS build_modes=1 native_owners=registered ps5_console=not_tested')
