// SPDX-FileCopyrightText: Copyright 2026 Eden Encore Project
// SPDX-License-Identifier: GPL-3.0-or-later
// Execute the real native DMA fetch admission helper using a mutable GMMU.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <set>
#include "core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h"

using Service::Nvidia::Devices::NativeGpfifoFetchMapped;

struct FakeGmmu {
    static constexpr std::uint64_t PageSize=4096;
    std::set<std::uint64_t> pages{};
    unsigned probes{};
    bool IsFullyMappedRange(std::uint64_t address,std::uint64_t size) {
        ++probes;
        assert(size && address);
        const auto first=address/PageSize;
        const auto last=(address+size-1)/PageSize;
        for (auto page=first; page<=last; ++page)
            if (!pages.contains(page)) return false;
        return true;
    }
};

int main() {
    constexpr std::uint64_t high=std::uint64_t{1}<<49;
    FakeGmmu memory;
    const auto callback=[&](std::uint64_t address,std::uint64_t size) {
        return memory.IsFullyMappedRange(address,size);
    };
    // Fence-only commands perform no GPU memory read.
    assert(NativeGpfifoFetchMapped(0,0,callback) && memory.probes==0);
    assert(NativeGpfifoFetchMapped(0x1000,0,callback) && memory.probes==0);
    // Nonempty malformed ranges must fail before the actual GMMU walker.
    assert(!NativeGpfifoFetchMapped(0,1,callback));
    assert(!NativeGpfifoFetchMapped(high,1,callback));
    assert(!NativeGpfifoFetchMapped(high-2,1,callback));
    assert(!NativeGpfifoFetchMapped(high-4,2,callback));
    assert(!NativeGpfifoFetchMapped(~std::uint64_t{0},~std::uint64_t{0},callback));
    assert(!NativeGpfifoFetchMapped(0x1000,~std::uint64_t{0},callback));
    assert(memory.probes==0);
    // Submit-time mapping does NOT guarantee execution-time mapping.
    memory.pages={1,2};
    assert(NativeGpfifoFetchMapped(0x1ffc,2,callback) && memory.probes==1);
    memory.pages.erase(2);
    assert(!NativeGpfifoFetchMapped(0x1ffc,2,callback) && memory.probes==2);
    // Unmapped packets cannot be interpreted as 0x00000000 commands.
    assert(!NativeGpfifoFetchMapped(0x2ffc,2,callback) && memory.probes==3);
    memory.pages.insert(2);
    memory.pages.insert(3);
    assert(NativeGpfifoFetchMapped(0x2ffc,2,callback) && memory.probes==4);
    // The uppermost word is in-bounds only when mapped.
    memory.pages.insert((high-4)/4096);
    assert(NativeGpfifoFetchMapped(high-4,1,callback));
    // Submission-time unmapped, execution-time newly mapped: permitted.
    memory.pages.erase(1);
    assert(!NativeGpfifoFetchMapped(0x1000,1,callback));
    memory.pages.insert(1);
    assert(NativeGpfifoFetchMapped(0x1000,1,callback));
    std::puts("P2_7_REAL_NATIVE_GPFIFO_FETCH_RECHECK_PASS");
}
