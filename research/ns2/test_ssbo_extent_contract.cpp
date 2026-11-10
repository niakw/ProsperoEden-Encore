// SPDX-License-Identifier: MIT
// Standalone host-only positive and negative research regression suite.
#include "ssbo_extent_contract.hpp"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>

using namespace encore_ns2_research;

constexpr Request Base(DescriptorKind kind = DescriptorKind::NativeBare) {
    return {.gpu_address = 0x20000000ULL, .descriptor_next_qword = 266,
            .memory_layout_bytes = 32 * MiB,
            .continuously_mapped_bytes = 32 * MiB,
            .driver_max_storage_range = 64 * MiB, .alignment = 256,
            .kind = kind, .compute = true, .written = false};
}
constexpr bool StaticChecks() {
    const auto b = Base();
    const auto good = ResolveExtent(b);
    return good && good.extent == 32 * MiB && good.bound_size == good.extent &&
           !good.used_declared_length;
}
static_assert(StaticChecks());

int main() {
    int cases = 0;
    const auto check = [&](bool pass) { assert(pass); ++cases; };
    {
        const auto d = ResolveExtent(Base());
        check(d && d.extent == 32 * MiB); // NS2 native read > 8 MiB, second word=266.
    }
    {
        auto r = Base(); r.descriptor_next_qword = 0x3F800000ULL;
        const auto d = ResolveExtent(r);
        check(d && d.extent == 32 * MiB && !d.used_declared_length); // 1.0f is not 1 GiB.
    }
    {
        auto r = Base(); r.continuously_mapped_bytes = 3 * MiB;
        check(ResolveExtent(r).extent == 3 * MiB); // Stop at mapping gap.
    }
    {
        auto r = Base(); r.written = true;
        check(ResolveExtent(r).extent == 8 * MiB); // No unbounded GPU dirty span.
    }
    {
        auto r = Base(DescriptorKind::NativeTable);
        check(ResolveExtent(r).extent == 32 * MiB);
    }
    {
        auto r = Base(DescriptorKind::LegacySized); r.descriptor_next_qword = 4096;
        const auto d = ResolveExtent(r);
        check(d && d.used_declared_length && d.extent == 4096);
    }
    {
        auto r = Base(DescriptorKind::LegacySized);
        r.descriptor_next_qword = (1ULL << 40) | 4096;
        const auto d = ResolveExtent(r);
        check(d && !d.used_declared_length && d.extent == 8 * MiB);
    }
    {
        auto r = Base(); r.gpu_address += 32;
        r.driver_max_storage_range = 16 * MiB;
        const auto d = ResolveExtent(r);
        check(d && d.offset == 32 && d.bound_size == 16 * MiB &&
              d.extent == 16 * MiB - 32);
    }
    {
        auto r = Base(); r.driver_max_storage_range = 0;
        check(ResolveExtent(r).status == Status::InvalidDriverRange);
    }
    {
        auto r = Base(); r.gpu_address = 0;
        check(ResolveExtent(r).status == Status::NullAddress);
    }
    {
        auto r = Base(); r.alignment = 3;
        check(ResolveExtent(r).status == Status::InvalidAlignment);
    }
    {
        auto r = Base(); r.continuously_mapped_bytes = 0;
        check(ResolveExtent(r).status == Status::BadMapping);
    }
    {
        auto r = Base(); r.gpu_address = std::numeric_limits<std::uint64_t>::max() - 4095;
        check(ResolveExtent(r).status == Status::AddressOverflow);
    }
    {
        auto r = Base(); r.kind = DescriptorKind::Unproven;
        check(ResolveExtent(r).status == Status::UnknownProvenance);
    }
    {
        auto r = Base(); r.gpu_address += 256;
        r.alignment = 512; r.driver_max_storage_range = 256;
        check(ResolveExtent(r).status == Status::InvalidDriverRange);
    }
    {
        auto r = Base(); r.compute = false;
        check(ResolveExtent(r).extent == 8 * MiB); // NS2 graphics != compute.
    }
    {
        auto r = Base(DescriptorKind::LegacySized);
        r.descriptor_next_qword = 16 * MiB;
        check(ResolveExtent(r).extent == 16 * MiB); // Explicit legitimate legacy size.
    }
    std::cout << "PASS: " << cases << " NS2 SSBO extent research contracts\n";
}
