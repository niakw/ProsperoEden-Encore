// SPDX-License-Identifier: MIT
#include <array>
#include <cassert>
#include <cstdint>
#include <vector>
#include "rdna2_nr_fswin_chain_layout_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;

int main(){
    const std::array<FSwinWindowLayout,3> legacy{};
    assert(CanFSwinChainWindowLayouts(legacy,16u));
    assert(!FSwinNeedsWindowRepack(legacy[0],legacy[1]));
    assert(!CanFSwinChainWindowLayouts(legacy,0u));
    assert(!CanFSwinChainWindowLayouts(legacy,257u));
    const std::array<FSwinWindowLayout,4> alternating{{
        {4,4,0,0},{4,4,1,1},{4,4,0,0},{4,4,-1,1},
    }};
    assert(CanFSwinChainWindowLayouts(alternating,16u));
    assert(FSwinNeedsWindowRepack(alternating[0],alternating[1]));
    assert(FSwinNeedsWindowRepack(alternating[1],alternating[2]));
    assert(!FSwinNeedsWindowRepack(alternating[0],alternating[2]));
    assert(CanFSwinChainWindowLayouts(
        std::array<FSwinWindowLayout,1>{{{1,1,1,0}}},1u));
    assert(CanFSwinChainWindowLayouts(
        std::array<FSwinWindowLayout,1>{{{16,16,-1,1}}},256u));
    auto bad=alternating;
    bad[2].windows_y=5u;
    assert(!CanFSwinChainWindowLayouts(bad,16u));
    bad=alternating;bad[0].windows_x=0u;
    assert(!CanFSwinChainWindowLayouts(bad,16u));
    bad=alternating;bad[0].windows_x=0u;bad[0].windows_y=0u;
    assert(!CanFSwinChainWindowLayouts(bad,16u));
    bad=alternating;bad[1].shift_x=2;
    assert(!CanFSwinChainWindowLayouts(bad,16u));
    bad=alternating;bad[1].shift_y=-2;
    assert(!CanFSwinChainWindowLayouts(bad,16u));
    const std::array<FSwinWindowLayout,2> mixed{{
        {0,0,0,0},{4,4,0,0},
    }};
    assert(!CanFSwinChainWindowLayouts(mixed,16u));
    const std::array<FSwinWindowLayout,2> no_grid_shift{{
        {0,0,0,0},{0,0,1,0},
    }};
    assert(!CanFSwinChainWindowLayouts(no_grid_shift,16u));
    const std::vector<FSwinWindowLayout> too_many(161);
    assert(!CanFSwinChainWindowLayouts(too_many,1u));
}
