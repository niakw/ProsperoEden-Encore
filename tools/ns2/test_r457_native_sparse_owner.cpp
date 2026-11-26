// SPDX-License-Identifier: GPL-3.0-or-later
// Exact native owner linked against host mocks: shared ZERO aliases, SIGSEGV
// promotion to OWN, budget rollback and teardown ownership.
#include "ns2_sparse_guest.h"
#include "ps5_ns2_guest_backing_plan.h"
#include <cassert>
#include <csignal>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <sys/mman.h>

using Eden::PS5::GuestBacking::Runtime;
using Eden::PS5::GuestBacking::kGranule;
using Eden::PS5::GuestBacking::kNs2Dram;
// These witnesses are touched from the SIGSEGV promotion path. Keep the
// mock signal-observable and allocation-free: a normal int/std::map makes the
// test itself undefined at -O1 even when the runtime correctly retries the
// faulting write.
static constexpr std::size_t kMaxMockOwners = 32;
static volatile std::sig_atomic_t next_physical_slot = 0;
static volatile std::sig_atomic_t successful_commits = 0;
static volatile std::sig_atomic_t released = 0;
static volatile std::sig_atomic_t fail_at = -1;
static volatile std::sig_atomic_t destructive_fail = 0;
static volatile std::sig_atomic_t alive[kMaxMockOwners]{};

static std::size_t OwnerSlot(std::int64_t physical) noexcept {
    assert(physical > 0 &&
           (static_cast<std::uint64_t>(physical) % kGranule) == 0);
    const auto slot = static_cast<std::size_t>(
        static_cast<std::uint64_t>(physical) / kGranule);
    assert(slot < kMaxMockOwners);
    return slot;
}

