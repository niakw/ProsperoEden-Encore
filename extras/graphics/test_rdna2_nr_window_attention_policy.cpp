// SPDX-License-Identifier: MIT
// Unfused RDNA2 64x32 attention: validated shape, packed FP8, stable softmax.
#include <cassert>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include "rdna2_nr_window_attention_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;

static float dequant(uint32_t raw){
    const auto e=(raw>>3)&15u, m=raw&7u;
    const float sign=(raw&128u)?-1.f:1.f;
    if(e==15u && m==7u)return std::numeric_limits<float>::quiet_NaN();
    if(e==0)return sign*float(m)*std::exp2(-9.f);
    return sign*float(8u+m)*std::exp2(float(int(e)-10));
}
static uint32_t quant(float v){
    const uint32_t s=std::signbit(v)?128u:0u;
    if(std::isnan(v))return s|127u;
    float a=std::fmin(std::fabs(v),448.f);
    if(a<0.015625f) {
        auto m=static_cast<uint32_t>(std::nearbyint(a*512.f));
        return s|(m>=8u?8u:m);
    }
    int e=static_cast<int>(std::floor(std::log2(a)));
    auto m=static_cast<uint32_t>(std::nearbyint((a/std::exp2(float(e))-1.f)*8.f));
    if(m==8u){++e;m=0u;}
    auto eb=static_cast<uint32_t>(e+7);
    if(eb>15u || (eb==15u && m>6u))return s|126u;
    return s|(eb<<3u)|m;
}
static std::array<uint8_t,32> attention(
    const std::array<uint8_t,32>& q,
    const std::array<std::array<uint8_t,32>,64>& k,
    const std::array<std::array<uint8_t,32>,64>& v,
    const std::array<float,64>& bias) {
    std::array<float,64> logits{}, weights{};
    float peak=-std::numeric_limits<float>::max();
    for(unsigned j=0;j<64;j++){
        float score=0.f;
        for(unsigned c=0;c<32;c++)
            score=std::fma(dequant(q[c]),dequant(k[j][c]),score);
        logits[j]=score+bias[j];
        peak=std::max(peak,logits[j]);
    }
    float denominator=0.f;
    for(unsigned j=0;j<64;j++){
        weights[j]=std::exp(logits[j]-peak);
        denominator+=weights[j];
    }
    denominator=std::max(denominator,6.103515625e-05f);
    std::array<float,32> context{};
    for(unsigned j=0;j<64;j++){
        float weight=dequant(quant(weights[j]/denominator));
        for(unsigned c=0;c<32;c++)
            context[c]=std::fma(weight,dequant(v[j][c]),context[c]);
    }
    std::array<uint8_t,32> out{};
    for(unsigned c=0;c<32;c++)out[c]=static_cast<uint8_t>(quant(context[c]));
    return out;
}
int main(){
    // Exact contract: one 64x32 E4M3FN tensor, one head, one window.
    WindowAttention p{0,0,0,0,0,1,1};
    AttentionStorage s{2048,2048,2048,2048,16384};
    assert(CanWindowAttention(p,s));
    assert(!CanWindowAttention(p,{2047,2048,2048,2048,16384}));
    assert(!CanWindowAttention(p,{2048,2047,2048,2048,16384}));
    assert(!CanWindowAttention(p,{2048,2048,2047,2048,16384}));
    assert(!CanWindowAttention(p,{2048,2048,2048,2047,16384}));
    assert(!CanWindowAttention(p,{2048,2048,2048,2048,16383}));
    p.heads=3;assert(!CanWindowAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,1,1};
    p.windows=65536;assert(!CanWindowAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,1,1};
    p.q_base_bytes=1;assert(!CanWindowAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,1,1};
    p.bias_base_floats=UINT32_MAX;
    assert(!CanWindowAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,1,1};
    p.out_base_bytes=UINT32_MAX-3u;
    assert(!CanWindowAttention(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));

    assert(quant(0.f)==0x00u);
    assert(quant(1.f)==0x38u);
    assert(quant(-2.f)==0xc0u);
    assert(quant(448.f)==0x7eu);
    assert(quant(0.015625f)==0x08u);
    assert(quant(1.f/64.f)==0x08u);
    assert(quant(1000.f)==0x7eu);
    assert(dequant(0x38u)==1.f);
    assert(dequant(0x08u)==1.f/64.f);

    std::array<uint8_t,32> q{};
    std::array<std::array<uint8_t,32>,64> k{},v{};
    std::array<float,64> bias{};
    // Zero Q/K and zero bias: exact 1/64 weight in E4M3FN.
    for(auto& token:v)token.fill(0x38u); // value +1 for all keys
    auto out=attention(q,k,v,bias);
    for(auto x:out)assert(x==0x38u); // context 64*(1/64)*1
    // Large relative bias: stable exponential and one-hot context.
    for(auto& token:v)token.fill(0x00u);
    v[7].fill(0x40u); // +2 at key 7
    bias[7]=100.f;
    out=attention(q,k,v,bias);
    for(auto x:out)assert(x==0x40u); // softmax key 7 rounds to 1
    bias[7]=-100.f;
    out=attention(q,k,v,bias);
    for(auto x:out)assert(x==0x00u);
    // Q/K score can determine selection even without a bias.
    bias.fill(0.f);
    q[0]=0x38u;
    k[7][0]=0x50u; // 8.0, stronger key 7 logit
    out=attention(q,k,v,bias);
    for(auto x:out)assert(dequant(x)>0.0f && dequant(x)<=2.0f);
}
