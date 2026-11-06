// SPDX-License-Identifier: MIT
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include "rdna2_nr_projection_quantized_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    for(const std::uint32_t channels:{32u,256u,512u,1024u,2048u}){
        const Projection p{2560u,channels,512u,512u,512u,0u,0u};
        const std::uint64_t f32=std::uint64_t(p.tokens)*channels*4u;
        const std::uint64_t fp8=std::uint64_t(p.tokens)*channels;
        const Storage storage{std::uint64_t(p.tokens)*512u,
                              std::uint64_t(channels)*512u,f32,f32};
        QuantizedProjectionPlan q{};
        assert(PrepareQuantizedProjection(p,storage,fp8,q));
        assert(q.quant.elements==fp8);
        assert(q.quant.input_offset_floats==0u);
        assert(q.quant.output_offset_bytes==0u);
        assert(q.fp32_bytes==f32&&q.fp8_bytes==fp8);
        assert(!PrepareQuantizedProjection(p,storage,fp8-1u,q));
        assert(q.fp32_bytes==0u&&q.fp8_bytes==0u);
    }
    const Projection bad_shape{3u,17u,32u,32u,32u,0u,0u};
    QuantizedProjectionPlan q{};
    assert(!PrepareQuantizedProjection(bad_shape,{4096,4096,4096,4096},
                                       4096,q));
    // ViT FFN expansion cannot silently bypass the scalar GEMM budget.
    const Projection huge{2560u,4096u,1024u,1024u,1024u,0u,0u};
    const Storage ample{2560u*1024u,4096u*1024u,
                        2560ull*4096u*4u,2560ull*4096u*4u};
    assert(!PrepareQuantizedProjection(huge,ample,2560ull*4096u,q));
}
