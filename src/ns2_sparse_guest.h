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
    // Clear is owned by the sparse runtime: zero clears touch only OWN
    // chunks and leave shared ZERO chunks unallocated; nonzero clears promote
    // the full range first and then write it.
    [[nodiscard]] bool Clear(std::size_t offset, std::size_t bytes,
                             std::uint32_t fill) noexcept;
    [[nodiscard]] bool EnsureReadable(std::size_t offset, std::size_t bytes) noexcept;
    // Called only after the guest buddy allocator proves complete 2 MiB
    // slots free. Replaces private OWN mappings with shared ZERO mappings.
    void ReleaseFreed(std::size_t offset, std::size_t bytes) noexcept;
    [[nodiscard]] bool HandleWriteFault(void* address) noexcept;

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
extern "C" bool EdenNs2EnsureGuestBackingReadable(const void* backing_base,
                                                    std::size_t offset,
                                                    std::size_t bytes) noexcept;
extern "C" void EdenNs2GuestBackingFreed(std::size_t offset,
                                          std::size_t bytes) noexcept;
