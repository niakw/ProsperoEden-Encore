// SPDX-License-Identifier: MIT
#include "rdna2_nr_preblock_boundary_policy.h"
#include <cassert>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Check(const char* path){
    std::ifstream f(path,std::ios::binary);assert(f);
    const std::string source{std::istreambuf_iterator<char>{f},
                             std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(source,rows)==NativePlanError::Ok);
    NativeUNetSkipMap graph{};
    assert(BuildNativeUNetSkipMap(rows,graph)==NativeUNetSkipError::Ok);
    const auto bytes=std::uint64_t(rows[1].width)*rows[1].height*32u;
    assert(CanNativePreblockBoundary(rows,graph,bytes));
    assert(!CanNativePreblockBoundary(rows,graph,bytes-1u));
    auto bad=rows;bad[0].width+=2u;
    assert(!CanNativePreblockBoundary(bad,graph,bytes));
    bad=rows;bad[0].output_channels=64u;
    assert(!CanNativePreblockBoundary(bad,graph,bytes));
    bad=rows;bad[1].width++;
    assert(!CanNativePreblockBoundary(bad,graph,bytes));
    bad=rows;bad[1].input0=2;
    assert(!CanNativePreblockBoundary(bad,graph,bytes));
    bad=rows;bad.push_back(rows[0]);
    assert(!CanNativePreblockBoundary(bad,graph,bytes));
    auto g=graph;
    for(auto& edge:g.edges)if(edge.channels==32u)++edge.skip_width;
    assert(!CanNativePreblockBoundary(rows,g,bytes));
    g=graph;
    for(auto& edge:g.edges)if(edge.channels==32u)++edge.down_block;
    // Downstream block ID is not assumed constant: this should remain
    // valid structurally when the downstream segment is relocated.
    assert(CanNativePreblockBoundary(rows,g,bytes));
}
int main(int argc,char** argv){
    assert(argc==3);
    Check(argv[1]);
    Check(argv[2]);
}
