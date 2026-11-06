// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R24 — candidate policy for manually forced MSAA; NOT a renderer.
//
// Guest sample count is part of image memory layout and framebuffer identity.
// Forcing 2x/4x/8x/16x requires *additional native shadow attachments*
// and explicit resolves to the unchanged guest targets. Merely replacing
// rasterizationSamples or ImageInfo::num_samples would corrupt guest memory.
#include <cstdint>
#include <limits>

namespace Eden::Graphics::MsaaForce {

enum class Requested : std::uint8_t { Auto=0, X2=2, X4=4, X8=8, X16=16 };

enum class Decision : std::uint8_t {
    NativeAuto,
    NativeGuestSamplesAlreadySatisfy,
    GuestMultisampleTopologyConflict,
    UnsupportedRequest,
    RequiresVulkan,
    UnsupportedFrameFormat,
    UnsupportedDimensions,
    UnsupportedBudget,
    UnsupportedMultisampleRead,
    ShadowRendererNotImplemented,
    CandidateOnly, // candidate, NEVER proof of active MSAA
};

// Bit masks correspond to the Vulkan sample-count bits, without requiring
// Vulkan headers in unit tests: x1=0x1, x2=0x2, ... x16=0x10.
[[nodiscard]] constexpr std::uint32_t Bit(Requested requested) noexcept {
    switch (requested) {
    case Requested::X2: return 0x2;
    case Requested::X4: return 0x4;
    case Requested::X8: return 0x8;
    case Requested::X16: return 0x10;
    default: return 0;
    }
}
struct Limits {
    bool vulkan{};
    std::uint32_t framebuffer_color_sample_bits{};
    std::uint32_t framebuffer_depth_sample_bits{};
    std::uint32_t color_format_sample_bits{}; // vkGetPhysicalDeviceImageFormatProperties
    std::uint32_t depth_format_sample_bits{}; // specific format & usage
    std::uint32_t max_framebuffer_width{};
    std::uint32_t max_framebuffer_height{};
    std::uint64_t free_transient_bytes{}; // safe application budget; 0 = unknown
};
struct GuestPass {
    std::uint32_t width{}, height{};
    std::uint32_t guest_samples{1};
    std::uint32_t color_bytes_per_pixel{4};
    std::uint32_t depth_bytes_per_pixel{4};
    std::uint32_t render_target_count{1};
    bool uses_depth{true};
    bool multisample_guest_reads{}; // unsupported until proven safe
    bool storage_or_alias_attachments{}; // no valid shadow resolve path
};
// Native draw eligibility is independent of guest image memory. The
// graphics pipeline MUST have been built against the exact native shadow
// render pass and its rasterization sample count. Never bind the ordinary
// 1x guest pipeline to a 4x/8x/16x shadow framebuffer.
struct NativeDrawBinding {
    std::uint64_t shadow_renderpass{};
    std::uint64_t graphics_pipeline_renderpass{};
    std::uint32_t shadow_samples{};
    std::uint32_t graphics_pipeline_samples{};
    bool guest_clear_verified{};
    bool shader_read_aliases_target{};
};
[[nodiscard]] constexpr bool CompatibleNativeDraw(
    const NativeDrawBinding& binding) noexcept {
    return binding.shadow_renderpass != 0 &&
           binding.graphics_pipeline_renderpass == binding.shadow_renderpass &&
           (binding.shadow_samples == 2 || binding.shadow_samples == 4 ||
            binding.shadow_samples == 8 || binding.shadow_samples == 16) &&
           binding.graphics_pipeline_samples == binding.shadow_samples &&
           binding.guest_clear_verified && !binding.shader_read_aliases_target;
}

struct Implementation {
    bool native_shadow_color{};
    bool native_shadow_depth{};
    bool resolve_color_to_guest{};
    bool resolve_depth_to_guest{};
    bool guest_layout_preserved{};
    bool sampled_guest_reads_coherent{};
};

struct Result {
    Decision decision;
    std::uint64_t estimated_attachment_bytes;
};
[[nodiscard]] constexpr Result Evaluate(Requested request,
                                         const GuestPass& guest,
                                         const Limits& hw,
                                         const Implementation& backend={}) noexcept {
    if (request==Requested::Auto) return {Decision::NativeAuto,0};
    const auto bit=Bit(request);
    if (!bit) return {Decision::UnsupportedRequest,0};
    if (guest.guest_samples!=1 && guest.guest_samples!=2 &&
        guest.guest_samples!=4 && guest.guest_samples!=8 &&
        guest.guest_samples!=16)
        return {Decision::GuestMultisampleTopologyConflict,0};
    // The guest already requested at least as many *real* samples.
    // Do not replace or downsample its rasterization state.
    if (guest.guest_samples >= static_cast<unsigned>(request))
        return {Decision::NativeGuestSamplesAlreadySatisfy,0};
    // Raising a multisampled guest render target further requires a
    // special multisample-to-multisample resolve path not yet available.
    if (guest.guest_samples!=1)
        return {Decision::GuestMultisampleTopologyConflict,0};
    if (!hw.vulkan) return {Decision::RequiresVulkan,0};
    if (!guest.width || !guest.height || guest.width>hw.max_framebuffer_width ||
        guest.height>hw.max_framebuffer_height ||
        guest.width>8192 || guest.height>8192 ||
        !guest.color_bytes_per_pixel || guest.color_bytes_per_pixel>16 ||
        guest.render_target_count==0 || guest.render_target_count>8)
        return {Decision::UnsupportedDimensions,0};
    if ((hw.framebuffer_color_sample_bits & bit)==0 ||
        (hw.color_format_sample_bits & bit)==0 ||
        (guest.uses_depth && (
            (hw.framebuffer_depth_sample_bits & bit)==0 ||
            (hw.depth_format_sample_bits & bit)==0)))
        return {Decision::UnsupportedFrameFormat,0};
    // Per-attachment allocation scales with sample count; conservative,
    // excludes tiling, alignment and backing single-sample guest surfaces.
    const auto bytes_per_pixel=static_cast<std::uint64_t>(
        guest.color_bytes_per_pixel)*guest.render_target_count +
        (guest.uses_depth ? guest.depth_bytes_per_pixel : 0U);
    const auto estimated=static_cast<std::uint64_t>(guest.width) * guest.height *
        bytes_per_pixel * static_cast<unsigned>(request);
    if (!hw.free_transient_bytes || estimated>hw.free_transient_bytes)
        return {Decision::UnsupportedBudget,estimated};
    if (guest.multisample_guest_reads || guest.storage_or_alias_attachments)
        return {Decision::UnsupportedMultisampleRead,estimated};
    if (!backend.native_shadow_color || !backend.resolve_color_to_guest ||
        !backend.guest_layout_preserved || !backend.sampled_guest_reads_coherent ||
        (guest.uses_depth &&
         (!backend.native_shadow_depth || !backend.resolve_depth_to_guest)))
        return {Decision::ShadowRendererNotImplemented,estimated};
    return {Decision::CandidateOnly,estimated};
}

} // namespace Eden::Graphics::MsaaForce
