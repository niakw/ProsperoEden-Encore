// SPDX-License-Identifier: MIT
// Host safety and numerical reference for RDNA2 32-head ViT QKV bridge.
#include "rdna2_nr_vit_qkv_norm_policy.h"
#include "rdna2_nr_projection_policy.h"
#include "rdna2_nr_vit_attention_policy.h"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
using namespace Eden::Graphics::NeuralRDNA2;
static float normalize(float x,float norm2,float temperature){
    return x*std::sqrt(32.0f)*temperature/
        std::sqrt(std::max(norm2,1e-30f));
}
int main(){
    constexpr std::uint32_t n=2560;
    const VitQkvNorm norm{n,0u,0u,0u,0u,0u};
    const VitQkvNormStorage size{
        std::uint64_t(n)*3072u*4u,128u,
        std::uint64_t(n)*1024u,std::uint64_t(n)*1024u,
        std::uint64_t(n)*1024u};
    assert(CanVitQkvNorm(norm,size));
    // Same exact buffers validate both sides of ViT QKV -> attention.
    const Projection gemm{n,3072u,1024u,1024u,1024u,0u,0u};
    const Storage storage{
        std::uint64_t(n)*1024u,3072ull*1024u,
        size.input_bytes,size.input_bytes};
    assert(CanDispatch(gemm,storage));
    const VitAttention attn{0u,0u,0u,0u,n};
    assert(CanVitAttention(attn,
        {size.q_bytes,size.k_bytes,size.v_bytes,size.q_bytes}));
    // Reject all incomplete tensor capacities (fail-closed).
    assert(!CanVitQkvNorm(norm,{size.input_bytes-4u,size.scale_bytes,
                                size.q_bytes,size.k_bytes,size.v_bytes}));
    assert(!CanVitQkvNorm(norm,{size.input_bytes,size.scale_bytes-4u,
                                size.q_bytes,size.k_bytes,size.v_bytes}));
    assert(!CanVitQkvNorm(norm,{size.input_bytes,size.scale_bytes,
                                size.q_bytes-1u,size.k_bytes,size.v_bytes}));
    assert(!CanVitQkvNorm(norm,{size.input_bytes,size.scale_bytes,
                                size.q_bytes,size.k_bytes-1u,size.v_bytes}));
    assert(!CanVitQkvNorm(norm,{size.input_bytes,size.scale_bytes,
                                size.q_bytes,size.k_bytes,size.v_bytes-1u}));
    auto bad=norm;
    bad.tokens=0u;assert(!CanVitQkvNorm(bad,size));
    bad.tokens=4097u;assert(!CanVitQkvNorm(bad,{
        UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=norm;bad.q_base_bytes=1u;
    assert(!CanVitQkvNorm(bad,{UINT64_MAX,UINT64_MAX,
                              UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=norm;bad.src_base_floats=UINT32_MAX-3u;
    assert(!CanVitQkvNorm(bad,{UINT64_MAX,UINT64_MAX,
                              UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=norm;bad.scale_base_floats=UINT32_MAX-3u;
    assert(!CanVitQkvNorm(bad,{UINT64_MAX,UINT64_MAX,
                              UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    bad=norm;bad.q_base_bytes=4u;
    auto padded=size;padded.q_bytes+=4u;
    assert(CanVitQkvNorm(bad,padded));
    bad=norm;bad.tokens=4096u;
    const VitQkvNormStorage max{
        4096ull*3072u*4u,128u,4096ull*1024u,
        4096ull*1024u,4096ull*1024u};
    assert(CanVitQkvNorm(bad,max));
    bad.tokens=4097u;assert(!CanVitQkvNorm(bad,max));
    // Numerical oracle: head-0 one-hot Q and K are cosine normalized;
    // V passes unchanged (the neural attention shader reads FP8 Q/K/V).
    std::array<float,32> q{},k{},v{};
    q[0]=3.0f; k[0]=4.0f; v[0]=2.0f;
    float qn=0.f,kn=0.f;
    for(unsigned c=0;c<32u;++c){
        qn=std::fma(q[c],q[c],qn);
        kn=std::fma(k[c],k[c],kn);
    }
    assert(std::fabs(normalize(q[0],qn,1.f)-std::sqrt(32.0f))<1e-5f);
    assert(std::fabs(k[0]/std::sqrt(kn)-1.f)<1e-5f);
    assert(v[0]==2.f);
    q.fill(0.f);k.fill(0.f);
    assert(normalize(q[0],0.f,2.f)==0.f);
}
