#!/usr/bin/env python3
"""Reject process-wide GPU ABI promotion in the real NS2 research NVDRV channel."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices"
source = (BASE / "nvhost_gpu.cpp").read_text()
# SwitchBrew retry ioctls are wire-compatible with the existing submit paths.
# Ensure the active dispatch reuses the same bounded helpers, not a fake success.
ioctl1 = source.split("NvResult nvhost_gpu::Ioctl1(", 1)[1].split(
    "NvResult nvhost_gpu::Ioctl2(", 1)[0]
ioctl2 = source.split("NvResult nvhost_gpu::Ioctl2(", 1)[1].split(
    "NvResult nvhost_gpu::Ioctl3(", 1)[0]
retry1 = ioctl1.split("case 0x19: { // NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO_RETRY", 1)[1].split(
    "case ", 1)[0]
retry2 = ioctl2.split("case 0x1c: { // NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO2_RETRY", 1)[1].split(
    "case ", 1)[0]
assert "(command.raw & 0xC000FFFFU) != 0xC0004819U" in retry1
assert "&nvhost_gpu::SubmitGPFIFOBase1, input, output, fd, false" in retry1
assert "if (command.raw != 0xC018481CU) break;" in retry2
assert "&nvhost_gpu::SubmitGPFIFOBase2, input, inline_input" in retry2
assert "output, fd);" in retry2
# Legacy NVHOST group-0/cmd-1 submit is intentionally not a native submit path.
group0 = ioctl1.split("case 0x0:", 1)[1].split("case 'H':", 1)[0]
assert "case 0x1:" not in group0
assert 'UNIMPLEMENTED_MSG("Unimplemented ioctl={:08X}", command.raw);' in ioctl1
assert "return NvResult::NotImplemented;" in ioctl1.split("UNIMPLEMENTED_MSG", 1)[1]
header = (BASE / "nvhost_gpu.h").read_text()
native_puller = (ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp").read_text()
native_mme_state = (ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/native_ampere_macro_state.h").read_text()
# BindObject must not change the active subchannel before native class
# authentication, or a rejected Ampere bind can hijack subsequent methods.
bind_source = native_puller.split("void Puller::ProcessBindMethod(", 1)[1].split(
    "void Puller::ProcessFenceActionMethod(", 1)[0]
ampere_3d_bind = bind_source.split(
    "if (engine_id == static_cast<EngineID>(0xc797)) {", 1)[1].split(
    "if (engine_id == static_cast<EngineID>(0xc7c0)) {", 1)[0]
ampere_compute_bind = bind_source.split(
    "if (engine_id == static_cast<EngineID>(0xc7c0)) {", 1)[1].split(
    "if (engine_id == static_cast<EngineID>(0xc7b5)) {", 1)[0]
ampere_dma_bind = bind_source.split(
    "if (engine_id == static_cast<EngineID>(0xc7b5)) {", 1)[1].split(
    "\n        return;\n    }\n", 1)[0]
binding_write = "bound_engines[method_call.subchannel] = engine_id;"

required_puller = (
    "engine_id == static_cast<EngineID>(0xc797)",
    "CallNative3D(dma_pusher,method_call.method,",
    "CallNative3D(dma_pusher,method,",
    "native_3d->ExecuteStagedWithEffects(",
    "DmaReadFifoed = 0x158",
    "IsFullyMappedRange(source, bytes)",
    "ReadBlock(source, data.data(), bytes)",
    "fifo.insert(fifo.end(), data.begin(), data.begin() + words)",
    "native_macro_method=method",
    "engine.draw_manager.DrawDeferred(engine)",
    "native_3d = std::make_unique<Tegra::NativeAmpereMacroState>(&native_mme_dram)",
    "if (native_3d_failed || native_macro_method)",
    "native_compute = std::make_unique<Tegra::NativeAmpereMacroState>(&native_mme_dram)",
)

required_cpp = (
    "bool nvhost_gpu::UsesNativeAbi(DeviceFD fd) const {",
    "return sessions.contains(fd) && native_generations.contains(fd);",
    "bool nvhost_gpu::NativeEpochCurrent(DeviceFD fd) const {",
    "native_generations.find(fd)",
    "NativeGpuProcessRegistry::Instance().IsCurrent(",
    "native_channel_registry.Bind(",
    "if (!opened || opened->process != native_owner)",
    "NativeGpuChannelRegistry::Instance().Unbind(channel_state.get());",
    "NvResult nvhost_gpu::AllocateObjectContext(IoctlAllocObjCtx& params, DeviceFD fd)",
    "NvResult nvhost_gpu::SubmitGPFIFOImpl(IoctlSubmitGpfifo& params, Tegra::CommandList&& entries, DeviceFD fd)",
    "const bool native = UsesNativeAbi(fd);",
    "if (UsesNativeAbi(fd)) {",
    "return WrapFixed(this, &nvhost_gpu::AllocateObjectContext, input, output, fd);",
    "return SubmitGPFIFOImpl(params, std::move(entries), fd);",
    "Kernel::KEvent* nvhost_gpu::QueryEvent(DeviceFD fd, u32 event_id)",
    "return UsesNativeAbi(fd) ? error_notifier_event : nullptr;",
)
# Native event 7 follows the actual querying FD, not a singleton session.
query_legacy = source.split("Kernel::KEvent* nvhost_gpu::QueryEvent(u32 event_id)", 1)[1].split("Kernel::KEvent* nvhost_gpu::QueryEvent(DeviceFD", 1)[0]
query_native = source.split("Kernel::KEvent* nvhost_gpu::QueryEvent(DeviceFD fd, u32 event_id)", 1)[1].split("bool nvhost_gpu::UsesNativeAbi", 1)[0]
assert "case 7:" not in query_legacy and "UsesNativeAbi" not in query_legacy
assert "if (event_id == 7)" in query_native
assert "return UsesNativeAbi(fd) ? error_notifier_event : nullptr;" in query_native
assert "return QueryEvent(event_id);" in query_native
assert "sessions.size()" not in query_native and "sessions.begin()" not in query_native
# The native submission envelope and every FD must be validated before
# even lazy InitChannel, binding a GPU owner or incrementing a syncpoint.
# The normal NS1 path still takes its historical legacy flags and counters.
submit=source.split("NvResult nvhost_gpu::SubmitGPFIFOImpl(",1)[1].split(
    "Core::Memory::Memory& nvhost_gpu::GetSessionMemory(",1)[0]
assert "const bool native = UsesNativeAbi(fd);" in submit
assert submit.index("const auto native_plan = native") < submit.index(
    "system.GPU().InitChannel(")
native_plan_reject = "if (native && !native_plan)"
assert native_plan_reject in submit
assert submit.index(native_plan_reject) < submit.index("system.GPU().InitChannel(")
native_plan_block = submit.split(native_plan_reject, 1)[1].split("system.GPU().InitChannel(", 1)[0]
assert "return NvResult::BadParameter;" in native_plan_block
assert submit.index("if (!opened || opened->process != native_owner)") < submit.index(
    "system.GPU().InitChannel(")
# G10 native waits are now descriptor-owned scheduler metadata. Capture an
# exact syncpoint-generation lease before any channel mutation, attach it to
# the command list, and let the native scheduler suspend only that channel.
native_wait_guard = "if (native && flags.fence_wait.Value()) {"
assert native_wait_guard in submit
native_wait_block = submit.split(native_wait_guard, 1)[1].split(
    "system.GPU().InitChannel(", 1)[0]
for token in (
    "CaptureNativeSyncpointLease(",
    "if (!lease)",
    "return NvResult::BadParameter;",
    "entries.native_syncpoint_wait.emplace(Tegra::NativeSyncpointWait{",
    "std::move(lease)",
    "catch (const std::bad_alloc&)",
    "return NvResult::InsufficientMemory;",
):
    assert token in native_wait_block, token
assert "IsFenceSignalled(params.fence)" not in native_wait_block
assert "return NvResult::NotImplemented;" not in native_wait_block
assert submit.index(native_wait_guard) < submit.index("system.GPU().InitChannel(")
assert submit.index(native_wait_guard) < submit.index("IncrementSyncpointMaxExt(")
# FENCE_ACTION Acquire remains unsupported in the puller because native
# GPFIFO waits no longer synthesize that legacy method packet.
assert "Native GPFIFO FENCE_ACTION acquire unsupported" in native_puller
assert submit.index("system.GPU().InitChannel(") < submit.index(
    "native_channel_registry.Bind(")
assert submit.index("native_channel_registry.Bind(") < submit.index(
    "IncrementSyncpointMaxExt(")
assert submit.index("native_channel_registry.Bind(") < submit.index("AttachFaultNotifier(") < submit.index("IncrementSyncpointMaxExt(")
assert "const u32 increment = native\n        ? native_plan->increment_total" in submit
assert "const u32 native_completion = native_plan ? native_plan->completion_count : 0;" in submit
assert "u32{params.fence.value}" in submit
required_header = (
    "NvResult AllocateObjectContext(IoctlAllocObjCtx& params, DeviceFD fd);",
    "NvResult SubmitGPFIFOImpl(IoctlSubmitGpfifo& params, Tegra::CommandList&& entries, DeviceFD fd);",
    "bool UsesNativeAbi(DeviceFD fd) const;",
    "bool NativeEpochCurrent(DeviceFD fd) const;",
)
# Native H:0x1b kickoff pointer lists must be mapped in their exact FD
# process before any command reads or GPU queue submission.
kickoff = source.split("NvResult nvhost_gpu::SubmitGPFIFOBase1(", 1)[1].split(
    "NvResult nvhost_gpu::SubmitGPFIFOBase2(", 1)[0]
kickoff_preflight = "NativeGpfifoGuestHeadersReadable("
kickoff_read = "this->GetSessionMemory(fd).ReadBlock("
guard = (ROOT / "vendor/encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_submission.h").read_text()
checks = [
    (kickoff_preflight in kickoff and kickoff_read in kickoff and
     kickoff.index(kickoff_preflight) < kickoff.index(kickoff_read) and
     "if (UsesNativeAbi(fd) &&" in kickoff and
     "session->process->GetMemory().IsValidVirtualAddressRange(" in kickoff and
     "return NvResult::InvalidSize;" in kickoff and
     "if (count == 0) return true;" in guard and
     "if (address == 0 || entry_size == 0 ||" in guard and
     "count > std::numeric_limits<std::size_t>::max() / entry_size" in guard and
     "address > std::numeric_limits<std::uint64_t>::max() - bytes" in guard,
     "native kickoff maps every guest header with overflow-safe bounded helper, leaving NS1 unchanged"),
    (all(s in source for s in required_cpp), "native source uses exact caller FD"),
    (all(s in header for s in required_header), "native header exposes caller FD"),
    (all(s in native_puller for s in required_puller),
     "actual research Puller owns authenticated native 3D/Turing macro dispatch"),
    (all(s in native_mme_state for s in (
        "ExecuteStagedWithEffects(",
        "ExecuteWithMutableFifo(",
        "return effect(address, value, fifo, *active_dram, stage_read);",
        "fifo.reserve(MaxFifo);",
    )), "native MME staging exposes only rollback-safe FIFO/DRAM effects"),
    (binding_write not in bind_source.split(
        "if (engine_id == static_cast<EngineID>(0xc797)) {", 1)[0],
     "native classes do not commit binding before authentication"),
    (ampere_3d_bind.count(binding_write) == 1 and
     ampere_3d_bind.index(binding_write) > ampere_3d_bind.index("if (native_3d_failed || native_macro_method)"),
     "native 3D bind commits only after channel authorization and valid MME state"),
    (ampere_compute_bind.count(binding_write) == 1 and
     ampere_compute_bind.index(binding_write) > ampere_compute_bind.index("IsNative(") and
     "EngineTypes::KeplerCompute" in ampere_compute_bind and
     "retire_native_3d();" in ampere_compute_bind,
     "native compute class binds only after channel authorization and revokes previous 3D owner"),
    (ampere_dma_bind.count(binding_write) == 1 and
     ampere_dma_bind.index(binding_write) > ampere_dma_bind.index("IsNative("),
     "native DMA bind commits only after channel authorization"),
    ("UsesNativeAbi()" not in source + header, "no unscoped native ABI call"),
    (source.count("return SubmitGPFIFOImpl(params, std::move(entries), fd);") == 2,
     "both GPFIFO submit paths propagate FD"),
    ("output, fd);" in source, "inline submit passes FD"),
    ("for (const auto& [other_fd, session_id] : sessions)" in source,
     "native channel rejects mixed-process FDs before GPU queue work"),
]
errors = [message for passed, message in checks if not passed]
if errors:
    print("NS2 NVDRV per-FD ABI isolation: FAILED: " + "; ".join(errors), file=sys.stderr)
    raise SystemExit(1)
print("NS2 NVDRV per-FD ABI isolation source gate: PASS")
print("No NS2 GPU hardware or PS5 gameplay inference.")
