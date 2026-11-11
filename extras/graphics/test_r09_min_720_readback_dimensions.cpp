// SPDX-License-Identifier: MIT
// Host geometry check against vendor research PR #42, NEVER a GPU test.
#include "video_core/renderer_vulkan/nr_rdna2_readback_dimensions.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>

namespace P=Vulkan::R09ReadbackPolicy;
struct Shape {std::uint32_t w,h;std::uint64_t bytes;};
constexpr std::array<Shape,2> Good{{
    {1280u,720u,14'745'600u},
    {1920u,1080u,33'177'600u},
}};
constexpr std::array<Shape,11> Bad{{
    {0u,0u,0u},{1280u,0u,0u},{0u,720u,0u},
    {1920u,720u,0u},{1280u,1080u,0u},{3840u,2160u,0u},
    {2560u,1440u,0u},{320u,180u,0u},
    {1u,1u,0u},{UINT32_MAX,UINT32_MAX,0u},
    {1281u,720u,0u},
}};
constexpr bool Verify() {
    for (const auto& x:Good)
        if (!P::Supported(x.w,x.h) ||
            P::Rgba32fBytes(x.w,x.h)!=x.bytes) return false;
    for (const auto& x:Bad)
        if (P::Supported(x.w,x.h) ||
            P::Rgba32fBytes(x.w,x.h)!=0u) return false;
    return true;
}
static_assert(Verify(), "unsafe R09 GPU readback dimensions");
int main(){
    assert(Verify());
    std::cout<<"R09_READBACK_720_1080_SIZE_AND_11_INVALID_EXTENTS_PASS "
                "trained_model=NO ps5=NO runtime=OFF\n";
}
