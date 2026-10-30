#!/usr/bin/env python3
"""Static source-owner guard for research NS2 CMake overlays, not a native build."""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text(encoding="utf-8")
NS2 = ROOT / "headless/ns2/overrides/core"

def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)

def main() -> int:
    try:
        require('option(EDEN_NS2_METADATA_EXPERIMENTAL' in CMAKE,
                "No metadata opt-in")
        require('option(EDEN_NS2_EXEFS_EXPERIMENTAL' in CMAKE,
                "No ExeFS opt-in")
        require('option(EDEN_NS2_CPU6_EXPERIMENTAL' in CMAKE,
                "No CPU6 opt-in")
        require('EDEN_NS2_CPU6_EXPERIMENTAL OR' in CMAKE,
                "Final release must reject CPU6 experiment")
        cpu6 = ROOT / "headless/ns2/cpu6"
        require("NUM_CPU_CORES = 6" in (cpu6 / "core/hardware_properties.h").read_text(),
                "Six-core hardware map missing")
        require("MAX_NUM_CPU_CORES = 6" in
                (cpu6 / "dynarmic/interface/exclusive_monitor.h").read_text(),
                "Six-slot Dynarmic exclusive monitor missing")
        require('EDEN_NS2_METADATA_EXPERIMENTAL=ON' in CMAKE,
                "ExeFS must require metadata opt-in")
        require('EDEN_NS2_METADATA_EXPERIMENTAL OR EDEN_NS2_EXEFS_EXPERIMENTAL' in CMAKE,
                "Final release must reject experimental selectors")
        selection = CMAKE.index("# Experimental ExeFS bridge must be selected AFTER")
        am_selection = CMAKE.index("# Research-only Switch 2 AM command 320.")
        release_gate = CMAKE.index("# Release gate: Vulkan/RADV")
        require(selection < am_selection < release_gate,
                "NS2 AM and ExeFS owners must be selected after maintained Encore owners")
        property_sets = [i for i in range(len(CMAKE)) if
                         CMAKE.startswith("set_property(TARGET core PROPERTY SOURCES", i)]
        require(sum(i > selection for i in property_sets) == 5,
                "Unexpected source owner after ExeFS (expected ExeFS, AM, NVDRV, supervisor)")
        require('EDEN_NS2_A64_EXPERIMENTAL OR EDEN_NS2_AM_EXPERIMENTAL OR' in CMAKE,
                "Final release must reject NS2 application-manager experiment")
        require('option(EDEN_NS2_AM_EXPERIMENTAL' in CMAKE and
                'if(NOT EDEN_NS2_METADATA_EXPERIMENTAL)' in CMAKE[am_selection:release_gate] and
                'list(FIND eden_ns2_am_sources "${EDEN_APP_FUNCTION_SOURCE}"' in CMAKE,
                "NS2 application manager must require metadata and maintained source owner")
        scale_selection = CMAKE.index("# Research-only AM proxy command 60 and graphics scaling service.")
        require(am_selection < scale_selection < release_gate,
                "Graphics scaling source owner must precede final release gate")
        require("option(EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL" in CMAKE and
                "if(NOT EDEN_NS2_AM_EXPERIMENTAL)" in CMAKE[scale_selection:release_gate] and
                "EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL OR" in CMAKE,
                "Graphics scaling option must depend on AM and remain release-forbidden")
        scale_root = ROOT / "headless/ns2/am/core/hle/service/am/service"
        proxy = (scale_root / "application_proxy.cpp").read_text()
        scale = (scale_root / "graphics_scaling_parameters_functions.cpp").read_text()
        require("{60, D<&IApplicationProxy::GetGraphicsScalingParametersFunctions>" in proxy and
                "GetGraphicsScalingParametersFunctions(" in proxy,
                "NS2 proxy command 60 must instantiate real graphics scaling service")
        require("{1050, nullptr, \"SetGraphicsScaleChangedNotificationEnabled\"}" in scale and
                "*out_parameters = {10, 1, 1}" in scale,
                "Research graphics scale must not pretend to implement notifications")
        session_selection = CMAKE.index("# Switch 2 GPU TIPC service and bounded worker transport.")
        require(session_selection < release_gate and
                'option(EDEN_NS2_GPU_SESSION_EXPERIMENTAL' in CMAKE and
                'EDEN_NS2_GPU_SESSION_EXPERIMENTAL OR' in CMAKE,
                "NS2 GPU service must remain opt-in and forbidden in release")
        require("if(NOT EDEN_NS2_NVDRV_EXPERIMENTAL)" in
                CMAKE[session_selection:release_gate] and
                'target_sources(core PRIVATE "${EDEN_NS2_GPU_SESSION_SOURCE}"' in CMAKE,
                "NS2 GPU service must require NVDRV and compile real source")
        session_root = ROOT / "headless/ns2/gpu_session/core/hle/service/am/service"
        service_cpp = (session_root / "gpu_session.cpp").read_text()
        service_h = (session_root / "gpu_session.h").read_text()
        require("RegisterHandlersTipc(functions)" in service_cpp and
                "GpuSessionProtocol::DeviceSlots devices" in (session_root / "gpu_worker_shared.h").read_text() and
                "GpuSessionProtocol::AddressSpaceSlots m_address_spaces" in service_h and
                "rb.Push(Kernel::ResultNotImplemented.raw)" in service_cpp and
                "{11, &IGpuSession::GetNotificationRange" in service_cpp and
                "{12, &IGpuSession::GetNotificationEvent" in service_cpp and
                "m_shared->event_context.CreateEvent" in service_cpp and
                "event_context.CloseEvent" in (session_root / "gpu_worker_shared.h").read_text() and
                "readable->Open(kernel)" in service_cpp and
                "{21, &IGpuSession::RequestWorker" in service_cpp and
                "{22, &IGpuSession::AcquireWorker" in service_cpp and
                "CreateWorkerKernelSession(system, ctx" in service_cpp and
                "m_worker->Close(kernel)" in service_cpp and
                "client->Open(kernel)" in service_cpp and
                "{33, &IGpuSession::CreateAddressSpace" in service_cpp and
                "{41, &IGpuSession::CreateGraphicsDevice" in service_cpp and
                "{42, &IGpuSession::DestroyGraphicsDevice" in service_cpp and
                "{202, &IGpuSession::GetAddressSpacePartition" in service_cpp and
                "{203, &IGpuSession::GetAddressSpacePartition" in service_cpp and
                'm_module->Open("/dev/nvhost-as-gpu"' in service_cpp and
                "ioctl.raw = 0x40284109" in service_cpp and
                "ioctl.raw = 0xc0404108" in service_cpp and
                "m_module->Close(" in service_cpp and
                "CloseSession(Nvidia::NvCore::SessionId{" in service_cpp,
                "NS2 GPU service must own real NVDRV descriptors and safely close them")
        worker_header = ROOT / "headless/ns2/hle/core/hle/service/am/service/gpu_worker_protocol.h"
        worker_cpp = worker_header.read_text()
        require("class MappingLedger" in worker_cpp and
                "LedgerStatus RecordMapped" in worker_cpp and
                "LedgerStatus RecordUnmapped" in worker_cpp and
                "DecodeMap(" in worker_cpp and "DecodeUnmap(" in worker_cpp and
                "DecodeModify(" in worker_cpp and
                "MaxMappings = 4096" in worker_cpp,
                "NS2 4K worker preflight / bounded ledger missing")
        worker_hle_cpp = (session_root / "gpu_worker.cpp").read_text()
        require("IGpuWorker::HandleSyncRequest" in worker_hle_cpp and
                "Kernel::ResultNotImplemented.raw" in worker_hle_cpp and
                "IGpuWorker::~IGpuWorker()" in worker_hle_cpp and
                "m_process->Close(kernel)" in worker_hle_cpp and
                "RegisterHandlersTipc(functions)" in worker_hle_cpp and
                "{101, &IGpuWorker::CreateGpuAccessibleMemory" in worker_hle_cpp and
                "{102, &IGpuWorker::DestroyGpuAccessibleMemory" in worker_hle_cpp and
                "LockForMapDeviceAddressSpace" in worker_hle_cpp and
                "Kernel::KMemoryState::FlagCanAlignedDeviceMap" in worker_hle_cpp and
                "Kernel::KMemoryState::FlagReferenceCounted" in worker_hle_cpp and
                "KMemoryAttribute::GpuAccessible" not in worker_hle_cpp and
                "UnlockForDeviceAddressSpace" in worker_hle_cpp and
                "CreateHandle(size, handle)" in worker_hle_cpp and
                "handle->dupes == 1" in worker_hle_cpp and
                "Kernel::ResultBusy" in worker_hle_cpp and
                "m_shared->events[notification]->Signal(kernel)" in worker_hle_cpp and
                "DecodeGpuMemoryRelease(command)" in worker_hle_cpp and
                '{211, &IGpuWorker::NormalMapGpuMemory4K' not in worker_hle_cpp,
                "Native GPU worker IPC must reject unsupported mappings")
        require('target_sources(core PRIVATE "${EDEN_NS2_GPU_SESSION_SOURCE}"' in CMAKE and
                '"${EDEN_NS2_GPU_WORKER_SOURCE}")' in CMAKE and
                "EDEN_NS2_GPU_WORKER_SOURCE" in CMAKE[session_selection:release_gate],
                "Native worker source must be gated with GPU session research owner")
        supervisor_selection = CMAKE.index("# Research-only SelfController -> GraphicsSupervisor")
        require(session_selection < supervisor_selection < release_gate and
                "EDEN_NS2_GRAPHICS_SUPERVISOR_EXPERIMENTAL OR" in CMAKE and
                "if(NOT EDEN_NS2_GPU_SESSION_EXPERIMENTAL OR NOT EDEN_NS2_AM_EXPERIMENTAL)" in CMAKE,
                "NS2 supervisor must require AM/GPU and be release-forbidden")
        require('list(FIND eden_ns2_supervisor_sources' in CMAKE and
                '"hle/service/am/service/self_controller.cpp" eden_ns2_self_idx' in CMAKE and
                'set_property(TARGET core PROPERTY SOURCES "${eden_ns2_supervisor_sources}")' in CMAKE,
                "NS2 supervisor must replace only pinned CMIF SelfController owner")
        sup_cpp = (ROOT / "headless/ns2/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp").read_text()
        self_cpp = (ROOT / "headless/ns2/self_controller/core/hle/service/am/service/self_controller.cpp").read_text()
        require("m_bootstrap.CanOpenGpuSession(packet, module != nullptr)" in sup_cpp and
                'GetService<Nvidia::NVDRV>("nvdrv:s", true)' in sup_cpp and
                "CreateMetadataSession(system, ctx," in sup_cpp and
                "handler->RegisterAddressSpace(*id)" in sup_cpp and
                "m_bootstrap.GpuContextReady()" in sup_cpp and
                "Kernel::ResultNotImplemented.raw" in sup_cpp and
                "{434, &IGraphicsSupervisor::RegisterGpuAddressSpace" in sup_cpp and
                "{497, &IGraphicsSupervisor::OpenGpuSession" in sup_cpp,
                "Supervisor must require real NVDRV module and register only owned GPU VA")
        require('{2000, &ISelfController::GetGraphicsSupervisor' in self_cpp and
                "server.RegisterSession(&session->GetServerSession()" in self_cpp and
                "rb.PushCopyObjects(ctx, m_graphics_supervisor_session)" in self_cpp,
                "CMIF SelfController must create a real supervisor copy-handle session")
        nvdrv_selection = CMAKE.index("# Native Switch 2 GPU capabilities IOCTLs, experimental only;")
        require(am_selection < nvdrv_selection < release_gate,
                "NVDRV research must select after maintained Encore owners and before release gate")
        require('option(EDEN_NS2_NVDRV_EXPERIMENTAL' in CMAKE and
                'EDEN_NS2_NVDRV_EXPERIMENTAL OR' in CMAKE and
                'list(FIND eden_ns2_nvdrv_sources' in CMAKE and
                '"hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp" eden_ns2_nvdrv_idx' in CMAKE,
                "NVDRV opt-in, original source owner or final release protection missing")
        nvdrv_root = ROOT / "headless/ns2/nvdrv/core/hle/service/nvdrv/devices"
        ctrl = (nvdrv_root / "nvhost_ctrl_gpu.cpp").read_text()
        ioctl = (nvdrv_root / "native_characteristics_ioctl.h").read_text()
        require('WriteNativeCharacteristicsIoctlReply(' in ctrl and
                'return WrapFixedInlOut(this, &nvhost_ctrl_gpu::GetCharacteristics3' in ctrl and
                'native_characteristics_ioctl.h' in ctrl,
                "Research native response must preserve original ioctl fallback")
        require('raw != 0xc0e04705U && raw != 0xc0e84705U' in ioctl,
                "Native ioctl handler must match only exact native commands")
        am_root = ROOT / "headless/ns2/am/core/hle/service/am/service"
        am_impl = (am_root / "application_functions.cpp").read_text()
        am_header = (am_root / "application_functions.h").read_text()
        require("GetScreenShotAndContinuousRecordingInitiallyEnabled" in am_impl and
                "GetScreenShotAndContinuousRecordingInitiallyEnabled" in am_header,
                "AM 320 declaration/handler missing")
        require("last_reported_title.exchange(title_id" in am_impl,
                "Maintained Encore application metadata diagnostic behavior lost")
        require('eden_ns2_loader_origin' in CMAKE and
                'eden_ns2_romdir_origin' in CMAKE and
                'list(FIND eden_ns2_exefs_sources "${eden_ns2_original}"' in CMAKE,
                "No version-aware source ownership check")
        loader = (NS2 / "loader/loader.cpp").read_text(encoding="utf-8")
        romdir = (NS2 / "loader/deconstructed_rom_directory.cpp").read_text(encoding="utf-8")
        header = (NS2 / "loader/deconstructed_rom_directory.h").read_text(encoding="utf-8")
        require('extension == "nsz"' in loader and 'extension == "xcz"' in loader,
                "NCZ/NSZ/XCZ loader behavior lost")
        require('<< 14) & 0xffc000' in romdir,
                "16-KiB-aligned Encore ASLR offset lost")
        require('!metadata.UsesExtendedAcid()' in romdir,
                "Extended ACID Dynarmic path guard lost")
        require('bool standalone{true}' in header,
                "Standalone ExeFS state missing")
        require(loader.index('IdentifyFileLoader<AppLoader_DeconstructedRomDirectory>')
                < loader.index('IdentifyFileLoader<AppLoader_NSO>'),
                "ExeFS identification is after generic NSO")
        print("NS2 research source owner / ExeFS safety guards: PASS")
    except (AssertionError, ValueError, OSError) as exc:
        print(f"NS2 source selection check FAILED: {exc}", file=sys.stderr)
        return 1
    print("NOTE: static selection proof only; no complete PS5 CMake configure/compile")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
