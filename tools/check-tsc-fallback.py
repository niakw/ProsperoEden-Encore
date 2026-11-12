#!/usr/bin/env python3
"""Compile the actual generated frequency-selection block against CPUID cases."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
cache = Path((root / '.local/headless-cache').read_text().strip())
# The staged source can already contain the maintained R23 native TSC
# backport. Replaying it over that cache is not a valid upstream oracle.
# Replay from the immutable pinned Eden source, then accept only a fully
# recognized staged state, never an unknown or partially edited cache input.
original = (root / 'vendor/sources/eden/src/common/cpu_features.cpp').read_text()
derived = (root / 'vendor/encore-active/eden-core/src' / 'common/cpu_features.cpp').read_text()
prepared = (cache / 'source/src/common/cpu_features.cpp').read_text()
assert prepared in (original, derived), (
    'Unrecognized native TSC staged source; refusing stale/partial cache overlay')
expected = original.replace('        } else {\n            caps.tsc_frequency = X64::EstimateRDTSCFrequency();\n        }', '        }').replace(
    '    if (max_std_fn >= 0x16) {',
    "    if (caps.invariant_tsc && caps.tsc_frequency < 1'000'000'000ULL) {\n        caps.tsc_frequency = X64::EstimateRDTSCFrequency();\n    }\n\n    if (max_std_fn >= 0x16) {")
# R23 #71: the maintained WallClock also replaces a broken 0.64
# nanoseconds-to-RDTSC conversion. Prove that additional exact delta
# independently; do not reject an approved native fix as unknown drift.
ns_to_ticks_original = """u64 WallClock::NsToTicks(std::chrono::nanoseconds ns) const {
    return invariant ? MultiplyHigh(ns.count(), rdtsc_ns_factor) : ns.count();
}"""
ns_to_ticks_reviewed = """u64 WallClock::NsToTicks(std::chrono::nanoseconds ns) const {
    if (!invariant) {
        return static_cast<u64>(ns.count());
    }
    // A nanosecond-to-RDTSC ratio greater than one does not fit in
    // 0.64 fixed-point: at 2/3/4 GHz the old factor wraps to zero.
    // The product fits in 128 bits for any signed nanosecond duration
    // and any measured 64-bit host frequency.
    if (ns.count() <= 0) {
        return 0;
    }
    const auto product = static_cast<unsigned __int128>(ns.count()) *
                         static_cast<unsigned __int128>(rdtsc_frequency);
    return static_cast<u64>(product / NsRatio::den);
}"""
assert expected.count(ns_to_ticks_original) == 1
expected = expected.replace(ns_to_ticks_original, ns_to_ticks_reviewed)
ns_fixed_factor = """    , rdtsc_ns_factor{invariant_ ? GetFixedPoint64Factor(rdtsc_frequency_, NsRatio::den) : 1}
"""
assert expected.count(ns_fixed_factor) == 1
expected = expected.replace(ns_fixed_factor, "", 1)
# N76 extends the shared CPU clock with a metadata-selected guest rate.
# Reconstruct the original native TSC owner by removing ONLY this exact
# guarded include and one guarded CNTPCT block. NS1 selector parity remains
# byte-for-byte, and unqualified changes still fail the audit.
ns2_header = '#ifdef EDEN_NS2_GUEST_COUNTER\n#include "encore/guest_counter_policy.h"\n#endif\n'
ns2_block = '''#ifdef EDEN_NS2_GUEST_COUNTER
    // Shared guest-clock policy: Nintendo's second-generation SDK converts
    // CNT ticks using 31.25 MHz. Keep the original fast path for Switch 1.
    if (Eden::GuestCounter::Rate() != Eden::GuestCounter::Switch1Hz) {
        if (!invariant)
            return static_cast<s64>(Eden::GuestCounter::NanosecondsToGuest(
                static_cast<u64>(GetUptime())));
        const u64 factor = Eden::GuestCounter::NativeFactor();
        if (factor != 0)
            return MultiplyHigh(GetUptime(), factor);
        // A missing host clock calibration must not divide by zero or
        // silently keep the wrong 19.2 MHz guest rate.
        if (rdtsc_frequency == 0)
            return 0;
        return MultiplyHigh(GetUptime(),
                            GetFixedPoint64Factor(Eden::GuestCounter::Rate(),
                                                  rdtsc_frequency));
    }
#endif
'''
assert derived.count(ns2_header) == 1, "N76 header changed"
assert derived.count(ns2_block) == 1, "N76 rate body changed"
ns1_derived = derived.replace(ns2_header, "", 1).replace(ns2_block, "", 1)
assert ns1_derived == expected and ns1_derived.count('X64::EstimateRDTSCFrequency()') == 1
selection = derived[derived.index('    if (max_std_fn >= 0x15) {'):derived.index('    if (max_std_fn >= 0x16) {')]
code = '''
#include <cassert>
#include <cstdint>
using u64 = uint64_t;
static unsigned estimates;
static u64 estimated;
namespace X64 { u64 EstimateRDTSCFrequency() { ++estimates; return estimated; } }
void __cpuid(int*, int) {} // cpu_id already holds the requested fixture.
u64 select(unsigned max_std_fn, bool invariant, int denominator, int numerator, int crystal) {
    int cpu_id[]{denominator, numerator, crystal, 0};
    struct { bool invariant_tsc; u64 tsc_frequency = 0, tsc_crystal_ratio_denominator = 0,
        tsc_crystal_ratio_numerator = 0, crystal_frequency = 0; } caps{invariant};
''' + selection + '''
    return caps.tsc_frequency;
}
int main() {
    estimated = 2'200'000'000;
    assert(select(0x10, true, 0, 0, 0) == estimated && estimates == 1);
    assert(select(0x15, true, 2, 4, 0) == estimated && estimates == 2);
    assert(select(0x15, true, 0, 0, 0) == estimated && estimates == 3);
    assert(select(0x15, true, 1, 100, 24'000'000) == 2'400'000'000 && estimates == 3);
    assert(select(0x10, false, 0, 0, 0) == 0 && estimates == 3);
    estimated = 0;
    assert(select(0x10, true, 0, 0, 0) == 0 && estimates == 4);
    estimated = 500'000'000;
    assert(select(0x10, true, 0, 0, 0) < 1'000'000'000 && estimates == 5);
}
'''
with tempfile.TemporaryDirectory(prefix='eden-tsc-') as directory:
    path = Path(directory)
    (path / 'check.cpp').write_text(code)
    subprocess.run(['clang++-18', '-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror',
                    str(path / 'check.cpp'), '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True, timeout=5)
print('Actual TSC selector: missing leaf/crystal/denominator, valid CPUID, noninvariant and rejected estimates PASS')
