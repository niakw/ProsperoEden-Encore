#!/usr/bin/env python3
"""N66: compile the actual vendor Queue::BindSparseImage implementation under UBSan."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "vendor/encore-active/eden-vulkan/include/video_core/vulkan_common/vulkan_wrapper.h"
source = WRAPPER.read_text(encoding="utf-8")
start_mark = "    VkResult BindSparse(Span<VkBindSparseInfo> bind_infos,"
end_mark = "    VkResult Present(const VkPresentInfoKHR& present_info)"
assert source.count(start_mark) == 1, "Queue sparse native owner changed"
start = source.index(start_mark)
end = source.index(end_mark, start)
methods = source[start:end]
assert "BindSparseImage(VkImage image" in methods
assert "return BindSparse(submit, completion);" in methods
assert "dld->vkQueueBindSparse" in methods
assert "if (!image || !completion" in methods
assert "VkSparseImageMemoryBindInfo image_info" in methods
assert "VkSparseImageOpaqueMemoryBindInfo tail_info" in methods

cpp = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
using u32=std::uint32_t;
using VkQueue=void*;
using VkImage=void*;
using VkDeviceMemory=void*;
using VkFence=void*;
using VkResult=std::int32_t;
constexpr VkResult VK_SUCCESS=0, VK_ERROR_INITIALIZATION_FAILED=-3;
constexpr VkResult VK_ERROR_DEVICE_LOST=-4, VK_ERROR_FEATURE_NOT_PRESENT=-8;
constexpr u32 VK_STRUCTURE_TYPE_BIND_SPARSE_INFO=7;
struct Subresource { u32 aspectMask{},mipLevel{},arrayLayer{}; };
struct Extent { u32 width{},height{},depth{}; };
struct VkSparseImageMemoryBind {
    Subresource subresource{};
    struct { std::int32_t x{}, y{}, z{}; } offset{};
    Extent extent{};
    VkDeviceMemory memory{};
    std::uint64_t memoryOffset{};
    u32 flags{};
};
struct VkSparseMemoryBind {
    std::uint64_t resourceOffset{},size{};
    VkDeviceMemory memory{};
    std::uint64_t memoryOffset{};
    u32 flags{};
};
struct VkSparseImageMemoryBindInfo {
    VkImage image{};
    u32 bindCount{};
    const VkSparseImageMemoryBind* pBinds{};
};
struct VkSparseImageOpaqueMemoryBindInfo {
    VkImage image{};
    u32 bindCount{};
    const VkSparseMemoryBind* pBinds{};
};
struct VkBindSparseInfo {
    u32 sType{};
    const void* pNext{};
    u32 waitSemaphoreCount{};
    const void* pWaitSemaphores{};
    u32 bufferBindCount{};
    const void* pBufferBinds{};
    u32 imageOpaqueBindCount{};
    const VkSparseImageOpaqueMemoryBindInfo* pImageOpaqueBinds{};
    u32 imageBindCount{};
    const VkSparseImageMemoryBindInfo* pImageBinds{};
    u32 signalSemaphoreCount{};
    const void* pSignalSemaphores{};
};
template<class T> struct Span {
    const T* ptr{};
    u32 count{};
    constexpr Span()=default;
    constexpr Span(const T& value):ptr(&value),count(1){}
    constexpr Span(const T* values,u32 size):ptr(values),count(size){}
    constexpr u32 size() const {return count;}
    constexpr bool empty() const {return count==0;}
    constexpr const T* data() const {return ptr;}
    constexpr const T* begin() const {return ptr;}
    constexpr const T* end() const {return ptr+count;}
};
struct DeviceDispatch {
    VkResult (*vkQueueBindSparse)(VkQueue,u32,const VkBindSparseInfo*,VkFence){};
};
struct Queue {
    VkQueue queue{};
    const DeviceDispatch* dld{};
""" + methods + r"""
};
static int calls=0;
static VkResult output=VK_SUCCESS;
static VkQueue expected_queue=reinterpret_cast<void*>(0x1234);
static VkImage expected_image=reinterpret_cast<void*>(0x2345);
static VkFence expected_fence=reinterpret_cast<void*>(0x3456);
static bool expect_tiles=true, expect_tails=true;
static VkResult Dispatch(VkQueue queue,u32 count,const VkBindSparseInfo* binds,VkFence fence) {
    assert(queue==expected_queue&&count==1&&binds&&fence==expected_fence);
    const auto& s=binds[0];
    assert(s.sType==VK_STRUCTURE_TYPE_BIND_SPARSE_INFO);
    assert(s.waitSemaphoreCount==0&&s.signalSemaphoreCount==0&&s.bufferBindCount==0);
    assert(s.imageBindCount==(expect_tiles?1U:0U));
    assert(s.imageOpaqueBindCount==(expect_tails?1U:0U));
    if(expect_tiles) {
        assert(s.pImageBinds && s.pImageBinds->image==expected_image);
        assert(s.pImageBinds->bindCount==1 && s.pImageBinds->pBinds);
        assert(s.pImageBinds->pBinds[0].extent.width==64);
    } else assert(!s.pImageBinds);
    if(expect_tails) {
        assert(s.pImageOpaqueBinds && s.pImageOpaqueBinds->image==expected_image);
        assert(s.pImageOpaqueBinds->bindCount==1 && s.pImageOpaqueBinds->pBinds);
        assert(s.pImageOpaqueBinds->pBinds[0].size==65536);
    } else assert(!s.pImageOpaqueBinds);
    ++calls; return output;
}
int main(){
    DeviceDispatch d{Dispatch};
    Queue q{expected_queue,&d};
    VkSparseImageMemoryBind tile{};
    tile.memory=reinterpret_cast<void*>(0x111);
    tile.extent={64,64,1};
    tile.subresource.aspectMask=1;
    VkSparseMemoryBind tail{};
    tail.memory=reinterpret_cast<void*>(0x222);
    tail.size=65536;
    const Span<VkSparseImageMemoryBind> tiles{tile};
    const Span<VkSparseMemoryBind> tails{tail};
    const Span<VkSparseImageMemoryBind> no_tiles{};
    const Span<VkSparseMemoryBind> no_tails{};
    // Fail closed before any driver call.
    assert(q.BindSparseImage(nullptr,tiles,tails,expected_fence)==VK_ERROR_INITIALIZATION_FAILED);
    assert(q.BindSparseImage(expected_image,tiles,tails,nullptr)==VK_ERROR_INITIALIZATION_FAILED);
    assert(q.BindSparseImage(expected_image,no_tiles,no_tails,expected_fence)==VK_ERROR_INITIALIZATION_FAILED);
    tile.memory=nullptr;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_INITIALIZATION_FAILED);
    tile.memory=reinterpret_cast<void*>(0x111);
    tile.extent.width=0;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_INITIALIZATION_FAILED);
    tile.extent.width=64;
    tile.subresource.aspectMask=0;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_INITIALIZATION_FAILED);
    tile.subresource.aspectMask=1;
    tail.size=0;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_INITIALIZATION_FAILED);
    tail.size=65536;
    assert(q.BindSparseImage(expected_image,Span<VkSparseImageMemoryBind>{&tile,65537},tails,expected_fence)==VK_ERROR_INITIALIZATION_FAILED);
    assert(calls==0);
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_SUCCESS&&calls==1);
    expect_tails=false;
    assert(q.BindSparseImage(expected_image,tiles,no_tails,expected_fence)==VK_SUCCESS&&calls==2);
    expect_tails=true; expect_tiles=false;
    assert(q.BindSparseImage(expected_image,no_tiles,tails,expected_fence)==VK_SUCCESS&&calls==3);
    expect_tiles=true;
    output=VK_ERROR_DEVICE_LOST;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_DEVICE_LOST&&calls==4);
    d.vkQueueBindSparse=nullptr;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_FEATURE_NOT_PRESENT);
    assert(q.BindSparseImage(expected_image,no_tiles,tails,expected_fence)==VK_ERROR_FEATURE_NOT_PRESENT);
    assert(calls==4);
    q.dld=nullptr;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_FEATURE_NOT_PRESENT);
    q.dld=&d; q.queue=nullptr;
    assert(q.BindSparseImage(expected_image,tiles,tails,expected_fence)==VK_ERROR_FEATURE_NOT_PRESENT);
}
""";
with tempfile.TemporaryDirectory(prefix="encore-ns2-sparse-submit-") as td:
    src = Path(td) / "test.cpp"
    src.write_text(cpp)
    for compiler in ("clang++", "g++"):
        exe = Path(td) / compiler.replace("+", "p")
        subprocess.run([compiler, "-std=c++20", "-O2", "-Wall", "-Wextra",
                        "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        str(src), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
print("N66_NATIVE_VULKAN_SPARSE_QUEUE_SUBMIT_PASS")
