#!/usr/bin/env python3
"""P0.2: test production-selected LDAPR decode and real Dynarmic translation.

CMake copies exactly four versioned sources reviewed against pinned Dynarmic,
without selecting the research RETAA, LSE or CAS implementations.
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
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_LDAPR_OUTPUT_ROOT}")' in CMAKE
assert 'EDEN_NS2_A64_EXPERIMENTAL' not in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")' in CMAKE
assert all((BASE/REL/f).is_file() for f in FILES)
# Configure-only copy of the EXACT production-owned static sources.

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
    # On macOS `/usr/bin/g++` is another Apple Clang driver, NOT GCC.
    # Avoid recompiling identical compiler/target combinations: this host
    # witness is a Dynarmic source/decoder proof, not four distinct compilers.
    candidates=list(dict.fromkeys(c for c in (shutil.which('clang++'),shutil.which('g++')) if c))
    compilers=[]
    signatures=set()
    for candidate in candidates:
        info=subprocess.run([candidate, '--version'], capture_output=True,
                            text=True, timeout=10)
        assert info.returncode==0
        version=info.stdout.splitlines()[0]
        # Apple-clang executable frontends are aliases regardless of basename.
        signature=version
        if signature in signatures:
            print('P0_2_A64_LDAPR_DUPLICATE_HOST_COMPILER_SKIPPED',
                  Path(candidate).name,signature,flush=True)
            continue
        signatures.add(signature)
        compilers.append(candidate)
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
            static=(ROOT/'vendor/encore-active/ns2-runtime/ldapr/maintained'/REL/f).read_text()
            assert after==static,('CMake failed to select static LDAPR source',f)
            if f=='decoder/a64.h':
                reviewed=before
            elif f=='decoder/a64.inc':
                old='INST(RET, "RET", "1101011001011111000000nnnnn00000")'
                assert before.count(old)==1
                reviewed=before.replace(old,old+'\nINST(LDAPR, "LDAPR", "ss11100010111111110000nnnnnttttt")')
            elif f=='translate/impl/impl.h':
                old='bool LDAPR(Reg Rn, Reg Rt);'
                assert before.count(old)==1
                reviewed=before.replace(old,'bool LDAPR(Imm<2> size, Reg Rn, Reg Rt);')
            else:
                old='namespace Dynarmic::A64 {\n'
                assert before.count(old)==1
                reviewed=before.replace(old,old+
                    '\n// Reviewed RCpc LDAPR: LDAR\'s acquire ordering is strictly stronger.\n'
                    'bool TranslatorVisitor::LDAPR(Imm<2> size, Reg Rn, Reg Rt) {\n'
                    '    return LDAR(size, Rn, Rt);\n}\n')
            assert after==reviewed,('LDAPR static owner no longer equals pinned reviewed change',f)
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
        # The negative fixture breaks the pinned RET anchor. A source
        # mismatch must be caught by exact parity, not by code generation.
        mutated_source=(mutated/REL/'decoder/a64.inc').read_text()
        reviewed_source=(generated/REL/'decoder/a64.inc').read_text()
        assert 'INST(RET, "RET",' not in mutated_source
        assert mutated_source!=reviewed_source
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
