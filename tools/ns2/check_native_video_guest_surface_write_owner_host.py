#!/usr/bin/env python3
"""H05: execute actual native GraphicsSupervisor::WriteVideoSurface on guest memory.

The exact maintained C++ owner is extracted, compiled and executed against
process/NVMap/mapping stand-ins. It rejects retired/foreign mappings without
writing bytes or invalidating GPU caches. Separately, the real FFmpeg/Pump
harness tests video decode; this test is not an authenticated live TIPC or
real Vulkan release-fence witness and cannot close H05 by itself.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp"
source=P.read_text()
start="bool IGraphicsSupervisor::WriteVideoSurface("
end="\n// 901 and 1001 are the SDK's video codec/server-context admission calls."
assert source.count(start)==source.count(end)==1
owner=start+source.split(start,1)[1].split(end,1)[0]
for requirement in (
    "m_native_memory_mutex", "m_video_pools.Lookup(image_id)",
    "view->backing != expected.backing", "gpu_mapped != expected.gpu_mapped",
    "session->process != m_process", "IsValidVirtualAddressRange(",
    "GetMemory().WriteBlock(", "system.GPU().InvalidateRegion("):
    assert requirement in owner,requirement
assert owner.index("GetMemory().WriteBlock(") < owner.index("system.GPU().InvalidateRegion(")
cpp=r"""
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <span>
#include <vector>
#include <cstdio>
using u8=std::uint8_t;using u32=std::uint32_t;using u64=std::uint64_t;
namespace Common {struct ProcessAddress{u64 address;};}
struct VideoSurface {
 struct Layout {std::size_t image_bytes{};bool nv12{};} layout;
 u32 image_id{};u64 backing{},address{};bool gpu_mapped{};
};
struct VideoPoolView {u64 backing{};std::size_t offset{},size{};};
struct VideoPool {
 std::optional<VideoPoolView> view;
 std::optional<VideoPoolView> Lookup(u32 id){return id==9?view:std::nullopt;}
};
struct MemoryRecord {bool bound{};u64 guest_address{};std::size_t size{};};
struct NativeMemory {
 std::optional<MemoryRecord> record;
 std::optional<MemoryRecord> Get(u64 id){return id==12?record:std::nullopt;}
};
struct GuestMemory {
 bool valid{true},writable{true};
 std::vector<u8> bytes=std::vector<u8>(4096,0xCC);
 unsigned writes{};
 bool IsValidVirtualAddressRange(Common::ProcessAddress address,std::size_t n){
  return valid&&address.address==0x2000&&n<=bytes.size();
 }
 bool WriteBlock(Common::ProcessAddress address,const u8* p,std::size_t n){
  if(!writable||address.address!=0x2000||n>bytes.size())return false;
  std::memcpy(bytes.data(),p,n);++writes;return true;
 }
};
struct KProcess {GuestMemory memory;GuestMemory& GetMemory(){return memory;}};
struct NvMapHandle {bool allocated{};u64 address{},d_address{};u32 session_id{};};
struct NvMapFile {
 std::optional<NvMapHandle> handle;
 const NvMapHandle* GetHandle(u64 id){return id==12&&handle?&*handle:nullptr;}
};
struct Session {KProcess* process{};};
struct ModuleContainer {
 NvMapFile nvmap;Session session;
 NvMapFile& GetNvMapFile(){return nvmap;}
 const Session* GetSession(u32 id)const{return id==34?&session:nullptr;}
};
struct NativeModule {ModuleContainer container;ModuleContainer& GetContainer(){return container;}};
struct GPU {
 unsigned invalidations{};u64 address{};std::size_t bytes{};
 void InvalidateRegion(u64 a,std::size_t n){++invalidations;address=a;bytes=n;}
};
struct System {struct GPU gpu;struct GPU& GPU(){return gpu;}};
struct Mapping {unsigned references{};};
struct IGraphicsSupervisor {
 std::mutex m_native_memory_mutex;
 VideoPool m_video_pools;
 NativeMemory m_native_memory;
 NativeModule* m_native_module{};
 KProcess* m_process{};
 std::map<std::pair<u32,u32>,Mapping> m_video_mappings;
 System& system;
 bool WriteVideoSurface(u32 image_id,const VideoSurface& expected,std::span<const u8> pixels);
};
__REAL_OWNER__
int main(){
 System sys;KProcess process;NativeModule module;
 IGraphicsSupervisor owner{{},{},{},&module,&process,{},sys};
 owner.m_video_pools.view=VideoPoolView{12,0,384};
 owner.m_native_memory.record=MemoryRecord{true,0x2000,4096};
 module.container.nvmap.handle=NvMapHandle{true,0x2000,0x9000,34};
 module.container.session.process=&process;
 VideoSurface surface{{384,true},9,12,0x2000,false};
 std::vector<u8> pixels(384);
 for(std::size_t i=0;i<pixels.size();++i)pixels[i]=u8((i*3+1)&0xff);
 auto safe=[&](){return process.memory.writes==0&&sys.gpu.invalidations==0&&
                        process.memory.bytes[0]==0xCC;};
 {auto bad=surface;bad.layout.image_bytes=385;
  assert(!owner.WriteVideoSurface(9,bad,pixels)&&safe());}
 {auto bad=surface;bad.image_id=8;
  assert(!owner.WriteVideoSurface(9,bad,pixels)&&safe());}
 {auto bad=surface;bad.backing=11;
  assert(!owner.WriteVideoSurface(9,bad,pixels)&&safe());}
 {auto bad=surface;bad.gpu_mapped=true;
  assert(!owner.WriteVideoSurface(9,bad,pixels)&&safe());}
 {auto save=module.container.session.process;
  module.container.session.process=nullptr;
  assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
  module.container.session.process=save;}
 {auto save=owner.m_native_memory.record;
  owner.m_native_memory.record->bound=false;
  assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
  owner.m_native_memory.record=save;}
 {auto save=owner.m_native_memory.record;
  owner.m_native_memory.record->guest_address=~u64{0};
  assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
  owner.m_native_memory.record=save;}
 {auto save=owner.m_video_pools.view;
  owner.m_video_pools.view->offset=4095;
  assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
  owner.m_video_pools.view=save;}
 {auto save=module.container.nvmap.handle;
  module.container.nvmap.handle->allocated=false;
  assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
  module.container.nvmap.handle=save;}
 process.memory.valid=false;
 assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
 process.memory.valid=true;
 process.memory.writable=false;
 assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
 process.memory.writable=true;
 owner.m_video_mappings[{1,9}]={1};
 assert(!owner.WriteVideoSurface(9,surface,pixels)&&safe());
 surface.gpu_mapped=true;
 assert(owner.WriteVideoSurface(9,surface,pixels));
 assert(process.memory.writes==1&&sys.gpu.invalidations==1&&
        sys.gpu.address==0x9000&&sys.gpu.bytes==pixels.size());
 assert(std::equal(pixels.begin(),pixels.end(),process.memory.bytes.begin()));
 std::puts("H05_REAL_GUEST_WRITE_OWNER_PASS bytes=384 gpu_invalidation_after_write=1"
           " invalid_mapping_and_foreign_process=refused negative_cases=12"
           " real_video_tipc=no real_vulkan_fence=no");
}
""".replace("__REAL_OWNER__",owner)
ccs=list(dict.fromkeys(c for c in
    (shutil.which("clang++"),shutil.which("g++")) if c))
assert ccs
with tempfile.TemporaryDirectory(prefix="eden-h05-real-guest-write-") as tmp:
    src=Path(tmp)/"host.cpp"
    src.write_text(cpp)
    for cc in ccs:
        for opt in ("-O0","-O2"):
            exe=Path(tmp)/(Path(cc).name.replace("+","p")+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-pthread",str(src),"-o",str(exe)]
            built=subprocess.run(args,text=True,capture_output=True,
                                 timeout=60,env=os.environ.copy())
            assert built.returncode==0,(cc,built.stderr[-6000:])
            result=subprocess.run([str(exe)],text=True,capture_output=True,
                                  timeout=25,env=os.environ.copy())
            assert result.returncode==0,(cc,result.stderr[-6000:])
            print(Path(cc).name,opt,result.stdout.strip(),flush=True)
