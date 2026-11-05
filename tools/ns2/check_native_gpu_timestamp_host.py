#!/usr/bin/env python3
"""P2.7 source-extracted real GPU::Impl::GetTicks (shared NS1/NS2 Vulkan owner)."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT/'vendor/encore-active/eden-core/src/video_core/gpu_vulkan.cpp'
CLOCK=ROOT/'vendor/encore-active/eden-core/include/encore/guest_counter_policy.h'
source=OWNER.read_text()
cmake=(ROOT/'headless/CMakeLists.txt').read_text()
assert CLOCK.is_file()
assert '#include "encore/guest_counter_policy.h"' in source
assert "Eden::GuestCounter::Rate() == Eden::GuestCounter::Switch2Hz" in source
assert "GetGlobalTimeNs().count()" in source
assert "GpuClockMultiplier(Settings::values.gpu_clock.GetValue())" in source
assert 'foreach(n76_target IN ITEMS core common eden-headless video_core)' in cmake
assert 'EDEN_NS2_GUEST_COUNTER=1' in cmake
npdm=(ROOT/'vendor/encore-active/ns2-runtime/metadata/core/loader/deconstructed_rom_directory.cpp').read_text()
main=(ROOT/'headless/main.cpp').read_text()
assert 'SelectProgram(metadata.IsSwitch2(), Common::g_cpu_caps.tsc_frequency)' in npdm
assert 'SelectProgram(false, Common::g_cpu_caps.tsc_frequency)' in main
assert 'EDEN_NS2_GUEST_COUNTER' not in (ROOT/'vendor/sources/eden/src/video_core/gpu.cpp').read_text()

def actual_function(marker):
    assert source.count(marker)==1
    start=source.index(marker)
    at=source.index('{',start)
    depth=0
    for end in range(at,len(source)):
        if source[end]=='{':depth+=1
        elif source[end]=='}':
            depth-=1
            if depth==0:return source[start:end+1]
    raise AssertionError('unbalanced source')
multiplier=actual_function('constexpr u64 GpuClockMultiplier(')
get_ticks=actual_function('[[nodiscard]] u64 GetTicks() const {')
assert '#if defined(PS5_NATIVE) && defined(EDEN_NS2_GUEST_COUNTER)' in get_ticks
assert get_ticks.count('GetGlobalTimeNs()')==1 and get_ticks.count('GetGPUTicks()')==1

CPP=r'''
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <initializer_list>
using u64=std::uint64_t;
namespace Settings {
enum class GpuClock {Normal,Boost,Overclock};
struct Option {GpuClock value{GpuClock::Normal};
 GpuClock GetValue() const{return value;}};
struct Values {Option gpu_clock{};};
inline Values values{};
}
#include "encore/guest_counter_policy.h"
__MULT__
struct Timing {
 u64 gpu{};
 std::chrono::nanoseconds ns{};
 mutable int gpu_reads{},ns_reads{};
 u64 GetGPUTicks() const {++gpu_reads;return gpu;}
 std::chrono::nanoseconds GetGlobalTimeNs() const {++ns_reads;return ns;}
};
struct System {
 Timing time{};
 const Timing& CoreTiming() const{return time;}
};
struct Impl {
 const System& system;
__TICKS__
};
int main(){
 using namespace Eden::GuestCounter;
 constexpr u64 base=293'036'000'000'000ULL;
 constexpr u64 guest_start=95'000'000'000ULL;
 [[maybe_unused]] constexpr u64 calibration_offset=guest_start-base;
 System system{};
 Impl impl{system};
 for(auto clock:{Settings::GpuClock::Normal,Settings::GpuClock::Boost,
                 Settings::GpuClock::Overclock}){
  Settings::values.gpu_clock.value=clock;
  const u64 divisor=GpuClockMultiplier(clock);
  SelectProgram(false,3'000'000'000ULL);
  assert(Rate()==Switch1Hz);
  for(const u64 ticks:{u64{0},u64{1},u64{255},u64{256},u64{511},
                       u64{512},u64{614'400'000},u64{180'041'318'400'000}}){
   system.time.gpu=ticks;
   system.time.ns=std::chrono::nanoseconds{static_cast<std::int64_t>(base)};
   system.time.gpu_reads=system.time.ns_reads=0;
   assert(impl.GetTicks()==ticks/divisor);
   assert(system.time.gpu_reads==1 && system.time.ns_reads==0);
  }
#ifdef EXPECT_AMPERE
  SelectProgram(true,3'000'000'000ULL);
  assert(Rate()==Switch2Hz);
  for(u64 elapsed=0;elapsed<=1'000'000'000ULL;elapsed+=31'250'000){
   const u64 ns=base+elapsed;
   system.time.ns=std::chrono::nanoseconds{static_cast<std::int64_t>(ns)};
   system.time.gpu=ns*384/625;
   system.time.gpu_reads=system.time.ns_reads=0;
   const u64 actual=impl.GetTicks();
   assert(actual==ns && actual+calibration_offset==guest_start+elapsed);
   assert(system.time.gpu_reads==0 && system.time.ns_reads==1);
   const u64 finish=ns+5'000'000, present=finish+200'000+calibration_offset;
   assert(present-(actual+5'000'000+calibration_offset)==200'000);
  }
  system.time.ns=std::chrono::nanoseconds{-1};
  system.time.gpu_reads=system.time.ns_reads=0;
  assert(impl.GetTicks()==0);
  assert(system.time.gpu_reads==0 && system.time.ns_reads==1);
#else
  SelectProgram(true,3'000'000'000ULL);
  system.time.gpu=614'400'000;
  system.time.gpu_reads=system.time.ns_reads=0;
  assert(impl.GetTicks()==614'400'000/divisor);
  assert(system.time.gpu_reads==1 && system.time.ns_reads==0);
#endif
  SelectProgram(false,3'000'000'000ULL);
  system.time.gpu=614'400'000;
  system.time.gpu_reads=system.time.ns_reads=0;
  assert(impl.GetTicks()==614'400'000/divisor);
  assert(system.time.gpu_reads==1 && system.time.ns_reads==0);
 }
 std::puts("P2_7_REAL_GPU_TIMESTAMP_OWNER_PASS"
#ifdef EXPECT_AMPERE
           " ns2_nanoseconds=1 ns1_transition=1"
#else
           " legacy_ns1_ticks=1"
#endif
 );
}
'''
CPP=CPP.replace('__MULT__',multiplier).replace('__TICKS__',get_ticks)
compilers=list(dict.fromkeys(filter(None,[shutil.which('clang++'),shutil.which('g++')])))
assert compilers
env=dict(os.environ)
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='encore-native-gpu-time-') as tmp:
    src=Path(tmp)/'main.cpp'
    src.write_text(CPP)
    for compiler in compilers:
        for opt in ('-O0','-O2'):
            for mode in ('native','legacy','without_ps5'):
                defs=['-DPS5_NATIVE=1','-DEDEN_NS2_GUEST_COUNTER=1',
                      '-DEXPECT_AMPERE=1'] if mode=='native' else (
                    ['-DPS5_NATIVE=1'] if mode=='legacy' else
                    ['-DEDEN_NS2_GUEST_COUNTER=1'])
                exe=Path(tmp)/(Path(compiler).name+opt+mode)
                args=[compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror',
                      '-fsanitize=undefined','-fno-sanitize-recover=all',
                      *defs,'-I',str(CLOCK.parents[1]),str(src),'-o',str(exe)]
                built=subprocess.run(args,env=env,text=True,capture_output=True,timeout=65)
                assert built.returncode==0,(opt,mode,built.stderr[-4000:])
                ran=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=30)
                assert ran.returncode==0,(opt,mode,ran.stderr,ran.stdout)
                print(Path(compiler).name,opt,mode,ran.stdout.strip(),flush=True)
