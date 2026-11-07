// SPDX-License-Identifier: MIT
#include "rdna2_nr_hdr_proxy_policy.h"
#include <cassert>
#include <cmath>
#include <limits>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr std::uint64_t pixels=1080ull*1920ull;
    const NRHDRProxyShape s{1080u,1920u,1.0f,0u};
    const std::array<std::uint64_t,2> full{pixels*16u,pixels*16u};
    assert(CanNRHDRProxy(s,full));
    auto bad=s;bad.width=0u;assert(!CanNRHDRProxy(bad,full));
    bad=s;bad.height=0u;assert(!CanNRHDRProxy(bad,full));
    bad=s;bad.paper_white=0.01f;assert(!CanNRHDRProxy(bad,full));
    bad=s;bad.paper_white=std::numeric_limits<float>::infinity();
    assert(!CanNRHDRProxy(bad,full));
    bad=s;bad.reserved=1u;assert(!CanNRHDRProxy(bad,full));
    auto caps=full;caps[0]--;assert(!CanNRHDRProxy(s,caps));
    caps=full;caps[1]--;assert(!CanNRHDRProxy(s,caps));
    caps=full;caps[1]=257ull*1024u*1024u;
    assert(!CanNRHDRProxy(s,caps));
    assert(HDRProxyReference(0.0f,1.0f)==0.0f);
    assert(HDRProxyReference(-7.0f,1.0f)==0.0f);
    assert(HDRProxyReference(
        std::numeric_limits<float>::quiet_NaN(),1.0f)==0.0f);
    const float half=HDRProxyReference(0.5f,1.0f);
    assert(half>0.7f&&half<0.8f);
    const float bright=HDRProxyReference(1.0f,1.0f);
    assert(std::isfinite(bright)&&bright>0.8f&&bright<1.0f);
    assert(std::fabs(HDRProxyReference(100000.0f,1.0f)-1.0f)<1e-6f);
}
