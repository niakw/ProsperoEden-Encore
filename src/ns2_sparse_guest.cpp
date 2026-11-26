// SPDX-License-Identifier: GPL-3.0-or-later
#include "ns2_sparse_guest.h"
#include "ps5_ns2_guest_backing_plan.h"
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <csignal>
#include <cstring>
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
void* ReserveGuestMemoryRange(std::size_t) noexcept;
bool CommitMemoryRange(void*, std::size_t, std::int64_t*) noexcept;
}
extern "C" {
std::int32_t sceKernelReleaseDirectMemory(std::int64_t, std::size_t);
std::int32_t sceKernelMapDirectMemory(void**, std::size_t, int, int,
                                     std::int64_t, std::size_t);
std::int32_t sceKernelEnableDmemAliasing();
}

namespace Eden::PS5::GuestBacking {
namespace {
std::mutex registry_mutex;
Runtime* active_guest = nullptr;
std::atomic<Runtime*> active_guest_signal{nullptr};
std::atomic<unsigned> signal_users{0};
std::once_flag signal_once;
bool signal_installed = false;
struct sigaction previous_segv{}, previous_bus{};
thread_local bool owner_gate_held = false;

bool MapPhysical(void* address, int protection, std::int64_t physical) noexcept {
    void* at = address;
    return sceKernelMapDirectMemory(&at, kGranule, protection, MAP_FIXED,
                                    physical, kGranule) == 0 &&
           at == address;
}

void RestoreZero(void* address, std::int64_t zero_physical,
                 std::int64_t old_physical) noexcept {
    if (!MapPhysical(address, PROT_READ, zero_physical)) std::abort();
    if (old_physical >= 0 &&
        sceKernelReleaseDirectMemory(old_physical, kGranule) != 0)
        std::abort();
}

void ForwardSignal(int signal, siginfo_t* info, void* context) noexcept {
    const struct sigaction& previous = signal == SIGSEGV ? previous_segv : previous_bus;
    if (previous.sa_flags & SA_SIGINFO) {
        previous.sa_sigaction(signal, info, context);
    } else if (previous.sa_handler == SIG_DFL) {
        std::signal(signal, SIG_DFL);
    } else if (previous.sa_handler != SIG_IGN) {
        previous.sa_handler(signal);
    }
}

void GuestSignal(int signal, siginfo_t* info, void* context) noexcept {
    signal_users.fetch_add(1, std::memory_order_acq_rel);
    Runtime* const guest = active_guest_signal.load(std::memory_order_acquire);
    const bool handled = guest && info && guest->HandleWriteFault(info->si_addr);
    signal_users.fetch_sub(1, std::memory_order_acq_rel);
    if (handled) return;
    ForwardSignal(signal, info, context);
}

bool InstallGuestSignal() noexcept {
    std::call_once(signal_once, [] {
        struct sigaction action{};
        action.sa_sigaction = GuestSignal;
        action.sa_flags = SA_SIGINFO | SA_RESTART;
        sigemptyset(&action.sa_mask);
        if (sigaction(SIGSEGV, &action, &previous_segv) == 0) {
            if (sigaction(SIGBUS, &action, &previous_bus) == 0) {
                signal_installed = true;
            } else if (sigaction(SIGSEGV, &previous_segv, nullptr) != 0) {
                std::abort();
            }
        }
    });
    return signal_installed;
}
} // namespace

struct Runtime::Impl {
    struct GateGuard {
        Impl& owner;
        bool locked{};
        bool waited{};
        explicit GateGuard(Impl& owner_) : owner(owner_) {
            if (owner_gate_held) return;
            while (owner.gate.test_and_set(std::memory_order_acquire))
                waited = true;
            owner_gate_held = true;
            locked = true;
        }
        ~GateGuard() {
            if (!locked) return;
            owner_gate_held = false;
            owner.gate.clear(std::memory_order_release);
        }
        explicit operator bool() const noexcept { return locked; }
    };

    Plan plan;
    std::size_t bytes;
    std::uint8_t* base{};
    std::vector<std::int64_t> physical;
    std::int64_t zero_physical{-1};
    std::atomic_flag gate = ATOMIC_FLAG_INIT;
    std::atomic<std::uint64_t> fault_promotions{0};
    std::atomic<std::uint64_t> fault_denials{0};
    bool installed{};
    bool failure_reported{};