namespace Common {
void* ReserveMemoryRange(std::size_t bytes) noexcept {
    auto* p = mmap(nullptr,bytes,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_NORESERVE,-1,0);
    return p == MAP_FAILED ? nullptr : p;
}
// The host model exercises ZERO/OWN lifecycle independently of PS5 VA hints.
void* ReserveGuestMemoryRange(std::size_t bytes) noexcept {
    return ReserveMemoryRange(bytes);
}
bool CommitMemoryRange(void* at, std::size_t bytes, std::int64_t* physical) noexcept {
    if (fail_at == successful_commits) {
        if (destructive_fail) {
            void* hole = mmap(at,bytes,PROT_NONE,
                              MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
            assert(hole == at);
        }
        return false;
    }
    void* p = mmap(at,bytes,PROT_READ|PROT_WRITE,
                   MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
    if (p != at) return false;
    const auto slot = static_cast<std::size_t>(next_physical_slot) + 1;
    next_physical_slot = static_cast<std::sig_atomic_t>(slot);
    assert(slot < kMaxMockOwners && alive[slot] == 0);
    *physical = static_cast<std::int64_t>(slot * kGranule);
    alive[slot] = 1;
    successful_commits =
        static_cast<std::sig_atomic_t>(successful_commits + 1);
    // MAP_ANONYMOUS supplies zero-filled pages, matching the production
    // CommitMemoryRange postcondition without invoking allocator-backed mocks.
    return true;
}
}
extern "C" std::int32_t sceKernelEnableDmemAliasing() { return 0; }
extern "C" std::int32_t sceKernelMapDirectMemory(void** at, std::size_t bytes,
                                                   int protection, int,
                                                   std::int64_t physical,
                                                   std::size_t alignment) {
    assert(bytes == kGranule && alignment == kGranule);
    const auto slot = OwnerSlot(physical);
    assert(alive[slot] != 0);
    void* mapped = mmap(*at,bytes,protection,
                        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
    return mapped == *at ? 0 : -1;
}
extern "C" std::int32_t sceKernelReleaseDirectMemory(std::int64_t pa, std::size_t bytes) {
    assert(bytes == kGranule);
    const auto slot = OwnerSlot(pa);
    assert(alive[slot] != 0);
    alive[slot] = 0;
    released = static_cast<std::sig_atomic_t>(released + 1);
    return 0;
}

int main() {
    // The ownership/accounting model is generation-neutral. Validate every
    // guest DRAM layout accepted by NS1/NS2 before exercising the exact
    // native ZERO/OWN runtime below.
    constexpr std::uint64_t GiB = 1ull << 30;
    constexpr std::uint64_t layouts[] = {
        4ull * GiB, 6ull * GiB, 8ull * GiB, 10ull * GiB, 12ull * GiB,
    };
    for (const auto bytes : layouts) {
        const auto budget = bytes < 6ull * GiB ? bytes : 6ull * GiB;
        Eden::PS5::GuestBacking::Plan plan(bytes, budget);
        assert(plan.Valid());
        assert(plan.VirtualBytes() == bytes);
        assert(plan.ChunkCount() == bytes / kGranule);
        assert(plan.BudgetBytes() == budget);
        assert(plan.UsedBytes() == 0);
    }

    assert(EdenNs2CommitGuestBacking(nullptr,0,kGranule));
    assert(EdenNs2EnsureGuestBackingReadable(nullptr,0,kGranule));

    // Execute the real native owner for every NS1 DRAM layout, not only the
    // accounting Plan. Exercise both the first and last native granule so a
    // layout-size error cannot hide behind the low-address ZERO/OWN path.
    constexpr std::uint64_t ns1_layouts[] = {
        4ull * GiB, 6ull * GiB, 8ull * GiB, 10ull * GiB,
    };
    for (const auto bytes : ns1_layouts) {
        next_physical_slot = 0;
        successful_commits = 0;
        released = 0;
        fail_at = -1;
        destructive_fail = 0;

        const auto budget = bytes < 6ull * GiB ? bytes : 6ull * GiB;
        {
            Runtime ns1_guest(bytes, budget);
            assert(ns1_guest.Valid() && ns1_guest.VirtualBytes() == bytes);
            assert(successful_commits == 1); // one shared ZERO physical block
            assert(ns1_guest.UsedBytes() == 0);
            auto* ns1_base = static_cast<std::uint8_t*>(ns1_guest.Base());
            const auto tail = static_cast<std::size_t>(bytes - kGranule + 128);
            assert(ns1_base[0] == 0 && ns1_base[tail] == 0);
            assert(ns1_guest.Install());
            assert(EdenNs2EnsureGuestBackingReadable(ns1_base, 0, bytes));

            ns1_base[128] = 0x4A;
            ns1_base[tail] = 0x6C;
            assert(ns1_base[128] == 0x4A && ns1_base[tail] == 0x6C);
            assert(ns1_guest.UsedBytes() == 2 * kGranule);
            assert(successful_commits == 3);

            EdenNs2GuestBackingFreed(0, kGranule);
            EdenNs2GuestBackingFreed(bytes - kGranule, kGranule);
            assert(ns1_guest.UsedBytes() == 0);
            assert(ns1_base[128] == 0 && ns1_base[tail] == 0);
            assert(released == 2);
            ns1_guest.Uninstall();
        }
        assert(released == 3); // two private OWN blocks + shared ZERO
        for (std::size_t slot = 1; slot < kMaxMockOwners; ++slot)
            assert(alive[slot] == 0);
    }

    // Reset mock accounting so the long NS2 transaction below keeps its
    // historical exact counters and rollback assertions.
    next_physical_slot = 0;
    successful_commits = 0;
    released = 0;
    fail_at = -1;
    destructive_fail = 0;

    {
        Runtime guest(kNs2Dram,5*kGranule);
        assert(guest.Valid() && guest.VirtualBytes()==kNs2Dram);
        assert(successful_commits==1); // one shared ZERO physical block
        assert(guest.UsedBytes()==0);
        auto* base=static_cast<std::uint8_t*>(guest.Base());
        assert(base[0]==0 && base[4*kGranule+123]==0);
        assert(guest.Install());
        assert(!EdenNs2EnsureGuestBackingReadable(nullptr,0,kGranule));
        assert(EdenNs2EnsureGuestBackingReadable(base,0,kNs2Dram));
        assert(successful_commits==1); // PTE/readability takes no OWN block

        // First write faults on the read-only ZERO alias. The handler maps
        // a private zeroed block and the faulting instruction repeats.
        base[64]=0x7A;
        assert(base[64]==0x7A);
        assert(guest.UsedBytes()==kGranule);
        assert(successful_commits==2);

        // Once the guest page heap proves this whole 2 MiB block free, the
        // private PA returns to the pool and the bytes read as ZERO again.
        EdenNs2GuestBackingFreed(0,kGranule);
        assert(guest.UsedBytes()==0);
        assert(base[64]==0);
        const auto after_free=successful_commits;
        base[64]=0x31;
        if (base[64] != 0x31 || successful_commits != after_free + 1) {
            std::fprintf(stderr,
                         "R457_REPROMOTE_DIAG value=%u commits=%d after_free=%d used=%llu\n",
                         static_cast<unsigned>(base[64]), successful_commits, after_free,
                         static_cast<unsigned long long>(guest.UsedBytes()));
        }
        assert(base[64]==0x31);
        assert(successful_commits==after_free+1);
        assert(guest.UsedBytes()==kGranule);

        assert(guest.Clear(2*kGranule+17,4096,0));
        const auto after_repromote=successful_commits;
        assert(after_repromote==after_free+1 && guest.UsedBytes()==kGranule);
        assert(base[2*kGranule+17]==0);

        // Mixed ZERO/OWN zero clear must not promote the untouched neighbor.
        base[kGranule-16]=0x52; // still the first OWN chunk
        const auto before_mixed=successful_commits;
        assert(guest.Clear(kGranule-32,64,0));
        assert(base[kGranule-16]==0);
        assert(successful_commits==before_mixed && guest.UsedBytes()==kGranule);

        // Nonzero fill needs writable backing and is performed by the owner.
        assert(guest.Clear(2*kGranule+17,4096,0x45));
        assert(guest.UsedBytes()==2*kGranule);
        assert(base[2*kGranule+17]==0x45);

        // Failed two-chunk admission restores every new chunk to ZERO.
        const auto before=successful_commits;
        fail_at=before+1;
        destructive_fail=true; // emulate MAP_FIXED failure that damaged VA
        assert(!guest.Commit(3*kGranule,2*kGranule));
        fail_at=-1;
        destructive_fail=false;
        assert(guest.UsedBytes()==2*kGranule);
        // Both the staged first chunk and the destructively failed second
        // chunk must again be readable ZERO aliases after rollback.
        assert(base[3*kGranule]==0 && base[4*kGranule]==0);
        // One PA was returned by the earlier page-heap OWN->ZERO,
        // and the newly staged chunk was returned by this failed admission.
        assert(released==2);

        assert(guest.Commit(3*kGranule,kGranule));
        assert(guest.UsedBytes()==3*kGranule);
        base[3*kGranule]=0xC5;
        assert(base[3*kGranule]==0xC5);
        assert(guest.Commit(4*kGranule,kGranule));
        assert(guest.UsedBytes()==4*kGranule);
        assert(!guest.Commit(5*kGranule,2*kGranule));
        assert(guest.UsedBytes()==4*kGranule);

        guest.Uninstall();
        assert(EdenNs2CommitGuestBacking(nullptr,0,kGranule));
    }
    for (std::size_t slot=1; slot<kMaxMockOwners; ++slot)
        assert(alive[slot] == 0);
    // one page-heap return + one rolled-back OWN + four live OWN + shared ZERO.
    assert(released==7);
    std::puts("R457_PS5_DEMAND_ZERO_GUEST_REAL_OWNER_MOCK_PASS");
}
