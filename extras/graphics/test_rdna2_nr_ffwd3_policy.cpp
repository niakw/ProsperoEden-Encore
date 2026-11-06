// SPDX-License-Identifier: MIT
// Scalar grouped-FFWD3 reference: 8 groups, 3 quantized dense stages.
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>
#include "rdna2_nr_ffwd3_policy.h"
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
    if(a<0.015625f){
        auto m=static_cast<unsigned>(std::nearbyint(a*512.f));
        return sign|(m>=8u?8u:m);
    }
    int e=static_cast<int>(std::floor(std::log2(a)));
    auto m=static_cast<unsigned>(std::nearbyint((a/std::exp2(float(e))-1.f)*8.f));
    if(m==8u){++e;m=0u;}
    auto ex=static_cast<unsigned>(e+7);
    if(ex>15u||(ex==15u&&m>6u))return sign|126u;
    return sign|(ex<<3u)|m;
}
static float cubic(float x){
    float t=std::fmax(-4.f,std::fmin(x,4.f));
    float u=std::fma(-0.055908203125f,std::fabs(t),0.447265625f);
    return x*std::fma(t,u,0.89453125f);
}
static std::vector<uint8_t> reference(
    const std::vector<uint8_t>& x,
    const std::vector<uint8_t>& w1,
    const std::vector<uint8_t>& w2,
    const std::vector<uint8_t>& w3) {
    assert(x.size()==512u);
    std::vector<uint8_t> out(512,0u);
    for(unsigned group=0;group<8;group++){
        std::vector<uint8_t> a(64,0u),b(256,0u);
        for(unsigned c=0;c<64;c++){
            float sum=0.f;
            for(unsigned k=0;k<512;k++)
                sum=std::fma(decode(x[k]),decode(w1[(group*64+c)*512+k]),sum);
            a[c]=static_cast<uint8_t>(quant(sum));
        }
        for(unsigned c=0;c<256;c++){
            float sum=0.f;
            for(unsigned k=0;k<64;k++)
                sum=std::fma(decode(a[k]),decode(w2[(group*256+c)*64+k]),sum);
            b[c]=static_cast<uint8_t>(quant(cubic(sum)));
        }
        for(unsigned c=0;c<64;c++){
            float sum=0.f;
            for(unsigned k=0;k<256;k++)
                sum=std::fma(decode(b[k]),decode(w3[(group*64+c)*256+k]),sum);
            out[group*64+c]=static_cast<uint8_t>(quant(sum));
        }
    }
    return out;
}
int main(){
    FFWD3 p{0,0,0,0,0,1};
    FFWD3Storage s{512,262144,131072,131072,512};
    assert(CanFFWD3(p,s));
    assert(!CanFFWD3(p,{511,262144,131072,131072,512}));
    assert(!CanFFWD3(p,{512,262143,131072,131072,512}));
    assert(!CanFFWD3(p,{512,262144,131071,131072,512}));
    assert(!CanFFWD3(p,{512,262144,131072,131071,512}));
    assert(!CanFFWD3(p,{512,262144,131072,131072,511}));
    p.tokens=0;assert(!CanFFWD3(p,s));
    p.tokens=65536;assert(!CanFFWD3(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={1,0,0,0,0,1};assert(!CanFFWD3(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));
    p={0,UINT32_MAX-3u,0,0,0,1};
    assert(!CanFFWD3(p,{UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}));

    std::vector<uint8_t> x(512,0),w1(262144,0),w2(131072,0),w3(131072,0);
    x[0]=0x38u;
    w1[0]=0x38u; // group 0 stage 1 output 0 receives +1
    w2[0]=0x38u; // group 0 stage 2 output 0 receives +1
    w3[0]=0x38u; // group 0 stage 3 output 0 receives +1
    auto out=reference(x,w1,w2,w3);
    assert(out.size()==512u);
    assert(out[0]==quant(cubic(1.f)));
    assert(out[0]==0x3au); // cubic-SiLU-like(1) -> nearest E4M3 1.25
    for(unsigned i=1;i<512;i++)assert(out[i]==0u);
    x[0]=0u;
    out=reference(x,w1,w2,w3);
    for(auto v:out)assert(v==0u);
    assert(quant(448.f)==0x7eu);
    assert(quant(-2.f)==0xc0u);
}