    void ReportCommitDenial(const char* stage, std::size_t offset,
                            std::size_t length) noexcept {
        if (failure_reported) return;
        failure_reported = true;
        std::fprintf(stderr,
                     "EDEN_NS2_SPARSE_COMMIT_DENIED stage=%s offset=%zu bytes=%zu"
                     " resident=%llu budget=%llu\n",
                     stage, offset, length,
                     static_cast<unsigned long long>(plan.UsedBytes()),
                     static_cast<unsigned long long>(plan.BudgetBytes()));
    }

    Impl(std::size_t capacity, std::size_t budget)
      : plan(capacity, budget), bytes(capacity),
        physical(plan.ChunkCount(), -1) {
        if (!plan.Valid()) return;
        base = static_cast<std::uint8_t*>(Common::ReserveGuestMemoryRange(capacity));
        if (!base) return;

        // One real 2 MiB block supplies zeroes to all untouched guest chunks.
        // Reads never fault; the first write promotes that chunk to OWN.
        (void)sceKernelEnableDmemAliasing();
        if (!Common::CommitMemoryRange(base, kGranule, &zero_physical) ||
            zero_physical < 0) {
            (void)munmap(base, bytes);
            base = nullptr;
            zero_physical = -1;
            return;
        }
        bool ok = MapPhysical(base, PROT_READ, zero_physical);
        for (std::size_t index = 1; ok && index < plan.ChunkCount(); ++index)
            ok = MapPhysical(base + index * kGranule, PROT_READ, zero_physical);
        if (!ok) {
            if (munmap(base, bytes) != 0) std::abort();
            if (sceKernelReleaseDirectMemory(zero_physical, kGranule) != 0)
                std::abort();
            base = nullptr;
            zero_physical = -1;
        }
    }

    ~Impl() {
        if (!base) return;
        if (munmap(base, bytes) != 0) std::abort();
        for (const auto owner : physical) {
            if (owner >= 0 &&
                sceKernelReleaseDirectMemory(owner, kGranule) != 0)
                std::abort();
        }
        if (zero_physical >= 0 &&
            sceKernelReleaseDirectMemory(zero_physical, kGranule) != 0)
            std::abort();
    }

    bool ValidateLocked(std::size_t offset, std::size_t length) noexcept {
        return base && offset <= bytes && length <= bytes - offset;
    }

    bool CommitLocked(std::size_t offset, std::size_t length) {
        if (!ValidateLocked(offset, length)) {
            ReportCommitDenial("range", offset, length);
            return false;
        }
        if (!length) return true;
        const auto first = offset / kGranule;
        const auto last = (offset + length - 1) / kGranule + 1;
        const auto admit = plan.Begin(first * kGranule, (last - first) * kGranule);
        if (!admit) {
            ReportCommitDenial("admission", offset, length);
            return false;
        }
        const auto rollback = [&] {
            const auto retired = plan.Abort(*admit);
            if (!retired) std::abort();
            for (const auto& part : *retired) {
                auto* at = base + part.index * kGranule;
                RestoreZero(at, zero_physical, part.physical);
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
                // A failed MAP_FIXED is not allowed to leave a hole while
                // the Plan rolls this newcomer back to ZERO. Reinstall the
                // shared read-only zero alias before cancelling ownership.
                if (!MapPhysical(at, PROT_READ, zero_physical)) std::abort();
                rollback();
                ReportCommitDenial("native_physical_map", offset, length);
                return false;
            }
            if (pa < 0 || !plan.Stage(*admit, index, pa)) {
                if (pa < 0) std::abort();
                RestoreZero(at, zero_physical, pa);
                rollback();
                ReportCommitDenial("ownership_stage", offset, length);
                return false;
            }
            physical[index] = pa;
        }
        if (!plan.Publish(*admit)) std::abort();
        return true;
    }

    bool Commit(std::size_t offset, std::size_t length) {
        GateGuard lock{*this};
        if (!lock) return false;
        return CommitLocked(offset, length);
    }

