// SPDX-License-Identifier: MIT
// Eden Encore R09 — independent host safety contract for the RDNA2
// FP8→FP32 Vulkan GEMM building block, not a DLSS feature.
#pragma once
#include <cstdint>
#include <limits>

namespace Eden::Graphics::NeuralRDNA2 {
struct Projection {
    std::uint32_t tokens, channels, inner;
    std::uint32_t lda_bytes, ldw_bytes;
    std::uint32_t a_base_bytes, w_base_bytes;
};
struct Storage {
    std::uint64_t activation_bytes, weight_bytes, output_bytes;
    std::uint64_t free_transient_bytes;
};
constexpr std::uint32_t kLocal = 16;
constexpr std::uint64_t kMaxTemp = 256ull << 20;
constexpr std::uint64_t kMaxProducts = 8ull * 1024ull * 1024ull * 1024ull;

[[nodiscard]] constexpr bool CanDispatch(const Projection& p, const Storage& s) {
    if (!p.tokens || !p.channels || !p.inner || !p.lda_bytes || !p.ldw_bytes) return false;
    // Canonical 1x1 projections are far below this bound. Without it,
    // (K+15) in the uint32 shader dispatch can overflow.
    if (p.inner > 8192u) return false;
    if (p.lda_bytes < p.inner || p.ldw_bytes < p.inner) return false;
    // Plain Vulkan 1.1 tiled 16x16, no cooperative matrices or FP8 extension.
    const auto t = std::uint64_t(p.tokens), n = std::uint64_t(p.channels);
    const auto k = std::uint64_t(p.inner);
    if (t * n > kMaxProducts / k) return false;
    const auto a_end = std::uint64_t(p.a_base_bytes) + (t - 1) * p.lda_bytes + k;
    const auto w_end = std::uint64_t(p.w_base_bytes) + (n - 1) * p.ldw_bytes + k;
    // Shader byte addressing is 32-bit; refuse arithmetic wrap, even if
    // an oversize host allocation nominally covers the memory.
    if (a_end > std::numeric_limits<std::uint32_t>::max() ||
        w_end > std::numeric_limits<std::uint32_t>::max()) return false;
    // Every source is uint32 packed. The caller must allocate enough
    // storage for the last partial word accessed by the shader.
    const auto a_rounded = (a_end + 3ull) & ~3ull;
    const auto w_rounded = (w_end + 3ull) & ~3ull;
    if (a_rounded > s.activation_bytes || w_rounded > s.weight_bytes) return false;
    const std::uint64_t output_size = t * n * sizeof(float);
    if (output_size > s.output_bytes || output_size > s.free_transient_bytes ||
        output_size > kMaxTemp) return false;
    // GPU dispatch limits are renderer-owned. No dispatch issued here.
    return (n + kLocal - 1u) / kLocal <= 65535u &&
           (t + kLocal - 1u) / kLocal <= 65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
