// SPDX-FileCopyrightText: Copyright 2026 Eden Encore Project
// SPDX-License-Identifier: GPL-3.0-or-later
// Host miniature of the real PS5 GPU pthread catch + fence publication order.
// Uses production gpu_failure.h and native GPFIFO fetch helper unchanged.
#include <atomic>
#include <cassert>
#include <cstdint>
#include <exception>
#include <stdexcept>
#include <stop_token>
#include <thread>
#include <chrono>
#include <cstdio>
#include <string_view>
#include "gpu_failure.h"
#include "core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h"

int main() {
    using Service::Nvidia::Devices::NativeGpfifoFetchMapped;
    Eden::ResetGpuFailureForTitle();
    std::stop_source stop;
    std::atomic<std::uint64_t> acknowledged{6};
    std::atomic<int> dispatch_calls{0},map_checks{0};
    std::atomic<bool> mapped{true};
    constexpr std::uint64_t queue_fence=7;
    const auto owner=[&] {
        try {
            // The initial ioctl succeeds: the GMMU is still mapped.
            assert(NativeGpfifoFetchMapped(0x2000,4,[&](auto,auto){
                ++map_checks;
                return mapped.load();
            }));
            // Guest Unmap after NVDRV admission, before the worker's fetch.
            mapped=false;
            ++dispatch_calls;
            if (!NativeGpfifoFetchMapped(0x2000,4,[&](auto,auto){
                    ++map_checks;
                    return mapped.load();
                })) {
                throw std::runtime_error("Native GPFIFO command unmapped at GPU fetch");
            }
            // Exactly like GPUThread::RunWorker's post-scheduler queue fence.
            acknowledged.store(queue_fence,std::memory_order_release);
        } catch (const std::exception&) {
            Eden::RecordGpuFailure(std::current_exception());
            stop.request_stop();
        }
    };
    std::thread worker(owner);
    worker.join();
    assert(dispatch_calls==1 && map_checks==2);
    assert(stop.stop_requested());
    assert(acknowledged.load(std::memory_order_acquire)==6);
    const auto observer=Eden::TakeGpuFailure();
    assert(observer);
    // Delivering the alert once does not consume the persistent fatal cause.
    assert(!Eden::TakeGpuFailure());
    const auto another=Eden::PeekGpuFailure();
    assert(another);
    try {
        std::rethrow_exception(another);
        assert(false);
    } catch (const std::runtime_error& exception) {
        assert(std::string_view(exception.what()) ==
               "Native GPFIFO command unmapped at GPU fetch");
    }
    // Requests cannot be acknowledged by a later no-op GPU Tick on a
    // stopped worker. Only complete title teardown clears the latched error.
    assert(acknowledged.load(std::memory_order_acquire)<queue_fence);
    Eden::ResetGpuFailureForTitle();
    assert(!Eden::PeekGpuFailure() && !Eden::TakeGpuFailure());
    std::puts("P2_7_GPU_FETCH_FATAL_NO_FALSE_FENCE_PASS");
}
