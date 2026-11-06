// SPDX-License-Identifier: MIT
// Verify U-Net skip relationships against BOTH recovered native plans.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(const char* path,bool original){
    std::ifstream f(path,std::ios::binary);
    assert(f);
    const std::string text{std::istreambuf_iterator<char>{f},
                           std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> steps;
    assert(ParseNativePlan(text,steps)==NativePlanError::Ok);
    NativeUNetSkipMap map{};
    assert(BuildNativeUNetSkipMap(steps,map)==NativeUNetSkipError::Ok);
    assert(map.count==4u);
    constexpr std::array<std::uint32_t,4> original_down{22,14,8,4};
    constexpr std::array<std::uint32_t,4> original_up{48,56,62,66};
    constexpr std::array<std::uint32_t,4> small_down{8,6,4,2};
    constexpr std::array<std::uint32_t,4> small_up{22,24,26,28};
    const auto& downs=original?original_down:small_down;
    const auto& ups=original?original_up:small_up;
    for(std::size_t i=0u;i<map.count;++i){
        const auto& edge=map.edges[i];
        assert(edge.down_block==downs[i]);
        assert(edge.up_block==ups[i]);
        assert(edge.channels==(i==0u?256u:i==1u?128u:i==2u?64u:32u));
        assert(edge.up_input_block+1u==edge.up_block);
    }
    // Never accept a dangling or mismatched skip producer.
    auto malformed=steps;
    for(auto& s:malformed)
        if(s.block==ups[0]){
            s.input1=999;
            break;
        }
    assert(BuildNativeUNetSkipMap(malformed,map)==
           NativeUNetSkipError::MissingProducer);
    assert(map.count==0u);
    // A skip's width is an architectural constraint, not a guess.
    malformed=steps;
    for(auto& s:malformed)
        if(s.block==ups[1]){
            ++s.input_channels;
            break;
        }
    assert(BuildNativeUNetSkipMap(malformed,map)==
           NativeUNetSkipError::BadShape);
    assert(map.count==0u);
    malformed=steps;
    for(auto& s:malformed)
        if(s.block==downs[0]){
            ++s.output_channels;
            break;
        }
    assert(BuildNativeUNetSkipMap(malformed,map)==
           NativeUNetSkipError::BadShape);
    assert(map.count==0u);
    malformed=steps;
    malformed.erase(
        std::remove_if(malformed.begin(),malformed.end(),
            [first=ups[0]](const auto& s){return s.block==first;}),
        malformed.end());
    assert(BuildNativeUNetSkipMap(malformed,map)==
           NativeUNetSkipError::Incomplete);
}
int main(int argc,char**argv){
    assert(argc==3);
    Check(argv[1],true);
    Check(argv[2],false);
}
