// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Experimental Switch 2 worker IPC endpoint. Having a kernel session does
// not imply native 4-KiB VA mapping, NvMap registration or GPU submissions.
#include <memory>
#include "core/hle/service/service.h"

namespace Kernel { class KProcess; }
namespace Service::Nvidia { class Module; }

namespace Service::AM {
class IGpuWorker final : public ServiceFramework<IGpuWorker> {
public:
    IGpuWorker(Core::System& system, std::shared_ptr<Nvidia::Module> module,
               Kernel::KProcess* process);
    ~IGpuWorker() override;

    Result HandleSyncRequest(Kernel::KServerSession& session,
                             HLERequestContext& ctx) override;
private:
    std::shared_ptr<Nvidia::Module> m_module;
    Kernel::KProcess* const m_process;
};
} // namespace Service::AM
