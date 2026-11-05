// SPDX-FileCopyrightText: Copyright 2026 Eden Encore Project
// SPDX-License-Identifier: GPL-3.0-or-later
// Host execution of real process/channel/graphics/compute GPU registry owners.
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <new>

#include "core/hle/service/nvdrv/devices/native_gpu_channel_registry.h"

namespace Kernel { class KProcess {}; }
namespace Tegra::Control { struct ChannelState {}; }

namespace {
std::atomic<bool> fail_next_allocation{false};
void FailOnce() { fail_next_allocation.store(true, std::memory_order_relaxed); }
void ConfirmConsumed() { assert(!fail_next_allocation.load(std::memory_order_relaxed)); }
} // namespace
void* operator new(std::size_t size) {
    if (fail_next_allocation.exchange(false, std::memory_order_relaxed))
        throw std::bad_alloc{};
    if (void* ptr=std::malloc(size ? size : 1)) return ptr;
    throw std::bad_alloc{};
}
void operator delete(void* ptr) noexcept { std::free(ptr); }
void operator delete(void* ptr,std::size_t) noexcept { std::free(ptr); }

int main() {
    using namespace Service::Nvidia::Devices;
    auto& processes=NativeGpuProcessRegistry::Instance();
    auto& channels=NativeGpuChannelRegistry::Instance();
    Kernel::KProcess process{}, other_process{};
    Tegra::Control::ChannelState channel{}, other_channel{};
    int graphics{}, compute{}, second_graphics{}, second_compute{};
    assert(processes.Count()==0);
    // 1. Process registration does not publish an empty epoch after failure.
    FailOnce();
    assert(!processes.Register(&process));
    ConfirmConsumed();
    assert(processes.Count()==0 && !processes.CaptureTicket(&process));
    assert(processes.Register(&process));
    const auto process_ticket=processes.CaptureTicket(&process);
    assert(process_ticket && process_ticket->generation==1);
    // 2. Failed channel map insertion must not consume a new generation.
    FailOnce();
    assert(!channels.Bind(&channel,&process));
    ConfirmConsumed();
    assert(!channels.IsNative(&channel));
    assert(channels.Bind(&channel,&process));
    const auto ticket=channels.CaptureTicket(&channel);
    assert(ticket && ticket->generation==process_ticket->generation &&
           ticket->channel_generation==1);
    // 3. Engine binds reject guest-controlled map allocation failures,
    // without publishing the engine or poisoning an existing channel.
    FailOnce();
    assert(!channels.BindGraphicsEngine(&channel,&graphics,2));
    ConfirmConsumed();
    assert(!channels.CaptureGraphicsTicket(&graphics));
    assert(channels.IsCurrent(&channel,*ticket));
    assert(channels.BindGraphicsEngine(&channel,&graphics,2));
    const auto graphics_ticket=channels.CaptureGraphicsTicket(&graphics);
    assert(graphics_ticket && graphics_ticket->channel_generation==1);
    FailOnce();
    assert(!channels.BindComputeEngine(&channel,&compute,4));
    ConfirmConsumed();
    assert(!channels.CaptureComputeTicket(&compute));
    assert(channels.BindComputeEngine(&channel,&compute,4));
    const auto compute_ticket=channels.CaptureComputeTicket(&compute);
    assert(compute_ticket && channels.IsComputeCurrent(&compute,*compute_ticket));
    assert(channels.IsGraphicsCurrent(&graphics,*graphics_ticket));
    // 4. A distinct process registration can fail without invalidating
    // existing channel/engine process epochs.
    FailOnce();
    assert(!processes.Register(&other_process));
    ConfirmConsumed();
    assert(processes.Count()==1 && channels.IsCurrent(&channel,*ticket) &&
           channels.IsComputeCurrent(&compute,*compute_ticket) &&
           channels.IsGraphicsCurrent(&graphics,*graphics_ticket));
    // Same-channel rebind is an existing map node and must not allocate.
    assert(channels.Bind(&channel,&process));
    // 5. Once unbound, all captured shader tickets stay invalid even if the
    // same pointer/guest process is reintroduced with a new channel epoch.
    channels.Unbind(&channel);
    assert(!channels.IsNative(&channel));
    assert(!channels.IsGraphicsCurrent(&graphics,*graphics_ticket));
    assert(!channels.IsComputeCurrent(&compute,*compute_ticket));
    assert(channels.Bind(&channel,&process));
    const auto reopened=channels.CaptureTicket(&channel);
    assert(reopened && reopened->channel_generation==2);
    assert(!channels.IsCurrent(&channel,*ticket));
    assert(!channels.CaptureGraphicsTicket(&graphics));
    assert(!channels.CaptureComputeTicket(&compute));
    // 6. A failed second channel cannot corrupt first channel’s bindings.
    FailOnce();
    assert(!channels.Bind(&other_channel,&process));
    ConfirmConsumed();
    assert(channels.IsCurrent(&channel,*reopened) && !channels.IsNative(&other_channel));
    assert(channels.Bind(&other_channel,&process));
    const auto sibling=channels.CaptureTicket(&other_channel);
    assert(sibling && sibling->channel_generation==3);
    assert(channels.BindGraphicsEngine(&channel,&second_graphics,1));
    assert(channels.BindComputeEngine(&other_channel,&second_compute,1));
    channels.Unbind(&other_channel);
    assert(channels.IsCurrent(&channel,*reopened));
    assert(!channels.CaptureComputeTicket(&second_compute));
    channels.Unbind(&channel);
    processes.Unregister(&process);
    assert(processes.Count()==0 && !processes.IsCurrent(*process_ticket));
    assert(!channels.IsCurrent(&channel,*reopened));
    return 0;
}
