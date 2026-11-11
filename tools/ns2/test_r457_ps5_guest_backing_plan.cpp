// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only R457 NS2 12GiB virtual admission / segmented physical ownership.
// This is NOT an emulator or a PS5 direct-memory syscall test.
#include "ps5_ns2_guest_backing_plan.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
using namespace Eden::PS5::GuestBacking;

int main() {
    constexpr auto G = kGranule;
    constexpr auto D = kNs2Dram;
    Plan plan(D, 4ull << 30);
    assert(plan.Valid() && plan.ChunkCount() == 6144);
    assert(plan.VirtualBytes() == D && plan.UsedBytes() == 0);
    assert(!plan.Begin(D - 1, G)); // unaligned
    assert(!plan.Begin(D - G, 2 * G)); // out of bounds
    assert(!plan.Begin(1, G)); // unaligned
    assert(!plan.Begin(0, 0));
    auto first = plan.Begin(0, 2 * G);
    assert(first && first->newcomers == 2);
    assert(!plan.Begin(D - G, G)); // no concurrent mutations
    assert(!plan.Publish(*first)); // hardware ownership not staged
    assert(plan.Stage(*first, 0, 0));
    assert(!plan.Stage(*first, 1, 0)); // no duplicated direct-memory owner
    assert(plan.Stage(*first, 1, 2 * G)); // physically NON-contiguous
    assert(plan.Publish(*first));
    assert(plan.At(0).state == State::Resident && plan.UsedBytes() == 2 * G);
    auto second = plan.Begin(D - G, G);
    assert(second && second->newcomers == 1);
    assert(plan.Stage(*second, 6143, 20 * G));
    assert(plan.Publish(*second)); // both ends of 12GiB VA range possible
    assert(plan.UsedBytes() == 3 * G);
    auto mixed = plan.Begin(0, 3 * G);
    assert(mixed && mixed->newcomers == 1); // preserve two resident chunks
    assert(plan.Stage(*mixed, 2, 30 * G));
    auto release = plan.Abort(*mixed);
    assert(release && release->size() == 1);
    assert(release->at(0).index == 2 && release->at(0).physical == 30 * G);
    assert(!plan.Publish(*mixed)); // retiring chunks never become residents
    assert(!plan.FinishAbort(*mixed)); // owner unmap/release not acknowledged
    assert(!plan.ReleaseAcknowledged(*mixed, 2, 40 * G));
    assert(plan.ReleaseAcknowledged(*mixed, 2, 30 * G));
    assert(plan.FinishAbort(*mixed));
    assert(plan.UsedBytes() == 3 * G && plan.At(0).state == State::Resident);
    auto already = plan.Begin(0, G);
    assert(already && already->newcomers == 0);
    assert(plan.Publish(*already));

    Plan budget(D, 2 * G);
    assert(!budget.Begin(0, 3 * G));
    assert(budget.UsedBytes() == 0); // failed allocation changes no ownership
    auto partial = budget.Begin(0, 2 * G);
    assert(partial && partial->newcomers == 2);
    assert(budget.Stage(*partial, 0, 0));
    auto rollback = budget.Abort(*partial);
    assert(rollback && rollback->size() == 1);
    assert(budget.UsedBytes() == G);
    assert(!budget.FinishAbort(*partial));
    assert(budget.ReleaseAcknowledged(*partial, 0, 0));
    assert(budget.FinishAbort(*partial));
    assert(budget.UsedBytes() == 0);
    assert(!Plan(D + G, D).Valid()); // validation rejects improper budgets
    std::cout << "R457_NS2_GUEST_BACKING_ACCOUNTING_PASS\n";
}
