// SPDX-License-Identifier: GPL-3.0-or-later
#include "fsr31_vram_budget.h"
#include <cassert>
using namespace Eden::Graphics::Fsr31Budget;
int main() {
    const Memory ample{.device_local_bytes=8ULL*1024*MiB,
                       .used_bytes=2ULL*1024*MiB,.usage_is_known=true};
    const auto typical=Evaluate({1280,720,2560,1440},ample);
    assert(typical.decision==Decision::Allowed);
    assert(typical.nominal_bytes>80*MiB);
    assert(typical.required_bytes>typical.nominal_bytes);
    const auto near4k=Evaluate({2560,1440,3840,2160},ample);
    assert(near4k.decision==Decision::Allowed);
    assert(near4k.required_bytes>typical.required_bytes);
    assert(Evaluate({3840,2160,7680,4320},ample).decision==
           Decision::ExceedsAbsoluteLimit);
    assert(Evaluate({0,720,1920,1080},ample).decision==
           Decision::InvalidDimensions);
    assert(Evaluate({32,32,1920,1080},ample).decision==
           Decision::InvalidDimensions);
    assert(Evaluate({1280,720,3841,2160},ample).decision==
           Decision::InvalidDimensions);
    assert(Evaluate({9000,720,9000,1440},ample).decision==
           Decision::InvalidDimensions);
    assert(Evaluate({1920,1080,1280,720},ample).decision==
           Decision::InvalidDimensions);
    auto poor=ample;
    poor.used_bytes=poor.device_local_bytes-typical.required_bytes*2;
    assert(Evaluate({1280,720,2560,1440},poor).decision==
           Decision::InsufficientDeviceMemory);
    poor.used_bytes=0;
    poor.device_local_bytes=0;
    poor.usage_is_known=false;
    assert(Evaluate({1280,720,2560,1440},poor).decision==
           Decision::InsufficientDeviceMemory);
    return 0;
}
