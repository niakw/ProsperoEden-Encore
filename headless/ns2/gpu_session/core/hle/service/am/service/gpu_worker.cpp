// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#include <utility>
#include "core/core.h"
#include "core/hle/kernel/k_process.h"
#include "core/hle/kernel/svc_results.h"
#include "core/hle/service/am/service/gpu_worker.h"
#include "core/hle/service/ipc_helpers.h"

namespace Service::AM {
IGpuWorker::IGpuWorker(Core::System& system_, std::shared_ptr<Nvidia::Module> module,
                       Kernel::KProcess* process)
    : ServiceFramework{system_, "IGpuWorker"}, m_module{std::move(module)},
      m_process{process} {
    m_process->Open(kernel);
}
IGpuWorker::~IGpuWorker() { m_process->Close(kernel); }

Result IGpuWorker::HandleSyncRequest(Kernel::KServerSession& session,
                                     HLERequestContext& ctx) {
    // Do not report success for 101/102, 211-216 or any unsupported worker
    // operation until native process memory/pin/GMMU ownership exists.
    if (!ctx.IsTipc()) {
        return ServiceFrameworkBase::HandleSyncRequest(session, ctx);
    }
    IPC::ResponseBuilder rb{ctx, 2};
    rb.Push(Kernel::ResultNotImplemented.raw);
    return system.IsPoweredOn() ? ctx.WriteToOutgoingCommandBuffer() : ResultSuccess;
}
} // namespace Service::AM
