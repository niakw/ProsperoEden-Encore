// SPDX-License-Identifier: MIT
// Deterministic PCG/Box-Muller reference and bounds cases for noise-field.
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>
#include "rdna2_nr_noise_field_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
static uint32_t pcg(uint32_t v){
    v=(v>>((v>>28u)+4u))^v;
    return v*0x108EF2D9u;
}
static float uni(uint32_t v){
    auto t=pcg(v);
    return float(((t>>30u)^(t>>8u))+1u)*5.9604644775390625e-08f;
}
static void sample(uint32_t x,uint32_t y,uint32_t seed,float gain,float* out) {
    uint32_t base=(x*0x8DA6B343u)^(seed*0x9E3779B9u)^
                  (y*0xD8163841u)^0x243F6A88u;
    auto t=pcg(base),h=(t>>22u)^t;
    float a=uni(h*0x2C9277B5u+0xAC564B05u);
    float b=uni(h*0xFA6DC5F9u+0x4712A88Eu);
    float c=uni(h*0xCAA5B80Du+0x21DD796Bu);
    float d=uni(h*0x83232C31u+0x3463E0ACu);
    float r0=std::sqrt(-2.f*std::log(a)),r1=std::sqrt(-2.f*std::log(c));
    out[0]=gain*r0*std::cos(b*6.28318530718f);
    out[1]=gain*r0*std::sin(b*6.28318530718f);
    out[2]=gain*r1*std::cos(d*6.28318530718f);
}
int main() {
    NoiseField p{0,8,8,42,0.5f};
    assert(CanNoiseField(p,512));
    assert(!CanNoiseField(p,511));
    p.base_words=8; assert(!CanNoiseField(p,512));
    assert(CanNoiseField(p,544));
    p.base_words=UINT32_MAX-1u;assert(!CanNoiseField(p,UINT64_MAX));
    p={0,8,8,42,0.5f};
    p.width=9;assert(!CanNoiseField(p,UINT64_MAX));
    p={0,8,8,42,0.5f};
    p.height=0;assert(!CanNoiseField(p,UINT64_MAX));
    p={0,8,8,42,std::numeric_limits<float>::quiet_NaN()};
    assert(!CanNoiseField(p,UINT64_MAX));
    p.gain=std::numeric_limits<float>::infinity();
    assert(!CanNoiseField(p,UINT64_MAX));
    p={0,32768,32768,42,1.f};
    assert(!CanNoiseField(p,UINT64_MAX)); // transient memory cap
    float a[3],b[3],c[3];
    sample(0,0,42,0.5f,a);sample(0,0,42,0.5f,b);
    sample(0,0,43,0.5f,c);
    for(int i=0;i<3;i++) {
        assert(std::isfinite(a[i]) && a[i]==b[i]);
    }
    assert(a[0]!=c[0] || a[1]!=c[1] || a[2]!=c[2]);
    sample(7,7,42,0.f,b);
    for(float v:b)assert(v==0.f);
}
