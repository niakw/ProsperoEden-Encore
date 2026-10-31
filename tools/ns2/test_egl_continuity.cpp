// SPDX-License-Identifier: GPL-3.0-or-later
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "core/ns2_egl_continuity_guard.h"
static void Test(std::vector<std::uint32_t>& runs,std::size_t cut) {
    using Eden::NS2::Eglantine::CutContinuityAt;
    CutContinuityAt(cut,
        [&](std::size_t i) { return runs.at(i); },
        [&](std::size_t i, std::uint32_t n) { runs.at(i)=n; });
}
static void Check(bool condition) { if (!condition) std::abort(); }
int main() {
    std::vector<std::uint32_t> runs{7,6,5,4,3,2,1,0};
    Test(runs,3);
    Check((runs==std::vector<std::uint32_t>{2,1,0,4,3,2,1,0}));
    // Map/Unmap also clears the changed pages, as already implemented by PS5.
    runs[3]=runs[4]=0;
    Check((runs==std::vector<std::uint32_t>{2,1,0,0,0,2,1,0}));
    // Existing runs stopping before the changed range stay untouched.
    runs={2,1,0,0,0,0,0,0};
    Test(runs,6);
    Check((runs==std::vector<std::uint32_t>{2,1,0,0,0,0,0,0}));
    runs={7,6,5,4,3,2,1,0};
    Test(runs,0);
    Check(runs[0]==7 && runs[1]==6);
    Test(runs,8);
    Check((runs==std::vector<std::uint32_t>{7,6,5,4,3,2,1,0}));
    // Deterministic stress: all prefixes of long, 16-bit-count runs.
    for (std::size_t length=1;length<512;++length) {
        std::vector<std::uint32_t> original(length);
        for (std::size_t i=0;i<length;++i)
            original[i]=static_cast<std::uint32_t>(length-1-i);
        for (std::size_t cut=0;cut<=length;++cut) {
            auto copy=original;
            Test(copy,cut);
            for (std::size_t i=0;i<length;++i) {
                const auto expected=i<cut
                    ? static_cast<std::uint32_t>(cut-1-i)
                    : original[i];
                Check(copy[i]==expected);
            }
        }
    }
    std::puts("N50_EGLANTINE_CONTINUITY_CUT_PASS host=1 stress_prefixes=131328");
}
