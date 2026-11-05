#!/usr/bin/env python3
"""P2.4: real Ampere FRND CBUF lowering and ISA-field gate (host only)."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SHADER=ROOT/'vendor/encore-active/ns2-runtime/ampere'
SOURCE=ROOT/'tools/ns2/test_ampere_frnd_cbuf.cpp'
LOWER=(SHADER/'shader_recompiler/frontend/ampere/lower_to_maxwell.h').read_text()
assert 'case 0x307: case 0xb07:' in LOWER
assert 'constant_source && (!valid_cbuf() || insn.Bits(54, 5) >= 18)' in LOWER
assert 'constant_source ? cbuf()' in LOWER
TEST=(SOURCE).read_text()
assert 'FirstUnreviewedBit(inst,*row)' in TEST
compilers=list(dict.fromkeys(c for c in (shutil.which('clang++'),shutil.which('g++')) if c))
assert compilers,'C++ compiler missing'
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir(): env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='encore-frnd-cbuf-') as scratch:
    for compiler in compilers:
        for opt in (0,2):
            exe=Path(scratch)/f'{Path(compiler).name}-{opt}'
            cmd=[compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra',
                 '-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
                 '-I'+str(SHADER),'-I'+str(ROOT/'vendor/sources/eden/src'),
                 str(SOURCE),str(SHADER/'shader_recompiler/frontend/ampere/probe.cpp'),
                 str(SHADER/'shader_recompiler/frontend/ampere/lower_bridge.cpp'),'-o',str(exe)]
            build=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=90)
            assert build.returncode==0,build.stderr[-3500:]
            run=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=20)
            assert run.returncode==0,run.stderr[-3500:]
            assert 'P2_4_REAL_FRND_CBUF_LOWER_PASS' in run.stdout
            print('P2_4_FRND_CBUF_REAL_LOWER_HOST_PASS',Path(compiler).name,f'O{opt}',flush=True)
