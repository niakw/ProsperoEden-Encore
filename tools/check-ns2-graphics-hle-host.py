#!/usr/bin/env python3
"""Test the exact scoped GPU HLE headers from pinned Eden-NS2 plus uploaded patch."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
HEADERS=ROOT/"vendor/encore-active/ns2-runtime/hle"
NVDRV=ROOT/"vendor/encore-active/ns2-runtime/nvdrv"
EDEN=ROOT/"vendor/sources/eden/src"
SOURCE=ROOT/"tools/ns2/test_graphics_hle.cpp"
EXPECTED=[
    HEADERS/"core/hle/service/am/service/graphics_supervisor_protocol.h",
    HEADERS/"core/hle/service/am/service/native_image_layout.h",
    HEADERS/"core/hle/service/am/service/gpu_memory_registration.h",
    HEADERS/"core/hle/service/nvdrv/devices/native_gpu_kind.h",
    HEADERS/"core/hle/service/nvdrv/devices/native_sparse_remap.h",
    HEADERS/"core/hle/service/nvdrv/devices/native_gpu_context.h",
    HEADERS/"core/hle/service/am/service/graphics_syncpoint_cache.h",
    HEADERS/"core/hle/service/am/service/gpu_session_protocol.h",
    HEADERS/"core/hle/service/am/service/graphics_supervisor_bootstrap.h",
    HEADERS/"core/hle/service/am/service/gpu_worker_protocol.h",
]
def main()->int:
    if not all(f.is_file() for f in EXPECTED):
        print("NS2 graphics HLE overlay incomplete",file=sys.stderr)
        return 2
    # The real research-only supervisor, not just the standalone protocol,
    # handles creation/bind/destruction; no synthetic GPU work is advertised.
    supervisor=ROOT/"vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp"
    text=supervisor.read_text()
    for command, method in ((111,"CreateNativeMemory"),(112,"DestroyNativeMemory"),(114,"BindNativeMemory")):
        assert '{'+str(command)+', &IGraphicsSupervisor::'+method in text
    assert 'm_native_memory.ValidateBind(' in text
    assert 'table.QueryInfo(&info, &page, cursor)' in text
    # Accept only formatting whitespace; the same native-memory guard is required.
    assert re.search(r'NativeMemoryError\s*\(\s*m_native_memory\.Bind\s*\(', text)
    assert 'm_native_memory.Destroy(' in text
    # GSV 111/112/114 must use real NVMap handle identity and kernel page locks,
    # not acknowledge metadata-only resources that cannot become GPU images.
    for source in (
        'nvmap.CreateHandle(size, handle)',
        'm_native_memory.Adopt(id, size)',
        'auto handle = nvmap.GetHandle(packet[2])',
        'handle.reset(); // FreeHandle',
        'nvmap.FreeHandle(packet[2], false)',
        'table.LockForMapDeviceAddressSpace(',
        'handle->Alloc(',
        'm_native_memory.Bind(id, address, size)',
        'UnlockForDeviceAddressSpace(',
        'm_native_module->GetContainer().CloseSession(',
    ):
        assert source in text, "Missing real GSV NVMap lifetime owner: " + source
    assert 'm_native_memory.Create(size)' not in text, "Synthetic GSV native memory ID in runtime"
    # VI2 Event is a COPY descriptor; GSV GPU slot event (12) is MOVE
    # per libounce. Both retain the service-owned event and fail closed.
    vi_notify=text.split('void Event(HLERequestContext& ctx) {',1)[1].split('void VsyncEvent(',1)[0]
    assert 'IPC::ResponseBuilder rb{ctx,2,1,0};' in vi_notify
    assert 'rb.PushCopyObjects(ctx,m_event->GetReadableEvent());' in vi_notify
    assert 'AddMoveObject' not in vi_notify
    assert 'readable->Open(kernel)' not in vi_notify
    gpu_session=(ROOT/"vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
    gpu_notify=gpu_session.split('void IGpuSession::GetNotificationEvent(HLERequestContext& ctx) {',1)[1].split('IGpuSession::ResolveOpenedAddressSpace',1)[0]
    assert 'IPC::ResponseBuilder rb{ctx, 2, 0, 1};' in gpu_notify
    assert 'ctx.AddMoveObject(readable);' in gpu_notify
    assert 'ctx.AddCopyObject(readable);' not in gpu_notify
    assert 'readable->Open(kernel)' in gpu_notify
    assert 'readable->Close(kernel);' in gpu_notify
    assert 'catch (const std::bad_alloc&)' in gpu_notify
    assert 'result = Kernel::ResultOutOfResource;' in gpu_notify
    assert gpu_notify.index('ctx.AddMoveObject(readable);') < gpu_notify.index(
        'readable->Close(kernel);') < gpu_notify.index(
        'IPC::ResponseBuilder rb{ctx, 2, 0, 1};')
    # NX2 VI2 has an empty request-group acknowledgement only for 51.
    # Queries 103/104/105 must fill their full SDK payload, not return
    # success with stale input buffer words (HDR 104 can black out graphics).
    for number, method in (
        (51, "AcknowledgeDisplayPoll"),
        (103, "QueryRefreshRate"),
        (104, "QueryHdrStatus"),
        (105, "QueryPaperWhite"),
    ):
        assert '{'+str(number)+',&IVi2Session::'+method in text
    for evidence in (
        'void AcknowledgeDisplayPoll(HLERequestContext& ctx)',
        'void QueryRefreshRate(HLERequestContext& ctx)',
        'void QueryHdrStatus(HLERequestContext& ctx)',
        'void QueryPaperWhite(HLERequestContext& ctx)',
        'ValidateDisplayStatus(ctx, 103)',
        'ValidateDisplayStatus(ctx, 104)',
        'ValidateDisplayStatus(ctx, 105)',
        'GraphicsSupervisorProtocol::Vi2NominalRefreshRateHz',
        'GraphicsSupervisorProtocol::Vi2SdrOutputFormat',
        'GraphicsSupervisorProtocol::Vi2SdrPeakNits',
        'GraphicsSupervisorProtocol::Vi2SdrPaperWhiteNits',
        'GraphicsSupervisorProtocol::Vi2MaxResolutionMode(',
        'Settings::IsDockedMode()',
        'GetDisplayResolution(&width, &height, *m_display)',
        'return Kernel::ResultInvalidCombination;',
        'return m_display && m_vi ? ResultSuccess : Kernel::ResultInvalidState;',
    ):
        assert evidence in text, "Missing fail-closed VI2 payload owner: " + evidence
    # ioctl offset and buffer_offset are s64; the mapped address is u64.
    # Require rejection of negative user-provided values before conversion.
    nvmap_source=(ROOT/"vendor/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp").read_text()
    assert 'params.offset < 0 || params.buffer_offset < 0' in nvmap_source
    assert 'const u64 gpu_base = static_cast<u64>(params.offset);' in nvmap_source
    assert 'const u64 buffer_offset = static_cast<u64>(params.buffer_offset);' in nvmap_source
    assert 'mapping.ptr > std::numeric_limits<VAddr>::max() - buffer_offset' in nvmap_source
    assert 'mapping.ptr < 0 ||' not in nvmap_source
    assert 'width==1280&&height==720' not in text
    hdr=text.split('void QueryHdrStatus(HLERequestContext& ctx) {',1)[1].split(
        'void QueryPaperWhite(HLERequestContext& ctx) {',1)[0]
    assert 'IPC::ResponseBuilder rb{ctx, 5};' in hdr
    assert 'rb.Push<u64>(result.IsSuccess()' in hdr
    assert 'rb.Push<u32>(result.IsSuccess()' in hdr
    assert 'rb.Push(Kernel::ResultNotImplemented.raw)' in text
    # The guest's VI2 swap interval is forwarded to the real compositor.
    # A fixed 1-vblank default here can double 30 FPS game/audio pacing.
    assert 'DecodePresentSwapInterval(p[12])' in text
    assert 'input.swap_interval=1;' not in text
    # VI2 must connect real process-owned 429 image window aliases to the
    # existing display compositor, not return synthetic present success.
    for command, method in ((301,"InitializeDisplayContext"),
                            (303,"FinalizeDisplayContext"),
                            (305,"OpenDisplaySession")):
        assert '{'+str(command)+', &IGraphicsSupervisor::'+method in text
    for evidence in (
        'class IVi2Session final : public ServiceFramework<IVi2Session>',
        '{229,&IVi2Session::Present,"PresentClientBuffer"}',
        'GetService<VI::IManagerRootService>("vi:m",true)',
        'CreateManagedLayer(',
        '&layer,*m_display,m_aruid)',
        '&layer,*c->display,m_aruid)',
        'GetPresentImage(p[5])',
        'GetLayerProducerHandle(',
        'std::make_shared<android::GraphicBuffer>(',
        'c->producer->AttachBuffer(&idx,buffer)',
        'c->producer->QueueBuffer(idx,input,&output)',
        'c.producer->DetachNextBuffer(',
        'c.release_fences[slot]=release_fence',
        'const std::size_t fence_count = fence.num_fences;',
        'if (fence_count > fence.fences.size()) continue;',
        'for (std::size_t i=0;i<fence_count;++i) {',
        'if (point.id == -1) continue;',
        'if(!image||!image->window_pool||!m_native_module)return {}',
        'GetSyncpointManager().IsSyncpointAllocated(fence)',
        'c->retained[slot]=buffer',
        'backing_handle->Duplicate(true)',
        'image->size>backing_handle->orig_size-offset',
        'backing_session->process != m_process',
        'FreeHandle(*id,true)',
        'syncpoints.HasSyncpointExpired(point.id,point.value)',
        '{111,&IVi2Session::OpenEndpoint,"OpenEndpoint"}',
        '{112,&IVi2Session::CloseEndpoint,"CloseEndpoint"}',
        '{352,&IVi2Session::OutputLevels,"SetClientOutputLevels"}',
        '{106,&IVi2Session::MaxResolution,"GetBufferMaxResolution"}',
        'c->queued_modules[slot]=img->module',
        'it->available_bit=p[5]',
        'Signal(c.available_bit)',
        'Signal(c->release_bit)',
        'client->output_levels=values;',
        'std::isfinite(v)',
        'native->format=android::PixelFormat::Rgba8888;',
        'pref[6]==1&&outw<=width&&outh<=height',
    ):
        assert evidence in text, "VI2 compositor must preserve real queue/fence owner: " + evidence
    # VI2 201 -> 212 -> 251 is observed in the MKW boot trace. A
    # registered client can query availability before display binding; the
    # real compositor layer is created by the bind, and reused on rebind.
    vi2_bind = text.split('void Bind(HLERequestContext& ctx) {',1)[1].split(
        'void Unbind(HLERequestContext& ctx) {',1)[0]
    vi2_avail = text.split('void Availability(HLERequestContext& ctx) {',1)[1].split(
        'void OutputLevels(HLERequestContext& ctx) {',1)[0]
    assert 'if(c->layer){' in vi2_bind
    assert 'c->layer=layer;' in vi2_bind and 'c->display=m_display;' in vi2_bind
    assert 'CreateManagedLayer(' in vi2_bind
    assert 'Client* c=Find(W(p,2));result=Kernel::ResultNotFound;' in vi2_avail
    assert 'if(c){' in vi2_avail and 'if(c&&c->display&&m_vi)' not in vi2_avail
    assert 'mask=c->available;' in vi2_avail
    # New source reflects actual upstream unsigned u32 ABI. Keep the same
    # fail-closed ordering: bound the four-element array BEFORE reading any
    # per-slot syncpoint and retain queued GPU backing while work is pending.
    fence_guard = text.split("const std::size_t fence_count = fence.num_fences;", 1)[1].split(
        "c.queued[slot].reset();", 1)[0]
    assert fence_guard.index("if (fence_count > fence.fences.size()) continue;") < (
        fence_guard.index("const auto& point=fence.fences[i];"))
    assert "if (!done) continue;" in fence_guard
    assert "fence.num_fences < 0" not in fence_guard

    for command, method in (
        (901, "InitializeVideoCodecContext"),
        (902, "OpenVideoDecoderSession"), (905, "OpenVideoDecoderSession"),
        (906, "OpenVideoDecoderSession"),
        (903, "ReleaseVideoDecoderAccess"),
        (911, "CreateVideoImagePool"), (912, "DestroyVideoImagePool"),
        (961, "GetCpuVideoImageDescriptor"),
        (426, "MapVideoGpuImage"), (427, "UnmapVideoGpuImage"),
        (428, "QueryVideoGpuImage"),
    ):
        assert '{'+str(command)+', &IGraphicsSupervisor::'+method in text
    init_video = text.split('void IGraphicsSupervisor::InitializeVideoCodecContext(HLERequestContext& ctx) {',1)[1].split('\n}',1)[0]
    release_video = text.split('void IGraphicsSupervisor::ReleaseVideoDecoderAccess(HLERequestContext& ctx) {',1)[1].split('\n}',1)[0]
    open_video = text.split('void IGraphicsSupervisor::OpenVideoDecoderSession(HLERequestContext& ctx) {',1)[1].split('\n}',1)[0]
    for proof in (
        'packet[0] == 16 + 903 && packet[1] == 0',
        'm_video_decoder_access_held && m_video_decoder_creator.expired()',
        'm_video_decoder_access_held = false;',
        'm_video_decoder_creator.reset();',
    ):
        assert proof in release_video, 'Missing libounce 903 root decoder release: '+proof
    assert 'cmd == 905 ? (w[1] == 1 && w[2] <= 0xffU)' in open_video
    assert '!m_video_decoder_access_held' in open_video
    assert 'creator = handler;' in open_video
    assert 'ctx.AddMoveObject(client);' in open_video
    assert open_video.index('ctx.AddMoveObject(client);') < open_video.index(
        'm_video_decoder_access_held = true;')
    assert 'm_video_decoder_creator = std::move(creator);' in open_video
    assert 'IPC::ResponseBuilder rb{ctx, 2, 0, 1};' in open_video
    for command in (1001, 1002):
        assert '{'+str(command)+', &IGraphicsSupervisor::UnavailableVideoEncoder' in text
    assert 'rb.Push(Kernel::ResultNotImplemented.raw);' in text
    # ID-known / ABI-unknown commands must use fail-closed generic TIPC fallbacks,
    # not fabricated payload-aware stubs. Display fallback lives in the same owner.
    gsv_fallback = text.split(
        'Result IGraphicsSupervisor::HandleSyncRequest(Kernel::KServerSession& session,', 1
    )[1].split('void IGraphicsSupervisor::Initialize(', 1)[0]
    assert 'handlers_tipc.contains(ctx.GetCommand())' in gsv_fallback
    assert 'Kernel::ResultNotImplemented.raw' in gsv_fallback
    vi2_fallback = text.split(
        'Result HandleSyncRequest(Kernel::KServerSession& session,HLERequestContext& ctx) override {', 1
    )[1].split('private:', 1)[0]
    assert 'handlers_tipc.contains(ctx.GetCommand())' in vi2_fallback
    assert 'Kernel::ResultNotImplemented.raw' in vi2_fallback
    gpu_worker = (ROOT / 'vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp').read_text()
    worker_fallback = gpu_worker.split(
        'Result IGpuWorker::HandleSyncRequest(Kernel::KServerSession& session,', 1
    )[1].split('namespace GW = GpuWorkerProtocol;', 1)[0]
    assert 'handlers_tipc.contains(ctx.GetCommand())' in worker_fallback
    assert 'Kernel::ResultNotImplemented.raw' in worker_fallback
    worker_213 = gpu_worker.split(
        'void IGpuWorker::NormalUnmapGpuMemory4K(HLERequestContext& ctx) {', 1
    )[1].split('void IGpuWorker::CreateSparseRegion(HLERequestContext& ctx) {', 1)[0]
    assert 'IPC::ResponseBuilder rb{ctx, 2};' in worker_213
    assert 'rb.Push(unmapped);' not in worker_213
    for fw19 in (201, 202, 203, 204, 205, 207):
        assert ('{'+str(fw19)+', &IGpuWorker::') not in gpu_worker
    gpu_session = (ROOT / 'vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp').read_text()
    gpu_fallback = gpu_session.split(
        'Result IGpuSession::HandleSyncRequest(Kernel::KServerSession& session,', 1
    )[1].split('static Result Translate(', 1)[0]
    assert 'handlers_tipc.contains(ctx.GetCommand())' in gpu_fallback
    assert 'Kernel::ResultNotImplemented.raw' in gpu_fallback
    # 1691 is no longer ABI-unknown: it shares the reviewed feature-image
    # requirements-only calculator with 391/691/1291 below.
    for unknown in (12, 327, 437, 1061):
        assert ('{'+str(unknown)+', &IGraphicsSupervisor::') not in text
    # Lichii-known IDs below are deliberately registered and fail closed.
    lichii_fail_closed = (
        5, 120, 121, 122, 123, 124, 125, 131, 133,
        311, 312, 321, 361, 424, 425, 436,
        461, 462, 463, 464, 465, 466, 467, 468, 494,
        801, 802, 803, 811, 812, 813, 814, 861,
        1091, 1503, 1601, 1602, 1603, 1611, 1612,
    )
    for command in lichii_fail_closed:
        assert ('{'+str(command)+', &IGraphicsSupervisor::UnavailableDocumentedFeature') in text, command
    # VI2 53 now has a reviewed native timestamp reply. The other Lichii-
    # documented IDs are intentionally registered but must reject unknown
    # payloads: a structural stub is not an implemented ABI.
    assert '{53,&IVi2Session::GetRecordedTimestamps,"GetRecordedTimestamps"}' in text
    timestamps = text.split(
        'void GetRecordedTimestamps(HLERequestContext& ctx) {', 1
    )[1].split('void Event(HLERequestContext& ctx) {', 1)[0]
    for witness in (
        'const u32 recorder = p[5];',
        'recorder >= m_recorded_ticks.size()',
        'ctx.GetWriteBufferSize(0)',
        'ctx.WriteBufferB(ticks.data(), requested, 0)',
        'NativeTipcReplyWords(ctx, {static_cast<u32>(written), 0, 0});',
    ):
        assert witness in timestamps, "VI2 53 lost its bounded timestamp response: " + witness
    vi2_unknown = (
        13, 107, 108, 113, 230, 231, 232, 301, 302,
        353, 354, 355, 356, 358, 359,
    )
    for command in vi2_unknown:
        assert ('{'+str(command)+',&IVi2Session::Unsupported,"Unknown'+str(command)+'"}') in text, (
            f'VI2 unknown command {command} must be registered fail-closed')
    vi2_reject = text.split('void Unsupported(HLERequestContext& ctx) {', 1)[1].split(
        'void Handshake(HLERequestContext& ctx) {', 1)[0]
    assert 'rb.Push(Kernel::ResultNotImplemented.raw);' in vi2_reject
    assert 'ResultSuccess' not in vi2_reject
    assert '{102, &IGpuSession::' not in gpu_session
    # Each known optional GSV command is registered in the selected C++ owner.
    # These are not implementations: no fabricated success/handles for unsupported features.
    known_optional_gsv = (
        187, 211, 212, 213, 214, 215, 493, 612, 613, 614, 615,
        616, 620, 621, 622, 623, 624, 626, 627, 628, 629, 630, 632,
        633, 634, 636, 637, 638, 639, 640, 641, 650, 651, 652, 653,
        654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665,
        666, 667, 904, 921, 922, 1003, 1004, 1011, 1012, 1021,
        1022, 1203, 1301, 1302, 1325, 1326,
    )
    assert len(known_optional_gsv) == len(set(known_optional_gsv)) == 63
    assert '{126, &IGraphicsSupervisor::QuerySessionMode, "GetSessionFlag"}' in text
    assert 'm_bootstrap.QuerySessionMode(packet, mode)' in text
    for command in (1501, 1502):
        assert f'{{{command}, &IGraphicsSupervisor::InitializeInterModuleImageContext' in text
    assert 'm_bootstrap.InitializeInterModuleImageContext(packet, ctx.GetCommand())' in text
    for command in known_optional_gsv:
        assert ('{'+str(command)+', &IGraphicsSupervisor::UnavailableDocumentedFeature') in text, (
            f'optional GSV command {command} missing explicit fail-closed dispatch')
    # GSV 603 is no longer a generic stub: SDK 21 releases a real 602 MOVE
    # child context, while malformed and double-destroy calls fail closed.
    assert '{603, &IGraphicsSupervisor::DestroyCameraContext, "DestroyCameraContext"}' in text
    camera_open = text.split('void IGraphicsSupervisor::OpenCameraSession(HLERequestContext& ctx) {', 1)[1].split(
        'void IGraphicsSupervisor::DestroyCameraContext(HLERequestContext& ctx) {', 1)[0]
    camera_close = text.split('void IGraphicsSupervisor::DestroyCameraContext(HLERequestContext& ctx) {', 1)[1].split(
        'void IGraphicsSupervisor::OpenChatSession(HLERequestContext& ctx) {', 1)[0]
    assert camera_open.index('ctx.AddMoveObject(client);') < camera_open.index('++m_camera_contexts;')
    for proof in ('packet[0] == 16 + 603 && packet[1] == 0',
                  'if (m_camera_contexts != 0)', '--m_camera_contexts;',
                  'Kernel::ResultInvalidState'):
        assert proof in camera_close, proof
    assert 'rb.Push(result.raw);' in camera_close
    assert '{1411, &IGraphicsSupervisor::QueryNvDrvTransferMemoryUsage' in text
    usage = text.split('void IGraphicsSupervisor::QueryNvDrvTransferMemoryUsage(',1)[1].split('\n}',1)[0]
    assert 'm_nvsrv_session.lock()' in usage
    assert 'm_nvsrv_transfer_memory_size >> 32' in usage
    assert 'm_bootstrap_transfer_memory' not in usage
    explicit_reject = text.split(
        'void IGraphicsSupervisor::UnavailableDocumentedFeature(HLERequestContext& ctx) {', 1)[1].split('\n}', 1)[0]
    assert 'IPC::ResponseBuilder rb{ctx, 2};' in explicit_reject
    assert 'rb.Push(Kernel::ResultNotImplemented.raw);' in explicit_reject
    assert 'ResultSuccess' not in explicit_reject
    assert 'ctx.CommandBuffer()' not in explicit_reject
    # libounce _gsvSyncCreate: 21 configures the event slot count.
    assert '{21, &INativeSyncptSession::ConfigureSlots, "ConfigureSlots"}' in text
    syncpt21 = text.split('void ConfigureSlots(HLERequestContext& ctx) {', 1)[1].split(
        '    void QueryCounter(HLERequestContext& ctx) {', 1)[0]
    assert 'DecodeSyncptSlotCount(packet)' in syncpt21
    assert 'm_configured_slots = *count;' in syncpt21
    assert 'm_events.begin() + *count' in syncpt21
    assert 'if (slot >= m_configured_slots) return nullptr;' in text
    # GSV 202: no input payload and one real MOVE session handle.
    syncpt_open = text.split('void IGraphicsSupervisor::OpenSyncptSession(HLERequestContext& ctx) {', 1)[1].split('\n}', 1)[0]
    assert 'packet[0] != 16 + 202 || packet[1] != 0' in syncpt_open
    assert 'Kernel::ResultInvalidCombination.raw' in syncpt_open
    assert 'ctx.AddMoveObject(client);' in syncpt_open
    assert 'm_bootstrap.CurrentPhase() != GB::Phase::Ready' in syncpt_open
    assert '!m_syncpt_session.expired()' in syncpt_open
    assert syncpt_open.index('ctx.AddMoveObject(client);') < syncpt_open.index('m_syncpt_session = handler;')
    assert 'IPC::ResponseBuilder rb{ctx, 2, 0, 1};' in syncpt_open
    assert '{101, &IGraphicsSupervisor::CompleteBootstrap' in text
    assert '{301, &IGraphicsSupervisor::InitializeDisplayContext' in text
    assert '{305, &IGraphicsSupervisor::OpenDisplaySession' in text
    # GSV child sessions use true MOVE descriptors and never leak on OOM.
    camera = text.split(
        'void IGraphicsSupervisor::OpenCameraSession(HLERequestContext& ctx) {', 1)[1].split('\n}', 1)[0]
    assert 'const u64 version = u64{packet[2]} | (u64{packet[3]} << 32);' in camera
    assert 'packet[0] != 16 + 602 || packet[1] != 2 || version != 1' in camera
    for command, method in ((602, 'OpenCameraSession'), (1202, 'OpenChatSession')):
        body = text.split(
            f'void IGraphicsSupervisor::{method}(HLERequestContext& ctx) {{', 1)[1].split('\n}', 1)[0]
        assert 'IPC::ResponseBuilder rb{ctx, 2, 1, 0};' not in body
        assert 'IPC::ResponseBuilder rb{ctx, 2, 0, 1};' in body
        assert 'ctx.AddMoveObject(client);' in body
        assert 'client->Close(system.Kernel());' in body
        assert body.index('ctx.AddMoveObject(client);') < body.index(
            'IPC::ResponseBuilder rb{ctx, 2, 0, 1};')
    chat = text.split(
        'void IGraphicsSupervisor::OpenChatSession(HLERequestContext& ctx) {', 1)[1].split('\n}', 1)[0]
    assert 'packet[0] != 16 + 1202 || packet[1] != 0' in chat
    feature_admission = text.split(
        'void IGraphicsSupervisor::InitializeFeatureContext(HLERequestContext& ctx) {', 1)[1].split('\n}', 1)[0]
    assert 'command == 601 || command == 1201' in feature_admission
    assert 'packet[0] == 16 + command && packet[1] == 0' in feature_admission
    assert 'ResultInvalidCombination.raw' in feature_admission
    # S2 control-GPU pause and scheduling options must fail closed exactly.
    ctrl_gpu = (ROOT / 'vendor/encore-active/ns2-runtime/nvdrv/core/hle/'
                'service/nvdrv/devices/nvhost_ctrl_gpu.cpp').read_text()
    for num, raw in ((0x10, '0xC0084710U'), (0x1e, '0xC010471EU')):
        case = ctrl_gpu.split(f'case 0x{num:x}: // Switch 2 ', 1)[1].split('case ', 1)[0]
        assert f'if (command.raw != {raw}) break;' in case
        assert 'return NvResult::NotImplemented;' in case
    # Common feature-image sizing IDs use the same requirements-only layout
    # calculator. This must not create/map images or fabricate unknown formats.
    for command in (391, 691, 1291, 1691):
        assert ('{'+str(command)+', &IGraphicsSupervisor::CalculateFeatureImagePoolRequirements') in text
        assert ('{'+str(command)+', &IGraphicsSupervisor::UnavailableDocumentedFeature') not in text
    feature_sizer = text.split(
        'void IGraphicsSupervisor::CalculateFeatureImagePoolRequirements(HLERequestContext& ctx) {', 1
    )[1].split('static std::optional<NativeImageRequirements> ParseNativeImageRequest', 1)[0]
    assert 'CalculateFeatureImageRequirements(preference, packet[18])' in feature_sizer
    assert 'packet[1] == 17' in feature_sizer
    assert 'CreateNativeImage' not in feature_sizer
    layout_source = (ROOT / 'vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h').read_text()
    for proof in ('case 1:', 'case 4:', 'case 5:', 'case 0x38:',
                  'const u64 count = std::max<u64>(requested_count, 1);',
                  'const u64 alignment = std::max<u64>(4096, 64 * block_rows);'):
        assert proof in layout_source
    for proof in ('command == 901',
                  'packet[0] == command + 0x10 && packet[1] == 0',
                  'm_bootstrap.GpuContextReady()',
                  'source ? source->GetModule() : nullptr',
                  'if (module) result = ResultSuccess;'):
        assert proof in init_video, 'Missing fail-closed real video context admission: '+proof
    for snippet in (
        'CalculateNativeVideoImageLayout(preference, count)',
        'm_video_pools.Add(static_cast<u32>(m_next_image_id),',
        'm_native_memory.Get(backing)',
        'session && session->process == m_process',
        'handle->Duplicate(true)',
        'nvmap.PinHandle(backing, false)',
        'm_video_pools.Lookup(packet[2])',
        'm_video_pools.CpuImageDescriptor(packet[2])',
        'IPC::ResponseBuilder rb{ctx, 34};',

        'FindRegisteredGpuAddressSpace(packet[4])',
        'as->MapNativeImage(',
        'it->second.address_space->UnmapNative4K(',
        'm_video_mappings.erase(it)',
        'it->second.address_space == as',
        'const auto as = FindRegisteredGpuAddressSpace(packet[3]);',
        'nvmap.UnpinHandle(pool->backing)',
        'm_video_pools.GetByImage(packet[2])',
        'm_video_pools.RetireImage(packet[2])',
        'pool->remaining > 1',
        'm_video_pools.Remove(pool->first_id)',
        'for (const auto& [key, mapping] : m_video_mappings)',
    ):
        assert snippet in text, "Missing real NS2 video pool/GMMU ownership: " + snippet
    video_map = text.split('void IGraphicsSupervisor::MapVideoGpuImage(', 1)[1].split(
        'void IGraphicsSupervisor::UnmapVideoGpuImage(', 1)[0]
    # A pre-allocated owner is required before MapNativeImage can acquire
    # a real VA and pin. Never turn a failed map into a guest-visible ID.
    assert (video_map.index('m_video_mappings.try_emplace(') <
            video_map.index('as->MapNativeImage(') <
            video_map.index('staged->second.address = address;'))
    assert 'm_video_mappings.erase(staged);' in video_map
    assert 'catch (const std::bad_alloc&)' in video_map

    # Native GameChat pools and decoder pools intentionally use different
    # 426/428 reply ABIs. Keep both contracts explicit.
    layout_h = (ROOT / 'vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h').read_text()
    for snippet in ('native_gpu_layout{}', 'gpu_layout_code{}',
                    'block_height_log2{}', 'pitch_gobs{}'):
        assert snippet in layout_h, 'Missing GameChat native-image layout ABI: ' + snippet
    query_gpu = text.split(
        'void IGraphicsSupervisor::QueryVideoGpuImage(', 1
    )[1].split('void IGraphicsSupervisor::MapVideoGpuImage(', 1)[0]
    assert 'if (image->native_gpu_layout)' in query_gpu
    assert 'rb.Push(image_offset);' in query_gpu
    assert 'descriptor[2] = u64{image->block_height_log2}' in query_gpu
    assert 'if (image->native_gpu_layout)' in video_map
    assert 'second_reply = image->offset;' in video_map
    assert 'second_reply = address + size - 1;' in video_map
    assert 'descriptor[5] &= 0xffffffff00000000ULL;' in video_map

    assert '{423, &IGraphicsSupervisor::BindNativeGpuMemory' in text
    for snippet in (
        'GraphicsSupervisorProtocol::DecodeNativeParentBind(packet)',
        'session && session->process == m_process',
        'parent->Duplicate(true)',
        'nvmap.PinHandle(request->parent, false)',
        'nvmap.UnpinHandle(request->parent)',
        'nvmap.FreeHandle(request->parent, true)',
        'm_native_parents.try_emplace(',
        'm_native_parents.find(packet[2])',
        'result = BindNativeMemoryBacking(',
        'for (const auto& [child, parent] : m_native_parents)',
    ):
        assert snippet in text, "Missing real parent GSV 423 lifecycle: " + snippet
    parent_bind = text.split('void IGraphicsSupervisor::BindNativeGpuMemory(', 1)[1].split(
        'std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>', 1)[0]
    # A 423 child that has already been bound must never depend on a
    # subsequent fallible map allocation to remember its parent NVMap pin.
    assert (parent_bind.index('m_native_parents.try_emplace(') <
            parent_bind.index('parent->Duplicate(true)') <
            parent_bind.index('nvmap.PinHandle(request->parent, false)') <
            parent_bind.index('result = BindNativeMemoryBacking('))
    assert 'm_native_parents.erase(staged_parent);' in parent_bind
    assert 'catch (const std::bad_alloc&)' in parent_bind
    backing = text.split('Result IGraphicsSupervisor::BindNativeMemoryBacking(', 1)[1].split(
        'void IGraphicsSupervisor::BindNativeMemory(', 1)[0]
    # First-use NVDRV session creation can allocate; it must finish
    # before KPageTable::LockForMapDeviceAddressSpace side effects.
    assert backing.index('OpenSession(m_process).id') < backing.index(
        'LockForMapDeviceAddressSpace(')
    assert 'catch (const std::bad_alloc&)' in backing

    for command in (314,315):
        assert '{'+str(command)+', &IGraphicsSupervisor::ConfigureNativeWindowImagePool' in text
    window_pool = text.split('void IGraphicsSupervisor::ConfigureNativeWindowImagePool(', 1)[1].split(
        'void IGraphicsSupervisor::DestroyNativeImage(', 1)[0]
    assert 'const u32 count = create ? packet[3] : 0;' in window_pool
    assert 'm_native_images.ConfigureWindowPool(packet[2], count, create)' in window_pool
    assert 'packet[3] == 1' not in window_pool
    assert '!image->window_pool' in text
    for command, method in ((429,"CreateNativeImage"), (430,"DestroyNativeImage")):
        assert '{'+str(command)+', &IGraphicsSupervisor::'+method in text
    video_destroy = text.split('void IGraphicsSupervisor::DestroyVideoImagePool(', 1)[1].split(
        'void IGraphicsSupervisor::GetCpuVideoImageDescriptor(', 1)[0]
    assert 'chat_pool ? m_video_pools.Get(packet[2])' in video_destroy
    assert 'm_video_pools.GetByImage(packet[2])' in video_destroy
    assert 'if (!chat_pool && pool->remaining > 1)' in video_destroy
    assert 'm_video_pools.RetireImage(packet[2])' in video_destroy
    assert 'chat_pool ? m_video_pools.Remove(pool->first_id)' in video_destroy
    # Native present can fail allocations before or after its NVMap dupe.
    # A later shared_ptr control-block OOM must release the duplicate and
    # the service must return a refused image instead of throwing into IPC.
    vi2_lease = text.split('IGraphicsSupervisor::GetPresentImage(u32 id) {', 1)[1].split(
        'void IGraphicsSupervisor::InitializeDisplayContext(', 1)[0]
    assert vi2_lease.index('std::make_unique<u32>(backing)') < vi2_lease.index(
        'backing_handle->Duplicate(true)') < vi2_lease.index('lease_token.release()')
    assert vi2_lease.count('catch (const std::bad_alloc&)') == 2
    image_create = text.split('void IGraphicsSupervisor::CreateNativeImage(', 1)[1].split(
        'void IGraphicsSupervisor::ConfigureNativeWindowImagePool(', 1)[0]
    assert 'catch (const std::bad_alloc&)' in image_create
    # Reviewed 429 ABI: count=0 requests one image, matching Lichii/Eglantine.
    assert 'const u32 count = std::max<u32>(packet[18], 1);' in image_create
    assert 'const auto requirements = ::Service::AM::CalculateNativeImageRequirements(preferences, count);' in image_create
    assert 'm_next_image_id += count;' in image_create
    assert 'duplicated < count' in image_create and 'while (duplicated != 0)' in image_create
    assert 'packet[3] == 1' not in image_create
    assert 'image->offset > handle->orig_size' in vi2_lease
    assert image_create.index('m_native_images.Create(') < image_create.index(
        'catch (const std::bad_alloc&)') < image_create.index(
        'result = Kernel::ResultOutOfResource;',
        image_create.index('catch (const std::bad_alloc&)'))
    assert (ROOT / 'tools/ns2/check_native_vi2_oom_host.py').is_file()
    for snippet in (
        'm_native_images.Create(',
        'm_native_images.Destroy(packet[2])',
        'static_cast<u32>(m_next_image_id)',
        'handle->Duplicate(true)',
        'FreeHandle(\n                image->backing, true)',
        'for (const auto& [image_id, image] : m_native_images.Records())',
    ):
        assert snippet in text, "Missing native image NVMap ownership: " + snippet
    worker = (ROOT / 'vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp').read_text()
    dense = worker.split('Result IGpuWorker::BackGpuOnlyRegion(',1)[1].split(
        'bool IGpuWorker::RetireGpuOnlyRegion(',1)[0]
    assert dense.index('pending_region.try_emplace(') < dense.index(
        'memory.AllocateAndOpen(') < dense.index('RemapNativeSparse(') < dense.index(
        'm_dense_regions.merge(pending_region);')
    assert 'm_dense_regions.emplace(' not in dense
    assert (ROOT / 'tools/ns2/check_native_dense_ledger_oom_host.py').is_file()
    vsync_owner = text.split('void VsyncEvent(HLERequestContext& ctx) {', 1)[1].split(
        'void Notifications(HLERequestContext& ctx) {', 1)[0]
    assert vsync_owner.index('m_vsync_events.reserve(GraphicsSupervisorProtocol::RequestGroupCount);') < vsync_owner.index(
        'm_context.CreateEvent("NativeVi2Vsync")')
    assert vsync_owner.index('m_vsync->events.reserve(GraphicsSupervisorProtocol::RequestGroupCount);') < vsync_owner.index(
        'm_context.CreateEvent("NativeVi2Vsync")')
    assert vsync_owner.index('m_vsync->events.pop_back();') < vsync_owner.index(
        'm_context.CloseEvent(event);')
    assert (ROOT / 'tools/ns2/check_native_vi2_vsync_oom_host.py').is_file()
    present = text.split('void Present(HLERequestContext& ctx) {',1)[1].split(
        'void Cancel(HLERequestContext& ctx) {',1)[0]
    assert present.index('if(result.IsSuccess() && !m_poll){') < present.index(
        'c->producer->QueueBuffer(')
    assert 'm_poll=std::move(timer);' in present
    assert 'catch (const std::bad_alloc&)' in present
    assert (ROOT / 'tools/ns2/check_native_vi2_present_release_order_host.py').is_file()
    assert 'GpuContextReady()' in text
    assert 'ResultNotImplemented.raw' in text
    assert 'ResultInvalidCurrentMemory' in text
    for command, method in ((435,"CalculateNativeImageSize"),(1510,"CalculateNativeImageRequirements")):
        assert '{'+str(command)+', &IGraphicsSupervisor::'+method in text
    assert 'CalculateNativeImageRequirements(std::span<const u32>{data + 2, 16}, data[18])' in text
    assert 'if (data[1] != 17) return {};' in text
    assert 'rb.Push(request ? static_cast<u32>(request->alignment)' in text
    assert 'Kernel::KMemoryState::FlagMapped' in text
    compiler=shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        print("C++20 compiler missing",file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="encore-ns2-graphics-hle-") as tmp:
        for opt in ("-O0","-O2"):
            exe=Path(tmp)/("test"+opt)
            command=[compiler,"-std=c++20","-Wall","-Wextra","-Werror",
                     "-pedantic","-fsanitize=undefined","-fno-sanitize-recover=all",
                     opt,"-I",str(HEADERS),"-I",str(NVDRV),"-I",str(EDEN),str(SOURCE),
                     "-o",str(exe)]
            subprocess.run(command,check=True)
            subprocess.run([str(exe)],check=True,env={
                **os.environ,"UBSAN_OPTIONS":"halt_on_error=1"})
    print("No real NVDRV GPU session, PS5 rendering or game compatibility inferred.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
