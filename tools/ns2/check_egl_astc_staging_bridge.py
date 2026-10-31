#!/usr/bin/env python3
"""N59: execute real ASTC batch transaction with simulated GPU callbacks."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
N55=(ROOT/'headless/ns2/eglantine/video_core/texture_cache/ns2_astc_layer_plan.h').read_text()
N59=(ROOT/'headless/ns2/eglantine/video_core/texture_cache/ns2_astc_staging_bridge.h').read_text()
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
assert 'EDEN_NS2_ASTC_LAYER_DECODE_EXPERIMENTAL OR' in CMAKE
assert 'class AstcDirtyLayerPlanner' in N55
for check in ('planner.Commit(plan)', 'planner.Invalidate()', 'read_guest(', 'decode_batch(', 'guest_gpu_base + copy.guest_offset'):
    assert check in N59,check
with tempfile.TemporaryDirectory(prefix='n59-astc-staging-') as tmp:
    for cxx in ('clang++','g++'):
        exe=Path(tmp)/('test-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
                        '-fsanitize=undefined','-fno-sanitize-recover=all',
                        '-I',str(ROOT/'headless/ns2/eglantine'),
                        str(ROOT/'tools/ns2/test_egl_astc_staging_bridge.cpp'),
                        '-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('N59_BOUNDED_ASTC_STAGING_ORACLE_PASS')
