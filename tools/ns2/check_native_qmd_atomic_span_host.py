#!/usr/bin/env python3
"""P2.3 true post-translation atomic spans against live QMD3 descriptor lengths."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
# Prove that the admitted masked IR flows through the real renderer owner
# and its emitted SPIR-V index, rather than living only in this host test.
ampere=ROOT/'vendor/encore-active/ns2-runtime/ampere'
bridge=(ampere/'shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp').read_text()
gpu_owner=(ampere/'video_core/ns2_shader_spirv_compile.cpp').read_text()
atomic_owner=(ampere/'shader_recompiler/frontend/ampere/native_atomic_span.h').read_text()
emitter=(ROOT/'vendor/sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_atomic.cpp').read_text()
assert 'if (!NativeQmdAtomicStorageIRAdmissible(ir, profile))' in bridge
assert 'const auto atomic_spans = CollectNativeQmdAtomicSpans(ir);' in bridge
assert 'NativeQmdAtomicSpansFitBindings(' in gpu_owner
assert 'NativeQmdAtomicMaximumByteOffset(offset, width)' in atomic_owner
assert 'addition->GetOpcode() != Shader::IR::Opcode::IAdd32' in atomic_owner
assert '*and_mask > std::numeric_limits<u32>::max() - width - base' in atomic_owner
assert 'storage.gpu_address & (span.width - 1U)' in atomic_owner
assert 'Shader::IR::Opcode::ShiftLeftLogical32' in atomic_owner
assert 'shift >= 32' in atomic_owner
assert '*mask > (std::numeric_limits<u32>::max() >> shift)' in atomic_owner
assert 'instruction->GetOpcode() != Shader::IR::Opcode::BitwiseAnd32' in atomic_owner
assert 'const Id index{StorageIndex(ctx, offset, element_size)};' in emitter
assert 'return ctx.OpShiftRightLogical(ctx.U32[1], index, shift_id);' in emitter
ir=ROOT/'vendor/sources/eden/src/shader_recompiler/frontend/ir'
srcs=[ROOT/'tools/ns2/test_native_qmd_atomic_span.cpp'] + [
    ir/(name+'.cpp') for name in ('basic_block','microinstruction','opcodes','value')]
fmt=ROOT/'vendor/sources/fmt/include'
boost=ROOT/'vendor/sources/eden-cpm/boost/boost-1.90.0/libs'
includes=[fmt,ROOT/'vendor/encore-active/ns2-runtime/ampere',
          ROOT/'vendor/encore-active/ns2-runtime/gpu_dispatch',
          ROOT/'vendor/sources/eden/src',*sorted(boost.glob('*/include'))]
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir(): env['SDKROOT']=str(sdk)
compilers=list(dict.fromkeys(filter(None,[shutil.which('clang++'),shutil.which('g++')])))
assert compilers
with tempfile.TemporaryDirectory(prefix='encore-atomic-plan-') as tmp:
    for compiler in compilers:
        for optimization in ('-O0','-O2'):
            exe=Path(tmp)/('test-'+Path(compiler).name+optimization)
            args=[compiler,'-std=c++20',optimization,
                  '-Wall','-Wextra','-Werror','-Wno-unused-parameter',
                  '-DFMT_HEADER_ONLY','-fsanitize=undefined',
                  '-fno-sanitize-recover=all','-ffunction-sections',
                  '-fdata-sections']
            args += ['-I'+str(path) for path in includes if path.is_dir()]
            args += [str(path) for path in srcs]
            args += ['-Wl,-dead_strip' if sys.platform=='darwin'
                     else '-Wl,--gc-sections','-o',str(exe)]
            done=subprocess.run(args,env=env,capture_output=True,text=True,timeout=90)
            assert done.returncode==0,(compiler,optimization,done.stderr[-6500:])
            test=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=35)
            assert test.returncode==0,(compiler,optimization,test.stdout,test.stderr)
            print(Path(compiler).name,optimization,test.stdout.strip(),flush=True)
