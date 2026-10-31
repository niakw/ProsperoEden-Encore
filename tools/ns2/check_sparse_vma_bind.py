#!/usr/bin/env python3
"""N69: compile actual vendor native-Vulkan VMA transaction owner with Clang/GCC UBSan."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_sparse_bind_transaction.h"
s = HEADER.read_text(encoding="utf-8")
for key in ("AllocateSparseMemory(page_request, token)", "queue.BindSparseImage(",
            "fence.Wait(timeout_ns)", "budget_.Commit(logical)",
            "RetireAfterDeviceIdle", "budget_.Poison()",
            "image_memory.memoryTypeBits"):
    assert key in s, key
vulkan_stub = r"""
#pragma once
#include <cstdint>
using VkDeviceSize=std::uint64_t;
using VkImage=void*;
using VkDeviceMemory=void*;
using VkFence=void*;
using VkSemaphore=void*;
using VkResult=std::int32_t;
using VkImageAspectFlags=std::uint32_t;
using VkSparseImageFormatFlags=std::uint32_t;
constexpr auto VK_NULL_HANDLE=nullptr;
constexpr VkImageAspectFlags VK_IMAGE_ASPECT_COLOR_BIT=1;
constexpr VkSparseImageFormatFlags VK_SPARSE_IMAGE_FORMAT_SINGLE_MIPTAIL_BIT=1;
constexpr VkResult VK_SUCCESS=0;
constexpr VkResult VK_NOT_READY=1;
constexpr VkResult VK_TIMEOUT=2;
constexpr VkResult VK_ERROR_DEVICE_LOST=-4;
constexpr VkResult VK_ERROR_OUT_OF_DEVICE_MEMORY=-2;
constexpr VkResult VK_ERROR_INITIALIZATION_FAILED=-3;
struct VkExtent3D {std::uint32_t width{},height{},depth{};};
struct VkOffset3D {std::int32_t x{},y{},z{};};
struct VkImageSubresource {VkImageAspectFlags aspectMask{}; std::uint32_t mipLevel{},arrayLayer{};};
struct VkSparseImageFormatProperties {
 VkImageAspectFlags aspectMask{};
 VkExtent3D imageGranularity{};
 VkSparseImageFormatFlags flags{};
};
struct VkSparseImageMemoryRequirements {
 VkSparseImageFormatProperties formatProperties{};
 std::uint32_t imageMipTailFirstLod{};
 VkDeviceSize imageMipTailSize{},imageMipTailOffset{},imageMipTailStride{};
};
struct VkMemoryRequirements {
 VkDeviceSize size{},alignment{};
 std::uint32_t memoryTypeBits{};
};
struct VkSparseImageMemoryBind {
 VkImageSubresource subresource{};
 VkOffset3D offset{};
 VkExtent3D extent{};
 VkDeviceMemory memory{};
 VkDeviceSize memoryOffset{};
 std::uint32_t flags{};
};
struct VkSparseMemoryBind {
 VkDeviceSize resourceOffset{},size{};
 VkDeviceMemory memory{};
 VkDeviceSize memoryOffset{};
 std::uint32_t flags{};
};
"""
with tempfile.TemporaryDirectory(prefix="n69-sparse-native-") as tmp:
    d = Path(tmp)
    (d / "vulkan").mkdir()
    (d / "vulkan/vulkan_core.h").write_text(vulkan_stub)
    src = ROOT / "tools/ns2/test_sparse_vma_bind.cpp"
    for compiler in ("clang++", "g++"):
        exe = d / compiler.replace("+", "p")
        subprocess.run([compiler, "-std=c++20", "-O2", "-Wall", "-Wextra",
                        "-Werror", "-fsanitize=undefined",
                        "-fno-sanitize-recover=all", "-I", str(d),
                        "-I", str(ROOT / "vendor/encore-active/ns2-helpers/include"),
                        str(src), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
print("N69_REAL_VENDOR_VMA_BIND_OWNER_CLANG_GCC_UBSAN_PASS")
