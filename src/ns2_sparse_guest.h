// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstddef>
#include <cstdint>
#include <memory>

namespace Eden::PS5::GuestBacking {
// PS5-only experimental owned guest backing. Reserve 12 GiB virtual DRAM,
// commit real independent 2 MiB direct-memory blocks before publishing PTEs.
// No SIGSEGV-handler allocations, overcommit aliases, or silent truncation.
class Runtime {
public:
    Runtime(std::size_t virtual_bytes, std::size_t physical_budget);
    ~Runtime();
    Runtime(const Runtime&) = delete;
    Runtime& operator=(const Runtime&) = delete;

    [[nodiscard]] bool Valid() const noexcept;
    [[nodiscard]] void* Base() const noexcept;
    [[nodiscard]] std::size_t VirtualBytes() const noexcept;
    [[nodiscard]] std::size_t UsedBytes() const noexcept;
    [[nodiscard]] bool Commit(std::size_t offset, std::size_t bytes) noexcept;

    // Only one active guest reservation is allowed. A registry lock protects
    // admission calls against owner teardown. Engine must quiesce GPU first.
    [[nodiscard]] bool Install() noexcept;
    void Uninstall() noexcept;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // namespace Eden::PS5::GuestBacking

// Called by the maintained vendor PS5 MapMemoryRegion owners BEFORE PTE
// publication. Without an active NS2 sparse arena, this is an NS1 no-op.
extern "C" bool EdenNs2CommitGuestBacking(const void* backing_base,
                                            std::size_t offset,
                                            std::size_t bytes) noexcept;
