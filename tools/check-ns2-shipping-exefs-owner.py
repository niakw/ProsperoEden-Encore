#!/usr/bin/env python3
"""Validate one shipping PS5 ExeFS owner for NS1 and NS2."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
release = cmake.split('# The same maintained loader owns ordinary NS1 ExeFS', 1)[1].split(
    '# The Switch 2 GPU-access memory SVC', 1)[0]
assert 'set(EDEN_SHARED_NS2_EXEFS ON)' in release
assert 'if(EDEN_SHARED_NS2_EXEFS)' in release
assert 'if(NOT EDEN_REVIEWED_DUAL_NPDM)' in release
assert 'set_property(TARGET core PROPERTY SOURCES' in release
assert 'EDEN_NS2_EXEFS_EXPERIMENTAL' not in release
for name in ('loader.cpp', 'deconstructed_rom_directory.cpp'):
    assert (ROOT / 'vendor/encore-active/eden/src/core/loader' / name).is_file()
rom = (ROOT / "vendor/encore-active/eden/src/core/loader/deconstructed_rom_directory.cpp").read_text()
loader = (ROOT / "vendor/encore-active/eden/src/core/loader/loader.cpp").read_text()
for required in (
    "metadata.IsSwitch2()", "metadata.UsesExtendedAcid()",
    "Eden::NS2::ExeFS::PreflightNso",
    "Eden::NS2::ExeFS::AdmitKProcessCode",
    "Eden::NS2::ExeFS::MainThreadPermitted",
    "Eden::NS2::ExeFS::VerifyUncompressedTextHandoff",
):
    assert required in rom, required
assert "Eden::NS2::SvcTrace::Register" in rom
assert 'IdentifyFileLoader<AppLoader_DeconstructedRomDirectory>(file)' in loader
assert "Eden::NS2::Content::IdentifyName" in loader
assert "AppLoader_NSP" in loader and "AppLoader_XCI" in loader
# Regression: CMake selects metadata/loader.cpp AFTER the maintained NCZ loader.
# Keep NX, DNSP and DXCI dispatch in that actual shipping translation unit.
assert 'set(eden_ns2_replacement' in release
assert '"${EDEN_NS2_METADATA_OVERLAY}/core/loader/${eden_ns2_basename}")' in release
assert 'list(REMOVE_ITEM eden_ns2_exefs_sources "${eden_ns2_original}")' in release
assert 'list(APPEND eden_ns2_exefs_sources "${eden_ns2_replacement}")' in release
for required in (
    '#include "core/loader/nx.h"',
    'file->GetName() == "main"',
    'IdentifyFileLoader<AppLoader_NX>(file)',
    'AppLoader_NX::IsBootable(file)',
    'case FileType::NX:',
    'std::make_unique<AppLoader_NX>(system',
    'Eden::NS2::Content::Kind::DNSP',
    'Eden::NS2::Content::Kind::DXCI',
    'Eden::NS2::Content::Kind::NX',
    '!Eden::NS2::Content::MayFallbackByName(filename_kind)',
):
    assert required in loader, required
assert 'set(EDEN_SHARED_NS2_AM ON)' in cmake
assert 'if(EDEN_SHARED_NS2_AM)' in cmake
assert 'option(EDEN_NS2_AM_EXPERIMENTAL' not in cmake
am_file = (ROOT / "vendor/encore-active/eden/src/core/hle/service/am/service/application_functions.cpp").read_text()
assert '{320, D<&IApplicationFunctions::GetScreenShotAndContinuousRecordingInitiallyEnabled>' in am_file
assert "m_applet->screenshot_permission" in am_file
assert "m_applet->game_play_recording_supported" in am_file
assert 'if(EDEN_SHARED_NS2_NVDRV_CAPS)' in cmake
assert 'set(EDEN_SHARED_NS2_NVDRV_CAPS ON)' in cmake
nv = (ROOT / "vendor/encore-active/eden/src/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp").read_text()
assert "command.raw == 0xc0e04705U || command.raw == 0xc0e84705U" in nv
assert "WriteNativeCharacteristicsIoctlReply(" in nv
nv_selector = cmake.split('# The native GPU-characteristics IOCTL owner is additive:', 1)[1].split(
    '# Native GPU session HLE and bounded worker transport:', 1)[0]
assert 'if(EDEN_SHARED_NS2_NVDRV_CAPS)' in nv_selector
assert 'eden_ns2_as_idx' in nv_selector and 'eden_ns2_gpu_idx' in nv_selector
assert 'EDEN_NS2_NATIVE_GPU_PULLER' in nv_selector
assert 'EDEN_NS2_NVDRV_EXPERIMENTAL' not in nv_selector
assert 'Settings::SetNceEnabled(is_39bit && !metadata.UsesExtendedAcid())' in rom
# The shipping kernel must accept an NS2 12 GiB guest heap without changing
# the Switch 1 layout-specific cap or replacing the complete SVC dispatcher.
heap = cmake.split('# Shared kernel heap admission for Switch 2:', 1)[1].split(
    '# N3b: shared native PS5 applet compatibility', 1)[0]
assert 'set(EDEN_SHARED_NS2_KERNEL_HEAP ON)' in heap
assert 'PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM' in heap
assert 'set_property(TARGET core PROPERTY SOURCES' in heap
kernel_root = ROOT / 'vendor/encore-active/eden/src/core/hle/kernel'
addr = (kernel_root / 'k_address_space_info.cpp').read_text()
svc = (kernel_root / 'svc/svc_physical_memory.cpp').read_text()
assert '.size = 16_GiB' in addr and 'KAddressSpaceInfo::Type::Heap' in addr
assert '.size = 8_GiB' in addr and 'Ns2HeapInfo' in addr
assert 'Settings::MemoryLayout::Memory_12Gb' in addr and 'return Ns2HeapInfo;' in addr
assert 'if (width == 39 && type == KAddressSpaceInfo::Type::Heap' in addr
assert 'KSystemControl::Init::GetIntendedMemorySize()' in svc
assert '(std::max)(MainMemorySizeMax,' in svc
for owner in ('hle/kernel/k_address_space_info.cpp', 'hle/kernel/svc/svc_physical_memory.cpp'):
    assert owner in heap
assert 'EDEN_NS2_KERNEL_ROOT' in heap
# A 12 GiB guest kernel cannot work if the memory layout is selected only
# later by the ExeFS loader (after InitializeKernel). Use the maintained
# native Core::System as the source ancestor, preserving NS1 optimizations.
native_core = (ROOT / 'vendor/encore-active/eden/src/core/core_native.cpp').read_text()
shared_core = (ROOT / 'vendor/encore-active/eden/src/core/core.cpp').read_text()
selector = cmake.split('# The Core::System overlay is a fully maintained', 1)[1].split(
    '# RomFS builder parents', 1)[0]
assert 'PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM' in selector
assert 'eden/src/core/core.cpp' in selector
assert '#include "diagnostics.h"' in native_core and shared_core.startswith('#include "diagnostics.h"')
assert 'IsSwitch2LaunchProgram(' in shared_core
# The pre-kernel selector may preserve an already-identified NS2 extended ACID
# generation even if a *later* ACI/FAC/KAC validation fails. The real
# application loader still requires a fully valid NPDM; this early probe only
# determines the guest layout before InitializeKernel.
assert 'const auto status = metadata.Load(npdm);' in shared_core
assert 'const bool switch2 = metadata.IsSwitch2();' in shared_core
assert 'return switch2;' in shared_core
assert 'EDEN_NS2_PREKERNEL_NPDM status={} switch2={}' in shared_core
assert 'metadata.IsSwitch2()' in shared_core
for kind in ('NSP', 'XCI', 'NCA'):
    assert f'Loader::FileType::{kind}' in shared_core
assert 'xci.GetSecurePartitionNSP()' in shared_core
assert 'FileSys::ContentRecordType::Program' in shared_core
assert 'program->GetExeFS()' in shared_core
load = shared_core.split('SystemResultStatus Load(', 1)[1].split(
    'if (params.applet_type == Service::AM::AppletType::Application)', 1)[0]
assert load.index('IsSwitch2LaunchProgram(') < load.index('InitializeKernel(system);')
assert 'params.program_id, params.program_index' in load
assert 'Settings::MemoryLayout::Memory_12Gb' in load
assert 'SetGlobal(false)' in load and 'SetValue(Settings::MemoryLayout::Memory_12Gb)' in load
assert 'initialized_memory_layout != Settings::values.memory_layout_mode.GetValue()' in shared_core
# NS2 per-title 12 GiB memory override must return to the previous NS1
# global/custom profile after shutdown, including a direct title transition.
assert 'ns2_previous_layout_global = Settings::values.memory_layout_mode.UsingGlobal();' in shared_core
assert 'ns2_previous_layout = Settings::values.memory_layout_mode.GetValue();' in shared_core
assert 'void RestoreNs2MemoryLayout() {' in shared_core
assert 'layout.SetValue(ns2_previous_layout);' in shared_core
assert 'layout.SetGlobal(ns2_previous_layout_global);' in shared_core
assert shared_core.count('RestoreNs2MemoryLayout();') == 2
assert shared_core.index('kernel.Shutdown();') < shared_core.index('RestoreNs2MemoryLayout();', shared_core.index('kernel.Shutdown();'))
assert 'ns2_memory_layout_override = false;' in shared_core
assert 'Eden::NS2::SvcTrace::ResetForTitle();' in load
assert shared_core.count('Eden::NS2::SvcTrace::ResetForTitle();') == 2
assert shared_core.index('kernel.Shutdown();') < shared_core.index('Eden::NS2::SvcTrace::ResetForTitle();', shared_core.index('kernel.Shutdown();'))
assert 'bool extended_memory_layout' not in shared_core
# Real aud:u manager bridge is additive and shares maintained NS1 audio HLE.
audio_root = ROOT / 'vendor/encore-active/eden/src/core/hle/service/audio'
audio = (audio_root / 'audio.cpp').read_text()
client = (audio_root / 'nx2_audio_user_client.h').read_text()
audio_select = cmake.split('# Shared Switch 2 audio user + virtual device + real Sysmix stream service.', 1)[1].split(
    '# N3b: shared native PS5 applet compatibility', 1)[0]
assert 'PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM' in audio_select
assert 'set(EDEN_SHARED_NS2_AUDIO ON)' in audio_select
assert 'list(REMOVE_ITEM eden_ns2_audio_sources "hle/service/audio/audio.cpp")' in audio_select
assert 'set_property(TARGET core PROPERTY SOURCES' in audio_select
assert 'target_include_directories(core BEFORE PRIVATE' in audio_select
assert audio.count('RegisterNamedService("aud:u"') == 1
assert audio.count('RegisterNamedService("auddmg:u"') == 1
assert 'INx2AudioDeviceManagerService' in client
assert 'INx2AudioVirtualDeviceManager' in client
assert '{401, &INx2AudioVirtualDeviceManager::GetVirtualOutputDeviceProperties' in client
assert '{300, &INx2AudioVirtualDeviceManager::IsStreamFormatSupported' in client
assert '{700, &INx2AudioVirtualDeviceManager::AttachStream' in client
assert '{800, &INx2AudioVirtualDeviceManager::DetachStream' in client
assert 'streams->SetEngaged(id, true, ctx.GetThread().GetOwnerProcess())' in client
assert 'streams->SetEngaged(id, false, ctx.GetThread().GetOwnerProcess())' in client
assert 'SysmixOutput::IsFormatSupported(format, channels, sample_rate)' in client
assert 'INx2AudioSoundMixerService' in (
    audio_root / 'nx2_sysmix_user_service.h').read_text()
assert audio.count('RegisterNamedService("audsmx:u"') == 1
assert 'auto sysmix = std::make_shared<Nx2SysmixStreams>(system);' in audio
assert 'core/hle/service/audio/nx2_sysmix.cpp' in audio_select
sysmix_owner = (audio_root / 'nx2_sysmix.cpp').read_text()
assert 'ReadWordAcquire(memory,' in sysmix_owner
assert 'std::atomic_thread_fence(std::memory_order_acquire)' in sysmix_owner
assert 'WriteExclusive32(p.buffer + ReadOffset, next, read)' in sysmix_owner
assert 'if (p.host->GetQueueSize() >= NativeQueueHighWatermark)' in sysmix_owner
assert 'p.host->AppendBuffer(block, p.output);' in sysmix_owner
assert 'AudioCore::Sink::StreamType::Out' in sysmix_owner
assert 'TryAppendOutputBlock(' not in sysmix_owner
assert 'python3 -B tools/ns2/check_native_sysmix_pcm_ring_host.py' in (
    ROOT / '.github/workflows/encore-core-preflight.yml').read_text()
assert 'python3 -B tools/ns2/check_native_sysmix_registry_host.py' in (
    ROOT / '.github/workflows/encore-core-preflight.yml').read_text()
assert 'Result CreateBounded(Factory&& factory' in (
    audio_root / 'nx2_sysmix_user_service.h').read_text()
assert 'Result SetEngagedBatch(std::span<const u32> ids' in (
    audio_root / 'nx2_sysmix_user_service.h').read_text()
for name in ('audout:u', 'audren:u', 'audin:u', 'audctl', 'hwopus'):
    assert audio.count('RegisterNamedService("' + name + '"') == 1, name
for command, method, manager, service in (
    (0, 'GetAudioInManager', 'IAudioInManager', 'audin:u'),
    (1, 'GetAudioOutManager', 'IAudioOutManager', 'audout:u'),
    (2, 'GetAudioRendererManager', 'IAudioRendererManager', 'audren:u')):
    assert '{' + str(command) + ', &INx2AudioUserClient::' + method in client
    assert 'ReplyRegisteredManager<' + manager + '>(ctx, "' + service + '")' in client
assert 'auto manager = system.ServiceManager().GetService<T>(service);' in client
assert 'rb.PushIpcInterface<T>(ctx, manager)' in client
assert 'rb.Push(ResultNotFound);' in client
assert 'std::make_shared<IAudioOutManager>' not in client
assert 'std::make_shared<IAudioRendererManager>' not in client
assert 'auto stub fallback' not in client.lower()
streamplay = (audio_root.parent / 'nx2_streamplay.h').read_text()
assert audio.count('RegisterNamedService("stpl:u"') == 1
assert '{0, &INx2StreamPlayService::GetUserService' in streamplay
assert '{300, &INx2StreamPlayUserService::GetGuestHidSharedMemory' in streamplay
assert 'GuestHidMemorySize = 0x9b000' in streamplay
assert 'memory->Initialize(owner_kernel, system.DeviceMemory(), nullptr,' in streamplay
assert 'Kernel::Svc::MemoryPermission::ReadWrite' in streamplay
assert 'Kernel::Svc::MemoryPermission::Read' in streamplay
assert 'KSharedMemory::Register(owner_kernel, memory)' in streamplay
assert 'guest_hid_memory->Close(kernel)' in streamplay
assert 'rb.PushRaw(Nx2GuestHidMemoryConfig{GuestHidMemorySize, 0})' in streamplay
assert 'rb.PushCopyObjects(ctx, guest_hid_memory)' in streamplay
assert 'rb.PushIpcInterface<INx2StreamPlayUserService>(ctx, system)' in streamplay
assert 'service_context.CreateEvent(' not in streamplay
assert 'GetEvent (guessed)' not in streamplay
assert 'python3 -B tools/ns2/check_native_streamplay_guest_hid_host.py' in (
    ROOT / '.github/workflows/encore-core-preflight.yml').read_text()

# Shared NS2 GPU-access SVC 0x80 is restricted to an actual NS2
# ExeFS process and the 12 GiB profile; no blanket success of unknown calls.
gpu_svc = (ROOT / 'vendor/encore-active/eden/src/core/hle/kernel/svc.cpp').read_text()
assert 'Eden::NS2::SvcTrace::IsActive(process.GetProcessId())' in gpu_svc
assert 'Settings::MemoryLayout::Memory_12Gb' in gpu_svc
assert 'process.GetPageTable().Contains(address, size)' in gpu_svc
assert 'process.GetPageTable().SetMemoryAttribute(' in gpu_svc
assert 'GpuAccessible = (1 << 5)' in (
    ROOT / 'vendor/encore-active/eden/src/core/hle/kernel/svc_types.h').read_text()
assert 'else if (process.Is64Bit())' in gpu_svc
print("ENCORE_NS2_SHARED_EXEFS_SHIPPING_OWNER_PASS release=one ns1_nso_preserved=1 ns2_am_320=1 nvdrv_caps=1 kernel_heap=1 prekernel_layout=1 audio_u=1 streamplay=1")
