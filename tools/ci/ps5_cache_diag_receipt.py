#!/usr/bin/env python3
"""Exact reversible receipt for PS5 shader-cache admission diagnostics.

The historical Vulkan/R23 verified source must not change. This module
accepts ONLY the explicitly reviewed vendor diagnostic blob, removes seven
marked diagnostic-only additions in memory and recovers the prior raw Git blob.
Neither compiler inputs nor immutable R23/P24 receipt hashes are modified.
"""
from __future__ import annotations

import hashlib
import re

OWNER = "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp"
ORIGINAL_BLOB = "6efe1b10862135056c1df1b78007a1c9cb5a9610"
REVIEWED_DIAGNOSTIC_BLOB = "c79131ffafce0e2b33213051ae7a028c3c4ff33d"
REVIEWED_DRIVER_HEADER_BLOB = "c7e3ca901ea7ab82ec679c23cf43a1c556ac7e41"
REVIEWED_CACHE_VERSION_20_BLOB = "36aae4b17ef8e9681f62fabdd4cf37f09d0beefb"
REVIEWED_CACHE_VERSION_21_BLOB = "be5d48abd44996502b0829a6e0501d130a151455"
REVIEWED_FRAGMENT_SHUFFLE_FALLBACK_BLOB = "e10c4893c03da57dce7f607d3e0af46d62e343f1"
# Exact five reviewed #115 diff hunks, inverted ONLY for source comparison.
# Both raw source hashes must match; actual build uses the new vendor file.
DRIVER_HEADER_REVERSES = [
    [
        "// SPDX-License-Identifier: GPL-2.0-or-later\n\n#include <algorithm>\n#include <array>\n#include <chrono>\n#include <cstdio>\n// ENCORE_PS5_CACHE_DIAG_BEGIN\n",
        "// SPDX-License-Identifier: GPL-2.0-or-later\n\n#include <algorithm>\n#include <chrono>\n#include <cstdio>\n// ENCORE_PS5_CACHE_DIAG_BEGIN\n"
    ],
    [
        "#include \"video_core/vulkan_common/vulkan_wrapper.h\"\n#ifdef PS5_NATIVE\n#include <limits>\n#include <new>\n#include \"core/hle/service/nvdrv/devices/native_gpu_channel_registry.h\"\n#include \"video_core/native_shader_capture.h\"\n#include \"shader_recompiler/frontend/ampere/maxwell_environment.h\"\n",
        "#include \"video_core/vulkan_common/vulkan_wrapper.h\"\n#ifdef PS5_NATIVE\n#include <limits>\n#include \"core/hle/service/nvdrv/devices/native_gpu_channel_registry.h\"\n#include \"video_core/native_shader_capture.h\"\n#include \"shader_recompiler/frontend/ampere/maxwell_environment.h\"\n"
    ],
    [
        "constexpr size_t VULKAN_CACHE_FLUSH_MIN_SECONDS = 30;\nconstexpr std::array<char, 8> VULKAN_CACHE_MAGIC_NUMBER{'y', 'u', 'z', 'u', 'v', 'k', 'c', 'h'};\n\n#ifdef PS5_NATIVE\n// ENCORE_DRIVER_CACHE_HEADER_BEGIN\n// A driver blob is optional acceleration, distinct from the guest shader\n// environment records. Limit temporary cache staging memory, not the\n// driver's in-memory cache or the environment log.\nconstexpr size_t kNativeDriverCacheStagingLimit = 512ULL * 1024 * 1024;\nconstexpr size_t kNativeDriverCacheHeaderSize = 32;\n\nbool NativeDriverCacheHeaderMatches(\n    const std::array<unsigned char, kNativeDriverCacheHeaderSize>& header,\n    const VkPhysicalDeviceProperties& properties) {\n    // Vulkan header v1 is little-endian regardless of native struct packing.\n    const auto u32_le = [&header](size_t offset) -> u32 {\n        return static_cast<u32>(header[offset]) |\n               (static_cast<u32>(header[offset + 1]) << 8) |\n               (static_cast<u32>(header[offset + 2]) << 16) |\n               (static_cast<u32>(header[offset + 3]) << 24);\n    };\n    return u32_le(0) == kNativeDriverCacheHeaderSize &&\n           u32_le(4) == VK_PIPELINE_CACHE_HEADER_VERSION_ONE &&\n           u32_le(8) == properties.vendorID &&\n           u32_le(12) == properties.deviceID &&\n           std::equal(header.begin() + 16, header.end(), properties.pipelineCacheUUID);\n}\n// ENCORE_DRIVER_CACHE_HEADER_END\n#endif\n\n\ntemplate <typename Container>\nauto MakeSpan(Container& container) {\n    return std::span(container.data(), container.size());\n",
        "constexpr size_t VULKAN_CACHE_FLUSH_MIN_SECONDS = 30;\nconstexpr std::array<char, 8> VULKAN_CACHE_MAGIC_NUMBER{'y', 'u', 'z', 'u', 'v', 'k', 'c', 'h'};\n\ntemplate <typename Container>\nauto MakeSpan(Container& container) {\n    return std::span(container.data(), container.size());\n"
    ],
    [
        "        std::vector<char> cache_data;\n        if (pipeline_cache) {\n            pipeline_cache.Read(&cache_size, nullptr);\n            if (cache_size > kNativeDriverCacheStagingLimit) {\n                LOG_WARNING(Render_Vulkan, \"Driver cache exceeds native staging budget; retaining old cache\");\n                file.close();\n                std::error_code cleanup_error;\n                std::filesystem::remove(staging, cleanup_error);\n                return;\n            }\n            cache_data.resize(cache_size);\n            pipeline_cache.Read(&cache_size, cache_data.data());\n        }\n",
        "        std::vector<char> cache_data;\n        if (pipeline_cache) {\n            pipeline_cache.Read(&cache_size, nullptr);\n            cache_data.resize(cache_size);\n            pipeline_cache.Read(&cache_size, cache_data.data());\n        }\n"
    ],
    [
        "\n        static constexpr size_t header_size = magic_number.size() + sizeof(cache_version);\n        const size_t cache_size = static_cast<size_t>(end) - header_size;\n#ifdef PS5_NATIVE\n        if (cache_size < kNativeDriverCacheHeaderSize ||\n            cache_size > kNativeDriverCacheStagingLimit) {\n            LOG_WARNING(Render_Vulkan, \"Driver cache payload outside native staging bounds: {}\", cache_size);\n            return create_pipeline_cache(0, nullptr);\n        }\n        std::array<unsigned char, kNativeDriverCacheHeaderSize> driver_header{};\n        file.read(reinterpret_cast<char*>(driver_header.data()), driver_header.size());\n        if (!NativeDriverCacheHeaderMatches(driver_header, device.GetPhysical().GetProperties())) {\n            LOG_WARNING(Render_Vulkan, \"Driver cache header incompatible; using fresh driver cache\");\n            return create_pipeline_cache(0, nullptr);\n        }\n        file.seekg(static_cast<std::streamoff>(header_size), std::ios::beg);\n        std::vector<char> cache_data;\n        try {\n            cache_data.resize(cache_size);\n        } catch (const std::bad_alloc&) {\n            LOG_WARNING(Render_Vulkan, \"Driver cache allocation failed; using fresh driver cache\");\n            return create_pipeline_cache(0, nullptr);\n        }\n#else\n        std::vector<char> cache_data(cache_size);\n#endif\n        file.read(cache_data.data(), cache_size);\n\n        LOG_INFO(Render_Vulkan,\n",
        "\n        static constexpr size_t header_size = magic_number.size() + sizeof(cache_version);\n        const size_t cache_size = static_cast<size_t>(end) - header_size;\n        std::vector<char> cache_data(cache_size);\n        file.read(cache_data.data(), cache_size);\n\n        LOG_INFO(Render_Vulkan,\n"
    ]
]
OPEN = "ENCORE_PS5_CACHE_DIAG_BEGIN"
CLOSE = "ENCORE_PS5_CACHE_DIAG_END"
BLOCKS = 7
MARKED_BLOCK = re.compile(
    r"(?ms)^[ \t]*// ENCORE_PS5_CACHE_DIAG_BEGIN\n"
    r".*?^[ \t]*// ENCORE_PS5_CACHE_DIAG_END\n"
)


