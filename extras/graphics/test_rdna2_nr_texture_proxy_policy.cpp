// SPDX-License-Identifier: MIT
#include "rdna2_nr_texture_proxy_policy.h"
#include <cassert>
#include <cstdint>
#include <limits>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr NRTextureProxyShape p{1080u,1920u,1.0f,0u};
    constexpr std::uint64_t bytes=1080ull*1920ull*16u;
    assert(CanNRTextureProxy(p,{1920u,1080u},bytes));
    assert(!CanNRTextureProxy(p,{1080u,1920u},bytes));
    assert(!CanNRTextureProxy(p,{1920u,1080u},bytes-1u));
    assert(!CanNRTextureProxy(p,{1920u,1080u},257ull<<20));
    assert(NRTextureProxyIndex(p,0u,0u)==0u);
    assert(NRTextureProxyIndex(p,1u,0u)==1u);
    assert(NRTextureProxyIndex(p,0u,1u)==1080u);
    assert(NRTextureProxyIndex(p,1079u,1919u)==1080ull*1920ull-1u);
    auto bad=p;bad.raster_width=0u;
    assert(!CanNRTextureProxy(bad,{1920u,1080u},bytes));
    bad=p;bad.raster_height=0u;
    assert(!CanNRTextureProxy(bad,{1920u,1080u},bytes));
    bad=p;bad.color_mode=2u;
    assert(!CanNRTextureProxy(bad,{1920u,1080u},bytes));
    bad=p;bad.paper_white=0.0f;
    assert(!CanNRTextureProxy(bad,{1920u,1080u},bytes));
    bad=p;bad.paper_white=std::numeric_limits<float>::infinity();
    assert(!CanNRTextureProxy(bad,{1920u,1080u},bytes));
    bad=p;bad.color_mode=1u;
    assert(CanNRTextureProxy(bad,{1920u,1080u},bytes));
}
