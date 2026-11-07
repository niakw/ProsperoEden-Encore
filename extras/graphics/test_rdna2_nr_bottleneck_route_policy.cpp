// SPDX-License-Identifier: MIT
#include "rdna2_nr_bottleneck_route_policy.h"
#include <cassert>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(const char* file,bool original){
    std::ifstream in(file,std::ios::binary);
    assert(in);
    const std::string text{std::istreambuf_iterator<char>{in},
                           std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(text,rows)==NativePlanError::Ok);
    NativeSplitRoutes split{};
    NativeVitRoute vit{};
    assert(BuildNativeSplitRoutes(rows,split)==SplitNativeRoutesError::Ok);
    assert(BuildNativeVitRoute(rows,vit)==NativeVitRouteError::Ok);
    assert(CanLinkNativeNrBottleneckRoutes(split,vit));
    assert(split.runs[0].count==(original?8u:2u));
    assert(split.runs[1].count==(original?8u:2u));
    assert(vit.input_split_block==(original?30u:10u));
    assert(vit.decoder_block==(original?39u:19u));
    assert(vit.raster_width==33u&&vit.raster_height==60u);
    auto bad=vit;bad.decoder_block++;
    assert(!CanLinkNativeNrBottleneckRoutes(split,bad));
    bad=vit;bad.input_split_block++;
    assert(!CanLinkNativeNrBottleneckRoutes(split,bad));
    bad=vit;bad.raster_width++;
    assert(!CanLinkNativeNrBottleneckRoutes(split,bad));
    bad=vit;bad.blocks[3].input_block++;
    assert(!CanLinkNativeNrBottleneckRoutes(split,bad));
    auto missing=split;missing.runs[1].count--;
    assert(!CanLinkNativeNrBottleneckRoutes(missing,vit));
    missing=split;missing.blocks[missing.runs[0].start+
                                 missing.runs[0].count-1u].
                       plan.has_pooled_projection=false;
    assert(!CanLinkNativeNrBottleneckRoutes(missing,vit));
}
int main(int argc,char**argv){
    assert(argc==3);
    Check(argv[1],true);
    Check(argv[2],false);
}
