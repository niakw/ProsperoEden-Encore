// SPDX-License-Identifier: MIT
#include "rdna2_nr_nohistory_present_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    constexpr NRNoHistoryPresentShape s{1080u,1920u,0u,0u};
    constexpr std::uint64_t n=1080ull*1920ull*16u;
    assert(CanNRNoHistoryPresent(s,n,{1920u,1080u}));
    assert(!CanNRNoHistoryPresent(s,n,{1080u,1920u}));
    assert(!CanNRNoHistoryPresent(s,n-1u,{1920u,1080u}));
    assert(!CanNRNoHistoryPresent(s,257ull<<20,{1920u,1080u}));
    assert(NativeRgbaSourceIndex(s,0u,0u)==0u);
    assert(NativeRgbaSourceIndex(s,1u,0u)==1080u);
    assert(NativeRgbaSourceIndex(s,1919u,1079u)==
           (1080ull*1920ull-1u));
    auto bad=s;bad.raster_width=0u;
    assert(!CanNRNoHistoryPresent(bad,n,{1920u,1080u}));
    bad=s;bad.raster_height=0u;
    assert(!CanNRNoHistoryPresent(bad,n,{1920u,1080u}));
    bad=s;bad.reserved0=1u;
    assert(!CanNRNoHistoryPresent(bad,n,{1920u,1080u}));
    bad=s;bad.reserved1=1u;
    assert(!CanNRNoHistoryPresent(bad,n,{1920u,1080u}));
}
