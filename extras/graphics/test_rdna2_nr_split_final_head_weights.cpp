// SPDX-License-Identifier: MIT
#include "video_core/renderer_vulkan/nr_rdna2_split_final_head_weight_loader.h"
#include "rdna2_nr_projection_quantized_policy.h"
#include <cassert>
#include <cstdint>
#include <span>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    std::vector<std::uint8_t> raw(1024u*512u,0x38u);
    raw[0]=0u;raw.back()=0x40u;
    std::vector<std::uint8_t> out;
    assert(DecodeSplitFinalHeadWeights(raw,out));
    assert(out.size()==1024u*512u);
    assert(out[0]==0x80u&&out.back()==0x40u);
    assert(!DecodeSplitFinalHeadWeights(
      std::span<const std::uint8_t>{raw.data(),raw.size()-1u},out));
    assert(out.empty());
    raw[102u]=0x7fu;
    assert(!DecodeSplitFinalHeadWeights(raw,out)&&out.empty());
    raw[102u]=0xffu;
    assert(!DecodeSplitFinalHeadWeights(raw,out)&&out.empty());
    const Projection native{1920u,1024u,512u,512u,512u,0u,0u};
    const Storage sizes{1920ull*512u,1024u*512u,
                        1920ull*1024u*4u,1920ull*1024u*4u};
    QuantizedProjectionPlan plan{};
    assert(PrepareQuantizedProjection(native,sizes,1920ull*1024u,plan));
    assert(plan.quant.elements==1920u*1024u);
    assert(!PrepareQuantizedProjection(native,sizes,
                                      1920ull*1024u-1u,plan));
    assert(!PrepareQuantizedProjection(native,
        {sizes.activation_bytes-1u,sizes.weight_bytes,
         sizes.output_bytes,sizes.free_transient_bytes},
         1920ull*1024u,plan));
    // Whole 8x5-window domain: 2560 tokens, remaining ones zero-filled.
    const Projection whole{2560u,1024u,512u,512u,512u,0u,0u};
    const Storage padded{2560ull*512u,1024u*512u,
                         2560ull*1024u*4u,2560ull*1024u*4u};
    assert(PrepareQuantizedProjection(whole,padded,2560ull*1024u,plan));
    assert(plan.quant.elements==2560u*1024u);
    assert(!PrepareQuantizedProjection(whole,
        {padded.activation_bytes,padded.weight_bytes,
         padded.output_bytes-4u,padded.free_transient_bytes},
         2560ull*1024u,plan));
}
