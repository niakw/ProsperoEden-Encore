// SPDX-License-Identifier: MIT
#include "rdna2_nr_vit_native_route_policy.h"
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
void Check(const char* file,bool original){
    std::ifstream stream(file,std::ios::binary);
    assert(stream);
    const std::string text{std::istreambuf_iterator<char>{stream},
                           std::istreambuf_iterator<char>{}};
    std::vector<NativePlanStep> rows;
    assert(ParseNativePlan(text,rows)==NativePlanError::Ok);
    NativeVitRoute route{};
    assert(BuildNativeVitRoute(rows,route)==NativeVitRouteError::Ok);
    assert(route.count==8u&&route.tokens==2560u);
    assert(route.input_split_block==(original?30u:10u));
    assert(route.decoder_block==(original?39u:19u));
    assert(route.blocks[0].block==(original?31u:11u));
    assert(route.blocks[7].block==(original?38u:18u));
    for(std::uint32_t i=0u;i<8u;++i){
        const auto& b=route.blocks[i];
        assert(b.block==route.blocks[0].block+i);
        assert(b.tokens==route.tokens);
        assert(b.input_block==(i==0u?route.input_split_block:
                               route.blocks[i-1u].block));
        for(std::uint32_t j=0u;j<5u;++j)
            assert(rows[b.first_row+j].layer==j);
    }
    auto broken=rows;
    for(auto& r:broken)if(r.type=="CCVit1DFfnContract"){
        r.output_channels=2048u;break;
    }
    assert(BuildNativeVitRoute(broken,route)!=NativeVitRouteError::Ok);
    assert(route.count==0u);
    broken=rows;
    for(auto& r:broken)if(r.type=="CCVit1DQKV"){
        r.input0=0;break;
    }
    assert(BuildNativeVitRoute(broken,route)!=NativeVitRouteError::Ok);
    assert(route.count==0u);
    broken=rows;
    for(auto& r:broken)if(r.type=="CCDecInputUpsample"){
        r.input1=0;break;
    }
    assert(BuildNativeVitRoute(broken,route)!=NativeVitRouteError::Ok);
    assert(route.count==0u);
    broken=rows;
    for(auto& r:broken)if(r.type=="CCVit1DProjection"){
        r.tokens--;break;
    }
    assert(BuildNativeVitRoute(broken,route)!=NativeVitRouteError::Ok);
    assert(route.count==0u);
}
int main(int argc,char** argv){
    assert(argc==3);
    Check(argv[1],true);
    Check(argv[2],false);
}
