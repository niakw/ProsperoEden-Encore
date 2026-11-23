// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstddef>
#include <cstdint>
#include <memory>

namespace Eden::PS5::GuestBacking {
// PS5-only owned guest backing for the supported NS1/NS2 DRAM layouts.
// Reserve 4/6/8/10/12 GiB of guest VA and keep untouched 2 MiB chunks on
// one shared read-only ZERO block. First writes promote one chunk to OWN.
// The handler performs no STL/heap allocation; overcommit aliases and silent
// layout truncation are forbidden.
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

// Historical C ABI names are retained for vendor compatibility. These hooks
// now target the active PS5 sparse arena for either NS1 or NS2; with no active
// arena they remain safe no-ops. Readability is established before PTE publish.
extern "C" bool EdenNs2CommitGuestBacking(const void* backing_base,
                                            std::size_t offset,
                                            std::size_t bytes) noexcept;
extern "C" bool EdenNs2EnsureGuestBackingReadable(const void* backing_base,
                                                    std::size_t offset,
                                                    std::size_t bytes) noexcept;
extern "C" void EdenNs2GuestBackingFreed(std::size_t offset,
                                          std::size_t bytes) noexcept;
