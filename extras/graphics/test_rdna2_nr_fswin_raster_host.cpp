// SPDX-License-Identifier: MIT
// Reversible first-layer host feature-window packing with edge padding.
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <span>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_fswin_raster_host.h"
using namespace Eden::Graphics::NeuralRDNA2;

static void Roundtrip(std::uint32_t width,std::uint32_t height,
                      std::uint32_t channels) {
    const FSwinRasterLayout layout{
        width,height,(width+7u)/8u,(height+7u)/8u,channels,0u};
    std::vector<std::uint8_t> raster(
        std::size_t(width)*height*channels);
    for(std::size_t i=0;i<raster.size();++i)
        raster[i]=std::uint8_t((i*57u+(i>>5u))&255u);
    std::vector<std::uint8_t> packed,restored;
    assert(PackFSwinFeatureRaster(raster,layout,packed));
    assert(packed.size()==
        std::size_t(layout.windows_x)*layout.windows_y*64u*channels);
    assert(UnpackFSwinFeatureRaster(packed,layout,restored));
    assert(restored==raster);
    // In-place source/output alias remains safe: read into a new scratch.
    auto alias=raster;
    assert(PackFSwinFeatureRaster(
        std::span<const std::uint8_t>{alias.data(),alias.size()},
        layout,alias));
    assert(alias==packed);
    assert(!PackFSwinFeatureRaster(
        std::span<const std::uint8_t>{raster.data(),raster.size()-1u},
        layout,restored));
    assert(restored.empty());
}
int main(){
    for(std::uint32_t channels:{32u,64u,128u,256u}){
        Roundtrip(1,1,channels);
        Roundtrip(7,13,channels);
        Roundtrip(8,8,channels);
        Roundtrip(9,9,channels);
        Roundtrip(31,17,channels);
        Roundtrip(64,16,channels);
    }
    FSwinRasterLayout invalid{9u,9u,1u,1u,32u,0u};
    std::vector<std::uint8_t> input(9u*9u*32u),out(3u,0xabu);
    assert(!PackFSwinFeatureRaster(input,invalid,out));
    assert(out.empty());
    invalid.width=0u;
    assert(!UnpackFSwinFeatureRaster(input,invalid,out));
}
