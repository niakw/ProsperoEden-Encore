// SPDX-License-Identifier: MIT
// Standalone host-only native QMD3 / Vulkan descriptor range admission.
#include "native_vk_range_contract.hpp"
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <limits>

using namespace encore_ns2_research;
constexpr VkRangeLimits Limits{65536, 32ULL * 1024 * 1024, 256, 256};
constexpr VkRangeRequest Storage{VkBindingKind::Storage, 0x400000, 8192};
constexpr VkRangeResolved Resolved{Storage, 256, 12288, 0x80000000, false};
static_assert(CheckNativeVkRange(Storage, Limits) == VkRangeStatus::Ok);
static_assert(CheckNativeVkResolved(Resolved, Limits) == VkRangeStatus::Ok);
int main() {
    int n = 0;
    auto check = [&](bool ok) { ++n; if (!ok) {std::cerr << "FAILED test #" << n << "\n"; std::abort();} };
    check(CheckNativeVkRange(Storage, Limits) == VkRangeStatus::Ok);
    check(CheckNativeVkResolved(Resolved, Limits) == VkRangeStatus::Ok);
    auto s = Storage;
    s.bytes = 0;
    check(CheckNativeVkRange(s, Limits) == VkRangeStatus::EmptyRange);
    s = Storage;
    s.guest_gpu_address = 0;
    check(CheckNativeVkRange(s, Limits) == VkRangeStatus::GpuOutOfBounds);
    s.guest_gpu_address = kNativeGpuVABound;
    check(CheckNativeVkRange(s, Limits) == VkRangeStatus::GpuOutOfBounds);
    s.guest_gpu_address = kNativeGpuVABound - 4096;
    check(CheckNativeVkRange(s, Limits) == VkRangeStatus::GpuOutOfBounds);
    s = Storage;
    s.bytes = 256ULL * 1024 * 1024 + 1;
    check(CheckNativeVkRange(s, Limits) == VkRangeStatus::NativeSpanTooLarge);
    s = Storage;
    s.bytes = 32ULL * 1024 * 1024;
    check(CheckNativeVkRange(s, Limits) == VkRangeStatus::Ok);
    s.bytes++;
    check(CheckNativeVkRange(s, Limits) == VkRangeStatus::DriverRangeExceeded);
    auto limits = Limits;
    limits.max_storage_range = 0;
    check(CheckNativeVkRange(Storage, limits) == VkRangeStatus::DriverRangeExceeded);
    limits = Limits;
    limits.max_storage_range = 256ULL * 1024 * 1024;
    s.bytes = 256ULL * 1024 * 1024;
    check(CheckNativeVkRange(s, limits) == VkRangeStatus::Ok);
    s = Storage;
    s.kind = VkBindingKind::Uniform;
    s.bytes = 65536;
    check(CheckNativeVkRange(s, limits) == VkRangeStatus::Ok);
    s.bytes++;
    check(CheckNativeVkRange(s, limits) == VkRangeStatus::DriverRangeExceeded);
    limits.max_uniform_range = 8192;
    s.bytes = 8193;
    check(CheckNativeVkRange(s, limits) == VkRangeStatus::DriverRangeExceeded);
    s.bytes = 8192;
    check(CheckNativeVkRange(s, limits) == VkRangeStatus::Ok);
    auto r = Resolved;
    r.buffer_offset = 128;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::MisalignedOffset);
    r = Resolved;
    r.backing_bytes = 8447;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::BackingTooSmall);
    r.backing_bytes = 8448;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::Ok);
    r.buffer_offset = std::numeric_limits<u64>::max() - 255;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::BackingTooSmall);
    r = Resolved;
    r.descriptor_buffer = true;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::Ok);
    r.vk_device_base_address = 0;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::InvalidDeviceAddress);
    r.vk_device_base_address = std::numeric_limits<u64>::max() - 128;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::InvalidDeviceAddress);
    r.vk_device_base_address = std::numeric_limits<u64>::max() - 256;
    check(CheckNativeVkResolved(r, Limits) == VkRangeStatus::Ok);
    r = Resolved;
    limits = Limits;
    limits.storage_offset_alignment = 0;
    check(CheckNativeVkResolved(r, limits) == VkRangeStatus::InvalidAlignment);
    limits.storage_offset_alignment = 3;
    check(CheckNativeVkResolved(r, limits) == VkRangeStatus::InvalidAlignment);
    limits.storage_offset_alignment = 512;
    check(CheckNativeVkResolved(r, limits) == VkRangeStatus::MisalignedOffset);
    r.buffer_offset = 512;
    check(CheckNativeVkResolved(r, limits) == VkRangeStatus::Ok);
    r.request.kind = VkBindingKind::Uniform;
    limits.uniform_offset_alignment = 1024;
    check(CheckNativeVkResolved(r, limits) == VkRangeStatus::MisalignedOffset);
    r.buffer_offset = 1024;
    check(CheckNativeVkResolved(r, limits) == VkRangeStatus::Ok);
    r.request.bytes = 65537;
    check(CheckNativeVkResolved(r, limits) == VkRangeStatus::DriverRangeExceeded);
    std::cout << "PASS: " << n << " native Vulkan range contracts\n";
}
