// SPDX-License-Identifier: GPL-3.0-or-later
#include "fxaa_quality_select.h"
#include <cassert>
#include <thread>
#include <atomic>
int main() {
    using namespace Eden::Graphics;
    SetEnhancedFxaa(false);
    assert(!EnhancedFxaa());
    SetEnhancedFxaa(true);
    assert(EnhancedFxaa());
    std::atomic<bool> run{true};
    std::thread toggle([&] {
        for (int n=0;n<10000;++n)
            SetEnhancedFxaa((n&1)!=0);
        run.store(false);
    });
    while (run.load()) (void)EnhancedFxaa();
    toggle.join();
    SetEnhancedFxaa(false);
    assert(!EnhancedFxaa());
    return 0;
}
