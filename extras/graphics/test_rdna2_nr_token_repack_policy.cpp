// SPDX-License-Identifier: MIT
// CPU reference for the public MIT network token-tile permutation.
#include <cassert>
#include <cstdint>
#include <vector>
#include <algorithm>
#include "rdna2_nr_token_repack_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;

static uint32_t offset(uint32_t token,uint32_t channel,uint32_t c) {
    return ((token/16u)*(c/16u)+channel/16u)*256u+(token%16u)*16u;
}
static void repack(std::vector<uint8_t>& mem,TokenRepack p) {
    assert(CanRepack(p,mem.size()));
    const uint32_t runs=p.channels/16u;
    for(uint32_t i=0;i<p.width*p.height*runs;++i){
        uint32_t raster=i/runs,channel=(i%runs)*16u;
        uint32_t x=raster%p.width,y=raster/p.width;
        uint32_t tile=((y/4u)*(p.width/4u)+x/4u)*16u+(y%4u)*4u+x%4u;
        auto from=p.inverse ? raster:tile, to=p.inverse ? tile:raster;
        const auto src=p.src_base_bytes+offset(from,channel,p.channels);
        const auto dst=p.dst_base_bytes+offset(to,channel,p.channels);
        std::copy_n(mem.begin()+src,16,mem.begin()+dst);
    }
}
int main(){
    TokenRepack p{0,2048,8,8,32,0};
    std::vector<uint8_t> data(6144,0);
    for(uint32_t i=0;i<2048;++i)data[i]=uint8_t((i*29u+11u)&255u);
    const auto initial=data;
    assert(CanRepack(p,data.size()));
    repack(data,p);
    TokenRepack back{2048,4096,8,8,32,1};
    assert(CanRepack(back,data.size()));
    repack(data,back);
    assert(std::equal(data.begin(),data.begin()+2048,data.begin()+4096));
    assert(!CanRepack({0,0,8,8,32,0},data.size()));
    assert(!CanRepack({0,1024,8,8,32,0},data.size()));
    assert(!CanRepack({0,2048,7,8,32,0},data.size()));
    assert(!CanRepack({0,2048,8,8,31,0},data.size()));
    assert(!CanRepack({0,2048,8,8,32,2},data.size()));
    assert(!CanRepack({1,2048,8,8,32,0},data.size()));
    assert(!CanRepack({0,2048,8,8,32,0},2048));
    assert(!CanRepack({0,UINT32_MAX-15u,8,8,32,0},UINT64_MAX));
    return 0;
}
