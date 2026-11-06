// SPDX-License-Identifier: MIT
// Bijective reference: canonical [512,512] -> original FFWD3 bit maps.
#include "video_core/renderer_vulkan/nr_rdna2_split_ffwd_weight_loader.h"
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static std::vector<std::uint8_t> CanonicalFromFragment(
    const std::vector<std::uint8_t>& raw) {
    std::vector<std::uint8_t> matrix(kSplitFFMatrix);
    for(std::size_t kg=0u;kg<16u;++kg)
      for(std::size_t ng=0u;ng<32u;++ng)
        for(std::size_t half=0u;half<2u;++half)
          for(std::size_t lane=0u;lane<32u;++lane)
            for(std::size_t byte=0u;byte<8u;++byte){
                const auto n=ng*16u+half*8u+lane/4u;
                const auto k=kg*32u+8u*(byte/2u)+
                             2u*(lane%4u)+(byte%2u);
                const auto src=(kg*32u+ng)*512u+
                                lane*16u+half*8u+byte;
                matrix[n*512u+k]=raw[src];
            }
    return matrix;
}
int main() {
    std::vector<std::uint8_t> original_a(kSplitFFMatrix);
    std::vector<std::uint8_t> original_b(kSplitFFMatrix);
    // All values are finite E4M3FN, distinct enough to expose permutations.
    for(std::size_t i=0u;i<kSplitFFMatrix;++i){
        original_a[i]=static_cast<std::uint8_t>(1u+(i*37u)%120u);
        original_b[i]=static_cast<std::uint8_t>(1u+(i*47u)%120u);
    }
    auto can_a=CanonicalFromFragment(original_a);
    auto can_b=CanonicalFromFragment(original_b);
    std::vector<std::uint8_t> roundtrip;
    assert(SplitFFCanonicalToFragment(can_a,roundtrip));
    assert(roundtrip==original_a);
    assert(SplitFFCanonicalToFragment(can_b,roundtrip));
    assert(roundtrip==original_b);
    assert(!SplitFFCanonicalToFragment(
        std::span<const std::uint8_t>{can_a.data(),can_a.size()-1u},
        roundtrip));
    assert(roundtrip.empty());

    SplitFFWDWeights decoded;
    assert(DecodeSplitFFWDWeights(can_a,can_b,decoded));
    assert(decoded.w1.size()==262144u);
    assert(decoded.w2.size()==131072u);
    assert(decoded.w3.size()==131072u);
    for(std::uint32_t g=0u;g<8u;++g) {
        for(std::uint32_t r=0u;r<64u;++r)
            for(std::uint32_t k=0u;k<512u;++k)
                assert(decoded.w1[(g*64u+r)*512u+k]==
                       original_a[SplitFFSourceA(g,r,k)]);
        for(std::uint32_t j=0u;j<256u;++j)
            for(std::uint32_t r=0u;r<64u;++r)
                assert(decoded.w2[(g*256u+j)*64u+r]==
                       original_b[SplitFFSourceQ0(g,j,r)]);
        for(std::uint32_t n=0u;n<64u;++n)
            for(std::uint32_t j=0u;j<256u;++j)
                assert(decoded.w3[(g*64u+n)*256u+j]==
                       original_b[SplitFFSourceQ2(g,n,j)]);
    }
    // Fail atomically on size mismatch or nonfinite FP8 values.
    assert(!DecodeSplitFFWDWeights(
        std::span<const std::uint8_t>{can_a.data(),can_a.size()-1u},
        can_b,decoded));
    assert(decoded.w1.empty()&&decoded.w2.empty()&&decoded.w3.empty());
    can_a[100u]=0x7fu;
    assert(!DecodeSplitFFWDWeights(can_a,can_b,decoded));
    assert(decoded.w1.empty()&&decoded.w2.empty()&&decoded.w3.empty());
    can_a[100u]=0x38u;
    can_b[101u]=0xffu;
    assert(!DecodeSplitFFWDWeights(can_a,can_b,decoded));
    assert(decoded.w1.empty()&&decoded.w2.empty()&&decoded.w3.empty());
}
