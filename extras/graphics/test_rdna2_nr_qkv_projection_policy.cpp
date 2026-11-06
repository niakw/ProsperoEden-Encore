// SPDX-License-Identifier: MIT
// RDNA2 triple projection host contract and Q/K/V numerical reference.
#include <cassert>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>
#include "rdna2_nr_qkv_projection_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;

static float fp8_decode(unsigned raw) {
    unsigned e=(raw>>3u)&15u,m=raw&7u;
    float sign=(raw&128u)?-1.f:1.f;
    if(e==15u&&m==7u)return std::numeric_limits<float>::quiet_NaN();
    if(e==0u)return sign*float(m)*std::exp2(-9.f);
    return sign*float(8u+m)*std::exp2(float(int(e)-10));
}
static unsigned fp8_quant(float v) {
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
static std::array<std::array<unsigned,32>,3> project(
    const std::array<uint8_t,512>& activation,
    const std::vector<uint8_t>& w, float scale) {
    std::array<std::array<float,32>,3> stages{};
    for(unsigned part=0;part<3;part++)
        for(unsigned c=0;c<32;c++)
            for(unsigned k=0;k<512;k++)
                stages[part][c]=std::fma(fp8_decode(activation[k]),
                    fp8_decode(w[((part*32+c)*512)+k]),stages[part][c]);
    float qnorm=0.f,knorm=0.f;
    for(unsigned c=0;c<32;c++){
        qnorm=std::fma(stages[0][c],stages[0][c],qnorm);
        knorm=std::fma(stages[1][c],stages[1][c],knorm);
    }
    qnorm=std::sqrt(qnorm);knorm=std::sqrt(knorm);
    std::array<std::array<unsigned,32>,3> out{};
    for(unsigned c=0;c<32;c++){
        out[0][c]=fp8_quant(scale*(qnorm>0.f?stages[0][c]/qnorm:0.f));
        out[1][c]=fp8_quant(knorm>0.f?stages[1][c]/knorm:0.f);
        out[2][c]=fp8_quant(stages[2][c]);
    }
    return out;
}
int main(){
    QkvProjection p{0,0,0,0,0,0,1,1};
    QkvStorage s{32768,49152,4,2048,2048,2048};
    assert(CanQkvProjection(p,s));
    assert(!CanQkvProjection(p,{32767,49152,4,2048,2048,2048}));
    assert(!CanQkvProjection(p,{32768,49151,4,2048,2048,2048}));
    assert(!CanQkvProjection(p,{32768,49152,3,2048,2048,2048}));
    assert(!CanQkvProjection(p,{32768,49152,4,2047,2048,2048}));
    assert(!CanQkvProjection(p,{32768,49152,4,2048,2047,2048}));
    assert(!CanQkvProjection(p,{32768,49152,4,2048,2048,2047}));
    p.heads=3;assert(!CanQkvProjection(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,0,1,1};p.windows=65536;
    assert(!CanQkvProjection(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,0,1,1};p.a_base_bytes=1;
    assert(!CanQkvProjection(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,0,1,1};p.q_base_bytes=UINT32_MAX-3u;
    assert(!CanQkvProjection(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,0,1,1};p.scale_base_floats=UINT32_MAX;
    assert(!CanQkvProjection(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,0,0,0,0,0,8193,16};
    assert(!CanQkvProjection(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));

    std::array<uint8_t,512> x{};x[0]=0x38; // +1
    std::vector<uint8_t> w(3u*32u*512u,0u);
    w[(0*32+0)*512]=0x38; // Q[0]=+1
    w[(1*32+0)*512]=0x40; // K[0]=+2
    w[(2*32+0)*512]=0x48; // V[0]=+4
    auto out=project(x,w,2.f);
    assert(out[0][0]==0x40u);
    assert(out[1][0]==0x38u);
    assert(out[2][0]==0x48u);
    for(unsigned part=0;part<3;part++)
        for(unsigned c=1;c<32;c++)assert(out[part][c]==0u);
    // Zero vector uses zero Q/K rather than division by zero or NaN.
    x.fill(0u);out=project(x,w,2.f);
    for(auto& vec:out)for(auto z:vec)assert(z==0u);
    assert(fp8_quant(448.f)==0x7eu);
    assert(fp8_quant(-2.f)==0xc0u);
    assert(fp8_decode(0x38u)==1.f);
}
