#!/usr/bin/env python3
"""P2.4: test real Ampere scalar ALU, including BREV/POPC multi-source and IABS literals."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SHADER=ROOT/'vendor/encore-active/ns2-runtime/ampere'
SOURCE=ROOT/'tools/ns2/test_ampere_scalar_alu_sources.cpp'
LOWER=(SHADER/'shader_recompiler/frontend/ampere/lower_to_maxwell.h').read_text()
assert 'case 0x307: case 0xb07:' in LOWER
assert 'constant_source && (!valid_cbuf() || insn.Bits(54, 5) >= 18)' in LOWER
assert 'constant_source ? cbuf()' in LOWER
assert 'case 0x207: case 0x807: case 0xa07: case 0xc07:' in LOWER
assert 'case 0x20a: case 0x80a: case 0xa0a: case 0xc0a:' in LOWER
assert 'case 0x308: case 0x908: case 0xb08: case 0xd08:' in LOWER
assert 'uses_uniform_bank |= op == 0x4a4 || op == 0x2bf || op == 0xc07' in LOWER
assert 'case 0x2bf: { // UPOPC:' in LOWER
assert 'case 0x213: case 0x813: case 0xa13: case 0xc13:' in LOWER
assert 'case 0x301: case 0x901: case 0xb01: case 0xd01:' in LOWER
assert 'case 0x300: case 0x900: case 0xb00: case 0xd00:' in LOWER
assert 'opcode == 0x900 ? 0 : insn.Bits(63, 1)' in LOWER
assert 'case 0x309: case 0x909: case 0xb09: case 0xd09:' in LOWER
assert 'opcode == 0x909 ? 0 : insn.Bits(63, 1)' in LOWER
assert 'opcode == 0x4a4 ? 0x424' in LOWER
assert 'native uniform multiply immediate predication' in LOWER
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
            assert 'P2_4_REAL_AMPERE_SCALAR_ALU_SOURCE_PASS' in run.stdout
            print('P2_4_SCALAR_ALU_REAL_LOWER_HOST_PASS',Path(compiler).name,f'O{opt}',flush=True)
