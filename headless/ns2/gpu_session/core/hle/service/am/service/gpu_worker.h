// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Experimental Switch 2 worker IPC endpoint. Having a kernel session does
// not imply native 4-KiB VA mapping, NvMap registration or GPU submissions.
#include <memory>
#include <mutex>
#include <optional>
#include <vector>
#include "core/hle/service/service.h"

namespace Kernel { class KProcess; }
namespace Service::Nvidia { class Module; }

namespace Service::AM {
struct GpuWorkerSharedState;
class IGpuWorker final : public ServiceFramework<IGpuWorker> {
public:
    IGpuWorker(Core::System& system, std::shared_ptr<Nvidia::Module> module,
               Kernel::KProcess* process, std::shared_ptr<GpuWorkerSharedState> shared);
    ~IGpuWorker() override;

    Result HandleSyncRequest(Kernel::KServerSession& session,
                             HLERequestContext& ctx) override;
private:
    void CreateGpuAccessibleMemory(HLERequestContext& ctx);
    void DestroyGpuAccessibleMemory(HLERequestContext& ctx);
    Result RegisterMemory(u64 begin, u64 end, u32 flags, u32 device, u32& id);
    Result ReleaseMemory(u32 id, u32 notification);
    std::mutex m_mutex;
    std::shared_ptr<GpuWorkerSharedState> m_shared;
    std::optional<std::size_t> m_nv_session;
    std::vector<u32> m_memory;
    std::shared_ptr<Nvidia::Module> m_module;
    Kernel::KProcess* const m_process;
};
} // namespace Service::AM
