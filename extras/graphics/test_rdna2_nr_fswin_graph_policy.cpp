// SPDX-License-Identifier: MIT
// Host-only proof that six FSwin pass contracts compose for all C.
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "rdna2_nr_fswin_graph_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u}){
        FSwinGraph p{};
        const auto heads=C/32u;
        for(std::uint32_t i=0;i<4u;++i){
            const auto in=64u*(i==1u?4u*C:C);
            const auto w=i==0u?4u*C*C:i==1u?C*128u:C*C;
            const auto out=64u*(i==0u?4u*C:C);
            p.dense[i]={0,0,0,0,0,1,C,i};
            p.dense_storage[i]={in,w,64u*C,4u*C,out};
        }
        const auto tensor=64u*C;
        p.qkv={0,0,0,0,0,0,1,C,heads};
        p.qkv_storage={tensor,3u*C*C,heads*4u,tensor,tensor,tensor};
        p.attention={0,0,0,0,0,1,heads};
        p.attention_storage={tensor,tensor,tensor,tensor,
                             heads*64u*64u*4u};
        assert(CanFSwinGraph(p));
        p.dense[3].stage=2;assert(!CanFSwinGraph(p));
        p.dense[3].stage=3;
        p.qkv.channels=512;assert(!CanFSwinGraph(p));
        p.qkv.channels=C;
        p.attention.heads++;assert(!CanFSwinGraph(p));
        p.attention.heads=heads;
        p.dense_storage[1].weight_bytes--;assert(!CanFSwinGraph(p));
        p.dense_storage[1].weight_bytes++;
        assert(CanFSwinGraph(p));
    }
}
