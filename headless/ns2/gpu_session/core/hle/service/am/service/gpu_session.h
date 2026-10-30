// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// An intentionally incomplete but real TIPC service owner. Graphics/NVDRV
// commands are NOT advertised until their actual backing services exist.
#include <memory>
#include <mutex>
#include <optional>
#include "core/hle/service/service.h"
#include "core/hle/service/am/service/gpu_session_protocol.h"

namespace Kernel { class KProcess; }
namespace Service::Nvidia { class Module; }
namespace Service::AM {
class IGpuSession final : public ServiceFramework<IGpuSession> {
public:
    IGpuSession(Core::System& system, std::shared_ptr<Nvidia::Module> module,
                Kernel::KProcess* process);
    Result RegisterAddressSpace(u32 id);
    ~IGpuSession() override;
    Result HandleSyncRequest(Kernel::KServerSession& session, HLERequestContext& ctx) override;
private:
    void CreateAddressSpace(HLERequestContext& ctx);
    void GetAddressSpacePartition(HLERequestContext& ctx);
    void CreateGraphicsDevice(HLERequestContext& ctx);
    void DestroyGraphicsDevice(HLERequestContext& ctx);
    std::mutex m_lock;
    GpuSessionProtocol::DeviceSlots m_devices;
    GpuSessionProtocol::AddressSpaceSlots m_address_spaces;
    std::shared_ptr<Nvidia::Module> m_module;
    Kernel::KProcess* const m_process;
    std::optional<std::size_t> m_nv_session;
};
} // namespace Service::AM
