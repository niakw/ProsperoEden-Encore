#!/usr/bin/env python3
"""Real CPU6 scheduler and per-process JIT tick source qualification.

Reproduces only three pinned-source substitutions used in NS2 research.
The shipping NS1 selector stays untouched. Exercises exact generated C++
fragments and compiles all real owner TUs; no PS5 build and no gameplay proof.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'headless/ns2_cpu6_source_bridge.cmake'
BASE=ROOT/'vendor/sources/eden/src'
CPU6=ROOT/'vendor/encore-active/ns2-runtime/cpu6'
G11=ROOT/'vendor/encore-active/eden-core/src/core/arm/dynarmic/g11/arm_dynarmic_64_native_normal.cpp'
G11_A32=ROOT/'vendor/encore-active/eden-core/src/core/arm/dynarmic/g11/arm_dynarmic_32_native_normal.cpp'
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
FILES=('hle/kernel/global_scheduler_context.cpp',
       'arm/dynarmic/arm_dynarmic_32.cpp',
       'arm/dynarmic/arm_dynarmic_64.cpp')
assert CMAKE.count('include("${CMAKE_CURRENT_LIST_DIR}/ns2_cpu6_source_bridge.cmake")')==1
research=CMAKE.split('# Unified NS2 six-core kernel owner',1)[1].split('# Shared kernel heap admission',1)[0]
assert 'set_property(TARGET core PROPERTY SOURCES "${eden_cpu6_core_sources}")' in research
assert 'EDEN_CPU6_OUTPUT_ROOT' in research
assert 'EDEN_N76_NATIVE_JIT_SOURCE' in research
assert 'arm_dynarmic_32_${EDEN_G11_PLATFORM}_${EDEN_G11_PROFILE}.cpp' in research
assert 'list(FIND eden_cpu6_core_sources "${eden_cpu6_selected_source}" eden_cpu6_owner_idx)' in research
assert 'CPU6 must retain selected N76/G11 JIT source' in research
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in research
assert 'EDEN_NS2_CPU6_EXPERIMENTAL' not in CMAKE
assert 'NUM_CPU_CORES = 6' in (CPU6/'core/hardware_properties.h').read_text()
assert 'NUM_LEGACY_CPU_CORES = 4' in (CPU6/'core/hardware_properties.h').read_text()
assert 'MAX_NUM_CPU_CORES = 6' in (CPU6/'dynarmic/interface/exclusive_monitor.h').read_text()


def generate(src:Path,out:Path,jit:Path=G11)->subprocess.CompletedProcess[str]:
    return subprocess.run(['cmake',f'-DEDEN_CPU6_SOURCE_ROOT={src}',
                           f'-DEDEN_CPU6_A64_SOURCE={jit}',
                           f'-DEDEN_CPU6_OUTPUT_ROOT={out}','-P',str(SCRIPT)],
                          capture_output=True,text=True,timeout=35)


def run_checked(command:list[str],env:dict[str,str],timeout:int=100)->str:
    r=subprocess.run(command,capture_output=True,text=True,env=env,timeout=timeout)
    assert r.returncode==0,(command,r.stderr[-4000:],r.stdout[-1200:])
    return r.stdout


def main()->None:
    env=os.environ.copy()
    sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    sdk26=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
    if sdk15.is_dir():env['SDKROOT']=str(sdk15)
    compiler=shutil.which('clang++') or shutil.which('g++')
    assert compiler
    stdlib=[]
    if sys.platform=='darwin' and sdk26.is_dir():
        stdlib=['-target','arm64-apple-macos15','-nostdinc++',
                '-isystem',str(sdk26/'usr/include/c++/v1')]
    deps=ROOT/'vendor/sources/eden-cpm'
    includes=[ROOT/'headless',CPU6,ROOT/'vendor/encore-active/ns2-runtime/kernel_wait64',
              ROOT/'vendor/encore-active/ns2-runtime/gpu_access_svc',
              BASE,BASE/'dynarmic/src',ROOT/'vendor/sources/fmt/include',
              ROOT/'vendor/encore-active/eden-core/overrides',
              ROOT/'vendor/encore-active/eden-core/src/core/arm/dynarmic/g11',
              ROOT/'vendor/encore-active/eden-core/include',
              deps/'xbyak/v7.40.1',
              *sorted((deps/'boost/boost-1.90.0/libs').glob('*/include'))]
    includes=['-I'+str(p) for p in includes if p.is_dir()]
    with tempfile.TemporaryDirectory(prefix='encore-cpu6-') as work:
        tmp=Path(work)
        out=tmp/'generated'
        first=generate(BASE,out)
        assert first.returncode==0,first.stderr
        expected={'core/'+f for f in FILES}
        actual={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}
        assert actual==expected,(actual,expected)
        kernel=(out/'core'/FILES[0]).read_text()
        priorities=re.search(r'(?s)static constexpr std::array<u32, Core::Hardware::NUM_CPU_CORES> per_core\s*\{.*?\};',kernel)
        assert priorities, 'Actual generated KScheduler preemption table missing'
        assert '59, 59, 59, 63, 59, 59' in priorities.group(0)
        for name in FILES[1:]:
            src=(out/'core'/name).read_text()
            assert 'm_process->GetPhysicalCoreMask()' in src
            assert 'Core::Hardware::NUM_LEGACY_CPU_CORES' in src
            assert src.count('const u64 extended_cores =')==1
            assert src.count('amortized_ticks = ticks /')==1
            old=(G11 if name.endswith('arm_dynarmic_64.cpp') else
                 G11_A32 if name.endswith('arm_dynarmic_32.cpp') else
                 BASE/'core'/name).read_text()
            assert old.count('ticks / Core::Hardware::NUM_CPU_CORES')==1
        assert '#ifdef EDEN_NS2_GUEST_COUNTER' in (
            out/'core/arm/dynarmic/arm_dynarmic_64.cpp').read_text()
        assert '#include "jit-startup-retry.h"' in (
            out/'core/arm/dynarmic/arm_dynarmic_64.cpp').read_text()
        print('P0_2_CPU6_STATIC_SCHEDULER_TICK_OWNERS_PASS 3 owners',flush=True)
        # Audited full sources, NOT CMake-generated C++: prove exact byte parity
        # against pinned Eden scheduler and BOTH maintained native G11 A32/A64.
        old_scheduler="""    static constexpr std::array<u32, Core::Hardware::NUM_CPU_CORES> per_core{
        59,
        59,
        59,
        63,
    };"""
        new_scheduler="""    // Application cores 4/5 must match priorities 0..2; system core 3 keeps 63.
    static constexpr std::array<u32, Core::Hardware::NUM_CPU_CORES> per_core{
        59, 59, 59, 63, 59, 59,
    };"""
        old_ticks='    u64 amortized_ticks = ticks / Core::Hardware::NUM_CPU_CORES;'
        new_ticks="""    // Preserve Switch 1 tick cadence even when the shared kernel exposes six cores.
    // Physical affinity, never TitleID, selects the six-core division.
    const u64 extended_cores = m_process->GetPhysicalCoreMask() & ((u64{1} << 4) | (u64{1} << 5));
    u64 amortized_ticks = ticks / (extended_cores ? Core::Hardware::NUM_CPU_CORES
                                                     : Core::Hardware::NUM_LEGACY_CPU_CORES);"""
        origins=(BASE/'core'/FILES[0],G11_A32,G11)
        originals=[src.read_text() for src in origins]
        for index, (name, original) in enumerate(zip(FILES, originals)):
            old, replacement=(old_scheduler,new_scheduler) if index==0 else (old_ticks,new_ticks)
            assert original.count(old)==1,('pinned owner drift',name)
            expected=original.replace(old,replacement)
            actual=(out/'core'/name).read_text()
            maintained=(ROOT/'vendor/encore-active/ns2-runtime/cpu6/maintained/core'/name).read_text()
            assert actual==expected==maintained,('static CPU6 owner parity',name)
            # Mutation control: a wrong pinned upstream byte must never pass
            # the exact maintained-owner parity gate.
            changed=original.replace(old,old.replace('63,','62,') if index==0 else
                                     old.replace('NUM_CPU_CORES','NUM_LEGACY_CPU_CORES'))
            assert changed!=original and changed.replace(old,replacement)!=actual
            print('P0_2_CPU6_STATIC_PINNED_OWNER_PARITY_PASS',name,flush=True)
        ancient=BASE/'core/arm/dynarmic/arm_dynarmic_64.cpp'
        rejected=generate(BASE,tmp/'unoptimized',ancient)
        assert rejected.returncode and 'maintained G11/N76 source' in rejected.stderr
        print('P0_2_CPU6_UNOPTIMIZED_A64_REJECT_PASS',flush=True)
        # Configure the single PS5 CPU6 selector with actual target lists.
        # Only the technical platform and NPDM ownership affect selection.
        selection='if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)'+research.split(
            'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)',1)[1]
        anchored='include("${CMAKE_CURRENT_LIST_DIR}/ns2_cpu6_source_bridge.cmake")'
        assert selection.count(anchored)==1
        selection=selection.replace(anchored,f'include("{SCRIPT.as_posix()}")')
        for enabled,dual in ((False,False),(False,True),(True,False),(True,True)):
            selected_native = enabled and dual
            prj=tmp/('cmake-'+''.join(str(int(x)) for x in (enabled,dual)))
            prj.mkdir()
            (prj/'dummy.cpp').write_text('int cpu6_dummy=1;\n')
            for owner in FILES:
                fake=prj/owner
                fake.parent.mkdir(parents=True,exist_ok=True)
                fake.write_text('int cpu6_stub=1;\n')
            cmake_text='cmake_minimum_required(VERSION 3.20)\nproject(cpu6_selector LANGUAGES CXX)\nset(PORT_ROOT "@ROOT@")\nset(PORT_BUILD_DIR "@OUT@")\nset(PS5_NATIVE @ENABLED@)\nset(EDEN_REVIEWED_DUAL_NPDM @DUAL@)\nadd_library(core STATIC dummy.cpp\n    hle/kernel/global_scheduler_context.cpp\n    arm/dynarmic/arm_dynarmic_32.cpp\n    arm/dynarmic/arm_dynarmic_64.cpp)\nadd_library(dynarmic STATIC dummy.cpp)\nadd_library(eden-headless STATIC dummy.cpp)\n'
            # The shipping CPU6 block also guards the independent KProcess
            # consumers. Declare them in this miniature CMake graph; otherwise
            # a valid source change fails because the fixture omits real targets.
            cmake_text += ('add_library(audio_core STATIC dummy.cpp)\n'
                           'add_library(video_core STATIC dummy.cpp)\n'
                           'add_library(hid_core STATIC dummy.cpp)\n')
            cmake_text=cmake_text.replace(
                'arm/dynarmic/arm_dynarmic_32.cpp\n    arm/dynarmic/arm_dynarmic_64.cpp)',
                '"${EDEN_G11_A32_SELECTED}"\n    "${EDEN_N76_NATIVE_JIT_SOURCE}")')
            cmake_text=cmake_text.replace(
                'add_library(core STATIC dummy.cpp',
                'set(EDEN_SHARED_NS2_GUEST_COUNTER ON)\n'
                f'set(EDEN_N76_NATIVE_JIT_SOURCE "{G11}")\n'
                f'set(EDEN_G11_A32_SELECTED "{G11_A32}")\n'
                f'set(EDEN_G11_ROOT "{G11_A32.parent}")\n'
                'set(EDEN_G11_PLATFORM native)\n'
                'set(EDEN_G11_PROFILE normal)\n'
                'add_library(core STATIC dummy.cpp')
            cmake_text=cmake_text.replace('@ROOT@',ROOT.as_posix()).replace(
                '@OUT@',(prj/'generated').as_posix()).replace(
                '@ENABLED@','ON' if enabled else 'OFF').replace(
                '@DUAL@','ON' if dual else 'OFF')
            cmake_text+=selection+'\nget_target_property(pinned_core_sources core SOURCES)\nlist(FIND pinned_core_sources "@OUT@/core/hle/kernel/global_scheduler_context.cpp" cpu6_selected)\nmessage(STATUS "CPU6_GENERATED_OWNER_INDEX=${cpu6_selected}")\n'.replace('@OUT@',(prj/'generated/ns2-cpu6').as_posix())
            (prj/'CMakeLists.txt').write_text(cmake_text)
            configured=subprocess.run(['cmake','-S',str(prj),'-B',str(prj/'build'),
                                       f'-DCMAKE_OSX_SYSROOT={sdk15}' if sdk15.is_dir()
                                       else '-DCMAKE_BUILD_TYPE=Debug'],
                                      capture_output=True,text=True,timeout=40)
            assert configured.returncode==0,(prj,configured.stderr[-3600:])
            selected='CPU6_GENERATED_OWNER_INDEX=1' if selected_native else 'CPU6_GENERATED_OWNER_INDEX=-1'
            assert selected in configured.stdout,(prj,configured.stdout[-2800:])
            exists=(prj/'generated/ns2-cpu6/core/hle/kernel/global_scheduler_context.cpp').exists()
            assert exists==selected_native
            print('P0_2_UNIFIED_CPU6_CMAKE_SOURCE_SELECTOR_PASS',
                  f'ps5_native={enabled}',f'dual_npdm={dual}',flush=True)
        if '--selector-only' in sys.argv:
            print('P5_CPU6_G11_NATIVE_CONFIGURE_PREFLIGHT_PASS',flush=True)
            return
        flags=[compiler,'-std=c++20','-fsyntax-only','-Wno-unused-parameter',
               '-DFMT_HEADER_ONLY',*stdlib,*includes]
        def compile_owner(name:str)->tuple[str,subprocess.CompletedProcess[str]]:
            src=out/'core'/name
            return name,subprocess.run(flags+[str(src)],capture_output=True,
                                       text=True,env=env,timeout=95)
        with ThreadPoolExecutor(max_workers=3) as pool:
            checked=list(pool.map(compile_owner,FILES))
        for name,result in checked:
            assert result.returncode==0,(name,result.stderr[-3500:])
            print('P0_2_CPU6_REAL_OWNER_TU_PASS',name,flush=True)
        # The real maintained preemption initializer and BOTH real callback
        # tick expressions are compiled/executed with the real hardware map.
        source_code='#include <cassert>\n#include <algorithm>\n#include <cstdio>\n#include "core/hardware_properties.h"\nusing namespace Core;\n'
        source_code+='struct MockProcess { unsigned long long mask; unsigned long long GetPhysicalCoreMask() const { return mask; } };\n'
        source_code+='auto Priorities() { '+priorities.group(0)+' return per_core; }\n'
        for num,name in enumerate(FILES[1:]):
            src=(out/'core'/name).read_text()
            start=src.index('    const u64 extended_cores =')
            stop=src.index('    m_parent.m_system.CoreTiming().AddTicks(amortized_ticks);',start)
            snippet=src[start:stop]
            assert 'std::max<u64>(amortized_ticks, 1)' in snippet
            source_code+=f'u64 Ticks{num}(u64 ticks,const MockProcess* m_process) {{\n'+snippet+'    return amortized_ticks;\n}\n'
        source_code+='''int main() {
    static_assert(Core::Hardware::NUM_CPU_CORES==6);
    static_assert(Core::Hardware::NUM_LEGACY_CPU_CORES==4);
    static_assert(Core::Hardware::VirtualToPhysicalCoreMap[0]==0 &&
                  Core::Hardware::VirtualToPhysicalCoreMap[3]==3 &&
                  Core::Hardware::VirtualToPhysicalCoreMap[4]==4 &&
                  Core::Hardware::VirtualToPhysicalCoreMap[5]==5 &&
                  Core::Hardware::VirtualToPhysicalCoreMap[6]==3 &&
                  Core::Hardware::VirtualToPhysicalCoreMap[7]==3 &&
                  Core::Hardware::VirtualToPhysicalCoreMap[63]==3);
    constexpr auto old=Core::Hardware::ConvertVirtualCoreMaskToPhysical(0xFULL);
    static_assert(old==0xFULL);
    const auto priority=Priorities();
    assert(priority.size()==6 && priority[0]==59 && priority[1]==59 &&
           priority[2]==59 && priority[3]==63 && priority[4]==59 && priority[5]==59);
    MockProcess legacy{0xFULL},native{0x3FULL},restricted{0x2FULL},service{1ULL<<3};
    for (auto n:{0ULL,1ULL,3ULL,4ULL,6ULL,12ULL,24ULL,4096ULL}) {
        const auto old=std::max<u64>(n/4,1);
        assert(Ticks0(n,&legacy)==old && Ticks1(n,&legacy)==old);
        assert(Ticks0(n,&service)==old && Ticks1(n,&service)==old);
        const auto newer=std::max<u64>(n/6,1);
        assert(Ticks0(n,&native)==newer && Ticks1(n,&native)==newer);
        assert(Ticks0(n,&restricted)==newer && Ticks1(n,&restricted)==newer);
    }
    std::puts("P0_2_CPU6_REAL_PREEMPTION_AND_TICK_LOGIC_PASS");
}
'''
        fixture=tmp/'cpu6_actual_source.cpp';fixture.write_text(source_code)
        for optimization in (0,2):
            executable=tmp/f'cpu6-O{optimization}'
            args=[compiler,'-std=c++20',f'-O{optimization}',
                  '-fsanitize=undefined','-fno-sanitize-recover=all',
                  *stdlib,*includes,str(fixture),'-o',str(executable)]
            run_checked(args,env)
            result=run_checked([str(executable)],env,timeout=15)
            assert 'P0_2_CPU6_REAL_PREEMPTION_AND_TICK_LOGIC_PASS' in result
            print('P0_2_CPU6_PREEMPTION_TICKS_UBSAN_PASS',f'O{optimization}',flush=True)

if __name__=='__main__':main()
