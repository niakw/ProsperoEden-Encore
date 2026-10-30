// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// An intentionally incomplete but real TIPC service owner. Graphics/NVDRV
// commands are NOT advertised until their actual backing services exist.
#include <mutex>
#include "core/hle/service/service.h"
#include "core/hle/service/am/service/gpu_session_protocol.h"

namespace Service::AM {
class IGpuSession final : public ServiceFramework<IGpuSession> {
public:
    explicit IGpuSession(Core::System& system);
    ~IGpuSession() override;
    Result HandleSyncRequest(Kernel::KServerSession& session, HLERequestContext& ctx) override;
private:
    void CreateGraphicsDevice(HLERequestContext& ctx);
    void DestroyGraphicsDevice(HLERequestContext& ctx);
    std::mutex m_lock;
    GpuSessionProtocol::DeviceSlots m_devices;
};
} // namespace Service::AM