    bool Clear(std::size_t offset, std::size_t length, std::uint32_t fill) {
        GateGuard lock{*this};
        if (!lock || !ValidateLocked(offset, length)) return false;
        if (!length) return true;

        if (fill == 0) {
            // ZERO chunks already contain the requested bytes and must stay
            // shared. Clear only intersections with private OWN chunks.
            const auto first = offset / kGranule;
            const auto last = (offset + length - 1) / kGranule + 1;
            for (auto index = first; index < last; ++index) {
                const auto state = plan.At(index).state;
                if (state == State::Unmapped) continue;
                if (state != State::Resident) return false;
                const auto chunk_begin = index * kGranule;
                const auto begin = (std::max)(offset, chunk_begin);
                const auto end = (std::min)(offset + length, chunk_begin + kGranule);
                std::memset(base + begin, 0, end - begin);
            }
            return true;
        }

        // A nonzero clear cannot be represented by the shared ZERO block.
        // Admit every touched chunk before the first byte is modified so OOM
        // never leaves a partially filled guest range.
        if (!CommitLocked(offset, length)) return false;
        std::memset(base + offset, static_cast<int>(fill), length);
        return true;
    }

    bool EnsureReadable(std::size_t offset, std::size_t length) noexcept {
        GateGuard lock{*this};
        if (!lock || !ValidateLocked(offset, length)) return false;
        if (!length) return true;
        const auto first = offset / kGranule;
        const auto last = (offset + length - 1) / kGranule + 1;
        for (auto index = first; index < last; ++index) {
            const auto state = plan.At(index).state;
            if (state != State::Unmapped && state != State::Resident)
                return false;
        }
        return true;
    }

    void ReleaseFreed(std::size_t offset, std::size_t length) noexcept {
        GateGuard lock{*this};
        if (!lock || !ValidateLocked(offset, length) || !length) return;

        // Only whole native granules fully contained in the proven-free
        // page-heap block may be returned. Never touch live partial edges.
        const auto first = (offset + kGranule - 1) / kGranule;
        const auto last = (offset + length) / kGranule;
        for (auto index = first; index < last; ++index) {
            const auto state = plan.At(index).state;
            if (state == State::Unmapped) continue;
            if (state != State::Resident) return;

            const auto old_physical = physical[index];
            if (old_physical < 0) std::abort();
            auto* const at = base + index * kGranule;

            // Revoke the writable CPU mapping before returning its direct PA.
            // If ZERO cannot be installed, restore OWN and keep accounting.
            if (!MapPhysical(at, PROT_READ, zero_physical)) {
                if (!MapPhysical(at, PROT_READ | PROT_WRITE, old_physical))
                    std::abort();
                return;
            }
            if (sceKernelReleaseDirectMemory(old_physical, kGranule) != 0)
                std::abort();
            physical[index] = -1;
            if (!plan.ReleaseResident(index, old_physical)) std::abort();
        }
    }

