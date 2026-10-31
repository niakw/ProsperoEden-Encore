#!/usr/bin/env python3
"""N62: extract actual native VMA methods and prove bounded allocation/cleanup."""
from pathlib import Path
import subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'vendor/encore-active/eden-vulkan/vulkan_memory_allocator.cpp'
HDR=ROOT/'vendor/sources/eden/src/video_core/vulkan_common/vulkan_memory_allocator.h'
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
assert 'EDEN_NS2_SPARSE_VMA_ALLOCATOR_EXPERIMENTAL OR' in CMAKE
assert 'EDEN_NS2_SPARSE_RESIDENCY_GATE_EXPERIMENTAL OR' in CMAKE
assert 'NOT EDEN_NS2_SPARSE_RESIDENCY_GATE_EXPERIMENTAL OR' in CMAKE
assert 'EDEN_FINAL_RELEASE_PROFILE)' in CMAKE
with tempfile.TemporaryDirectory(prefix='n62-vma-sparse-') as td:
    temp=Path(td)
    subprocess.run([sys.executable,str(ROOT/'tools/ns2/prepare_egl_sparse_vma_owner.py'),
      '--header',str(HDR),'--source',str(SRC),'--output',str(temp)],check=True)
    h=(temp/'include/video_core/vulkan_common/vulkan_memory_allocator.h').read_text()
    code=(temp/'vulkan_memory_allocator.cpp').read_text()
    original=SRC.read_text()
    assert len(code)-len(original) < 2300
    assert 'MemoryAllocator::CreateImage' in code
    assert 'MemoryAllocator::Commit(' in code
    assert 'VMA_ALLOCATION_CREATE_WITHIN_BUDGET_BIT' in code
    assert 'VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE' in code
    assert 'void ReleaseSparseMemory(SparseMemoryAllocation &allocation)' in h
    start=code.index('bool MemoryAllocator::AllocateSparseMemory(')
    end=code.index('vk::Buffer MemoryAllocator::CreateBuffer(',start)
    functions=code[start:end]
    cpp=r'''#include <cassert>
#include <cstdint>
#include <cstddef>
#define VK_NULL_HANDLE nullptr
using VkResult=int;
constexpr VkResult VK_SUCCESS=0;
constexpr unsigned VMA_ALLOCATION_CREATE_WITHIN_BUDGET_BIT=1;
constexpr unsigned VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE=2;
constexpr unsigned VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT=4;
using VkDeviceSize=std::uint64_t;
using VkDeviceMemory=void*;
using VmaAllocation=void*;
struct VkMemoryRequirements { VkDeviceSize size{},alignment{};unsigned memoryTypeBits{}; };
struct VmaAllocationCreateInfo { unsigned flags{},usage{},requiredFlags{},memoryTypeBits{}; };
struct VmaAllocationInfo { VkDeviceMemory deviceMemory{};VkDeviceSize offset{}; };
struct MemoryAllocator {
    struct SparseMemoryAllocation {
        VmaAllocation allocation{};
        VkDeviceMemory memory{};
        VkDeviceSize offset{};
    };
    void* allocator{};
    bool AllocateSparseMemory(const VkMemoryRequirements &, SparseMemoryAllocation &)const noexcept;
    void ReleaseSparseMemory(SparseMemoryAllocation &)const noexcept;
};
int alloc_calls=0,free_calls=0,fail_mode=0;
VkResult vmaAllocateMemory(void*,const VkMemoryRequirements* req,
                          const VmaAllocationCreateInfo* ci,
                          VmaAllocation* a,VmaAllocationInfo* info){
    ++alloc_calls;
    assert(req->size>0&&req->alignment>0&&req->memoryTypeBits!=0);
    assert(ci->flags==VMA_ALLOCATION_CREATE_WITHIN_BUDGET_BIT);
    assert(ci->usage==VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE);
    assert(ci->requiredFlags==VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    assert(ci->memoryTypeBits==req->memoryTypeBits);
    if(fail_mode==1){*a=nullptr;return -1;}
    *a=reinterpret_cast<void*>(0x100);
    if(fail_mode==2){info->deviceMemory=nullptr;return 0;}
    if(fail_mode==3){info->deviceMemory=nullptr;return -1;}
    info->deviceMemory=reinterpret_cast<void*>(0x200);
    info->offset=65536;
    return VK_SUCCESS;
}
void vmaFreeMemory(void*,VmaAllocation a){
    assert(a==reinterpret_cast<void*>(0x100));++free_calls;
}
''' +functions+r'''
int main(){
    MemoryAllocator a{};
    MemoryAllocator::SparseMemoryAllocation token{};
    const VkMemoryRequirements good{262144,65536,3};
    assert(!a.AllocateSparseMemory({0,65536,3},token));
    assert(!a.AllocateSparseMemory({4,0,3},token));
    assert(!a.AllocateSparseMemory({4,100,3},token));
    assert(!a.AllocateSparseMemory({4,4,0},token));
    assert(alloc_calls==0);
    for(int mode=1;mode<=3;++mode){
        fail_mode=mode;assert(!a.AllocateSparseMemory(good,token));
        assert(!token.allocation&&!token.memory&&token.offset==0);
    }
    assert(alloc_calls==3 && free_calls==2);
    fail_mode=0;
    assert(a.AllocateSparseMemory(good,token));
    assert(token.allocation&&token.memory&&token.offset==65536);
    assert(!a.AllocateSparseMemory(good,token)); // no token replacement/leak
    assert(alloc_calls==4);
    a.ReleaseSparseMemory(token);
    assert(!token.allocation&&!token.memory&&token.offset==0);
    assert(free_calls==3);
    a.ReleaseSparseMemory(token);
    assert(free_calls==3);
}
'''
    (temp/'test.cpp').write_text(cpp)
    for cxx in ('clang++','g++'):
        exe=temp/('n62-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
          '-fsanitize=undefined','-fno-sanitize-recover=all',str(temp/'test.cpp'),
          '-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('N62_NATIVE_PS5_VMA_SPARSE_ALLOC_ROLLBACK_PASS')
