// SPDX-License-Identifier: MIT
#include "rdna2_nr_vit_boundary_repack_policy.h"
#include <cassert>
using namespace Eden::Graphics::NeuralRDNA2;
int main() {
    constexpr VitBoundaryRepack to_vit{60,33,1024,2560,0,0,0};
    constexpr VitBoundaryRepack to_tiles{60,33,1024,2560,1,0,0};
    static_assert(sizeof(VitBoundaryRepack)==7u*sizeof(std::uint32_t));
    static_assert(VitTiledTokenCount(to_vit)==2160);
    static_assert(VitBoundaryGrid(to_vit)==2560);
    static_assert(VitBoundaryGrid(to_tiles)==2160);
    static_assert(CanVitBoundaryRepack(to_vit,{2160ull*1024,2560ull*1024}));
    static_assert(CanVitBoundaryRepack(to_tiles,{2560ull*1024,2160ull*1024}));
    static_assert(!CanVitBoundaryRepack(to_vit,{2160ull*1024-1,2560ull*1024}));
    static_assert(!CanVitBoundaryRepack(to_tiles,{2560ull*1024,2160ull*1024-1}));
    static_assert(!CanVitBoundaryRepack({0,33,1024,2560,0,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({60,33,256,2560,0,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({60,33,1024,2560,2,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({60,33,1024,2560,0,1,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({60,33,1024,1900,0,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({4096,4096,1024,4096,0,0,0},{1ull<<32,1ull<<32}));
}
