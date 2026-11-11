// SPDX-License-Identifier: GPL-3.0-or-later
// The EXACT PS5 Runtime TU is linked with mocked syscall ownership, not a
// reimplementation of its transactions. No real PS5 mapping is claimed.
#include "ns2_sparse_guest.h"
#include "ps5_ns2_guest_backing_plan.h"
#include <cassert>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
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
extern "C" std::int32_t sceKernelReleaseDirectMemory(std::int64_t pa, std::size_t bytes) {
    assert(bytes == kGranule);
    assert(alive.count(pa) && alive[pa]);
    alive[pa] = false;
    ++released;
    return 0;
}

int main() {
    assert(EdenNs2CommitGuestBacking(nullptr,0,kGranule)); // NS1 no active owner
    {
        Runtime guest(kNs2Dram,5*kGranule);
        assert(guest.Valid() && guest.VirtualBytes()==kNs2Dram);
        assert(guest.Install());
        auto* base = static_cast<std::uint8_t*>(guest.Base());
        assert(!EdenNs2CommitGuestBacking(nullptr,0,kGranule)); // wrong owner
        assert(!guest.Commit(kNs2Dram-1,2));
        assert(!guest.Commit(0,6*kGranule)); // budget fail before first mapping
        assert(guest.UsedBytes()==0 && successful_commits==0);
        assert(EdenNs2CommitGuestBacking(base,0,kGranule+1));
        assert(successful_commits==2 && guest.UsedBytes()==2*kGranule);
        base[kGranule-2]=0xA2; base[kGranule+2]=0xB3;
        assert(guest.Commit(1,kGranule+2)); // existing PA remains owned
        assert(successful_commits==2 && base[kGranule-2]==0xA2);
        assert(EdenNs2CommitGuestBacking(base,kNs2Dram-1,1));
        assert(base[kNs2Dram-1]==0); base[kNs2Dram-1]=0xC5;
        assert(guest.UsedBytes()==3*kGranule);
        fail_at = successful_commits+1;
        assert(!guest.Commit(3*kGranule,2*kGranule)); // second PA fails
        assert(guest.UsedBytes()==3*kGranule);
        assert(released==1); // rollback: exact newly staged piece
        fail_at=-1;
        assert(guest.Commit(3*kGranule,kGranule)); // zero-filled retry
        assert(base[3*kGranule]==0);
        assert(guest.UsedBytes()==4*kGranule);
        assert(guest.Commit(4*kGranule,kGranule));
        assert(guest.UsedBytes()==5*kGranule);
        assert(!guest.Commit(6*kGranule,kGranule)); // hard budget
        assert(base[kGranule-2]==0xA2 && base[kGranule+2]==0xB3);
        assert(base[kNs2Dram-1]==0xC5);
        guest.Uninstall();
        assert(EdenNs2CommitGuestBacking(nullptr,0,kGranule));
    }
    assert(released==6); // 1 rolled back + 5 committed at teardown
    for (const auto& [pa,live]:alive) assert(!live);
    std::puts("R457_PS5_SPARSE_GUEST_REAL_OWNER_MOCK_PASS");
}
