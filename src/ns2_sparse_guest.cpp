// SPDX-License-Identifier: GPL-3.0-or-later
#include "ns2_sparse_guest.h"
#include "ps5_ns2_guest_backing_plan.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <limits>
#include <mutex>
#include <new>
#include <vector>
#include <sys/mman.h>

#ifndef PS5_NATIVE
#error "This PS5 direct-memory guest residency owner must never ship on desktop"
#endif

namespace Common {
void* ReserveMemoryRange(std::size_t) noexcept;
bool CommitMemoryRange(void*, std::size_t, std::int64_t*) noexcept;
}
extern "C" std::int32_t sceKernelReleaseDirectMemory(std::int64_t, std::size_t);

namespace Eden::PS5::GuestBacking {
namespace {
std::mutex registry_mutex;
Runtime* active_guest = nullptr;

// A published PA must never be freed while its CPU VA is still live.
// Use the same fixed PROT_NONE reclaim pattern as the qualified native heap
// rollback; the caller must also have quiesced external GPU aliases.
void Retract(void* address, std::int64_t physical) noexcept {
    auto* hole = mmap(address, kGranule, PROT_NONE,
                      MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (hole != address) std::abort();
    if (sceKernelReleaseDirectMemory(physical, kGranule) != 0) std::abort();
}
}

struct Runtime::Impl {
    Plan plan;
    std::size_t bytes;
    std::uint8_t* base{};
    std::vector<std::int64_t> physical;
    std::mutex mutex;
    bool installed{};

    Impl(std::size_t capacity, std::size_t budget)
      : plan(capacity, budget), bytes(capacity),
        physical(plan.ChunkCount(), -1) {
        if (plan.Valid()) {
            base = static_cast<std::uint8_t*>(Common::ReserveMemoryRange(capacity));
        }
    }
    ~Impl() {
        if (!base) return;
        // This is only safe after HostMemory and every GPU/user has stopped
        // accessing the reservation. Revoke its full CPU VA FIRST.
        if (munmap(base, bytes) != 0) std::abort();
        for (const auto owner : physical) {
            if (owner >= 0 && sceKernelReleaseDirectMemory(owner, kGranule) != 0)
                std::abort();
        }
    }
    bool Commit(std::size_t offset, std::size_t length) {
        std::lock_guard lock{mutex};
        if (!base || offset > bytes || length > bytes - offset) return false;
        if (!length) return true;
        const auto first = offset / kGranule;
        const auto last = (offset + length - 1) / kGranule + 1;
        const auto admit = plan.Begin(first * kGranule, (last - first) * kGranule);
        if (!admit) return false; // budget or pending owner; never overcommit
        const auto rollback = [&] {
            const auto retired = plan.Abort(*admit);
            if (!retired) std::abort();
            for (const auto& part : *retired) {
                auto* at = base + part.index * kGranule;
                Retract(at, part.physical);
                physical[part.index] = -1;
                if (!plan.ReleaseAcknowledged(*admit, part.index, part.physical))
                    std::abort();
            }
            if (!plan.FinishAbort(*admit)) std::abort();
        };
        for (auto index = first; index < last; ++index) {
            if (plan.At(index).state == State::Resident) continue;
            std::int64_t pa = -1;
            auto* at = base + index * kGranule;
            if (!Common::CommitMemoryRange(at, kGranule, &pa)) {
                rollback();
                return false;
            }
            if (pa < 0 || !plan.Stage(*admit, index, pa)) {
                // Kernel MAP succeeded but ownership staging failed:
                // the new mapping is not PTE-published. Revoke it first.
                if (pa < 0) std::abort();
                Retract(at, pa);
                rollback();
                return false;
            }
            physical[index] = pa;
        }
        if (!plan.Publish(*admit)) std::abort();
        return true;
    }
};

Runtime::Runtime(std::size_t capacity, std::size_t budget)
  : impl_(std::make_unique<Impl>(capacity, budget)) {}
Runtime::~Runtime() { Uninstall(); }
bool Runtime::Valid() const noexcept { return impl_ && impl_->base && impl_->plan.Valid(); }
void* Runtime::Base() const noexcept { return Valid() ? impl_->base : nullptr; }
std::size_t Runtime::VirtualBytes() const noexcept { return impl_ ? impl_->bytes : 0; }
std::size_t Runtime::UsedBytes() const noexcept {
    if (!impl_) return 0;
    std::lock_guard lock{impl_->mutex};
    return static_cast<std::size_t>(impl_->plan.UsedBytes());
}
bool Runtime::Commit(std::size_t offset, std::size_t bytes) noexcept {
    if (!impl_) return false;
    try {
        return impl_->Commit(offset, bytes);
    } catch (...) {
        // Never publish an alias when the physical ownership is uncertain.
        std::abort();
    }
}
bool Runtime::Install() noexcept {
    std::lock_guard lock{registry_mutex};
    if (!Valid() || active_guest) return false;
    active_guest = this;
    impl_->installed = true;
    return true;
}
void Runtime::Uninstall() noexcept {
    std::lock_guard lock{registry_mutex};
    if (active_guest == this) active_guest = nullptr;
    if (impl_) impl_->installed = false;
}

} // namespace Eden::PS5::GuestBacking

extern "C" bool EdenNs2CommitGuestBacking(const void* backing_base,
                                            std::size_t offset,
                                            std::size_t bytes) noexcept {
    std::lock_guard lock{Eden::PS5::GuestBacking::registry_mutex};
    const auto* owner = Eden::PS5::GuestBacking::active_guest;
    if (!owner) return true;
    if (owner->Base() != backing_base) return false;
    return Eden::PS5::GuestBacking::active_guest->Commit(offset, bytes);
}
