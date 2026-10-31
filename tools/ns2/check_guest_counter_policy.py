#!/usr/bin/env python3
"""N76: compile exact vendor guest-clock policy + inspect native owners."""
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).resolve().parents[2]
vendor=root/"vendor/encore-active/eden-core"
clock=(vendor/"src/common/cpu_features.cpp").read_text()
jit=(vendor/"src/core/arm/dynarmic/arm_dynarmic_64.cpp").read_text()
npdm=(root/"vendor/encore-active/ns2-experimental/src/core/file_sys/program_metadata.cpp").read_text()
loader=(root/"vendor/encore-active/ns2-experimental/src/core/loader/deconstructed_rom_directory.cpp").read_text()
cmake=(root/"headless/CMakeLists.txt").read_text()
for witness in ("Eden::GuestCounter::NativeFactor()", "Eden::GuestCounter::NanosecondsToGuest(", "rdtsc_frequency == 0"):
    assert witness in clock,witness
assert "config.cntfrq_el0 = static_cast<u32>(Eden::GuestCounter::Rate());" in jit
assert "Eden::GuestCounter::SelectProgram(" not in npdm
assert "Eden::GuestCounter::SelectProgram(metadata.IsSwitch2(), Common::g_cpu_caps.tsc_frequency)" in loader
assert loader.index("Eden::GuestCounter::SelectProgram(") > loader.index("metadata.Reload(npdm)")
assert loader.index("Eden::GuestCounter::SelectProgram(") < loader.index("is_loaded = true")
assert "option(EDEN_NS2_GUEST_COUNTER_EXPERIMENTAL" in cmake
assert "N76 requires PS5 NS2 research metadata+A64 (non-release)" in cmake
assert "n76_core_sources" in cmake
program=r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include "encore/guest_counter_policy.h"
using namespace Eden::GuestCounter;
static std::uint64_t Counter(std::uint64_t ticks) {
 return static_cast<std::uint64_t>(
   (static_cast<unsigned __int128>(ticks)*NativeFactor())>>64);
}
int main() {
 static_assert(Switch1Hz==19'200'000 && Switch2Hz==31'250'000);
 assert(Rate()==Switch1Hz);
 SelectProgram(false,3'000'000'000ULL);
 assert(NanosecondsToGuest(1'000'000'000ULL)==19'200'000ULL);
 assert(CpuTicksToGuest(1'020'000'000ULL)==19'200'000ULL);
 SelectProgram(true,3'000'000'000ULL);
 assert(Rate()==Switch2Hz);
 assert(NanosecondsToGuest(1'000'000'000ULL)==31'250'000ULL);
 assert(CpuTicksToGuest(1'020'000'000ULL)==31'250'000ULL);
 assert(NanosecondsToGuest(16'666'666)==520'833ULL);
 const auto ticks=Counter(3'000'000'000ULL);
 assert(ticks>=31'249'998ULL && ticks<=31'250'001ULL);
 SelectProgram(false,3'000'000'000ULL);
 assert(Rate()==Switch1Hz);
 assert(Counter(3'000'000'000ULL)>=19'199'998ULL);
 SelectProgram(true,0);
 assert(Rate()==Switch2Hz && NativeFactor()==0);
 SelectProgram(false,0);
 assert(Rate()==Switch1Hz && NativeFactor()==0);
 std::puts("N76_GUEST_COUNTER_RESET_AND_RATIO_PASS");
}
"""
with tempfile.TemporaryDirectory(prefix="n76-clock-") as tmp:
 d=Path(tmp)
 src=d/"test.cpp";src.write_text(program)
 for compiler in ("clang++","g++"):
  exe=d/compiler.replace("+","p")
  subprocess.run([compiler,"-std=c++20","-O2","-Wall","-Wextra","-Werror",
    "-fsanitize=undefined","-fno-sanitize-recover=all",
    "-I",str(vendor/"include"),str(src),"-o",str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
print("N76_ENCORE_CLOCK_CLANG_GCC_UBSAN_PASS")
