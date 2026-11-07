// SPDX-License-Identifier: MIT
#include "rdna2_nr_nohistory_compose_policy.h"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
using namespace Eden::Graphics::NeuralRDNA2;
int main() {
    constexpr std::uint64_t pix=1920ull*1080ull;
    constexpr std::array<std::uint64_t,3> bytes{
        pix*16u,pix*32u,pix*16u};
    const NRNoHistoryComposeShape shape{1080u,1920u,1.0f,0u};
    assert(CanNRNoHistoryCompose(shape,bytes));
    auto bad=shape;
    bad.width=0u;assert(!CanNRNoHistoryCompose(bad,bytes));
    bad=shape;bad.height=0u;assert(!CanNRNoHistoryCompose(bad,bytes));
    bad=shape;bad.intensity=-0.01f;assert(!CanNRNoHistoryCompose(bad,bytes));
    bad=shape;bad.intensity=1.01f;assert(!CanNRNoHistoryCompose(bad,bytes));
    bad=shape;bad.intensity=std::numeric_limits<float>::quiet_NaN();
    assert(!CanNRNoHistoryCompose(bad,bytes));
    bad=shape;bad.reserved=1u;assert(!CanNRNoHistoryCompose(bad,bytes));
    auto tiny=bytes;tiny[0]--;
    assert(!CanNRNoHistoryCompose(shape,tiny));
    tiny=bytes;tiny[1]--;
    assert(!CanNRNoHistoryCompose(shape,tiny));
    tiny=bytes;tiny[2]--;
    assert(!CanNRNoHistoryCompose(shape,tiny));
    tiny=bytes;tiny[2]=257ull*1024u*1024u;
    assert(!CanNRNoHistoryCompose(shape,tiny));
    auto rgb=NRNoHistoryComposeReference({0.5f,0.25f,1.0f,0.7f},
                                         {0.0f,0.0f,0.0f},1.0f);
    assert(rgb[0]==0.5f&&rgb[1]==0.25f&&rgb[2]==1.0f);
    assert(std::fabs(rgb[3]-0.7f)<1e-6f);
    rgb=NRNoHistoryComposeReference({0.5f,0.25f,0.75f,1.0f},
                                    {1.0f,-1.0f,2.0f},1.0f);
    assert(rgb[0]==0.75f&&rgb[1]==0.0f&&rgb[2]==1.0f);
    rgb=NRNoHistoryComposeReference({0.5f,0.25f,0.75f,1.0f},
                                    {1.0f,-1.0f,2.0f},0.5f);
    assert(rgb[0]==0.625f&&rgb[1]==0.125f&&rgb[2]==0.875f);
    rgb=NRNoHistoryComposeReference({0.5f,0.25f,0.75f,1.0f},
          {std::numeric_limits<float>::infinity(),0.0f,1.0f},1.0f);
    assert(rgb[0]==0.5f&&rgb[1]==0.25f&&rgb[2]==0.75f);
}
