// SPDX-License-Identifier: MIT
// Scalar numerical oracle for ViT probability-before-normalization contract.
#include <cassert>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include "rdna2_nr_vit_attention_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
static float decode(unsigned r){
    unsigned e=(r>>3u)&15u,m=r&7u;
    float sign=(r&128u)?-1.f:1.f;
    if(e==15u&&m==7u)return std::numeric_limits<float>::quiet_NaN();
    if(e==0u)return sign*float(m)*std::exp2(-9.f);
    return sign*float(8u+m)*std::exp2(float(int(e)-10));
}
static unsigned quant(float v){
    unsigned sign=std::signbit(v)?128u:0u;
    if(std::isnan(v))return sign|127u;
    float a=std::fmin(std::fabs(v),448.f);
    if(a<0.015625f) {
        auto m=static_cast<unsigned>(std::nearbyint(a*512.f));
        return sign|(m>=8u?8u:m);
    }
    int e=static_cast<int>(std::floor(std::log2(a)));
    auto m=static_cast<unsigned>(std::nearbyint((a/std::exp2(float(e))-1.f)*8.f));
    if(m==8u){++e;m=0u;}
    auto eb=static_cast<unsigned>(e+7);
    if(eb>15u||(eb==15u&&m>6u))return sign|126u;
    return sign|(eb<<3u)|m;
}
// Includes half mantissa transform; coefficients exactly representable in f16.
// This CPU test does not certify bitwise equivalence of GPU half FMA.
static float vit_exp(float x) {
    const float y=std::clamp(std::fma(x,0.08953857421875f,1.708984375f),
                            1.439453125f,1.9775390625f);
    const auto mant=static_cast<unsigned>(std::nearbyint((y-1.f)*1024.f));
    const unsigned half=(mant&1023u)<<4u;
    const unsigned e=(half>>10u)&31u, m=half&1023u;
    if(e==0u)return float(m)*std::exp2(-24.f);
    return (1.f+float(m)/1024.f)*std::exp2(float(int(e)-15));
}
static std::array<unsigned,32> context(
    const std::array<std::array<uint8_t,32>,3>& q,
    const std::array<std::array<uint8_t,32>,3>& k,
    const std::array<std::array<uint8_t,32>,3>& v,
    unsigned query,unsigned tokens) {
    std::array<float,32> ctx{};
    float den=0.f;
    for(unsigned key=0;key<tokens;key++){
        float score=0.f;
        for(unsigned c=0;c<32;c++)
            score=std::fma(decode(q[query][c]),decode(k[key][c]),score);
        float p=vit_exp(score);
        den+=p;
        float pq=decode(quant(p));
        for(unsigned c=0;c<32;c++)
            ctx[c]=std::fma(pq,decode(v[key][c]),ctx[c]);
    }
    std::array<unsigned,32> out{};
    for(unsigned c=0;c<32;c++)
        out[c]=quant(ctx[c]/std::max(den,6.198883056640625e-05f));
    return out;
}
int main(){
    VitAttention p{0,0,0,0,1};
    VitAttentionStorage s{1024,1024,1024,1024};
    assert(CanVitAttention(p,s));
    assert(!CanVitAttention(p,{1023,1024,1024,1024}));
    assert(!CanVitAttention(p,{1024,1023,1024,1024}));
    assert(!CanVitAttention(p,{1024,1024,1023,1024}));
    assert(!CanVitAttention(p,{1024,1024,1024,1023}));
    p.tokens=0;assert(!CanVitAttention(p,s));
    p.tokens=2049;assert(!CanVitAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={1,0,0,0,1};assert(!CanVitAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,UINT32_MAX-3u,1};
    assert(!CanVitAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,2048};
    assert(CanVitAttention(p,{2097152,2097152,2097152,2097152}));

    std::array<std::array<uint8_t,32>,3> q{},k{},v{};
    // For two equal logits, the value 0.5 survives E4M3FN quantization.
    v[0].fill(0x38u);
    v[1].fill(0x00u);
    auto o=context(q,k,v,0u,2u);
    for(auto z:o)assert(std::fabs(decode(z)-0.5f)<0.125f);
    // With all zero values, all 32 outputs must be exactly zero.
    v[0].fill(0u);
    o=context(q,k,v,0u,2u);
    for(auto z:o)assert(z==0u);
    // A nonzero Q·K shifts the weighted result toward the matching value.
    q[0][0]=0x40u; // +2
    k[0][0]=0x48u; // +4
    v[0].fill(0x38u);
    o=context(q,k,v,0u,2u);
    for(auto z:o)assert(decode(z)>0.5f);
    // Denominator includes unquantized exp; numerator uses FP8 exp.
    assert(vit_exp(0.f)>0.f);
    assert(std::fabs(decode(quant(vit_exp(0.f)))-vit_exp(0.f))>0.f);
    assert(quant(448.f)==0x7eu);
}
