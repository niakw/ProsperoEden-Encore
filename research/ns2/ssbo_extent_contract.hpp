// SPDX-License-Identifier: MIT
// Research-only host contract; not wired to production renderer.
#pragma once
#include <algorithm>
#include <cstdint>
#include <limits>

namespace encore_ns2_research {
constexpr std::uint64_t MiB = 1024ULL * 1024ULL;
constexpr std::uint64_t LegacyFallback = 8ULL * MiB;

enum class DescriptorKind : std::uint8_t {
    LegacySized,   // Next qword is a candidate packed length.
    NativeBare,    // Next qword is a guest parameter, never a length.
    NativeTable,   // Explicitly proven native indirection table.
    Unproven       // Fail closed on unverified provenance.
};
enum class Status : std::uint8_t {
    Ok, NullAddress, InvalidAlignment, BadMapping, AddressOverflow,
    InvalidDriverRange, UnknownProvenance
};
struct Request {
    std::uint64_t gpu_address{};
    std::uint64_t descriptor_next_qword{};
    std::uint64_t memory_layout_bytes{};
    std::uint64_t continuously_mapped_bytes{};
    std::uint64_t driver_max_storage_range{};
    std::uint32_t alignment{1};
    DescriptorKind kind{DescriptorKind::Unproven};
    bool compute{};
    bool written{};
};
struct Decision {
    Status status{Status::BadMapping};
    std::uint64_t aligned_address{};
    std::uint64_t offset{};
    std::uint64_t extent{};
    std::uint64_t bound_size{};
    bool used_declared_length{};
    [[nodiscard]] constexpr explicit operator bool() const { return status == Status::Ok; }
};

// A candidate policy, **not** a live implementation. The caller must independently
// prove descriptor provenance and both mapping lengths at the same process epoch.
[[nodiscard]] constexpr Decision ResolveExtent(const Request& r) {
    Decision d{};
    if (r.gpu_address == 0) { d.status = Status::NullAddress; return d; }
    if (r.kind == DescriptorKind::Unproven) {
        d.status = Status::UnknownProvenance; return d;
    }
    if (r.alignment == 0 || (r.alignment & (r.alignment - 1)) != 0) {
        d.status = Status::InvalidAlignment; return d;
    }
    if (r.memory_layout_bytes == 0 || r.continuously_mapped_bytes == 0) {
        d.status = Status::BadMapping; return d;
    }
    const auto contiguous = std::min(r.memory_layout_bytes, r.continuously_mapped_bytes);
    if (r.gpu_address > std::numeric_limits<std::uint64_t>::max() - contiguous) {
        d.status = Status::AddressOverflow; return d;
    }
    d.offset = r.gpu_address & (r.alignment - 1);
    d.aligned_address = r.gpu_address - d.offset;
    // Vulkan range includes the alignment offset, not just the guest payload.
    const auto driver_max = std::min(r.driver_max_storage_range,
                                     std::uint64_t{std::numeric_limits<std::uint32_t>::max()});
    if (driver_max <= d.offset) {
        d.status = Status::InvalidDriverRange; return d;
    }
    const auto driver_capacity = driver_max - d.offset;
    const bool native_read = r.compute && !r.written &&
        (r.kind == DescriptorKind::NativeBare || r.kind == DescriptorKind::NativeTable);
    std::uint64_t desired = LegacyFallback;
    if (native_read) {
        desired = contiguous;
    } else if (r.kind == DescriptorKind::LegacySized &&
               r.descriptor_next_qword != 0 &&
               r.descriptor_next_qword <= std::numeric_limits<std::uint32_t>::max() &&
               r.descriptor_next_qword <= contiguous) {
        desired = r.descriptor_next_qword;
        d.used_declared_length = true;
    }
    d.extent = std::min({contiguous, desired, driver_capacity});
    d.bound_size = d.offset + d.extent;
    d.status = d.extent == 0 ? Status::InvalidDriverRange : Status::Ok;
    return d;
}
}  // namespace encore_ns2_research
