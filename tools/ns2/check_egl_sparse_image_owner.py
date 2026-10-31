#!/usr/bin/env python3
"""N64: compile/execute actual generated VkImage creation source and mock driver failures."""
from pathlib import Path
import subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/'vendor/encore-active/eden-vulkan/vulkan_memory_allocator.cpp'
HEADER=ROOT/'vendor/encore-active/ns2-helpers/include/video_core/vulkan_common/vulkan_memory_allocator.h'
WRAPPER=ROOT/'vendor/sources/eden/src/video_core/vulkan_common/vulkan_wrapper.cpp'
assert 'vmaDestroyImage(allocator, handle, allocation);' in WRAPPER.read_text()
with tempfile.TemporaryDirectory(prefix='n64-vendor-image-') as td:
    t=Path(td)
    code=NATIVE.read_text()
    hdr=HEADER.read_text()
    assert code.count('vk::Image MemoryAllocator::CreateSparseImage(')==1
    assert 'MemoryAllocator::AllocateSparseMemory(' in code
    assert 'MemoryAllocator::ReleaseSparseMemory(' in code
    assert 'CreateSparseImage(const VkImageCreateInfo &ci)' in hdr
    assert 'vk::Image MemoryAllocator::CreateImage(' in code
    start=code.index('vk::Image MemoryAllocator::CreateSparseImage(')
    end=code.index('bool MemoryAllocator::AllocateSparseMemory(',start)
    unit=code[start:end]
    cpp=r'''#include <cassert>
#include <cstdint>
#include <cstddef>
#define VK_NULL_HANDLE nullptr
using VkResult=int;
constexpr VkResult VK_SUCCESS=0;
constexpr unsigned VK_IMAGE_TYPE_2D=2;
constexpr unsigned VK_SAMPLE_COUNT_1_BIT=1;
constexpr unsigned VK_IMAGE_TILING_OPTIMAL=0;
constexpr unsigned VK_IMAGE_CREATE_SPARSE_BINDING_BIT=1u<<3;
constexpr unsigned VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT=1u<<4;
using VkDevice=void*;
using VkImage=void*;
using VmaAllocator=void*;
struct VkExtent3D{unsigned width{},height{},depth{};};
struct VkImageCreateInfo{
    unsigned flags{},imageType{},arrayLayers{},mipLevels{},samples{},tiling{},usage{};
    VkExtent3D extent{};
};
int creates=0,destroys=0,fail=0;
VkResult Create(VkDevice,const VkImageCreateInfo* ci,const void*,VkImage* img){
    ++creates;
    assert((ci->flags & (VK_IMAGE_CREATE_SPARSE_BINDING_BIT |
                          VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT)) ==
                        (VK_IMAGE_CREATE_SPARSE_BINDING_BIT |
                          VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT));
    *img=fail==1?nullptr:reinterpret_cast<void*>(0x100);
    return fail==2?-1:VK_SUCCESS;
}
void Destroy(VkDevice,VkImage image,const void*){
    assert(image==reinterpret_cast<void*>(0x100));++destroys;
}
struct DeviceDispatch {
    decltype(&Create) vkCreateImage=Create;
    decltype(&Destroy) vkDestroyImage=Destroy;
};
namespace vk {
struct Image {
    VkImage handle{};
    Image()=default;
    Image(VkImage image,unsigned,VkDevice,VmaAllocator,void* allocation,const DeviceDispatch&)
        :handle(image){assert(!allocation);}
    explicit operator bool()const{return handle!=nullptr;}
};
}
struct Device {
    bool sparse{};
    DeviceDispatch dld{};
    VkDevice logical=reinterpret_cast<void*>(0x200);
    bool IsSparseResidencyImage2DSupported()const{return sparse;}
    const DeviceDispatch& GetDispatchLoader()const{return dld;}
    const VkDevice* GetLogical()const{return &logical;}
};
struct MemoryAllocator {
    Device device{};
    VmaAllocator allocator{};
    vk::Image CreateSparseImage(const VkImageCreateInfo&)const;
};
''' +unit +r'''
int main(){
    MemoryAllocator m{};
    VkImageCreateInfo ci{};
    ci.imageType=VK_IMAGE_TYPE_2D;ci.arrayLayers=68;
    ci.mipLevels=4;ci.samples=VK_SAMPLE_COUNT_1_BIT;
    ci.tiling=VK_IMAGE_TILING_OPTIMAL;
    ci.extent={1024,1024,1};ci.usage=42;
    assert(!m.CreateSparseImage(ci));assert(creates==0);
    m.device.sparse=true;
    auto invalid=ci;invalid.imageType=0;
    assert(!m.CreateSparseImage(invalid));
    invalid=ci;invalid.arrayLayers=1;
    assert(!m.CreateSparseImage(invalid));
    invalid=ci;invalid.extent.depth=2;
    assert(!m.CreateSparseImage(invalid));
    assert(creates==0);
    m.device.dld.vkCreateImage=nullptr;
    assert(!m.CreateSparseImage(ci));
    m.device.dld.vkCreateImage=Create;
    m.device.dld.vkDestroyImage=nullptr;
    assert(!m.CreateSparseImage(ci));
    m.device.dld.vkDestroyImage=Destroy;
    assert(creates==0);
    fail=1;assert(!m.CreateSparseImage(ci));
    fail=2;assert(!m.CreateSparseImage(ci));assert(destroys==1);
    fail=0;auto image=m.CreateSparseImage(ci);
    assert(image&&image.handle==reinterpret_cast<void*>(0x100));
    assert(creates==3&&destroys==1);
}
'''
    source=t/'test.cpp';source.write_text(cpp)
    for cxx in ('clang++','g++'):
        exe=t/('n64-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
          '-fsanitize=undefined','-fno-sanitize-recover=all',
          str(source),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('N64_PS5_VULKAN_SPARSE_IMAGE_FACTORY_PASS')
