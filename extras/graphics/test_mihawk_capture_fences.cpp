// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_capture_fences.h"
#include <cassert>
#include <cstdint>

using namespace Eden::FeatureLab;
int main() {
    MihawkCaptureFences gate{};
    std::uint64_t completed = 0;
    auto is_free = [&](std::uint64_t serial) { return serial <= completed; };
    auto p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 0 && p.previous_gpu_tick == 0);
    assert(!gate.Acquire(is_free).valid); // only one pending command buffer
    assert(gate.Commit(p, 1));
    assert(gate.BusyUntil(0) == 1 && !gate.Pending());
    p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 1);
    assert(gate.Commit(p, 2));
    assert(gate.BusyUntil(1) == 2);
    assert(!gate.Acquire(is_free).valid); // GPU still reads snapshot slot 0
    completed = 1;
    p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 0 && p.previous_gpu_tick == 1);
    gate.AbortUnsubmitted(); // not queued: does not take a GPU serial
    assert(gate.BusyUntil(0) == 1 && gate.LatestGpuTick() == 2);
    p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 0);
    assert(gate.Commit(p, 4)); // unrelated GPU work may advance ticks
    assert(gate.BusyUntil(0) == 4 && gate.LatestGpuTick() == 4);
    assert(!gate.Acquire(is_free).valid); // slot 1 still not free
    completed = 2;
    p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 1);
    assert(!gate.Commit(p, 3)); // GPU submission tick regressed
    assert(gate.Quarantined() && !gate.Acquire(is_free).valid);
    gate.ResetAfterDeviceIdle();
    assert(!gate.Quarantined() && gate.LatestGpuTick() == 0);
    p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 0);
    assert(!gate.Commit(p, 0)); // missing actual tick is never accepted
    assert(gate.Quarantined());

    // Full sequence: generation holds old history + output until real
    // scheduler tick. Skipping a guest source frame invalidates the pair.
    gate.ResetAfterDeviceIdle();
    completed = 0;
    p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 0);
    assert(!gate.CanGenerate(p, 1, is_free));
    assert(gate.Commit(p, 8, 1, false));
    completed = 8;
    p = gate.Acquire(is_free);
    assert(p.valid && p.slot == 1);
    assert(gate.CanGenerate(p, 2, is_free));
    assert(!gate.CanGenerate(p, 3, is_free)); // frame ID gap
    assert(gate.Commit(p, 9, 2, true));
    assert(gate.BusyUntil(0) == 9 && gate.BusyUntil(1) == 9);
    assert(gate.OutputBusyUntil() == 9);
    completed = 8;
    assert(!gate.Acquire(is_free).valid); // old history still sampled by GPU
    completed = 9;
    p = gate.Acquire(is_free);
    assert(gate.CanGenerate(p, 3, is_free));
    assert(gate.Commit(p, 10, 3, true));
    completed = 10;
    p = gate.Acquire(is_free);
    assert(!gate.CanGenerate(p, 5, is_free)); // dropped frame 4
    assert(gate.Commit(p, 11, 5, false));
    completed = 11;
    p = gate.Acquire(is_free);
    assert(gate.CanGenerate(p, 6, is_free));
    gate.AbortUnsubmitted();

}
