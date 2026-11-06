// SPDX-License-Identifier: MIT
// Host FSwin plan proof for C=32/64/128/256 and nontrivial window counts.
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "video_core/renderer_vulkan/nr_rdna2_fswin_plan.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u}){
        for(std::uint32_t W:{1u,16u,256u}){
            FSwinGraph p{};
            assert(MakeFSwinGraphPlan(C,W,p));
            assert(CanFSwinGraph(p));
            const auto tokens=std::uint64_t(W)*64u;
            assert(p.dense[0].windows==W);
            assert(p.dense_storage[0].output_bytes==tokens*4u*C);
            assert(p.dense_storage[2].input_bytes==
                   tokens*C*(C==32u?4u:1u));
            assert(p.qkv_storage.q_bytes==tokens*C);
            assert(p.qkv_storage.weight_bytes==3ull*C*C);
            assert(p.attention_storage.bias_bytes==
                   std::uint64_t(C/32u)*4096u*4u);
            assert((p.dense[1].windows==0u)==(C==32u));
            assert((p.dense[1].channels==0u)==(C==32u));
            if(C>32u)
                assert(p.dense_storage[1].weight_bytes==
                       std::uint64_t(C)*128u);
        }
    }
    FSwinGraph empty{};
    assert(!MakeFSwinGraphPlan(16u,1u,empty));
    assert(!MakeFSwinGraphPlan(512u,1u,empty));
    assert(!MakeFSwinGraphPlan(64u,0u,empty));
    assert(!MakeFSwinGraphPlan(64u,257u,empty));
    assert(empty.dense[0].windows==0u);
}
