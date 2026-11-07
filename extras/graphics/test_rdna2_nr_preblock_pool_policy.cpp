// SPDX-License-Identifier: MIT
#include "rdna2_nr_preblock_pool_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main(){
    // Native 1920x1080 has a physically transposed 1080x1920 raster.
    constexpr PreblockPoolShape full{1080u,1920u};
    constexpr std::uint64_t raw=1080ull*1920u*64u;
    constexpr std::uint64_t pooled=540ull*960u*32u;
    static_assert(CanPreblockPool(full,{raw,pooled}));
    static_assert(!CanPreblockPool(full,{raw-1u,pooled}));
    static_assert(!CanPreblockPool(full,{raw,pooled-1u}));
    static_assert(!CanPreblockPool({1079u,1920u},{raw,pooled}));
    static_assert(!CanPreblockPool({1080u,1919u},{raw,pooled}));
    static_assert(!CanPreblockPool({0u,1920u},{raw,pooled}));
    // The packed FP8 preblock skip cannot be used as raw FP16 input.
    assert(!CanPreblockPool(full,{1080ull*1920u*32u,pooled}));
    // Deliberately refuses unbounded full-resolution buffers.
    assert(!CanPreblockPool({8192u,8192u},
                            {8192ull*8192u*64u,8192ull*8192u*8u}));
}
