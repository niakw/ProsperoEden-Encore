// SPDX-License-Identifier: MIT
#include <array>
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "video_core/renderer_vulkan/nr_rdna2_fswin_bindings.h"
using namespace Eden::Graphics::NeuralRDNA2;
static FSwinGraph MakePlan(std::uint32_t C){
    FSwinGraph plan{};
    const auto heads=C/32u;
    for(std::uint32_t i=0;i<4u;++i){
        if(i==1u&&C==32u)continue;
        plan.dense[i]={0,0,0,0,0,1,C,i};
        const auto in=64u*(i==1u||(i==2u&&C==32u)?4u*C:C);
        const auto wt=i==0u?4u*C*C:i==1u?C*128u:
                      (i==2u&&C==32u)?4u*C*C:C*C;
        const auto out=64u*(i==0u?4u*C:C);
        plan.dense_storage[i]={in,wt,64u*C,4u*C,out};
    }
    const auto total=64u*C;
    plan.qkv={0,0,0,0,0,0,1,C,heads};
    plan.qkv_storage={total,3u*C*C,4u*heads,total,total,total};
    plan.attention={0,0,0,0,0,1,heads};
    plan.attention_storage={total,total,total,total,heads*4096u*4u};
    return plan;
}
int main(){
    for(std::uint32_t C:{32u,64u,128u,256u}){
        FSwinLayerWeightRanges weights{};
        weights.channels=C;weights.heads=C/32u;
        const std::array<NeuralWeightRange*,9> ranges{
            &weights.expand,&weights.middle,&weights.contract,
            &weights.qkv,&weights.projection,&weights.residual_scale,
            &weights.attention_residual_scale,&weights.attention_bias,
            &weights.qk_scales};
        const std::array<std::uint64_t,9> lengths{
            4ull*C*C,C==32u?0ull:std::uint64_t(C)*128u,
            C==32u?4ull*C*C:std::uint64_t(C)*C,
            3ull*C*C,std::uint64_t(C)*C,4ull*C,4ull*C,
            std::uint64_t(weights.heads)*4096u*4u,
            4ull*weights.heads};
        std::uint64_t arena_bytes=0u;
        for(std::size_t i=0;i<ranges.size();++i){
            if(lengths[i]==0u)continue;
            ranges[i]->offset_bytes=std::uint32_t(arena_bytes);
            ranges[i]->length_bytes=std::uint32_t(lengths[i]);
            arena_bytes=(arena_bytes+lengths[i]+255u)&~255ull;
        }
        auto plan=MakePlan(C);
        assert(BindFSwinGraphWeights(weights,arena_bytes,plan));
        assert(CanFSwinGraph(plan));
        assert(plan.dense[0].w_base_bytes==weights.expand.offset_bytes);
        assert(plan.dense[2].w_base_bytes==weights.contract.offset_bytes);
        assert(plan.dense[3].w_base_bytes==weights.projection.offset_bytes);
        assert(plan.qkv.w_base_bytes==weights.qkv.offset_bytes);
        assert(plan.qkv.scale_base_floats==weights.qk_scales.offset_bytes/4u);
        assert(plan.attention.bias_base_floats==
               weights.attention_bias.offset_bytes/4u);
        assert(plan.dense[2].scale_base_floats==
               weights.residual_scale.offset_bytes/4u);
        assert(plan.dense[3].scale_base_floats==
               weights.attention_residual_scale.offset_bytes/4u);
        const auto saved=plan.qkv.w_base_bytes;
        auto bad=weights;bad.qkv.length_bytes--;
        assert(!BindFSwinGraphWeights(bad,arena_bytes,plan));
        assert(plan.qkv.w_base_bytes==saved);
        bad=weights;bad.qkv.offset_bytes=bad.expand.offset_bytes;
        assert(!BindFSwinGraphWeights(bad,arena_bytes,plan));
        bad=weights;bad.attention_bias.offset_bytes++;
        assert(!BindFSwinGraphWeights(bad,arena_bytes,plan));
        bad=weights;
        assert(!BindFSwinGraphWeights(bad,arena_bytes-1u,plan));
        bad=weights;bad.heads++;
        assert(!BindFSwinGraphWeights(bad,arena_bytes,plan));
        if(C==32u){
            bad=weights;bad.middle.length_bytes=128u;
            assert(!BindFSwinGraphWeights(bad,arena_bytes,plan));
        }
    }
}
