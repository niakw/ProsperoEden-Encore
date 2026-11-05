#!/usr/bin/env python3
"""P0.2: test production-selected LDAPR decode and real Dynarmic translation.

CMake generates exactly four files from pinned Dynarmic for the release,
without copying unverified research RETAA, LSE or CAS implementations.
Host tests compile the unmodified A64 translation unit and execute Dynarmic's
real decoder; no PS5 or full emulator build is performed.
"""
from pathlib import Path
import difflib
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
SCRIPT=ROOT/'headless/shared_a64_ldapr.cmake'
BASE=ROOT/'vendor/sources/eden/src/dynarmic/src'
REL=Path('dynarmic/frontend/A64')
FILES=('decoder/a64.h','decoder/a64.inc','translate/impl/impl.h',
       'translate/impl/load_store_exclusive.cpp')
assert 'set(EDEN_SHARED_NS2_A64_LDAPR ON)' in CMAKE
assert 'if(PS5_NATIVE AND EDEN_FINAL_RELEASE_PROFILE AND EDEN_REVIEWED_DUAL_NPDM)' in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_LDAPR_OUTPUT_ROOT}")' in CMAKE
assert 'if(EDEN_NS2_A64_EXPERIMENTAL)' in CMAKE
assert 'NOT EDEN_NS2_A64_EXPERIMENTAL' not in CMAKE.split('# P0.2: limited A64 LDAPR promotion',1)[1].split('# Six Switch 2',1)[0]
assert all((BASE/REL/f).is_file() for f in FILES)
# Run the EXACT production file transforms, not a Python reimplementation.

