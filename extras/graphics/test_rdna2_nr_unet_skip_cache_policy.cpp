// SPDX-License-Identifier: MIT
// Four retained U-Net skip buffers, validated against both model plans.
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_cache_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(const char* name) {
    std::ifstream f(name,std::ios::binary);assert(f);
    const std::string src{std::istreambuf_iterator<char>{f},
                          std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> steps;
    assert(ParseNativePlan(src,steps)==NativePlanError::Ok);
    NativeUNetSkipMap map{};
    assert(BuildNativeUNetSkipMap(steps,map)==NativeUNetSkipError::Ok);
    const std::array<NativeUNetSkipSurface,4> raster{{
        {67u,120u},{135u,240u},{270u,480u},{540u,960u}
    }};
    std::array<std::uint64_t,4> bytes{};
    assert(CanNativeUNetSkipSurfaces(map,raster,256ull<<20,bytes));
    constexpr std::array<std::uint64_t,4> expected{
        67ull*120ull*256ull,135ull*240ull*128ull,
        270ull*480ull*64ull,540ull*960ull*32ull
    };
    assert(bytes==expected);
    auto wrong=raster;wrong[0].width++;
    assert(!CanNativeUNetSkipSurfaces(map,wrong,256ull<<20,bytes));
    const std::array<std::uint64_t,4> zeros{};
    assert(bytes==zeros);
    wrong=raster;wrong[3].height=1920u;
    assert(!CanNativeUNetSkipSurfaces(map,wrong,256ull<<20,bytes));
    assert(!CanNativeUNetSkipSurfaces(map,raster,4096u,bytes));
    auto bad=map;
    bad.edges[1].down_block=bad.edges[0].down_block;
    assert(!CanNativeUNetSkipSurfaces(bad,raster,256ull<<20,bytes));
    bad=map;bad.edges[0].skip_windows_x++;
    assert(!CanNativeUNetSkipSurfaces(bad,raster,256ull<<20,bytes));
    bad=map;bad.count=3u;
    assert(!CanNativeUNetSkipSurfaces(bad,raster,256ull<<20,bytes));
}
int main(int argc,char**argv){
    assert(argc==3);
    Check(argv[1]);Check(argv[2]);
}
