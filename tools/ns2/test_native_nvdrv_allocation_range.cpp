// SPDX-License-Identifier: GPL-3.0-or-later
// Exercise the exact NS2 NVDRV fixed/remap allocation-range helper.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <map>
#include <random>
#include "core/hle/service/nvdrv/devices/native_gpu_allocation_range.h"

using u64 = std::uint64_t;
using Service::Nvidia::Devices::NativeGpuAllocation::FindContaining;
using Service::Nvidia::Devices::NativeGpuAllocation::ContainsSubrange;
static_assert(ContainsSubrange(0x4000,0x1000,0x3000));
static_assert(!ContainsSubrange(0x4000,0x1000,0x3001));
static_assert(!ContainsSubrange(0x4000,0x4000,1));
static_assert(!ContainsSubrange(0x4000,0,0));
static_assert(!ContainsSubrange(UINT64_MAX,UINT64_MAX,2));
struct Allocation { u64 size; };
using Allocations = std::map<u64, Allocation>;
static constexpr u64 Limit = u64{1} << 49;

static Allocations::iterator Oracle(Allocations& blocks, u64 address, u64 bytes) {
    if (!bytes || address >= Limit || bytes > Limit - address) return blocks.end();
    for (auto it = blocks.begin(); it != blocks.end(); ++it) {
        if (it->first >= Limit || it->second.size > Limit - it->first) continue;
        if (address < it->first) continue;
        const u64 offset = address - it->first;
        if (offset < it->second.size && bytes <= it->second.size - offset)
            return it;
    }
    return blocks.end();
}

static void Check(Allocations& blocks, u64 address, u64 bytes) {
    const auto previous_size = blocks.size();
    const auto actual = FindContaining(blocks, address, bytes);
    const auto expected = Oracle(blocks, address, bytes);
    assert((actual == blocks.end()) == (expected == blocks.end()));
    if (actual != blocks.end()) assert(actual->first == expected->first);
    assert(blocks.size() == previous_size);
}

int main() {
    Allocations empty;
    Check(empty, 0, 4096);
    Check(empty, (std::numeric_limits<u64>::max)(), 4096);
    Check(empty, 4096, 0);
    Allocations blocks;
    blocks.emplace(0x10000, Allocation{0x4000});
    blocks.emplace(0x30000, Allocation{0x8000});
    blocks.emplace(0x50000, Allocation{0x1000});
    // Empty/before-begin, after-end, gaps, exact start/end, and overflow.
    for (u64 address : {u64{0}, u64{0xffff}, u64{0x10000},
         u64{0x13fff}, u64{0x14000}, u64{0x2ffff},
         u64{0x30000}, u64{0x37fff}, u64{0x38000},
         u64{0x50000}, u64{0x50fff}, u64{0x51000},
         Limit-1, Limit, Limit+1, (std::numeric_limits<u64>::max)()}) {
        for (u64 bytes : {u64{0}, u64{1}, u64{4096}, u64{0x4000},
                          u64{0x8000}, (std::numeric_limits<u64>::max)()})
            Check(blocks, address, bytes);
    }
    // A forged reservation crossing the GPU VA boundary is never valid.
    blocks.emplace(Limit-0x1000, Allocation{0x2000});
    Check(blocks, Limit-0x1000, 1);
    blocks.erase(Limit-0x1000);
    blocks.emplace(Limit-0x4000, Allocation{0x4000});
    Check(blocks, Limit-0x4000, 0x4000);
    Check(blocks, Limit-0x4000, 0x4001);

    std::mt19937_64 rng{0xA9B74C132ULL};
    for (int i=0;i<15000;++i) {
        // Adjacent, missing, shortened and oversized native ioctl ranges.
        const u64 index = rng() % 9;
        const u64 start = 0x10000 + (index * 0x10000);
        if (i%3==0)
            blocks.insert_or_assign(start, Allocation{(1+(rng()%12))*4096});
        else if (i%17==0) blocks.erase(start);
        const u64 address = (i%11==0) ? rng()
            : (start + (rng()%0x10000));
        const u64 length = (i%23==0)
            ? (std::numeric_limits<u64>::max)() : (rng()%0x20001);
        Check(blocks, address, length);
    }
    std::puts("P1_2_NVDRV_ALLOCATION_RANGE_HOST_PASS");
}