def git_blob(content: str) -> str:
    raw = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def normalize_for_historical_proof(source: str) -> tuple[str, bool]:
    """Return old exact source and whether reviewed diagnostic blocks existed.

    Reject ANY unrelated byte change, marker drift, or missing sentinel.
    The normalized output is only used by source-integrity comparison.
    It must NOT replace the compiled production vendor file.
    """
    current = git_blob(source)
    # Vendor #180 preserves Eden #4503's exact broken-pattern predicate but
    # replaces the PS5-native whole-shader drop with the reviewed
    # Lichii/Eglantine broadcast/select fallback. Reverse ONLY those three
    # exact hunks for the immutable historical receipt.
    if current == REVIEWED_FRAGMENT_SHUFFLE_FALLBACK_BLOB:
        post_programs = "    std::array<Shader::IR::Program, Maxwell::MaxShaderProgram> programs;\n#ifdef PS5_NATIVE\n    // Eden #4503 drops known-broken non-NVIDIA fragment shaders entirely.\n    // On PS5 that visibly removes guest draws. Keep the exact predicate but\n    // route only matching programs through the newer Lichii/Eglantine\n    // broadcast/select SPIR-V fallback.\n    std::array<bool, Maxwell::MaxShaderProgram> fragment_shuffle_fallback{};\n#endif\n"
        pre_programs = "    std::array<Shader::IR::Program, Maxwell::MaxShaderProgram> programs;\n"
        post_skip = "        // Avoid native subgroup shuffle for the known PositionXY fragment\n        // pattern on non-NVIDIA drivers. Desktop/mobile preserve Eden #4503's\n        // fail-closed skip. PS5 instead uses the newer upstream broadcast\n        // fallback so the whole guest draw is not silently discarded.\n        if (device.GetDriverID() != VK_DRIVER_ID_NVIDIA_PROPRIETARY &&\n            Shader::Optimization::HasBrokenPattern(programs[index])) {\n#ifdef PS5_NATIVE\n            fragment_shuffle_fallback[index] = true;\n            LOG_WARNING(Render_Vulkan,\n                        \"0x{:016x}: using PS5 fragment shuffle fallback\",\n                        key.unique_hashes[index]);\n#else\n            LOG_WARNING(Render_Vulkan,\n                        \"0x{:016x}: skipping fragment shuffle with known driver issue\",\n                        key.unique_hashes[index]);\n            return nullptr;\n#endif\n        }"
        pre_skip = "        // Avoid compiling a known-broken fragment shuffle sourced from\n        // PositionXY on non-NVIDIA drivers (notably RADV/RDNA2). Recognize\n        // the IR pattern, not a broad title or vendor blacklist.\n        if (device.GetDriverID() != VK_DRIVER_ID_NVIDIA_PROPRIETARY &&\n            Shader::Optimization::HasBrokenPattern(programs[index])) {\n            LOG_WARNING(Render_Vulkan,\n                        \"0x{:016x}: skipping fragment shuffle with known driver issue\",\n                        key.unique_hashes[index]);\n            return nullptr;\n        }"
        post_emit = "        auto emit_profile = profile;\n#ifdef PS5_NATIVE\n        emit_profile.has_broken_spirv_fragment_shuffle = fragment_shuffle_fallback[index];\n#endif\n        const std::vector<u32> code{([&] { auto cost = Eden::Performance::VulkanTimer(22); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderSpirv, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return EmitSPIRV(emit_profile, runtime_info, program, binding); }())};"
        pre_emit = "        const std::vector<u32> code{([&] { auto cost = Eden::Performance::VulkanTimer(22); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderSpirv, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return EmitSPIRV(profile, runtime_info, program, binding); }())};"
        assert source.count(post_programs) == source.count(post_skip) == source.count(post_emit) == 1
        source = source.replace(post_programs, pre_programs, 1)
        source = source.replace(post_skip, pre_skip, 1)
        source = source.replace(post_emit, pre_emit, 1)
        current = git_blob(source)
        assert current == REVIEWED_CACHE_VERSION_21_BLOB, "Fragment-shuffle predecessor drift"
    # FC27 shader-IR changes deliberately invalidate the persistent cache.
    # Vendor's own frozen-R23 receipt proves these exact successors differ
    # from the reviewed driver-header owner only by CACHE_VERSION 19 -> 20/21.
    # Normalize only that one reviewed line in memory before the existing
    # driver-header and diagnostic reversals; production source is untouched.
    if current == REVIEWED_CACHE_VERSION_21_BLOB:
        assert source.count("constexpr u32 CACHE_VERSION = 21;") == 1
        source = source.replace("constexpr u32 CACHE_VERSION = 21;",
                                "constexpr u32 CACHE_VERSION = 19;", 1)
        current = git_blob(source)
        assert current == REVIEWED_DRIVER_HEADER_BLOB, "Cache v21 predecessor drift"
    elif current == REVIEWED_CACHE_VERSION_20_BLOB:
        assert source.count("constexpr u32 CACHE_VERSION = 20;") == 1
        source = source.replace("constexpr u32 CACHE_VERSION = 20;",
                                "constexpr u32 CACHE_VERSION = 19;", 1)
        current = git_blob(source)
        assert current == REVIEWED_DRIVER_HEADER_BLOB, "Cache v20 predecessor drift"
    if current == REVIEWED_DRIVER_HEADER_BLOB:
        for successor, predecessor in DRIVER_HEADER_REVERSES:
            assert source.count(successor) == 1, "Driver cache header hunk drift"
            source = source.replace(successor, predecessor, 1)
        current = git_blob(source)
        assert current == REVIEWED_DIAGNOSTIC_BLOB, "Driver cache predecessor drift"
    if OPEN not in source and CLOSE not in source:
        assert current == ORIGINAL_BLOB, (
            "Unknown native Vulkan pipeline owner without diagnostics", current)
        return source, False
    assert current == REVIEWED_DIAGNOSTIC_BLOB, (
        "Unreviewed PS5 shader-cache source; do not waive R23 checks", current)
    assert source.count(OPEN) == source.count(CLOSE) == BLOCKS
    for marker in ("EDEN_PS5_SHADER_CACHE_DISK",
                   "EDEN_PS5_SHADER_CACHE_ADMISSION",
                   "disk_graphics_admitted", "std::filesystem::file_size"):
        assert marker in source, ("Missing PS5 diagnostic contract", marker)
    normalized, count = MARKED_BLOCK.subn("", source)
    assert count == BLOCKS and OPEN not in normalized and CLOSE not in normalized, (
        "PS5 diagnostic boundaries changed", count)
    assert git_blob(normalized) == ORIGINAL_BLOB, (
        "PS5-only diagnostic removal changed original R23 owner")
    return normalized, True
