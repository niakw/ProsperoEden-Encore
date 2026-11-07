// SPDX-License-Identifier: MIT
#include "rdna2_nr_proxy_lift_link_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr NeuralProxyFeatures native{
        1920u,1080u,1920u,1080u,1920u,1080u,42u,
        0.0f,0.0f,0.0f,0.0f,0.0f};
    static_assert(CanNeuralProxyLiftLink(
        native,{1920u,1080u,0u}));
    assert(!CanNeuralProxyLiftLink(native,{1920u,1080u,1u}));
    assert(!CanNeuralProxyLiftLink(native,{1080u,1920u,0u}));
    assert(!CanNeuralProxyLiftLink(native,{1919u,1080u,0u}));
    auto bad=native;bad.valid_height=0u;
    assert(!CanNeuralProxyLiftLink(bad,{1920u,1080u,0u}));
    bad=native;bad.source_width=0u;
    assert(!CanNeuralProxyLiftLink(bad,{1920u,1080u,0u}));
    bad=native;bad.style=129.0f;
    assert(!CanNeuralProxyLiftLink(bad,{1920u,1080u,0u}));
    bad=native;bad.full_height=1152u;
    assert(CanNeuralProxyLiftLink(bad,{1920u,1152u,0u}));
    bad=native;bad.full_width=4096u;
    assert(!CanNeuralProxyLiftLink(bad,{4096u,1080u,0u}));
}
