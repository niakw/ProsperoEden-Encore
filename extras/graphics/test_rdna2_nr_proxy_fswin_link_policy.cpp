// SPDX-License-Identifier: MIT
#include "rdna2_nr_proxy_fswin_link_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr NeuralProxyFeatures original{
        1920u,1080u,1920u,1080u,1920u,1080u,42u,
        0.0f,0.0f,0.0f,0.0f,0.0f};
    constexpr std::uint64_t raster=1920ull*1080u*32u;
    constexpr std::uint64_t windows=240ull*135u*64u*32u;
    constexpr FSwinRasterLayoutStorage sizes{raster,windows};
    static_assert(CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,135u,0,0},32u,sizes));
    static_assert(CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,135u,-1,1},32u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,135u,0,0},64u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,1u},{240u,135u,0,0},32u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1080u,1920u,0u},{240u,135u,0,0},32u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{135u,240u,0,0},32u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,134u,0,0},32u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,135u,2,0},32u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,135u,0,-2},32u,sizes));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,135u,0,0},32u,
        {raster-1u,windows}));
    assert(!CanNeuralProxyFSwinLink(
        original,{1920u,1080u,0u},{240u,135u,0,0},32u,
        {raster,windows-1u}));
    auto padded=original;
    padded.full_height=1152u;
    assert(CanNeuralProxyFSwinLink(
        padded,{1920u,1152u,0u},{240u,144u,0,0},32u,
        {1920ull*1152u*32u,240ull*144u*64u*32u}));
    assert(!CanNeuralProxyFSwinLink(
        padded,{1920u,1080u,0u},{240u,144u,0,0},32u,sizes));
    auto malformed=original;
    malformed.valid_width=0u;
    assert(!CanNeuralProxyFSwinLink(
        malformed,{1920u,1080u,0u},{240u,135u,0,0},32u,sizes));
}
