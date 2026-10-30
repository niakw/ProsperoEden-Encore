// SPDX-License-Identifier: GPL-3.0-or-later
// N3n: process-scoped NS2 GPU shader compiler auth tickets.
#include <atomic>
#include <cassert>
#include <cstdio>
#include <thread>
#include <vector>
#include "core/hle/service/nvdrv/devices/native_gpu_process_registry.h"

namespace Kernel { class KProcess {}; }
using Service::Nvidia::Devices::NativeGpuProcessRegistry;

int main() {
    auto& registry = NativeGpuProcessRegistry::Instance();
    Kernel::KProcess a{}, b{}, c{};
    assert(registry.Count() == 0);
    assert(!registry.Register(nullptr));
    assert(!registry.CaptureTicket(nullptr));
    assert(!registry.CaptureTicket(&a));
    assert(!registry.IsCurrent({&a, 0}));

    assert(registry.Register(&a));
    const auto ticket_a = registry.CaptureTicket(&a);
    assert(ticket_a && registry.IsCurrent(*ticket_a));
    assert(!registry.IsCurrent({&b, ticket_a->generation}));
    assert(registry.Register(&a));
    registry.Unregister(&a);
    assert(registry.IsCurrent(*ticket_a)); // second live GPU worker
    assert(registry.Register(&b));
    const auto ticket_b = registry.CaptureTicket(&b);
    assert(ticket_b && ticket_b->generation != ticket_a->generation);
    registry.Unregister(&b);
    assert(!registry.IsCurrent(*ticket_b));
    registry.Unregister(&a);
    assert(!registry.CaptureTicket(&a));
    assert(!registry.IsCurrent(*ticket_a)); // teardown
    assert(registry.Register(&a));
    const auto ticket_reopened = registry.CaptureTicket(&a);
    assert(ticket_reopened && ticket_reopened->generation != ticket_a->generation);
    assert(!registry.IsCurrent(*ticket_a)); // same KProcess* reused
    assert(registry.IsCurrent(*ticket_reopened));

    // A still-live owning session holds an immutable ticket across
    // concurrent secondary-worker opening and closing.
    std::atomic<bool> failed{false};
    std::vector<std::thread> workers;
    for (int t = 0; t < 4; ++t) {
        workers.emplace_back([&] {
            for (int i = 0; i < 2000; ++i) {
                if (!registry.Register(&a) || !registry.IsCurrent(*ticket_reopened))
                    failed.store(true, std::memory_order_relaxed);
                registry.Unregister(&a);
                if (!registry.IsCurrent(*ticket_reopened))
                    failed.store(true, std::memory_order_relaxed);
            }
        });
    }
    for (auto& worker : workers) worker.join();
    assert(!failed.load());
    assert(registry.Count() == 1);

    // Bounded tracking cannot admit more than 256 simultaneous owners.
    // Allocation/teardown of unique pointers stays under explicit ownership.
    Kernel::KProcess processes[256]{};
    for (std::size_t i = 0; i < 255; ++i)
        assert(registry.Register(&processes[i]));
    assert(registry.Count() == 256);
    assert(!registry.Register(&c));
    assert(!registry.CaptureTicket(&c));
    for (std::size_t i = 0; i < 255; ++i)
        registry.Unregister(&processes[i]);
    registry.Unregister(&a);
    assert(!registry.IsCurrent(*ticket_reopened));
    assert(registry.Count() == 0);
    std::puts("NS2 GPU session registry: PASS (ownership, stale/reopen, concurrent workers, 256 cap)");
}
