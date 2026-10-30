// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

#include <utility>
#include "core/hle/service/am/service/gpu_worker_shared.h"
#include "core/hle/service/nvdrv/core/container.h"
#include "core/hle/service/nvdrv/nvdrv.h"

namespace Service::AM {
GpuWorkerSharedState::GpuWorkerSharedState(Core::System& system,
                                           std::shared_ptr<Nvidia::Module> module_)
    : event_context{system, "NS2GpuNotification"}, module{std::move(module_)} {}

GpuWorkerSharedState::~GpuWorkerSharedState() {
    // Worker clients can be moved to a different guest handle table. Kernel
    // events, live GPU address-space devices and NVDRV session therefore have
    // the lifetime of the last shared session/worker owner.
    for (auto* event : events) {
        if (event) event_context.CloseEvent(event);
    }
    for (const auto fd : address_spaces.OwnedIds()) {
        if (fd) module->Close(static_cast<Nvidia::DeviceFD>(*fd));
    }
    if (nv_session)
        module->GetContainer().CloseSession(Nvidia::NvCore::SessionId{*nv_session});
}
} // namespace Service::AM
