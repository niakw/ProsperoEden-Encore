// SPDX-License-Identifier: GPL-3.0-or-later
// Exact native owner linked against host mocks: shared ZERO aliases, SIGSEGV
// promotion to OWN, budget rollback and teardown ownership.
#include "ns2_sparse_guest.h"
#include "ps5_ns2_guest_backing_plan.h"
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <sys/mman.h>

using Eden::PS5::GuestBacking::Runtime;
using Eden::PS5::GuestBacking::kGranule;
using Eden::PS5::GuestBacking::kNs2Dram;
static std::int64_t pa_next = 0;
static int successful_commits = 0, released = 0, fail_at = -1;
static std::map<std::int64_t,bool> alive;

namespace Common {
void* ReserveMemoryRange(std::size_t bytes) noexcept {
    auto* p = mmap(nullptr,bytes,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_NORESERVE,-1,0);
    return p == MAP_FAILED ? nullptr : p;
}
bool CommitMemoryRange(void* at, std::size_t bytes, std::int64_t* physical) noexcept {
    if (fail_at == successful_commits) return false;
    void* p = mmap(at,bytes,PROT_READ|PROT_WRITE,
                   MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
    if (p != at) return false;
    pa_next += static_cast<std::int64_t>(kGranule);
    *physical = pa_next;
    assert(alive.emplace(pa_next,true).second);
    ++successful_commits;
    std::memset(at,0,bytes);
    return true;
}
}
extern "C" std::int32_t sceKernelEnableDmemAliasing() { return 0; }
extern "C" std::int32_t sceKernelMapDirectMemory(void** at, std::size_t bytes,
                                                   int protection, int,
                                                   std::int64_t physical,
                                                   std::size_t alignment) {
    assert(bytes == kGranule && alignment == kGranule);
    assert(alive.count(physical) && alive[physical]);
    void* mapped = mmap(*at,bytes,protection,
                        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
    return mapped == *at ? 0 : -1;
}
extern "C" std::int32_t sceKernelReleaseDirectMemory(std::int64_t pa, std::size_t bytes) {
    assert(bytes == kGranule);
    assert(alive.count(pa) && alive[pa]);
    alive[pa] = false;
    ++released;
    return 0;
}

int main() {
    assert(EdenNs2CommitGuestBacking(nullptr,0,kGranule));
    assert(EdenNs2EnsureGuestBackingReadable(nullptr,0,kGranule));
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

        assert(guest.Clear(2*kGranule+17,4096,0));
        assert(successful_commits==2 && guest.UsedBytes()==kGranule);
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
        assert(!guest.Commit(3*kGranule,2*kGranule));
        fail_at=-1;
        assert(guest.UsedBytes()==2*kGranule);
        assert(base[3*kGranule]==0 && base[4*kGranule]==0);
        assert(released==1);

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
    for (const auto& [pa,live]:alive) assert(!live);
    // one rolled-back OWN + four live OWN + one shared ZERO.
    assert(released==6);
    std::puts("R457_PS5_DEMAND_ZERO_GUEST_REAL_OWNER_MOCK_PASS");
}
