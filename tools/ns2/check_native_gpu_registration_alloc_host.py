#!/usr/bin/env python3
"""Prove native GPU process/channel/engine fail-closed allocation semantics.

Injects real std::bad_alloc at each native admission map through global new,
then tests process/channel generation epochs and NS1-unbound state. Host only.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
PROCESS=ROOT/'vendor/encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_process_registry.h'
CHANNEL=ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/native_gpu_channel_registry.h'
CPP=ROOT/'tools/ns2/test_native_gpu_registration_alloc.cpp'
for header in (PROCESS,CHANNEL):
    assert header.is_file()
    data=header.read_text()
    assert '#include <new>' in data
    assert 'catch (const std::bad_alloc&)' in data
    assert 'std::map<' in data
assert CHANNEL.read_text().count('catch (const std::bad_alloc&)')==3
assert 'last_channel_generation + 1' in CHANNEL.read_text()
assert '++last_channel_generation;' in CHANNEL.read_text()
compiler=shutil.which('clang++') or shutil.which('g++')
assert compiler
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
env=os.environ.copy()
if sdk.is_dir():env['SDKROOT']=str(sdk)
inc=['-I'+str(ROOT/'vendor/encore-active/ns2-runtime/hle'),
     '-I'+str(ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu')]
with tempfile.TemporaryDirectory(prefix='encore-native-registry-alloc-') as work:
    for opt in (0,2):
        exe=Path(work)/f'gpu-registry-O{opt}'
        command=[compiler,'-std=c++20',f'-O{opt}', '-Wall','-Wextra',
                 '-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
                 *inc,str(CPP),'-o',str(exe)]
        built=subprocess.run(command,capture_output=True,text=True,env=env,timeout=65)
        assert built.returncode==0,built.stderr[-5500:]
        executed=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=20)
        assert executed.returncode==0,executed.stderr[-5500:]
        print('P0_2_NATIVE_GPU_REGISTRY_FAILCLOSED_PASS',Path(compiler).name,f'O{opt}',flush=True)
