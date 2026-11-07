// SPDX-License-Identifier: MIT
#include "rdna2_nr_unet_up_sequence_policy.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Test(const char* name){
    std::ifstream f(name,std::ios::binary);assert(f);
    const std::string source{std::istreambuf_iterator<char>{f},
                             std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(source,rows)==NativePlanError::Ok);
    NativeUNetSkipMap graph{};
    assert(BuildNativeUNetSkipMap(rows,graph)==NativeUNetSkipError::Ok);
    std::array<FSwinWindowLayout,4> in{},out{};
    std::array<std::uint64_t,4> buffers{};
    std::uint64_t low=0u;
    for(const auto& e:graph.edges){
        const std::size_t i=e.channels==256u?0u:
                            e.channels==128u?1u:
                            e.channels==64u?2u:3u;
        in[i]={e.skip_windows_x,e.skip_windows_y,0,0};
        out[i]={e.skip_windows_x,e.skip_windows_y,-1,0};
        buffers[i]=std::uint64_t(e.skip_height)*e.skip_width*e.channels;
        if(i==0u)
            low=std::uint64_t(e.skip_height/2u)*
                (e.skip_width/2u)*512u;
    }
    assert(CanNativeUNetUpSequence(graph,in,out,low,buffers));
    assert(!CanNativeUNetUpSequence(graph,in,out,low-1u,buffers));
    for(std::size_t i=0u;i<4u;++i){
        auto smaller=buffers;smaller[i]--;
        assert(!CanNativeUNetUpSequence(graph,in,out,low,smaller));
        auto wrong_in=in;wrong_in[i].windows_y++;
        assert(!CanNativeUNetUpSequence(graph,wrong_in,out,low,buffers));
        wrong_in=in;wrong_in[i].shift_x=-2;
        assert(!CanNativeUNetUpSequence(graph,wrong_in,out,low,buffers));
        auto wrong_out=out;wrong_out[i].shift_y=2;
        assert(!CanNativeUNetUpSequence(graph,in,wrong_out,low,buffers));
    }
    auto bad=graph;bad.count=3u;
    assert(!CanNativeUNetUpSequence(bad,in,out,low,buffers));
    bad=graph;bad.edges[0].channels=512u;
    assert(!CanNativeUNetUpSequence(bad,in,out,low,buffers));
    bad=graph;bad.edges[1].up_input_block=bad.edges[1].up_block;
    assert(!CanNativeUNetUpSequence(bad,in,out,low,buffers));
}
int main(int argc,char** argv){
    assert(argc==3);
    Test(argv[1]);Test(argv[2]);
}
