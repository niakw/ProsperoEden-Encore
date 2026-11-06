#!/usr/bin/env python3
"""P1: actual NVMap low-area and NVDEC IOCTL pin-failure propagation."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[2]
vroot=root/'vendor'
if not (vroot/'encore-active').exists():vroot=root.parent/'vendor'
core=(vroot/'encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp').read_text()
nvdec=(vroot/'encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvhost_nvdec_common.cpp').read_text()
as_gpu=(vroot/'encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp').read_text()
cmake=(root/'headless/CMakeLists.txt').read_text()
assert 'EDEN_MAINTAINED_NVDRV_NVDEC' in cmake
assert 'list(APPEND core_sources "${EDEN_MAINTAINED_NVDRV_NVDEC}")' in cmake
assert 'const DAddr base = nvmap.PinHandle(entry.handle, false);' in as_gpu
assert 'NativePinnedPhysicalSpan(base, source, size)' in as_gpu
assert 'if (base) nvmap.UnpinHandle(entry.handle);' in as_gpu
assert 'const DAddr pinned = nvmap.PinHandle(params.handle, false);' in as_gpu
assert 'NativePinnedPhysicalSpan(pinned, params.buffer_offset, size)' in as_gpu
assert 'if (pinned) nvmap.UnpinHandle(params.handle);' in as_gpu
assert as_gpu.index('NativePinnedPhysicalSpan(pinned, params.buffer_offset, size)') < as_gpu.index('const DAddr device_address = pinned + params.buffer_offset;')
start='    const auto map_low_area = [&]() -> bool {'
end='\n    if (!handle_description->pins) {'
assert core.count(start)==1
low_area=core[core.index(start):core.index(end,core.index(start))]
assert 'if (!address) return false;' in low_area
assert 'handle_description->aligned_size > std::numeric_limits<u32>::max()' in low_area
assert 'if (low_area_pin && !map_low_area()) {' in core
assert core.count('unmap_queue.push_back(handle_description);')==3
assert 'if (!handle_description->d_address) return 0;' in core

start='NvResult nvhost_nvdec_common::MapBuffer('
end='\nNvResult nvhost_nvdec_common::UnmapBuffer('
assert nvdec.count(start)==nvdec.count(end)==1
fn=nvdec[nvdec.index(start):nvdec.index(end,nvdec.index(start))]
method=fn[fn.index('{')+1:fn.rindex('}')]
assert 'if (!pin_address || pin_address > std::numeric_limits<u32>::max())' in method
assert 'nvmap.UnpinHandle(entries[j].map_handle);' in method
assert 'return NvResult::InsufficientMemory;' in method
assert method.index('return NvResult::InsufficientMemory;') < method.index('return NvResult::Success;')
fixture=r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <limits>
#include <memory>
#include <span>
#include <vector>
using u32=std::uint32_t;using u64=std::uint64_t;using DAddr=u64;using GPUVAddr=u64;using DeviceFD=int;
enum class NvResult { Success, InsufficientMemory };
struct IoctlMapBuffer { u32 num_entries; };
struct MapBufferEntry { u32 map_handle;u32 map_address; };
struct FakeNvMap {
 std::vector<u32> unpinned;
 DAddr PinHandle(u32 handle, bool low_area) {
  assert(low_area);
  return handle==3 ? 0 : handle==4 ? u64{1}<<32 : handle*4096;
 }
 void UnpinHandle(u32 id) {unpinned.push_back(id);}
};
struct TestNVDEC {
 FakeNvMap nvmap;
 NvResult MapBuffer(IoctlMapBuffer& params, std::span<MapBufferEntry> entries, DeviceFD fd) {
  (void)fd;
__NVDEC_METHOD__
 }
};
struct Allocator {u32 address{}; unsigned calls{};u32 Allocate(u32){++calls;return address;} };
struct Gmmu {unsigned maps{}; void Map(u64,u64,u64){++maps;} };
struct Host1x {Allocator allocator;Gmmu gmmu_manager;Allocator& AllocatorRef(){return allocator;}
 Allocator& Allocator(){return allocator;} };
struct Handle {u64 aligned_size{};u32 pin_virt_address{};u64 d_address{4096};};
struct LowArea {
 Host1x host1x;
 std::shared_ptr<Handle> handle_description=std::make_shared<Handle>();
 bool Try() {
__LOW_AREA__
  return map_low_area();
 }
};
int main(){
 TestNVDEC ok;IoctlMapBuffer count{2};
 MapBufferEntry good[2]{{1,0},{2,0}};
 assert(ok.MapBuffer(count,good,0)==NvResult::Success);
 assert(good[0].map_address==4096 && good[1].map_address==8192);
 assert(ok.nvmap.unpinned.empty());
 TestNVDEC partial;IoctlMapBuffer count3{3};
 MapBufferEntry mix[3]{{1,0},{2,0},{3,0}};
 assert(partial.MapBuffer(count3,mix,0)==NvResult::InsufficientMemory);
 assert(mix[0].map_address==0 && mix[1].map_address==0 && mix[2].map_address==0);
 assert((partial.nvmap.unpinned==std::vector<u32>{1,2}));
 TestNVDEC oversized;IoctlMapBuffer count2{2};
 MapBufferEntry big[2]{{1,0},{4,0}};
 assert(oversized.MapBuffer(count2,big,0)==NvResult::InsufficientMemory);
 assert((oversized.nvmap.unpinned==std::vector<u32>{4,1}));
 LowArea area;area.handle_description->aligned_size=4096;
 assert(!area.Try() && area.host1x.gmmu_manager.maps==0);
 assert(area.handle_description->pin_virt_address==0);
 area.host1x.allocator.address=0x4000;
 assert(area.Try() && area.host1x.gmmu_manager.maps==1);
 assert(area.Try() && area.host1x.gmmu_manager.maps==1);
 LowArea wide;wide.handle_description->aligned_size=u64{1}<<33;
 wide.host1x.allocator.address=0x1000;
 assert(!wide.Try() && wide.host1x.allocator.calls==0);
}
'''
# Distinguish the mock's member name from its type to avoid a compiler clash.
fixture=fixture.replace('struct Allocator {','struct FakeAllocator {').replace('Allocator allocator','FakeAllocator allocator').replace('Allocator& AllocatorRef()','FakeAllocator& AllocatorRef()').replace('Allocator& Allocator()','FakeAllocator& Allocator()')
fixture=fixture.replace('__NVDEC_METHOD__',method).replace('__LOW_AREA__',low_area)
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
env=os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-pin-propagation-') as temp:
    source=Path(temp)/'pins.cpp';source.write_text(fixture)
    for compiler in compilers:
        for level in ('-O0','-O2'):
            exe=Path(temp)/(Path(compiler).name+level)
            cmd=[compiler,'-std=c++20',level,'-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',str(source),'-o',str(exe)]
            build=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=80)
            assert build.returncode==0,(cmd,build.stderr[-2500:])
            run=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=15)
            assert run.returncode==0,(cmd,run.stderr[-2500:])
            print(Path(compiler).name,level,'P1_NVDRV_PIN_FAILURE_OWNER_PASS',flush=True)
print('P1_NVDRV_PIN_FAILURE_PROPAGATION_PASS native_AS_guard=1 nvdec_rollback=1 low_area_oom=1')
