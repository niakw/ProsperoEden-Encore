// SPDX-License-Identifier: MIT
#include "rdna2_nr_unet_bottleneck_link_policy.h"
#include <cassert>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(const char* path){
    std::ifstream f(path,std::ios::binary);assert(f);
    const std::string text{std::istreambuf_iterator<char>{f},
                           std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(text,rows)==NativePlanError::Ok);
    NativeUNetSkipMap graph{};
    NativeSplitRoutes split{};
    NativeVitRoute vit{};
    assert(BuildNativeUNetSkipMap(rows,graph)==NativeUNetSkipError::Ok);
    assert(BuildNativeSplitRoutes(rows,split)==SplitNativeRoutesError::Ok);
    assert(BuildNativeVitRoute(rows,vit)==NativeVitRouteError::Ok);
    const auto& first=split.blocks[split.runs[0].start];
    const auto required=std::uint64_t(first.raster_width)*
                        first.raster_height*512u;
    assert(CanNativeUNetBottleneckLink(
        graph,split,vit,required,required,required));
    assert(!CanNativeUNetBottleneckLink(
        graph,split,vit,required-1u,required,required));
    assert(!CanNativeUNetBottleneckLink(
        graph,split,vit,required,required-1u,required));
    assert(!CanNativeUNetBottleneckLink(
        graph,split,vit,required,required,required-1u));
    auto g=graph;g.count=3u;
    assert(!CanNativeUNetBottleneckLink(g,split,vit,required,required,required));
    g=graph;for(auto& edge:g.edges)if(edge.channels==256u)++edge.down_block;
    assert(!CanNativeUNetBottleneckLink(g,split,vit,required,required,required));
    g=graph;for(auto& edge:g.edges)if(edge.channels==256u)++edge.up_input_block;
    assert(!CanNativeUNetBottleneckLink(g,split,vit,required,required,required));
    auto s=split;
    s.blocks[s.runs[0].start].raster_width++;
    assert(!CanNativeUNetBottleneckLink(graph,s,vit,required,required,required));
    s=split;s.blocks[s.runs[1].start+s.runs[1].count-1u].output_view=false;
    assert(!CanNativeUNetBottleneckLink(graph,s,vit,required,required,required));
    auto bad_vit=vit;bad_vit.raster_height++;
    assert(!CanNativeUNetBottleneckLink(graph,split,bad_vit,
                                        required,required,required));
}
int main(int argc,char** argv){
    assert(argc==3);
    Check(argv[1]);
    Check(argv[2]);
}
