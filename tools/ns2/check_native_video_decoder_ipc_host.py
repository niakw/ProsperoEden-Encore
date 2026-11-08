#!/usr/bin/env python3
"""P1.3: compile/replay actual decoder Pump and its real IPC owner contracts."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
vroot=root/'vendor'
if not (vroot/'encore-active').exists():
    vroot=root.parent/'vendor'  # isolated sparse checkout only
vroot=vroot/'encore-active/ns2-runtime'
source=(vroot/'video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp').read_text()
header=(vroot/'video_decoder/core/hle/service/am/service/graphics_video_decoder_session.h').read_text()
supervisor=(vroot/'graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp').read_text()
sh=(vroot/'graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h').read_text()
backend=(vroot/'video_decoder/video_core/host1x/nx2_video_decoder.cpp').read_text()
recipe=(root/'headless/CMakeLists.txt').read_text()
for cmd in (902,905,906,1002):
    assert f'{{{cmd}, &IGraphicsSupervisor::OpenVideoDecoderSession' in supervisor
for cmd, method in ((1,'CreateDecoderService'),(3,'GetEvent'),(6,'Start'),
                   (8,'Stop'),(101,'Configure'),(109,'SubmitInput'),
                   (115,'Finalize'),(200,'Initialize'),(201,'Initialize'),
                   (202,'Initialize'),(207,'Stop'),(212,'UnregisterBuffer'),
                   (213,'GetOutputInfo'),(311,'RegisterBuffer'),
                   (314,'ReleaseBuffer'),(400,'SubmitInput')):
    assert f'{{{cmd}, &IGraphicsVideoDecoderSession::{method}' in source
assert 'GetObjectFromHandle<Kernel::KTransferMemory>' in source
assert 'CreateMetadataSession(system, ctx, std::move(handler), &client)' in supervisor
assert 'm_owner->OpenVideoDecoderChildSession(ctx)' in source
assert 'm_context.CreateEvent("NS2VideoInputReady")' in source
assert 'm_ready_timer = Core::Timing::CreateEvent(' in source
assert 'ScheduleLoopingEvent(Interval, Interval, m_ready_timer)' in source
assert 'm_ready->Detach();' in source
assert 'UnscheduleEvent(m_ready_timer)' in source
assert source.index('m_ready->Detach();') < source.index('m_context.CloseEvent(m_event)')
assert 'rb.PushCopyObjects(ctx, m_event->GetReadableEvent());' in source
assert '!compressed.empty() && !m_decoder->Decode(compressed, pts, decoded)' in source
assert 'eos && !m_decoder->Drain(decoded)' in source
assert 'if (!m_decoder->Render(frame.picture,' in source
assert 'm_owner->WriteVideoSurface(next.id, *target, pixels)' in source
assert 'target->gpu_mapped && !target->layout.nv12' in source
assert 'Tegra::Texture::CalculateSize(true, BytesPerPixel' in source
assert 'Tegra::Texture::SwizzleTexture(tiled, pixels' in source
assert 'gpu_mapped != expected.gpu_mapped' in supervisor
assert 'entry.first.second == image_id && entry.second.references != 0;' in supervisor
assert 'm_registered.contains(image)' in source
assert 'm_guest_owned.contains(image)' in source
assert 'if (m_creator || !m_started || m_finalized)' in source
assert 'm_syncpoint = id;' in source
assert 'GetGuestSyncpointValue(id)' in source
assert 'm_bootstrap.GpuContextReady()' in supervisor
assert 'const bool shape = (cmd == 902 || cmd == 1002)' in supervisor
assert 'GetObjectFromHandle' in supervisor
assert 'IsValidVirtualAddressRange(' in supervisor
assert 'record->guest_address + view->offset != expected.address' in supervisor
assert 'm_process->GetMemory().WriteBlock(' in supervisor
assert 'system.GPU().InvalidateRegion(' in supervisor
assert 'return true;' in supervisor
assert 'target_sources(core PRIVATE "${EDEN_SHARED_NATIVE_VIDEO_SESSION_SOURCE}")' in recipe
assert 'friend class IGraphicsVideoDecoderSession' in sh
assert 'std::deque<PendingPicture> m_pending;' in header
assert 'bool Nx2VideoDecoder::Render(' in backend
assert 'sent = impl->context->SendPacket(packet);' in backend
assert 'avcodec_send_packet(impl->raw_context, packet.GetPacket())' in backend
assert 'impl->pending_pts.erase(it);' in backend
assert 'impl->pending_pts.erase(it);' in backend
assert 'std::nullopt' in backend
start='void IGraphicsVideoDecoderSession::Pump() {'
end='\nvoid IGraphicsVideoDecoderSession::SubmitInput('
assert source.count(start)==source.count(end)==1
method=source[source.index(start):source.index(end,source.index(start))]
assert method.index('if (!m_owner->WriteVideoSurface(') < method.index('syncpoints.IncrementGuest(m_syncpoint)')
assert 'IsReadyGuest(next.release->id, next.release->value)' in method
assert 'if (!m_decoder->Render(' in method
assert 'VideoDecoderProtocol::MarkLastEos(m_pending, m_outputs)' in source
assert 'VideoDecoderProtocol::IsWorkBufferOwned(memory.GetPointerUnsafe(),' in source
assert 'VideoDecoderProtocol::IsValidWorkBufferSize(memory->GetSize())' in source
assert 'm_work_buffer = std::move(memory);' in source
assert 'm_work_buffer.Reset(nullptr);' in source
assert 'Kernel::KScopedAutoObject<Kernel::KTransferMemory> m_work_buffer;' in header
assert 'compressed.empty() && !eos' in source
assert 'std::numeric_limits<s64>::max()' in source

fixture=r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <deque>
#include <memory>
#include <optional>
#include <set>
#include <span>
#include <vector>
using u8=std::uint8_t;using u32=std::uint32_t;using u64=std::uint64_t;
namespace Tegra::Host1x {
 enum class Nx2PictureFormat { Nv12, Bgra8, Rgba8 };
 struct Nx2Picture {u32 width{};u32 height{};u64 pts{};std::shared_ptr<int> frame;};
}
struct FakeSyncpoints {
 std::array<u32, 192> values{};
 bool IsReadyGuest(u32 id,u32 value)const{return values.at(id)>=value;}
 void IncrementGuest(u32 id){++values.at(id);}
};
struct FakeHost {FakeSyncpoints sync;FakeSyncpoints& GetSyncpointManager(){return sync;}};
struct FakeSystem {FakeHost host;FakeHost& Host1x(){return host;}int kernel{};int& Kernel(){return kernel;}};
struct FakeLayout {std::size_t image_bytes{64};u32 row_bytes{16};u32 chroma_offset{};u32 cpu_kind{8};bool nv12{};};
struct FakeOwner {
 struct VideoSurface {FakeLayout layout{};u32 width{4};u32 height{4};bool gpu_mapped{};};
 bool valid{true};bool writability{true};bool gpu{};bool nv12{};u32 writes{};std::vector<u8> last;
 std::optional<VideoSurface> LookupVideoSurface(u32)const{
  if (!valid) return {};
  return VideoSurface{FakeLayout{64,16,0,nv12?10U:8U,nv12},4,4,gpu};
 }
 bool WriteVideoSurface(u32,const VideoSurface& expected,std::span<const u8> bytes){
  if (!writability || expected.gpu_mapped != gpu) return false;
  ++writes;last.assign(bytes.begin(),bytes.end());return true;
 }
};
struct FakeDecoder {
 bool renderrunnable{true};
 bool Render(const Tegra::Host1x::Nx2Picture&,Tegra::Host1x::Nx2PictureFormat,
             u32,u32,u64,u64,std::span<u8> pixels){
  if(!renderrunnable)return false;
  std::fill(pixels.begin(),pixels.end(),u8{0xa5});return true;
 }
};
struct FakeEvent {u32 signals{};void Signal(int&){++signals;}};
struct FakeReady {bool room{};unsigned pulse{};void SetRoom(bool r){room=r;}void Notify(){if(room)++pulse;}};
namespace Tegra::Texture {
 inline unsigned swizzles{};
 std::size_t CalculateSize(bool, u32 bpp,u32 width,u32 height,u32,u32,u32){
  return std::size_t{bpp}*width*height;
 }
 void SwizzleTexture(std::span<u8> tiled,std::span<const u8> linear,u32,u32,u32,u32,u32,u32,
                     u32=1){
  ++swizzles;
  assert(tiled.size()>=linear.size());
  for(std::size_t i=0;i<linear.size();++i)tiled[i]=linear[i]^u8{0xff};
 }
}
struct IGraphicsVideoDecoderSession {
 static constexpr u32 NoSyncpoint=~u32{0};
 static constexpr std::size_t MaxFrames=16;
 static constexpr std::size_t MaxOutputs=128;
 struct ReleaseFence{u32 id{};u32 value{};};
 struct AvailableImage{u32 id{};std::optional<ReleaseFence> release;};
 struct PendingPicture{Tegra::Host1x::Nx2Picture picture;bool eos{};};
 struct Output{u32 image{},width{},height{};u64 pts{};bool eos{};};
 FakeSystem system;
 std::shared_ptr<FakeOwner> m_owner=std::make_shared<FakeOwner>();
 std::unique_ptr<FakeDecoder> m_decoder=std::make_unique<FakeDecoder>();
 std::deque<PendingPicture> m_pending;
 std::deque<AvailableImage> m_available;
 std::deque<Output> m_outputs;
 std::set<u32> m_guest_owned;
 FakeEvent event;
 FakeEvent* m_event=&event;
 FakeReady ready;
 FakeReady* m_ready=&ready;
 u32 m_syncpoint{4};
 bool m_started{true};
 void Pump();
};
__ACTUAL_PUMP__
static IGraphicsVideoDecoderSession::PendingPicture Pic(u64 pts,bool eos=false){
 return {{4,4,pts,std::make_shared<int>(5)},eos};
}
int main(){
 IGraphicsVideoDecoderSession run;
 auto& sync=run.system.Host1x().GetSyncpointManager();
 run.m_available.push_back({10,{}});
 run.m_pending.push_back(Pic(333));
 run.Pump();
 assert(run.m_outputs.size()==1 && run.m_outputs.front().image==10);
 assert(sync.values[4]==1 && run.m_owner->writes==1);
 assert(run.m_owner->last.size()==64 && run.m_owner->last[0]==0xa5);
 assert(run.m_guest_owned.contains(10) && run.m_available.empty() && run.m_pending.empty());
 // The decoder must never signal a fence if the target was destroyed.
 run.m_owner->valid=false;
 run.m_pending.push_back(Pic(444));run.m_available.push_back({11,{}});
 run.Pump();
 assert(sync.values[4]==1 && run.m_owner->writes==1 && run.m_outputs.size()==1);
 assert(run.m_pending.size()==1 && run.m_available.size()==1);
 run.m_owner->valid=true;run.m_decoder->renderrunnable=false;
 run.Pump();
 assert(sync.values[4]==1 && run.m_owner->writes==1);
 run.m_decoder->renderrunnable=true;run.m_owner->writability=false;
 run.Pump();
 assert(sync.values[4]==1 && run.m_owner->writes==1);
 run.m_owner->writability=true;
 run.Pump();
 assert(sync.values[4]==2 && run.m_owner->writes==2);
 // A release fence not yet reached must defer a valid decoded image.
 run.m_pending.push_back(Pic(555,true));
 run.m_available.push_back({12,IGraphicsVideoDecoderSession::ReleaseFence{9,3}});
 run.Pump();
 assert(sync.values[4]==2 && run.m_owner->writes==2);
 sync.values[9]=3;
 run.Pump();
 assert(sync.values[4]==3 && run.m_owner->writes==3 && run.m_outputs.back().eos);
 // P1.3: a stalled fence may block its OWN image, never a later ready
 // surface. The old FIFO-front Pump failed to produce image 17 here.
 run.m_pending.push_back(Pic(600));
 run.m_available.push_back({16,IGraphicsVideoDecoderSession::ReleaseFence{9,5}});
 run.m_available.push_back({17,{}});
 run.Pump();
 assert(sync.values[4]==4 && run.m_owner->writes==4);
 assert(run.m_outputs.back().image==17 &&
        run.m_available.size()==1 && run.m_available.front().id==16 &&
        !run.m_pending.size());
 run.m_pending.push_back(Pic(601));
 run.Pump();
 assert(sync.values[4]==4 && run.m_pending.size()==1);
 sync.values[9]=5;
 run.Pump();
 assert(sync.values[4]==5 && run.m_owner->writes==5 &&
        run.m_outputs.back().image==16 && run.m_available.empty());
 // An unstarted or unconfigured decoder cannot emit a guest frame.
 run.m_pending.push_back(Pic(777));run.m_available.push_back({13,{}});
 run.m_started=false;run.Pump();
 assert(sync.values[4]==5 && run.m_owner->writes==5);
 run.m_started=true;run.m_decoder.reset();run.Pump();
 assert(sync.values[4]==5 && run.m_owner->writes==5);
 // Restore the valid codec: real RGB GPU maps require the tiled handoff.
 run.m_decoder=std::make_unique<FakeDecoder>();
 run.Pump();
 assert(sync.values[4]==6 && run.m_owner->writes==6);
 run.m_owner->gpu=true;
 run.m_available.push_back({14,{}});run.m_pending.push_back(Pic(888));
 run.Pump();
 assert(sync.values[4]==7 && run.m_owner->writes==7 &&
        run.m_owner->last[0]==0x5a && Tegra::Texture::swizzles==1);
 // NV12 is deliberately pitch-linear even when mapped by the GPU.
 run.m_owner->nv12=true;
 run.m_available.push_back({15,{}});run.m_pending.push_back(Pic(999));
 run.Pump();
 assert(sync.values[4]==8 && run.m_owner->writes==8 &&
        run.m_owner->last[0]==0xa5 && Tegra::Texture::swizzles==1);
}
'''.replace('__ACTUAL_PUMP__',method)
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-native-video-ipc-') as temp:
    file=Path(temp)/'ipc.cpp';file.write_text(fixture)
    for compiler in compilers:
        for opt in ('-O0','-O2'):
            exe=Path(temp)/(Path(compiler).name+opt)
            cmd=[compiler,'-std=c++20',opt,'-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',str(file),'-o',str(exe)]
            res=subprocess.run(cmd,text=True,capture_output=True,env=env,timeout=90)
            assert res.returncode==0,(cmd,res.stderr[-2600:])
            got=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=15)
            assert got.returncode==0,(cmd,got.stderr[-2600:])
            print(Path(compiler).name,opt,'P1_NATIVE_VIDEO_REAL_PUMP_PASS',flush=True)
print('P1_NATIVE_VIDEO_IPC_HOST_PASS actual_decoder=1 actual_guest_write=1 release_fence=held no_fake_frame=1 rgb_gpu_tiling=1 nv12_pitch_linear=1')
