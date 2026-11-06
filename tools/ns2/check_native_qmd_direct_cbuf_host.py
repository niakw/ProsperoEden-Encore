#!/usr/bin/env python3
"""P2.3: compile real shared IR blocks/opcodes and native QMD3 CBUF guard."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[2]
ir=root/'vendor/sources/eden/src/shader_recompiler/frontend/ir'
files=[root/'tools/ns2/test_native_qmd_direct_cbuf.cpp'] + [
    ir/(name+'.cpp') for name in ('basic_block','microinstruction','opcodes','value')]
fmt=root/'build-ns2-a64/fmt/include'
if not (fmt/'fmt/core.h').exists():fmt=root/'vendor/sources/fmt/include'
includes=[fmt,root/'vendor/encore-active/ns2-runtime/ampere',
          root/'vendor/sources/eden/src']
# The local M1 build uses pinned modular CPM Boost; Linux CI has Boost headers
# in the compiler's system search path. Do not vendor or rewrite either.
for cache in (Path.home()/'.cache').glob('ps5-eden-*/source/.cache/cpm/boost/*/libs'):
    includes.extend(sorted(folder for folder in cache.rglob('include')
                           if (folder/'boost').is_dir()))
env=dict(os.environ)
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.exists():env['SDKROOT']=str(sdk)
# The real Ampere IR normalizer must reject U64 immediate and computed
# operands before calling Value::U32() or building SPIR-V access chains.
header = (root/'vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_indirect_cbuf.h').read_text()
assert 'bank_value.Type() != Shader::IR::Type::U32' in header
assert 'offset_value.Type() != Shader::IR::Type::U32' in header
assert 'index.Type() != Shader::IR::Type::U32' in header
assert 'offset.Type() != Shader::IR::Type::U32' in header
assert 'byte_offset.Type() != Shader::IR::Type::U32' in header
atomic_header=(root/'vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_global_atomic_binding.h').read_text()
bridge=(root/'vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp').read_text()
assert 'NativeAtomic::Rewrite(ir)' in bridge
assert 'Opcode::PackUint2x32' in atomic_header
assert 'Opcode::GetCbufU32x2' in atomic_header
assert 'rec.cbuf_offset == address->descriptor' in atomic_header
assert 'Opcode::CompositeConstructU32x2' in atomic_header
assert 'left_pointer == right_pointer' in atomic_header
assert 'Opcode::StorageAtomicAddF32' in atomic_header
assert 'Opcode::StorageAtomicMaxF16x2' in atomic_header

compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
with tempfile.TemporaryDirectory(prefix='encore-qmd-cbuf-') as temp:
    for compiler in compilers:
        exe=Path(temp)/Path(compiler).name
        args=[compiler,'-std=c++20','-O1','-Wall','-Wextra','-Werror',
              '-Wno-unused-parameter','-DFMT_HEADER_ONLY',
              '-fsanitize=undefined','-fno-sanitize-recover=all',
              '-ffunction-sections','-fdata-sections']
        args += ['-I'+str(path) for path in includes]
        args += [str(file) for file in files]
        args += ['-Wl,-dead_strip' if sys.platform=='darwin' else '-Wl,--gc-sections',
                 '-o',str(exe)]
        built=subprocess.run(args,env=env,capture_output=True,text=True,timeout=100)
        assert built.returncode==0,(compiler,built.stderr[-3000:])
        test=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=20)
        assert test.returncode==0,(compiler,test.stderr[-3000:])
        print(Path(compiler).name,test.stdout.strip(),flush=True)
