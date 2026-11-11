// SPDX-License-Identifier: GPL-3.0-or-later
// Linux proof only: 12 GiB continuous VIRTUAL address range, independent
// 2 MiB file-backed physical ownership, real page access and rollback.
// This does not emulate PS5 kernel syscalls, RADV or fastmem aliases.
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
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
#include <unistd.h>

using namespace Eden::PS5::GuestBacking;
constexpr std::size_t G = static_cast<std::size_t>(kGranule);

int main() {
    Plan plan(kNs2Dram, 16 * kGranule);
    assert(plan.Valid() && plan.ChunkCount() == 6144);
    void* reserve = mmap(nullptr, static_cast<std::size_t>(kNs2Dram),
                         PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
    if (reserve == MAP_FAILED) {
        std::perror("virtual reserve");
        return 2;
    }
    auto* base = static_cast<std::uint8_t*>(reserve);
    std::map<std::size_t, int> owners;

    const auto map_piece = [&](const Lease& lease, std::size_t index, std::int64_t owner) {
        const int fd = memfd_create("encore-ns2-chunk", MFD_CLOEXEC);
        if (fd < 0) return false;
        if (ftruncate(fd, static_cast<off_t>(G)) != 0) {
            close(fd);
            return false;
        }
        void* address = base + index * G;
        const void* mapped = mmap(address, G, PROT_READ | PROT_WRITE,
                                  MAP_SHARED | MAP_FIXED, fd, 0);
        if (mapped == MAP_FAILED || mapped != address) {
            close(fd);
            return false;
        }
        if (!plan.Stage(lease, index, owner)) {
            // Undo the mapping before disposing of its physical owner.
            void* hole = mmap(address, G, PROT_NONE,
                              MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE | MAP_FIXED, -1, 0);
            assert(hole == address);
            close(fd);
            return false;
        }
        owners.emplace(index, fd);
        return true;
    };

    const auto retire_piece = [&](const Lease& lease, const Reclaim& piece) {
        assert(owners.count(piece.index) == 1);
        void* address = base + piece.index * G;
        // Keep the 12 GiB VA reservation intact when withdrawing a chunk.
        void* hole = mmap(address, G, PROT_NONE,
                          MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE | MAP_FIXED, -1, 0);
        assert(hole == address);
        close(owners.at(piece.index));
        owners.erase(piece.index);
        assert(plan.ReleaseAcknowledged(lease, piece.index, piece.physical));
    };

    // Two independent file-backed owners at adjacent 2 MiB guest addresses.
    auto first = plan.Begin(0, 2 * kGranule);
    assert(first && first->newcomers == 2);
    assert(map_piece(*first, 0, 2 * kGranule));
    assert(map_piece(*first, 1, 12 * kGranule));
    assert(plan.Publish(*first));

    // Access crosses the 2 MiB boundary with no change in guest pointer.
    for (int i = 0; i < 8; ++i) base[G - 4 + i] = static_cast<std::uint8_t>(0xA0 + i);
    for (int i = 0; i < 8; ++i) assert(base[G - 4 + i] == 0xA0 + i);
    assert(base[16384 - 1] == 0); // untouched 16 KiB native granule is zero-filled

    // The final address of the 12 GiB guest range works without committing
    // the 6141 intervening physical chunks.
    auto last = plan.Begin(kNs2Dram - kGranule, kGranule);
    assert(last && map_piece(*last, 6143, 24 * kGranule));
    assert(plan.Publish(*last));
    base[kNs2Dram - 1] = 0x5B;
    assert(base[kNs2Dram - 1] == 0x5B);

    // Simulate failure after committing one part of a two-part admission.
    auto pending = plan.Begin(2 * kGranule, 2 * kGranule);
    assert(pending && pending->newcomers == 2);
    assert(map_piece(*pending, 2, 36 * kGranule));
    base[2 * G] = 0xBE;
    auto rollback = plan.Abort(*pending);
    assert(rollback && rollback->size() == 1);
    assert(!plan.FinishAbort(*pending));
    for (const auto& owner : *rollback) retire_piece(*pending, owner);
    assert(plan.FinishAbort(*pending));
    assert(plan.At(2).state == State::Unmapped && owners.count(2) == 0);
    assert(base[G - 4] == 0xA0 && base[kNs2Dram - 1] == 0x5B);
    assert(plan.UsedBytes() == 3 * kGranule);

    // The same abandoned slot can be admitted again without a stale owner.
    auto retry = plan.Begin(2 * kGranule, kGranule);
    assert(retry && map_piece(*retry, 2, 44 * kGranule));
    assert(plan.Publish(*retry));
    assert(base[2 * G] == 0); // a new backing starts zeroed
    assert(owners.size() == 4);
    for (auto [index, fd] : owners) {
        (void)index;
        assert(close(fd) == 0);
    }
    assert(munmap(reserve, static_cast<std::size_t>(kNs2Dram)) == 0);
    std::puts("R457_NS2_LINUX_SEGMENTED_VIRTUAL_12GIB_PASS");
}