    bool PromoteFault(void* fault) noexcept {
        if (!fault || !base || owner_gate_held) return false;
        const auto address = reinterpret_cast<std::uintptr_t>(fault);
        const auto begin = reinterpret_cast<std::uintptr_t>(base);
        if (address < begin || address - begin >= bytes) return false;
        const auto index = static_cast<std::size_t>((address - begin) / kGranule);

        GateGuard lock{*this};
        if (!lock) return false;
        const auto state = plan.At(index).state;
        // A second thread may have promoted this exact ZERO chunk while this
        // handler waited on the gate; retrying its original write is safe.
        // Without contention, a fault on an already writable OWN chunk is
        // unrelated to demand-zero and must reach the previous crash handler.
        if (state == State::Resident) return lock.waited;
        if (state != State::Unmapped) return false;

        const auto admit = plan.Begin(index * kGranule, kGranule);
        if (!admit) {
            fault_denials.fetch_add(1, std::memory_order_relaxed);
            return false;
        }

        std::int64_t pa = -1;
        auto* at = base + index * kGranule;
        if (!Common::CommitMemoryRange(at, kGranule, &pa)) {
            if (!plan.CancelSingleUnstaged(*admit)) std::abort();
            if (!MapPhysical(at, PROT_READ, zero_physical)) std::abort();
            fault_denials.fetch_add(1, std::memory_order_relaxed);
            return false;
        }
        if (pa < 0 || !plan.Stage(*admit, index, pa)) {
            if (pa >= 0) RestoreZero(at, zero_physical, pa);
            if (!plan.CancelSingleUnstaged(*admit)) std::abort();
            fault_denials.fetch_add(1, std::memory_order_relaxed);
            return false;
        }
        physical[index] = pa;
        if (!plan.Publish(*admit)) std::abort();
        fault_promotions.fetch_add(1, std::memory_order_relaxed);
        return true;
    }
};

Runtime::Runtime(std::size_t capacity, std::size_t budget)
  : impl_(std::make_unique<Impl>(capacity, budget)) {}
Runtime::~Runtime() { Uninstall(); }
bool Runtime::Valid() const noexcept {
    return impl_ && impl_->base && impl_->zero_physical >= 0 && impl_->plan.Valid();
}
void* Runtime::Base() const noexcept { return Valid() ? impl_->base : nullptr; }
std::size_t Runtime::VirtualBytes() const noexcept { return impl_ ? impl_->bytes : 0; }
std::size_t Runtime::UsedBytes() const noexcept {
    if (!impl_) return 0;
    Impl::GateGuard lock{*impl_};
    return lock ? static_cast<std::size_t>(impl_->plan.UsedBytes()) : 0;
}
bool Runtime::Commit(std::size_t offset, std::size_t bytes) noexcept {
    if (!impl_) return false;
    try {
        return impl_->Commit(offset, bytes);
    } catch (...) {
        std::abort();
    }
}
bool Runtime::Clear(std::size_t offset, std::size_t bytes,
                    std::uint32_t fill) noexcept {
    if (!impl_) return false;
    try {
        return impl_->Clear(offset, bytes, fill);
    } catch (...) {
        std::abort();
    }
}
bool Runtime::EnsureReadable(std::size_t offset, std::size_t bytes) noexcept {
    return impl_ && impl_->EnsureReadable(offset, bytes);
}
void Runtime::ReleaseFreed(std::size_t offset, std::size_t bytes) noexcept {
    if (impl_) impl_->ReleaseFreed(offset, bytes);
}
bool Runtime::HandleWriteFault(void* address) noexcept {
    return impl_ && impl_->PromoteFault(address);
}
bool Runtime::Install() noexcept {
    std::lock_guard lock{registry_mutex};
    if (!Valid() || active_guest || !InstallGuestSignal()) return false;
    active_guest = this;
    active_guest_signal.store(this, std::memory_order_release);
    impl_->installed = true;
    return true;
}
void Runtime::Uninstall() noexcept {
    {
        std::lock_guard lock{registry_mutex};
        if (active_guest == this) {
            active_guest_signal.store(nullptr, std::memory_order_release);
            active_guest = nullptr;
        }
        if (impl_) impl_->installed = false;
    }
    while (signal_users.load(std::memory_order_acquire) != 0) {}
}

} // namespace Eden::PS5::GuestBacking

extern "C" bool EdenNs2CommitGuestBacking(const void* backing_base,
                                            std::size_t offset,
                                            std::size_t bytes) noexcept {
    std::lock_guard lock{Eden::PS5::GuestBacking::registry_mutex};
    auto* const owner = Eden::PS5::GuestBacking::active_guest;
    if (!owner) return true;
    if (owner->Base() != backing_base) return false;
    return owner->Commit(offset, bytes);
}

extern "C" bool EdenNs2EnsureGuestBackingReadable(const void* backing_base,
                                                    std::size_t offset,
                                                    std::size_t bytes) noexcept {
    std::lock_guard lock{Eden::PS5::GuestBacking::registry_mutex};
    auto* const owner = Eden::PS5::GuestBacking::active_guest;
    if (!owner) return true;
    if (owner->Base() != backing_base) return false;
    return owner->EnsureReadable(offset, bytes);
}

extern "C" void EdenNs2GuestBackingFreed(std::size_t offset,
                                          std::size_t bytes) noexcept {
    std::lock_guard lock{Eden::PS5::GuestBacking::registry_mutex};
    auto* const owner = Eden::PS5::GuestBacking::active_guest;
    if (owner) owner->ReleaseFreed(offset, bytes);
}
