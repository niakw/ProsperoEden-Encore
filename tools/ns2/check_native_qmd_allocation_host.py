#!/usr/bin/env python3
"""Execute real QMD scheduler state-insertion failure under UBSan on host."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
HEADER=ROOT/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/native_qmd.h'
TEST=ROOT/'tools/ns2/test_native_qmd_allocation.cpp'
REGRESSIONS=ROOT/'tools/ns2/test_native_qmd_scheduler.cpp'
source=HEADER.read_text()
assert 'catch (const std::bad_alloc&)' in source
assert 'return "QMD state allocation failed";' in source
assert source.index('states.try_emplace(request.address)') < source.index('if (state.poisoned)')
compiler=shutil.which('clang++') or shutil.which('g++')
assert compiler
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
env=os.environ.copy()
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='encore-qmd-allocation-') as tmp:
    for test in (TEST,REGRESSIONS):
        for opt in (0,2):
            exe=Path(tmp)/(test.stem+f'-O{opt}')
            cmd=[compiler,'-std=c++20',f'-O{opt}', '-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',
                 '-I'+str(HEADER.parents[1]),str(test),'-o',str(exe)]
            built=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=60)
            assert built.returncode==0,built.stderr[-3800:]
            ran=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=20)
            assert ran.returncode==0,ran.stderr[-3800:]
            if test==TEST:
                assert 'P2_7_REAL_QMD_ALLOCATION_RECOVERY_PASS' in ran.stdout
            print('P2_7_NATIVE_QMD_SCHEDULER_HOST_PASS',test.name,
                  Path(compiler).name,f'O{opt}',flush=True)
