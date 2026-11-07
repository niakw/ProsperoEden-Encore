// SPDX-License-Identifier: MIT
#include "rdna2_nr_postblock_mix_policy.h"
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
    const PostblockMixShape s{rows[0].height,rows[0].width};
    const auto full=std::uint64_t(s.width)*s.height*32u;
    assert(CanNativePostblockMixBoundary(rows,s));
    assert(CanPostblockMix(s,{full/4u,full,128u,full}));
    assert(!CanPostblockMix(s,{full/4u-1u,full,128u,full}));
    assert(!CanPostblockMix(s,{full/4u,full-1u,128u,full}));
    assert(!CanPostblockMix(s,{full/4u,full,127u,full}));
    assert(!CanPostblockMix(s,{full/4u,full,128u,full-1u}));
    assert(!CanPostblockMix({s.width-1u,s.height},
                            {full/4u,full,128u,full}));
    auto bad=rows;bad.back().input1=1;
    assert(!CanNativePostblockMixBoundary(bad,s));
    bad=rows;bad.back().input0=0;
    assert(!CanNativePostblockMixBoundary(bad,s));
    bad=rows;bad.back().grid_x++;
    assert(!CanNativePostblockMixBoundary(bad,s));
    bad=rows;bad.back().width++;
    assert(!CanNativePostblockMixBoundary(bad,s));
    bad=rows;bad[0].width+=8u;
    assert(!CanNativePostblockMixBoundary(bad,s));
    bad=rows;bad[bad.size()-2u].channels=64u;
    assert(!CanNativePostblockMixBoundary(bad,s));
}
int main(int argc,char** argv){
    assert(argc==3);
    Check(argv[1]);Check(argv[2]);
}
