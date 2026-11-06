// SPDX-License-Identifier: MIT
// Compile and run with assertions even if caller passes -DNDEBUG.
#include <cassert>
#include <cstdint>
#include <cstring>
#include <vector>
#include <cmath>
#include <limits>
#include "rdna2_nr_projection_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;

static float e4m3(uint8_t bits) {
    auto exponent = (bits >> 3u) & 15u;
    auto fraction = bits & 7u;
    const float sign = bits & 128 ? -1.f : 1.f;
    if (exponent == 15 && fraction == 7) return std::numeric_limits<float>::quiet_NaN();
    if (exponent == 0) return sign * fraction * std::ldexp(1.f, -9);
    return sign * (8 + fraction) * std::ldexp(1.f, int(exponent) - 10);
}
// CPU reference to check the two independently packed E4M3 streams;
// this is NOT a performance or visual-quality proof on PS5.
static float project(const std::vector<uint8_t>& a,
                     const std::vector<uint8_t>& w,
                     const Projection& p, uint32_t m, uint32_t n) {
    float sum=0.f;
    for (uint32_t i=0; i<p.inner; ++i)
        sum=std::fma(e4m3(a[p.a_base_bytes+m*p.lda_bytes+i]),
                     e4m3(w[p.w_base_bytes+n*p.ldw_bytes+i]), sum);
    return sum;
}
int main() {
    Projection p{3,5,17,20,19,1,2};
    std::vector<uint8_t> a(64,0),w(104,0);
    for (uint32_t m=0; m<p.tokens; ++m) for (uint32_t k=0;k<p.inner;++k)
        a[p.a_base_bytes+m*p.lda_bytes+k]=((m+k)%2)?0x38:0xB8;
    for (uint32_t n=0; n<p.channels; ++n) for (uint32_t k=0;k<p.inner;++k)
        w[p.w_base_bytes+n*p.ldw_bytes+k]=(n%2)?0x40:0x38;
    Storage s{a.size(),w.size(),4096,4096};
    assert(CanDispatch(p,s));
    assert(project(a,w,p,0,0)==-1.f);
    assert(project(a,w,p,0,1)==-2.f);
    assert(project(a,w,p,0,2)==-1.f);
    assert(project(a,w,p,1,0)==1.f);
    assert(e4m3(0x00)==0.f);
    assert(e4m3(0x01)==std::ldexp(1.f,-9));
    assert(e4m3(0x7e)==448.f);
    assert(e4m3(0xfe)==-448.f);
    assert(std::isnan(e4m3(0x7f)));
    assert(std::isnan(e4m3(0xff)));
    assert(!CanDispatch(p,{59,w.size(),4096,4096}));
    assert(!CanDispatch(p,{a.size(),95,4096,4096}));
    assert(!CanDispatch(p,{a.size(),w.size(),4096,59}));
    auto invalid=p;
    invalid.lda_bytes=16;
    assert(!CanDispatch(invalid,s));
    invalid=p;invalid.tokens=0;
    assert(!CanDispatch(invalid,s));
    invalid=p;invalid.tokens=UINT32_MAX;invalid.channels=UINT32_MAX;
    assert(!CanDispatch(invalid,s));
    invalid=p;invalid.inner=8193;invalid.lda_bytes=8193;invalid.ldw_bytes=8193;
    assert(!CanDispatch(invalid,s));
    // Covers 32-bit byte-address overflow even if host claims >4GiB memory.
    invalid=p;invalid.tokens=100000u;invalid.lda_bytes=65535u;
    Storage giant{1ull<<33,1ull<<33,1ull<<33,1ull<<33};
    assert(!CanDispatch(invalid,giant));
    return 0;
}
