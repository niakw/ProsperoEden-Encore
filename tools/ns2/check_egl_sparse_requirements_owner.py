#!/usr/bin/env python3
"""N65: source-verified PS5 Vulkan sparse requirements query and driver edge oracles."""
from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'vendor/encore-active/eden-vulkan'
HEADER=SRC/'include/video_core/vulkan_common/vulkan_wrapper.h'
CPP=SRC/'vulkan_wrapper.cpp'
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
assert 'EDEN_NS2_SPARSE_IMAGE_REQUIREMENTS_EXPERIMENTAL OR' in CMAKE
assert 'NOT EDEN_NS2_SPARSE_IMAGE_FACTORY_EXPERIMENTAL OR' in CMAKE
with tempfile.TemporaryDirectory(prefix='n65-sparse-req-') as td:
    folder=Path(td)
    subprocess.run([sys.executable,str(ROOT/'tools/ns2/prepare_egl_sparse_requirements_owner.py'),
        '--header',str(HEADER),'--source',str(CPP),'--output',str(folder)],check=True)
    src=(folder/'vulkan_wrapper.cpp').read_text()
    hdr=(folder/'include/video_core/vulkan_common/vulkan_wrapper.h').read_text()
    assert 'GetSparseImageMemoryRequirements(VkImage image)' in src
    assert 'PFN_vkGetImageSparseMemoryRequirements' in src
    assert 'dld->vkGetDeviceProcAddr(handle, "vkGetImageSparseMemoryRequirements")' in src
    assert 'GetImageMemoryRequirements(VkImage image)' in src
    assert src.count('GetSparseImageMemoryRequirements(VkImage image)')==1
    assert hdr.count('GetSparseImageMemoryRequirements(VkImage image)')==1
    assert 'PFN_vkGetImageSparseMemoryRequirements' not in hdr # layout preserved
    start=src.index('std::vector<VkSparseImageMemoryRequirements>\nDevice::GetSparseImageMemoryRequirements')
    end=src.index('std::vector<VkPipelineExecutablePropertiesKHR> Device::GetPipelineExecutablePropertiesKHR',start)
    fn=src[start:end]
    cpp=r'''#include <cassert>
#include <cstdint>
#include <cstddef>
#include <vector>
#include <cstring>
using u32=std::uint32_t;
using VkDevice=void*;
using VkImage=void*;
struct VkSparseImageMemoryRequirements { unsigned aspect{}; };
using PFN_vkGetImageSparseMemoryRequirements=
    void(*)(VkDevice,VkImage,u32*,VkSparseImageMemoryRequirements*);
using PFN_vkVoidFunction=void(*)();
int requested_count=3,reported_second=3,calls=0;
bool available=true;
void Query(VkDevice,VkImage,u32* count,VkSparseImageMemoryRequirements* req){
    ++calls;
    if(req==nullptr){*count=static_cast<u32>(requested_count);return;}
    const auto capacity=*count;
    for(u32 i=0;i<capacity;++i)req[i].aspect=i+1;
    *count=static_cast<u32>(reported_second);
}
PFN_vkVoidFunction GetProc(VkDevice,const char* name){
    assert(std::strcmp(name,"vkGetImageSparseMemoryRequirements")==0);
    return available?reinterpret_cast<PFN_vkVoidFunction>(Query):nullptr;
}
struct DeviceDispatch {
    decltype(&GetProc) vkGetDeviceProcAddr=GetProc;
};
struct Device {
    VkDevice handle=reinterpret_cast<void*>(0x100);
    DeviceDispatch store{};
    const DeviceDispatch* dld=&store;
    std::vector<VkSparseImageMemoryRequirements>
        GetSparseImageMemoryRequirements(VkImage) const;
};
''' + fn +r'''
int main() {
    Device d{};
    const VkImage img=reinterpret_cast<void*>(0x200);
    assert(d.GetSparseImageMemoryRequirements(nullptr).empty()&&calls==0);
    d.store.vkGetDeviceProcAddr=nullptr;
    assert(d.GetSparseImageMemoryRequirements(img).empty()&&calls==0);
    d.store.vkGetDeviceProcAddr=GetProc;
    available=false;assert(d.GetSparseImageMemoryRequirements(img).empty()&&calls==0);
    available=true;
    requested_count=0;assert(d.GetSparseImageMemoryRequirements(img).empty());
    requested_count=65;assert(d.GetSparseImageMemoryRequirements(img).empty());
    requested_count=3;reported_second=3;
    auto result=d.GetSparseImageMemoryRequirements(img);
    assert(result.size()==3 && result[0].aspect==1 && result[2].aspect==3);
    reported_second=4;
    assert(d.GetSparseImageMemoryRequirements(img).empty());
    reported_second=0;
    assert(d.GetSparseImageMemoryRequirements(img).empty());
}
'''
    (folder/'test.cpp').write_text(cpp)
    for cxx in ('clang++','g++'):
        exe=folder/('n65-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
             '-fsanitize=undefined','-fno-sanitize-recover=all',
             str(folder/'test.cpp'),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('N65_NATIVE_VULKAN_SPARSE_REQUIREMENTS_QUERY_PASS')
