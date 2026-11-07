// SPDX-License-Identifier: MIT
// Learned NRMODEL1 image-boundary feature matrices. Intentionally accepts
// prepared 16-channel FP16 data, NOT raw RGB/depth/motion/textures.
#pragma once
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct ImageFeatureShape {
    std::uint32_t width{},height{},direction{};
};
struct ImageFeatureCapacity {
    std::uint64_t input_bytes{},weights_bytes{},output_bytes{};
};
[[nodiscard]] constexpr bool CanImageFeatureStage(
    const ImageFeatureShape& p,
    const ImageFeatureCapacity& buffers) noexcept {
    if(!p.width||!p.height||p.width>8192u||p.height>8192u||
       p.direction>1u)return false;
    constexpr std::uint64_t kLimit=256ull<<20;
    const auto pixels=std::uint64_t(p.width)*p.height;
    const auto bytes=pixels*32u;
    // 16 prepared FP16 inputs or 32 FP8 inputs, both exactly 32 B.
    // 32 FP8 outputs or 16 projected FP16 outputs, both exactly 32 B.
    return bytes>0u&&bytes<=kLimit&&
           buffers.input_bytes>=bytes&&
           buffers.output_bytes>=bytes&&
           buffers.weights_bytes>=1024u&&
           buffers.weights_bytes<=kLimit&&
           (std::uint64_t(p.width)+63u)/64u<=65535u&&
           p.height<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
