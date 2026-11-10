// SPDX-License-Identifier: MIT
// Research-only, fail-closed Vulkan range admission for native QMD3.
// This header is NOT linked into Encore or used by a PS5 pipeline.
#pragma once
#include <cstdint>
#include <limits>

namespace encore_ns2_research {
using u64 = std::uint64_t;
enum class VkBindingKind : std::uint8_t { Uniform, Storage };
enum class VkRangeStatus : std::uint8_t {
    Ok, EmptyRange, GpuOutOfBounds, NativeSpanTooLarge, DriverRangeExceeded,
    InvalidAlignment, MisalignedOffset, BackingTooSmall, InvalidDeviceAddress
};
struct VkRangeLimits {
    u64 max_uniform_range{};
    u64 max_storage_range{};
    u64 uniform_offset_alignment{};
    u64 storage_offset_alignment{};
};
struct VkRangeRequest {
    VkBindingKind kind{VkBindingKind::Storage};
    u64 guest_gpu_address{};
    u64 bytes{};
};
struct VkRangeResolved {
    VkRangeRequest request{};
    u64 buffer_offset{};
    u64 backing_bytes{};
    u64 vk_device_base_address{};
    bool descriptor_buffer{};
};
constexpr u64 kNativeGpuVABound = u64{1} << 49;
constexpr u64 kNativeQmdMaxContiguousBytes = 256ULL * 1024 * 1024;

// Preflight before any expensive GMMU scan/BufferCache::ObtainBuffer.
[[nodiscard]] constexpr VkRangeStatus CheckNativeVkRange(const VkRangeRequest& q,
                                                         const VkRangeLimits& limits) noexcept {
    if (q.bytes == 0) return VkRangeStatus::EmptyRange;
    if (q.guest_gpu_address == 0 || q.guest_gpu_address >= kNativeGpuVABound ||
        q.bytes > kNativeGpuVABound - q.guest_gpu_address)
        return VkRangeStatus::GpuOutOfBounds;
    if (q.bytes > kNativeQmdMaxContiguousBytes)
        return VkRangeStatus::NativeSpanTooLarge;
    const u64 driver_limit = q.kind == VkBindingKind::Storage
        ? limits.max_storage_range : limits.max_uniform_range;
    if (!driver_limit || q.bytes > driver_limit ||
        (q.kind == VkBindingKind::Uniform && q.bytes > 65536))
        return VkRangeStatus::DriverRangeExceeded;
    return VkRangeStatus::Ok;
}

// Must be checked after obtaining the actual Vulkan buffer/offset. No clamping.
[[nodiscard]] constexpr VkRangeStatus CheckNativeVkResolved(const VkRangeResolved& r,
                                                            const VkRangeLimits& limits) noexcept {
    const VkRangeStatus initial = CheckNativeVkRange(r.request, limits);
    if (initial != VkRangeStatus::Ok) return initial;
    const u64 alignment = r.request.kind == VkBindingKind::Storage
        ? limits.storage_offset_alignment : limits.uniform_offset_alignment;
    if (alignment == 0 || (alignment & (alignment - 1)) != 0)
        return VkRangeStatus::InvalidAlignment;
    if ((r.buffer_offset & (alignment - 1)) != 0)
        return VkRangeStatus::MisalignedOffset;
    // Overflow-safe backing bounds: never compute offset+bytes unchecked.
    if (r.buffer_offset > r.backing_bytes ||
        r.request.bytes > r.backing_bytes - r.buffer_offset)
        return VkRangeStatus::BackingTooSmall;
    if (r.descriptor_buffer &&
        (r.vk_device_base_address == 0 ||
         r.buffer_offset > std::numeric_limits<u64>::max() - r.vk_device_base_address))
        return VkRangeStatus::InvalidDeviceAddress;
    return VkRangeStatus::Ok;
}
} // namespace encore_ns2_research
