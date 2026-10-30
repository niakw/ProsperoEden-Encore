// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// Research-only real HLE registration, not linked in the Encore release.
// Only local device ID bookkeeping has a true backend. No false-positive
// success is sent for address spaces, notifications, GPU workers or queues.
#include <array>
#include <algorithm>
#include <cstdint>
#include <mutex>
#include "core/core.h"
#include "core/hle/kernel/svc_results.h"
#include "core/hle/service/am/service/gpu_session.h"
#include "core/hle/service/ipc_helpers.h"

namespace Service::AM {
namespace GP = GpuSessionProtocol;

IGpuSession::IGpuSession(Core::System& system_)
    : ServiceFramework{system_, "IGpuSession"} {
    static const FunctionInfo functions[] = {
        {41, &IGpuSession::CreateGraphicsDevice, "CreateGraphicsDevice"},
        {42, &IGpuSession::DestroyGraphicsDevice, "DestroyGraphicsDevice"},
        // Do not claim 11/12, 21/22, 33 or 202/203 until actual NVDRV,
        // event ownership, kernel sessions and VA partition handling exist.
    };
    RegisterHandlersTipc(functions);
}
IGpuSession::~IGpuSession() = default;

Result IGpuSession::HandleSyncRequest(Kernel::KServerSession& session,
                                     HLERequestContext& ctx) {
    if (!ctx.IsTipc() || handlers_tipc.contains(ctx.GetCommand())) {
        return ServiceFrameworkBase::HandleSyncRequest(session, ctx);
    }
    const auto guard=LockService();
    InvokeRequestTipc(ctx);
    IPC::ResponseBuilder rb{ctx, 2};
    rb.Push(Kernel::ResultNotImplemented.raw);
    return system.IsPoweredOn() ? ctx.WriteToOutgoingCommandBuffer() : ResultSuccess;
}

static Result Translate(GP::Status status) {
    switch (status) {
    case GP::Status::Success:       return ResultSuccess;
    case GP::Status::InvalidPacket: return Kernel::ResultInvalidCombination;
    case GP::Status::Unsupported:   return Kernel::ResultNotImplemented;
    case GP::Status::NotFound:      return Kernel::ResultNotFound;
    case GP::Status::OutOfResource: return Kernel::ResultOutOfResource;
    case GP::Status::InvalidState:  return Kernel::ResultInvalidState;
    }
    return Kernel::ResultNotImplemented;
}
void IGpuSession::CreateGraphicsDevice(HLERequestContext& ctx) {
    const std::scoped_lock lock{m_lock};
    const auto* packet=ctx.CommandBuffer();
    const std::array<GP::U32,8> command{
        packet[0],packet[1],packet[2],packet[3],
        packet[4],packet[5],packet[6],packet[7]};
    const auto outcome=m_devices.Create(command);
    IPC::ResponseBuilder rb{ctx,3};
    rb.Push(Translate(outcome.status).raw);
    rb.Push(outcome.id);
}
void IGpuSession::DestroyGraphicsDevice(HLERequestContext& ctx) {
    const std::scoped_lock lock{m_lock};
    const auto* packet=ctx.CommandBuffer();
    const std::array<GP::U32,3> command{packet[0],packet[1],packet[2]};
    const auto result=m_devices.Destroy(command);
    IPC::ResponseBuilder rb{ctx,2};
    rb.Push(Translate(result).raw);
}
} // namespace Service::AM
