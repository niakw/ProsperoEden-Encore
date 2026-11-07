// SPDX-License-Identifier: MIT
// Original and Compact native plans; one depth cannot be silently omitted.
#include "rdna2_nr_unet_down_sequence_policy.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Test(const char* path){
    std::ifstream f(path,std::ios::binary);assert(f);
    const std::string content{std::istreambuf_iterator<char>{f},
                              std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> steps;
    assert(ParseNativePlan(content,steps)==NativePlanError::Ok);
    NativeUNetSkipMap map{};
    assert(BuildNativeUNetSkipMap(steps,map)==NativeUNetSkipError::Ok);
    std::array<FSwinWindowLayout,4> in{},out{};
    std::array<std::uint64_t,4> down{};
    std::uint64_t first=0u;
    for(const auto& e:map.edges){
        const auto i=e.channels==32u?0u:e.channels==64u?1u:
                     e.channels==128u?2u:3u;
        in[i]={e.skip_windows_x,e.skip_windows_y,0,0};
        out[i]={e.skip_windows_x,e.skip_windows_y,0,-1};
        const auto w=e.skip_height,h=e.skip_width;
        down[i]=std::uint64_t(w/2u)*(h/2u)*(e.channels*2u);
        if(i==0u)first=std::uint64_t(w)*h*32u;
    }
    assert(CanNativeUNetDownSequence(map,in,out,first,down));
    assert(!CanNativeUNetDownSequence(map,in,out,first-1u,down));
    for(std::size_t i=0u;i<4u;++i){
        auto bad=down;bad[i]--;
        assert(!CanNativeUNetDownSequence(map,in,out,first,bad));
        auto bad_input=in;bad_input[i].windows_x++;
        assert(!CanNativeUNetDownSequence(map,bad_input,out,first,down));
        bad_input=in;bad_input[i].shift_y=-1;
        assert(!CanNativeUNetDownSequence(map,bad_input,out,first,down));
        auto bad_output=out;bad_output[i].shift_x=2;
        assert(!CanNativeUNetDownSequence(map,in,bad_output,first,down));
    }
    auto bad_map=map;bad_map.count=3u;
    assert(!CanNativeUNetDownSequence(bad_map,in,out,first,down));
    bad_map=map;bad_map.edges[0].channels=512u;
    assert(!CanNativeUNetDownSequence(bad_map,in,out,first,down));
    bad_map=map;bad_map.edges[1].down_block=bad_map.edges[2].down_block;
    assert(!CanNativeUNetDownSequence(bad_map,in,out,first,down));
}
int main(int argc,char** argv){
    assert(argc==3);
    Test(argv[1]);Test(argv[2]);
}
