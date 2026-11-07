// SPDX-License-Identifier: MIT
#include "rdna2_nr_vit_boundary_repack_policy.h"
#include <cassert>
using namespace Eden::Graphics::NeuralRDNA2;
int main() {
    constexpr VitBoundaryRepack to_vit{33,60,1024,2560,0,0,0};
    constexpr VitBoundaryRepack to_tiles{33,60,1024,2560,1,0,0};
    static_assert(sizeof(VitBoundaryRepack)==7u*sizeof(std::uint32_t));
    static_assert(VitTiledTokenCount(to_vit)==2160);
    // The 33-column raster uses 9 four-wide tiles per row. An
    // accidental 60x33 swap still occupies 2160 tokens but points
    // row 4 at tile #15 instead of tile #9.
    constexpr auto tile_index=[](std::uint32_t width,
                                 std::uint32_t x,std::uint32_t y){
        return ((y/4u)*((width+3u)/4u)+x/4u)*16u+
               (y%4u)*4u+x%4u;
    };
    static_assert(tile_index(to_vit.width,0u,4u)==144u);
    static_assert(tile_index(60u,0u,4u)==240u);
    static_assert(tile_index(to_vit.width,32u,59u)==2156u);
    static_assert(tile_index(to_vit.width,32u,59u)!=
                  tile_index(60u,32u,59u));
    static_assert(VitBoundaryGrid(to_vit)==2560);
    static_assert(VitBoundaryGrid(to_tiles)==2160);
    static_assert(CanVitBoundaryRepack(to_vit,{2160ull*1024,2560ull*1024}));
    static_assert(CanVitBoundaryRepack(to_tiles,{2560ull*1024,2160ull*1024}));
    static_assert(!CanVitBoundaryRepack(to_vit,{2160ull*1024-1,2560ull*1024}));
    static_assert(!CanVitBoundaryRepack(to_tiles,{2560ull*1024,2160ull*1024-1}));
    static_assert(!CanVitBoundaryRepack({0,60,1024,2560,0,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({33,60,256,2560,0,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({33,60,1024,2560,2,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({33,60,1024,2560,0,1,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({33,60,1024,1900,0,0,0},{1ull<<24,1ull<<24}));
    static_assert(!CanVitBoundaryRepack({4096,4096,1024,4096,0,0,0},{1ull<<32,1ull<<32}));
}
