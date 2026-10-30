// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Process-owned event and GPU device state shared across a GPU session and
// its independently refcounted worker. The kernel handles must outlive either.
#include <array>
#include <memory>
#include <mutex>

#include "core/hle/service/am/service/gpu_session_protocol.h"
#include "core/hle/service/kernel_helpers.h"

namespace Kernel { class KEvent; }
namespace Service::AM {

struct GpuWorkerSharedState {
    explicit GpuWorkerSharedState(Core::System& system)
        : event_context{system, "NS2GpuNotification"} {}
    ~GpuWorkerSharedState() {
        for (auto* event : events)
            if (event) event_context.CloseEvent(event);
    }
    GpuWorkerSharedState(const GpuWorkerSharedState&) = delete;
    GpuWorkerSharedState& operator=(const GpuWorkerSharedState&) = delete;

    std::mutex mutex;
    GpuSessionProtocol::DeviceSlots devices;
    KernelHelpers::ServiceContext event_context;
    std::array<Kernel::KEvent*, GpuSessionProtocol::MaxNotificationEvents> events{};
};
} // namespace Service::AM
