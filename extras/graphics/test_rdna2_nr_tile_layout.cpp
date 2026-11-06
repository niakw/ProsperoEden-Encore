// SPDX-License-Identifier: MIT
// RDNA2 import/export of MIT 16x16 E4M3FN tiled model matrices.
#include <cassert>
#include <cstdint>
#include <span>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_tile_layout.h"
using namespace Eden::Graphics::NeuralRDNA2;

static void check_shape(std::uint32_t rows,std::uint32_t columns){
    const std::size_t size=std::size_t(rows)*columns;
    std::vector<std::uint8_t> linear(size),tiled(size),restored(size);
    for(std::size_t i=0;i<size;++i)
        linear[i]=std::uint8_t(((i*53u)+(i>>8u)*79u+(i>>3u))&0xffu);
    assert(RowMajorToNeuralTiles(linear,tiled,rows,columns)==NeuralTileResult::Ok);
    assert(NeuralTilesToRowMajor(tiled,restored,rows,columns)==NeuralTileResult::Ok);
    assert(restored==linear);
    // Every destination element must originate from its exact row,col.
    for(std::uint32_t r=0;r<rows;r+=16u)
        for(std::uint32_t c=0;c<columns;c+=16u){
            const auto ix=Tile16Index(r,c,columns);
            assert(ix< size);
            assert(tiled[ix]==linear[RowMajorIndex(r,c,columns)]);
            const auto ix2=Tile16Index(r+15u,c+15u,columns);
            assert(tiled[ix2]==linear[RowMajorIndex(r+15u,c+15u,columns)]);
        }
}
int main(){
    static_assert(ValidNeuralTileShape(16,16));
    static_assert(Tile16Index(0,0,16)==0);
    static_assert(Tile16Index(15,15,16)==255);
    static_assert(Tile16Index(0,16,32)==256);
    static_assert(Tile16Index(16,0,32)==512);
    static_assert(!ValidNeuralTileShape(15,16));
    static_assert(!ValidNeuralTileShape(16,15));
    static_assert(!ValidNeuralTileShape(0,16));
    static_assert(!ValidNeuralTileShape(65536u,65536u));

    check_shape(16,16);
    check_shape(16,32);
    check_shape(32,16);
    check_shape(32,32);
    // QKV: [16 heads*96 output features,512 inputs].
    check_shape(1536,512);
    // FFWD3 W1/W2/W3: eight groups laid out contiguously.
    check_shape(512,512);
    check_shape(2048,64);
    check_shape(512,256);
    // ViT/global attention uses tiles of 16 token by 16 channels.
    check_shape(64,1024);

    std::vector<std::uint8_t> a(256),b(256);
    assert(NeuralTilesToRowMajor(a,b,0,16)==NeuralTileResult::InvalidShape);
    assert(NeuralTilesToRowMajor(a,b,16,12)==NeuralTileResult::InvalidShape);
    assert(NeuralTilesToRowMajor(
        std::span<const std::uint8_t>(a.data(),255),b,16,16)==
        NeuralTileResult::InsufficientInput);
    assert(NeuralTilesToRowMajor(
        a,std::span<std::uint8_t>(b.data(),255),16,16)==
        NeuralTileResult::InsufficientOutput);
    assert(NeuralTilesToRowMajor(a,a,16,16)==NeuralTileResult::Aliasing);
    std::vector<std::uint8_t> overlap(260u);
    assert(NeuralTilesToRowMajor(
        std::span<const std::uint8_t>(overlap.data(),256),
        std::span<std::uint8_t>(overlap.data()+4u,256),16,16)==
        NeuralTileResult::Aliasing);
    // Destination must not be touched when inputs fail validation.
    b.assign(256,0x5au);
    assert(NeuralTilesToRowMajor(
        std::span<const std::uint8_t>(a.data(),255),b,16,16)==
        NeuralTileResult::InsufficientInput);
    for(auto x:b)assert(x==0x5au);
}