def transform(base: Path,out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(['cmake',f'-DEDEN_A64_LDAPR_SOURCE_ROOT={base}',
                           f'-DEDEN_A64_LDAPR_OUTPUT_ROOT={out}','-P',str(SCRIPT)],
                          capture_output=True,text=True,timeout=30)

TEST_CPP=r'''
#include <cassert>
#include <cstdio>
#include "dynarmic/frontend/A64/decoder/a64.h"
#include "dynarmic/frontend/A64/translate/impl/impl.h"
int main() {
    using Dynarmic::A64::TranslatorVisitor;
    for (auto instruction : {0x38BFC000U, 0x78BFC000U,
                             0xB8BFC000U, 0xF8BFC000U}) {
        const auto op=Dynarmic::A64::GetName<TranslatorVisitor>(instruction);
        assert(op && *op == "LDAPR");
    }
    const auto cas=Dynarmic::A64::GetName<TranslatorVisitor>(0xC8A07C00U);
    const auto ldadd=Dynarmic::A64::GetName<TranslatorVisitor>(0xF8200000U);
    assert(!cas || *cas != "CAS");
    assert(!ldadd || *ldadd != "LDADD");
    const auto ret=Dynarmic::A64::GetName<TranslatorVisitor>(0xD65F03C0U);
    const auto reta=Dynarmic::A64::GetName<TranslatorVisitor>(0xD65F0BFFU);
    const auto retb=Dynarmic::A64::GetName<TranslatorVisitor>(0xD65F0FFFU);
    assert(ret && *ret == "RET");
    assert(!reta || *reta != "RETA");
    assert(!retb || *retb != "RETA");
    std::puts("SHARED_A64_LDAPR_REAL_DECODER_PASS");
}
'''


def main():
    compilers=list(dict.fromkeys(c for c in (shutil.which('clang++'),shutil.which('g++')) if c))
    assert compilers
    env=os.environ.copy()
    sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    sdk26=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
    if sdk15.is_dir():env['SDKROOT']=str(sdk15)
    incl=[]
    if sys.platform=='darwin' and sdk26.is_dir():
        incl=['-target','arm64-apple-macos15','-nostdinc++','-isystem',
              str(sdk26/'usr/include/c++/v1')]
    deps=ROOT/'vendor/sources/eden-cpm'
    additional=[BASE,ROOT/'vendor/sources/eden/src',deps/'fmt/12.1.0/include'] + \
               list((deps/'boost/boost-1.90.0/libs').glob('*/include'))
    with tempfile.TemporaryDirectory(prefix='encore-ldapr-release-') as td:
        temp=Path(td)
        generated=temp/'include'
        result=transform(BASE,generated)
        assert result.returncode==0,result.stderr
        # Exactly 4 reviewed files, anchored to the real pinned sources.
        actual={str(p.relative_to(generated)) for p in generated.rglob('*') if p.is_file()}
        expected={str(REL/f) for f in FILES}
        assert actual==expected,(sorted(actual),sorted(expected))
        for f in FILES:
            before=(BASE/REL/f).read_text()
            after=(generated/REL/f).read_text()
            changes=list(difflib.unified_diff(before.splitlines(),after.splitlines()))
            assert (len(changes)==0 if f=='decoder/a64.h' else 0<len(changes)<=26), (f,changes)
            assert 'INST(RETA,' not in after and 'INST(CAS,' not in after and 'INST(LDADD,' not in after
            if f=='decoder/a64.inc':
                assert after.count('INST(LDAPR,')==1
                assert after.count('INST(RET,')==1
            if f.endswith('load_store_exclusive.cpp'):
                assert after.count('TranslatorVisitor::LDAPR(')==1
                assert 'return LDAR(size, Rn, Rt);' in after
        print('P0_2_SHARED_A64_LDAPR_PINNED_SOURCE_DIFF_PASS files=4',flush=True)
        # A duplicate source instruction or changed decode anchor fails closed.
        mutated=temp/'mutated';shutil.copytree(BASE/REL,mutated/REL)
        path=mutated/REL/'decoder/a64.inc'
        path.write_text(path.read_text().replace('INST(RET, "RET",',
                                                  'INST(RETX, "RET",',1))
        bad=transform(mutated,temp/'invalid')
        assert bad.returncode!=0 and ('anchor' in bad.stderr.lower() or 'decoder changed' in bad.stderr.lower()),bad.stderr
        print('P0_2_SHARED_A64_LDAPR_SOURCE_DRIFT_REJECT_PASS',flush=True)
        decode=temp/'real_decoder.cpp';decode.write_text(TEST_CPP)
        core=BASE/REL/'translate/a64_translate.cpp'
        incs=['-I'+str(generated)]+['-I'+str(p) for p in additional]
        for compiler in compilers:
            # Full translation includes all maintained Dynarmic methods and
            # the generated LDAPR via source include; catches ODR/header ABI.
            c=subprocess.run([compiler,'-std=c++20','-O0','-fsyntax-only',*incl,*incs,
                               str(core)],capture_output=True,text=True,env=env,timeout=100)
            assert c.returncode==0,(compiler,c.stderr[-5000:])
            print('P0_2_SHARED_A64_LDAPR_REAL_TRANSLATOR_PASS',Path(compiler).name,flush=True)
            for opt in (0,2):
                output=temp/f'{Path(compiler).name}-O{opt}'
                build=subprocess.run([compiler,'-std=c++20',f'-O{opt}',
                                      '-fsanitize=undefined','-fno-sanitize-recover=all',
                                      *incl,*incs,str(decode),'-o',str(output)],
                                     capture_output=True,text=True,env=env,timeout=100)
                assert build.returncode==0,(compiler,opt,build.stderr[-5000:])
                run=subprocess.run([str(output)],capture_output=True,text=True,env=env,timeout=20)
                assert run.returncode==0,(compiler,opt,run.stderr[-2500:])
                assert 'SHARED_A64_LDAPR_REAL_DECODER_PASS' in run.stdout
                print('P0_2_SHARED_A64_LDAPR_REAL_DECODER_PASS',Path(compiler).name,
                      f'O{opt}',flush=True)

if __name__=='__main__':main()
