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
       p.direction>2u)return false;
    constexpr std::uint64_t kLimit=256ull<<20;
    const auto pixels=std::uint64_t(p.width)*p.height;
    const auto output_bytes=pixels*32u;
    // Stage 2 reads the pre-quantization FSwin result as FP16[32].
    // Stage 0/1 inputs are 32 bytes/pixel, stage 2 is 64 bytes/pixel.
    const auto input_bytes=pixels*(p.direction==2u?64u:32u);
    return input_bytes>0u&&input_bytes<=kLimit&&
           output_bytes<=kLimit&&
           buffers.input_bytes>=input_bytes&&
           buffers.output_bytes>=output_bytes&&
           buffers.weights_bytes>=1024u&&
           buffers.weights_bytes<=kLimit&&
           (std::uint64_t(p.width)+63u)/64u<=65535u&&
           p.height<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
