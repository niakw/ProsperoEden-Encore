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
REVIEWED_FRAGMENT_SHUFFLE_WITNESS_BLOB = "dcc4c9cbb4e3cec48ab4d1dece9f8708196c5f56"
REVIEWED_PIPELINE_DRAIN_BLOB = "e3910d11f33376097a90858118ba276f7e02cb70"
# NS1-only successors: integer fragment output typing and recent shader prewarm.
# Reverse their exact reviewed source hunks only for the immutable R23 oracle.
REVIEWED_IMMUTABLE_SNAPSHOT_BLOB = "ad07512d129667a617b49b448d898c5756c99025"
REVIEWED_PARALLEL_TIMING_BLOB = "52470b6160f6049801d963960adf6952c79a45cf"
PARALLEL_TIMING_REVERSES = [
    [
        "    std::array<std::exception_ptr, Maxwell::MaxShaderProgram> parallel_errors{};\n    // CachePhaseTimer's per-key shader attribution is intentionally thread-local.\n    // Give every stage worker a private accumulator, then merge after the owner\n    // joins them so EDEN_VULKAN_SHADER_MISS keeps the pre-parallel accounting.\n    std::array<::Eden::Performance::ShaderMissStageCosts, Maxwell::MaxShaderProgram>\n        parallel_stage_costs{};\n    if (parallel_translate_stages) {",
        "    std::array<std::exception_ptr, Maxwell::MaxShaderProgram> parallel_errors{};\n    if (parallel_translate_stages) {"
    ],
    [
        "                [this, env, stage_pools, cfg_offset, exits_to_dispatcher, index,\n                 &parallel_programs, &parallel_errors, &parallel_stage_costs] {\n                    struct ShaderMissStageScope {\n                        ::Eden::Performance::ShaderMissStageCosts* previous{\n                            ::Eden::Performance::shader_miss_stage_active};\n                        explicit ShaderMissStageScope(\n                            ::Eden::Performance::ShaderMissStageCosts* current) noexcept {\n                            ::Eden::Performance::shader_miss_stage_active = current;\n                        }\n                        ~ShaderMissStageScope() {\n                            ::Eden::Performance::shader_miss_stage_active = previous;\n                        }\n                    } shader_miss_stage_scope{&parallel_stage_costs[index]};\n                    struct PreflushedTexturePoolScope {",
        "                [this, env, stage_pools, cfg_offset, exits_to_dispatcher, index,\n                 &parallel_programs, &parallel_errors] {\n                    struct PreflushedTexturePoolScope {"
    ],
    [
        "        shader_translation_workers.WaitForRequests();\n        if (auto* const owner_stage_costs =\n                ::Eden::Performance::shader_miss_stage_active) {\n            for (size_t index = 0; index < Maxwell::MaxShaderProgram; ++index) {\n                if (key.unique_hashes[index] == 0) {\n                    continue;\n                }\n                // These are CPU-work totals, matching the former serial keyed\n                // timers. The enclosing miss cpu_ns remains the elapsed critical\n                // path and therefore reflects the parallel overlap.\n                owner_stage_costs->cfg_ns += parallel_stage_costs[index].cfg_ns;\n                owner_stage_costs->ir_ns += parallel_stage_costs[index].ir_ns;\n            }\n        }\n        for (size_t index = 0; index < Maxwell::MaxShaderProgram; ++index) {",
        "        shader_translation_workers.WaitForRequests();\n        for (size_t index = 0; index < Maxwell::MaxShaderProgram; ++index) {"
    ]
]
REVIEWED_PARALLEL_TRANSLATION_BLOB = "b28a190e92ca80b0385148a0b558828353326f12"
PARALLEL_TRANSLATION_REVERSES = [
    [
        "#include <cstdio>\n#include <exception>\n#include <stdexcept>\n// ENCORE_PS5_CACHE_DIAG_BEGIN",
        "#include <cstdio>\n// ENCORE_PS5_CACHE_DIAG_BEGIN"
    ],
    [
        "#ifdef PS5_NATIVE\nnamespace VideoCommon {\nvoid SetShaderTexturePoolPreflushedForThread(bool preflushed) noexcept;\n}\n#endif\n\nnamespace Vulkan {\n#ifdef PS5_NATIVE",
        "namespace Vulkan {\n#ifdef PS5_NATIVE"
    ],
    [
        "      use_vulkan_pipeline_cache{Settings::values.use_vulkan_driver_pipeline_cache.GetValue()},\n#ifdef PS5_NATIVE\n      shader_translation_workers(2, \"VkShaderTranslate\"),\n#endif\n      workers(device.HasBrokenParallelShaderCompiling() ? 1ULL : GetTotalPipelineWorkers(),\n              \"VkPipelineBuilder\", {}, Common::ThreadPlacement::Background),",
        "      use_vulkan_pipeline_cache{Settings::values.use_vulkan_driver_pipeline_cache.GetValue()},\n      workers(device.HasBrokenParallelShaderCompiling() ? 1ULL : GetTotalPipelineWorkers(),\n              \"VkPipelineBuilder\", {}, Common::ThreadPlacement::Background),"
    ],
    [
        "std::unique_ptr<GraphicsPipeline> PipelineCache::CreateGraphicsPipeline(\n    ShaderPools& pools, const GraphicsPipelineCacheKey& key,\n    std::span<Shader::Environment* const> envs, PipelineStatistics* statistics,\n    bool build_in_parallel, bool parallel_translate_stages) try {",
        "std::unique_ptr<GraphicsPipeline> PipelineCache::CreateGraphicsPipeline(\n    ShaderPools& pools, const GraphicsPipelineCacheKey& key,\n    std::span<Shader::Environment* const> envs, PipelineStatistics* statistics,\n    bool build_in_parallel) try {"
    ],
    [
        "    // Layer passthrough generation for devices without VK_EXT_shader_viewport_index_layer\n    Shader::IR::Program* layer_source_program{};\n\n#ifdef PS5_NATIVE\n    // Lichii's stage-parallel model adapted to Encore's active renderer:\n    // every stage owns its IR pools until SPIR-V emission has consumed the\n    // resulting Program. Only NS1 first-use calls can enable this flag; NS2\n    // native keeps its authenticated GMMU/channel translation synchronous.\n    std::array<std::unique_ptr<ShaderPools>, Maxwell::MaxShaderProgram> parallel_pools{};\n    std::array<std::unique_ptr<Shader::IR::Program>, Maxwell::MaxShaderProgram>\n        parallel_programs{};\n    std::array<std::exception_ptr, Maxwell::MaxShaderProgram> parallel_errors{};\n    if (parallel_translate_stages) {\n        size_t parallel_env_index{};\n        for (size_t index = 0; index < Maxwell::MaxShaderProgram; ++index) {\n            if (key.unique_hashes[index] == 0) {\n                continue;\n            }\n            Shader::Environment* const env = envs[parallel_env_index++];\n            const u32 cfg_offset{\n                static_cast<u32>(env->StartAddress() + sizeof(Shader::ProgramHeader))};\n            parallel_pools[index] = std::make_unique<ShaderPools>();\n            ShaderPools* const stage_pools = parallel_pools[index].get();\n            const bool exits_to_dispatcher = index == 0;\n            shader_translation_workers.QueueWork(\n                [this, env, stage_pools, cfg_offset, exits_to_dispatcher, index,\n                 &parallel_programs, &parallel_errors] {\n                    struct PreflushedTexturePoolScope {\n                        PreflushedTexturePoolScope() {\n                            VideoCommon::SetShaderTexturePoolPreflushedForThread(true);\n                        }\n                        ~PreflushedTexturePoolScope() {\n                            VideoCommon::SetShaderTexturePoolPreflushedForThread(false);\n                        }\n                    } texture_pool_scope;\n                    try {\n                        ::Eden::Performance::CachePhaseTimer cfg_stage_cost{\n                            ::Eden::Performance::CachePhase::ShaderCfg,\n                            ::Eden::Performance::detailed_gpu_profile.load(\n                                std::memory_order_relaxed)};\n                        auto cfg_cost = Eden::Performance::VulkanTimer(20);\n                        Shader::Maxwell::Flow::CFG cfg(\n                            *env, stage_pools->flow_block, cfg_offset, exits_to_dispatcher);\n                        cfg_cost.reset();\n                        cfg_stage_cost.Stop();\n                        auto program = ([&] {\n                            auto cost = Eden::Performance::VulkanTimer(21);\n                            ::Eden::Performance::CachePhaseTimer stage_cost{\n                                ::Eden::Performance::CachePhase::ShaderIr,\n                                ::Eden::Performance::detailed_gpu_profile.load(\n                                    std::memory_order_relaxed)};\n                            return TranslateProgram(stage_pools->inst, stage_pools->block,\n                                                    *env, cfg, host_info);\n                        }());\n                        parallel_programs[index] =\n                            std::make_unique<Shader::IR::Program>(std::move(program));\n                    } catch (...) {\n                        parallel_errors[index] = std::current_exception();\n                    }\n                });\n        }\n        // The GPU owner intentionally waits here. While it waits, the TIC pool\n        // that it flushed cannot be made GPU-dirty by a later draw/dispatch.\n        shader_translation_workers.WaitForRequests();\n        for (size_t index = 0; index < Maxwell::MaxShaderProgram; ++index) {\n            if (parallel_errors[index]) {\n                std::rethrow_exception(parallel_errors[index]);\n            }\n            if (key.unique_hashes[index] != 0 && !parallel_programs[index]) {\n                throw std::runtime_error(\"graphics shader translation worker returned no program\");\n            }\n        }\n    }\n#endif\n\n    for (size_t index = 0; index < Maxwell::MaxShaderProgram; ++index) {",
        "    // Layer passthrough generation for devices without VK_EXT_shader_viewport_index_layer\n    Shader::IR::Program* layer_source_program{};\n\n    for (size_t index = 0; index < Maxwell::MaxShaderProgram; ++index) {"
    ],
    [
        "#ifdef PS5_NATIVE\n        if (parallel_translate_stages) {\n            if (!uses_vertex_a || index != 1) {\n                programs[index] = std::move(*parallel_programs[index]);\n            } else {\n                auto& program_va{programs[0]};\n                auto program_vb{std::move(*parallel_programs[index])};\n                programs[index] = MergeDualVertexPrograms(program_va, program_vb, env);\n            }\n        } else\n#endif\n        {\n            const u32 cfg_offset{\n                static_cast<u32>(env.StartAddress() + sizeof(Shader::ProgramHeader))};\n            ::Eden::Performance::CachePhaseTimer cfg_stage_cost{\n                ::Eden::Performance::CachePhase::ShaderCfg,\n                ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)};\n            auto cfg_cost = Eden::Performance::VulkanTimer(20);\n            Shader::Maxwell::Flow::CFG cfg(env, pools.flow_block, cfg_offset, index == 0);\n            cfg_cost.reset();\n            cfg_stage_cost.Stop();\n            if (!uses_vertex_a || index != 1) {\n                // Normal path\n                programs[index] = ([&] { auto cost = Eden::Performance::VulkanTimer(21); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderIr, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return TranslateProgram(pools.inst, pools.block, env, cfg, host_info); }());\n            } else {\n                // VertexB path when VertexA is present.\n                auto& program_va{programs[0]};\n                auto program_vb{([&] { auto cost = Eden::Performance::VulkanTimer(21); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderIr, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return TranslateProgram(pools.inst, pools.block, env, cfg, host_info); }())};\n                programs[index] = MergeDualVertexPrograms(program_va, program_vb, env);\n            }\n        }\n",
        "        const u32 cfg_offset{static_cast<u32>(env.StartAddress() + sizeof(Shader::ProgramHeader))};\n        ::Eden::Performance::CachePhaseTimer cfg_stage_cost{\n            ::Eden::Performance::CachePhase::ShaderCfg,\n            ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)};\n        auto cfg_cost = Eden::Performance::VulkanTimer(20);\n        Shader::Maxwell::Flow::CFG cfg(env, pools.flow_block, cfg_offset, index == 0);\n        cfg_cost.reset();\n        cfg_stage_cost.Stop();\n        if (!uses_vertex_a || index != 1) {\n            // Normal path\n            programs[index] = ([&] { auto cost = Eden::Performance::VulkanTimer(21); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderIr, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return TranslateProgram(pools.inst, pools.block, env, cfg, host_info); }());\n        } else {\n            // VertexB path when VertexA is present.\n            auto& program_va{programs[0]};\n            auto program_vb{([&] { auto cost = Eden::Performance::VulkanTimer(21); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderIr, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return TranslateProgram(pools.inst, pools.block, env, cfg, host_info); }())};\n            programs[index] = MergeDualVertexPrograms(program_va, program_vb, env);\n        }\n"
    ],
    [
        "        auto pipeline = CreateGraphicsPipeline(\n            main_pools, graphics_key,\n            std::span<Shader::Environment* const>{ptrs.data(), active}, nullptr, true, false);",
        "        auto pipeline = CreateGraphicsPipeline(\n            main_pools, graphics_key,\n            std::span<Shader::Environment* const>{ptrs.data(), active}, nullptr, true);"
    ],
    [
        "    ([&] { auto cost = Eden::Performance::VulkanTimer(19); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderPoolReset, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return main_pools.ReleaseContents(); }());\n#ifdef PS5_NATIVE\n    bool parallel_translate_stages{};\n    const size_t shader_stage_count = std::count_if(\n        graphics_key.unique_hashes.begin(), graphics_key.unique_hashes.end(),\n        [](u64 hash) { return hash != 0; });\n    if (shader_stage_count >= 2) {\n        // Lichii upstream bound: flushing at most 4 MiB keeps this owner-thread\n        // operation cheaper than serializing multiple expensive IR translations.\n        constexpr u64 MaxFlushedTexturePoolBytes = u64{4} << 20;\n        const auto& tex_header = maxwell3d->regs.tex_header;\n        const u64 pool_bytes =\n            (u64{static_cast<u32>(tex_header.limit)} + 1) *\n            sizeof(Tegra::Texture::TICEntry);\n        const GPUVAddr pool_base = tex_header.Address();\n        const u64 last_offset = pool_bytes - 1;\n        if (pool_bytes <= MaxFlushedTexturePoolBytes &&\n            pool_base <= std::numeric_limits<GPUVAddr>::max() - last_offset) {\n            const GPUVAddr pool_last = pool_base + last_offset;\n            if (gpu_memory->IsWithinGPUAddressRange(pool_last)) {\n                // Flush once on the GPU owner. Translation workers use only\n                // ReadBlockUnsafe for TICs until this owner joins them.\n                gpu_memory->FlushRegion(pool_base, pool_bytes);\n                parallel_translate_stages = true;\n            }\n        }\n    }\n    auto pipeline{CreateGraphicsPipeline(main_pools, graphics_key, environments.Span(),\n                                         nullptr, true, parallel_translate_stages)};\n#else\n    auto pipeline{\n        CreateGraphicsPipeline(main_pools, graphics_key, environments.Span(), nullptr, true)};\n#endif",
        "    ([&] { auto cost = Eden::Performance::VulkanTimer(19); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderPoolReset, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return main_pools.ReleaseContents(); }());\n    auto pipeline{\n        CreateGraphicsPipeline(main_pools, graphics_key, environments.Span(), nullptr, true)};"
    ]
]
REVIEWED_FC27_NONE_RT_BLOB = "d222fb5565cdf8db30c6d3d464f107ff26a042c8"
REVIEWED_FC27_RECENT_128_BLOB = "79660c5cc4ff046f24e7ffa50ab066a86857698c"
NONE_RT_REVERSES = [("                // Unused color slots are encoded as RenderTargetFormat::NONE.\n                // They have no attachment whose numeric class needs decoding.\n                // Avoid the generic surface fallback/log and preserve the\n                // historical default Float type, matching Lichii's path.\n                if (format == Tegra::RenderTargetFormat::NONE) {\n                    info.color_output_types[i] = Shader::AttributeType::Float;\n                    continue;\n                }\n", "")]
REVIEWED_FRAGMENT_INTEGER_RT_BLOB = "a0e2a45b9b0f080b739d97abb92e9485a0063f73"
RECENT_128_PREWARM_REVERSES = [
    ("    // FC27: the old fixed 32-entry PREFIX admitted 18 compute and only\n    // 14 graphics shaders from a 28.7 MiB cache. Thousands of newer records\n    // were ignored and the GPU owner still translated 303 new graphics keys.\n    // A recorded FC27 warm cache contains 710 valid pipeline records, yet the\n    // 32-entry prewarm left 361 guest shaders to translate during the match.\n    // For a modest, already populated cache, admit the newest 128 builders\n    // before gameplay; preserve the 32-entry prefix for large/absent caches.\n    // This shifts some first-use work to loading without skipping any draw.\n    constexpr size_t kStartupPrewarmPipelines = 32;\n    constexpr size_t kRecentPrewarmPipelines = 128;\n    constexpr std::uintmax_t kRecentShaderCacheScanLimit = 64ULL << 20;\n    const bool prefer_recent_cache =\n        env_before.present && env_before.bytes > 12 &&\n        env_before.bytes <= kRecentShaderCacheScanLimit;\n    const size_t prewarm_pipeline_limit =\n        prefer_recent_cache ? kRecentPrewarmPipelines : kStartupPrewarmPipelines;\n", "    // FC27: the old fixed 32-entry PREFIX admitted 18 compute and only\n    // 14 graphics shaders from a 28.7 MiB cache. Thousands of newer records\n    // were ignored and the GPU owner still translated 303 new graphics keys.\n    // Parse modest caches once and retain only the newest 32 valid builders;\n    // a large cache keeps the existing fast prefix cap to avoid startup I/O.\n    constexpr size_t kStartupPrewarmPipelines = 32;\n    constexpr std::uintmax_t kRecentShaderCacheScanLimit = 64ULL << 20;\n    const bool prefer_recent_cache =\n        env_before.present && env_before.bytes > 12 &&\n        env_before.bytes <= kRecentShaderCacheScanLimit;\n"),
    ("if (recent_cache_builds.size() == prewarm_pipeline_limit)", "if (recent_cache_builds.size() == kStartupPrewarmPipelines)"),
    ("if (state.total == prewarm_pipeline_limit)", "if (state.total == kStartupPrewarmPipelines)"),
    ("static_cast<long long>(startup_prewarm_ms), prewarm_pipeline_limit);", "static_cast<long long>(startup_prewarm_ms), kStartupPrewarmPipelines);"),
]
REVIEWED_RECENT_PREWARM_BLOB = "cfac496d574010b8121611c8616d38bf7cdcbc41"
FRAGMENT_INTEGER_RT_REVERSES = [
    ("\n        info.dual_source_blend = key.state.attachment0_dual_source_blend != 0;\n\n        // Vulkan requires signed/unsigned fragment outputs to match the\n        // attachment's numeric class. Previously this was enabled only on\n        // MoltenVK: native PS5 RADV would emit floats for integer targets,\n        // making color writes poison/undefined (Vulkan shader interfaces).\n        // Keep the existing desktop policy; fix the PS5 renderer's ABI.\n        const bool require_typed_fragment_outputs =\n#ifdef PS5_NATIVE\n            true;\n#else\n            device.IsMoltenVK();\n#endif\n        if (require_typed_fragment_outputs) {\n            for (size_t i = 0; i < 8; ++i) {\n                const auto format = static_cast<Tegra::RenderTargetFormat>(key.state.color_formats[i]);\n                const auto pixel_format = VideoCore::Surface::PixelFormatFromRenderTargetFormat(format);",
     "\n        info.dual_source_blend = key.state.attachment0_dual_source_blend != 0;\n\n        if (device.IsMoltenVK()) {\n            for (size_t i = 0; i < 8; ++i) {\n                const auto format = static_cast<Tegra::RenderTargetFormat>(key.state.color_formats[i]);\n                const auto pixel_format = VideoCore::Surface::PixelFormatFromRenderTargetFormat(format);"),
]
RECENT_PREWARM_REVERSES = [
    ("        VideoCommon::LoadPipelines(reader_token, pipeline_cache_filename, CACHE_VERSION, load_compute,\n                                   load_graphics);\n#ifdef PS5_NATIVE\n        if (prefer_recent_cache && !stop_loading.stop_requested()) {\n            for (auto& build : recent_cache_builds) {\n                workers.QueueWork(std::move(build));\n                std::scoped_lock lock{state.mutex};\n                ++state.total;\n            }\n            recent_cache_builds.clear();\n        }\n    } catch (const std::exception& error) {\n        LOG_WARNING(Render_Vulkan, \"PS5 shader prewarm aborted: {}\", error.what());\n    } catch (...) {",
     "        VideoCommon::LoadPipelines(reader_token, pipeline_cache_filename, CACHE_VERSION, load_compute,\n                                   load_graphics);\n#ifdef PS5_NATIVE\n    } catch (const std::exception& error) {\n        LOG_WARNING(Render_Vulkan, \"PS5 shader prewarm aborted: {}\", error.what());\n    } catch (...) {"),
    ("    // workers.WaitForRequests() would permanently request_stop() on the\n    // shader-builder pool, breaking first-use shaders later in gameplay.\n#ifdef PS5_NATIVE\n    // Newest-entry mode must read to the last VALID record (also repairing\n    // a corrupt tail); large caches retain the old first-32 stop token.\n    const std::stop_token reader_token{\n        prefer_recent_cache ? stop_loading : startup_reader.get_token()};\n#else\n    const std::stop_token reader_token{stop_loading};\n#endif",
     "    // workers.WaitForRequests() would permanently request_stop() on the\n    // shader-builder pool, breaking first-use shaders later in gameplay.\n#ifdef PS5_NATIVE\n    const std::stop_token reader_token{startup_reader.get_token()};\n#else\n    const std::stop_token reader_token{stop_loading};\n#endif"),
    ("        ++state.disk_graphics_admitted;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n    }};\n    // Only the reader observes the quota stop. Passing this token to\n    // workers.WaitForRequests() would permanently request_stop() on the",
     "        ++state.disk_graphics_admitted;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        // Workers read total while holding state.mutex. Publish reader\n        // increments under the same lock to avoid a cache-prewarm data race.\n        {\n            std::scoped_lock count_lock{state.mutex};\n            ++state.total;\n        }\n#ifdef PS5_NATIVE\n        if (state.total == kStartupPrewarmPipelines)\n            startup_reader.request_stop();\n#endif\n    }};\n    // Only the reader observes the quota stop. Passing this token to\n    // workers.WaitForRequests() would permanently request_stop() on the"),
    ("            return;\n        }\n\n        schedule_prewarm([this, key, envs_ = std::move(envs), &state, &callback]() mutable {\n            ShaderPools pools;\n            boost::container::static_vector<Shader::Environment*, 5> env_ptrs;\n            for (auto& env : envs_) {",
     "            return;\n        }\n\n        workers.QueueWork([this, key, envs_ = std::move(envs), &state, &callback]() mutable {\n            ShaderPools pools;\n            boost::container::static_vector<Shader::Environment*, 5> env_ptrs;\n            for (auto& env : envs_) {"),
    ("                callback(VideoCore::LoadCallbackStage::Build, state.built, state.total);\n            }\n        });\n    }};\n    const auto load_graphics{[&](std::ifstream& file, std::vector<FileEnvironment> envs) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN",
     "                callback(VideoCore::LoadCallbackStage::Build, state.built, state.total);\n            }\n        });\n        // Workers read total while holding state.mutex. Publish reader\n        // increments under the same lock to avoid a cache-prewarm data race.\n        {\n            std::scoped_lock count_lock{state.mutex};\n            ++state.total;\n        }\n#ifdef PS5_NATIVE\n        if (state.total == kStartupPrewarmPipelines)\n            startup_reader.request_stop();\n#endif\n    }};\n    const auto load_graphics{[&](std::ifstream& file, std::vector<FileEnvironment> envs) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN"),
    ("        ComputePipelineCacheKey key;\n        file.read(reinterpret_cast<char*>(&key), sizeof(key));\n\n        schedule_prewarm([this, key, env_ = std::move(env), &state, &callback]() mutable {\n            ShaderPools pools;\n            auto pipeline{CreateComputePipeline(pools, key, env_, state.statistics.get(), false)};\n            std::scoped_lock lock{state.mutex};",
     "        ComputePipelineCacheKey key;\n        file.read(reinterpret_cast<char*>(&key), sizeof(key));\n\n        workers.QueueWork([this, key, env_ = std::move(env), &state, &callback]() mutable {\n            ShaderPools pools;\n            auto pipeline{CreateComputePipeline(pools, key, env_, state.statistics.get(), false)};\n            std::scoped_lock lock{state.mutex};"),
    ("    if (device.IsKhrPipelineExecutablePropertiesEnabled()) {\n        state.statistics = std::make_unique<PipelineStatistics>(device);\n    }\n    const auto schedule_prewarm = [&](Common::UniqueFunction<void> build) {\n#ifdef PS5_NATIVE\n        if (prefer_recent_cache) {\n            // No driver work while scanning the file. Move-only jobs own all\n            // shader environments and cannot outlive this loading function.\n            // Discard oldest unstarted work without creating GPU pipelines.\n            if (recent_cache_builds.size() == kStartupPrewarmPipelines)\n                recent_cache_builds.pop_front();\n            recent_cache_builds.emplace_back(std::move(build));\n            return;\n        }\n#endif\n        workers.QueueWork(std::move(build));\n        {\n            std::scoped_lock lock{state.mutex};\n            ++state.total;\n        }\n#ifdef PS5_NATIVE\n        if (state.total == kStartupPrewarmPipelines)\n            startup_reader.request_stop();\n#endif\n    };\n    const auto load_compute{[&](std::ifstream& file, FileEnvironment env) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE",
     "    if (device.IsKhrPipelineExecutablePropertiesEnabled()) {\n        state.statistics = std::make_unique<PipelineStatistics>(device);\n    }\n    const auto load_compute{[&](std::ifstream& file, FileEnvironment env) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE"),
    ("    constexpr size_t kStartupPrewarmPipelines = 32;\n    constexpr std::uintmax_t kRecentShaderCacheScanLimit = 64ULL << 20;\n    const bool prefer_recent_cache =\n        env_before.present && env_before.bytes > 12 &&\n        env_before.bytes <= kRecentShaderCacheScanLimit;\n    std::deque<Common::UniqueFunction<void>> recent_cache_builds;\n    const auto startup_prewarm_started = std::chrono::steady_clock::now();\n    std::stop_source startup_reader;\n#endif",
     "    constexpr size_t kStartupPrewarmPipelines = 32;\n    const auto startup_prewarm_started = std::chrono::steady_clock::now();\n    std::stop_source startup_reader;\n#endif"),
    ("#endif\n\n#ifdef PS5_NATIVE\n    // FC27: the old fixed 32-entry PREFIX admitted 18 compute and only\n    // 14 graphics shaders from a 28.7 MiB cache. Thousands of newer records\n    // were ignored and the GPU owner still translated 303 new graphics keys.\n    // Parse modest caches once and retain only the newest 32 valid builders;\n    // a large cache keeps the existing fast prefix cap to avoid startup I/O.\n    constexpr size_t kStartupPrewarmPipelines = 32;",
     "#endif\n\n#ifdef PS5_NATIVE\n    // Restore a bounded prefix of a title's saved pipelines before gameplay.\n    // Games with fewer cached entries load only those entries. This policy\n    // applies to every title (NS1 and NS2) without any title ID exceptions.\n    // Keep the worker queue, draw order and GPU fences unchanged.\n    constexpr size_t kStartupPrewarmPipelines = 32;"),
    ("#include \"dev_vulkan.h\"\n#include \"diagnostics.h\"\n#include <cstddef>\n#include <deque>\n#include <fstream>\n#include <iostream>\n#include <memory>",
     "#include \"dev_vulkan.h\"\n#include \"diagnostics.h\"\n#include <cstddef>\n#include <fstream>\n#include <iostream>\n#include <memory>"),
]

def reverse_reviewed_source(source: str, replacements: list[tuple[str, str]], label: str) -> str:
    for successor, predecessor in replacements:
        assert source.count(successor) == 1, (label + " hunk drift", successor[:100])
        source = source.replace(successor, predecessor, 1)
    return source

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


def reverse_immutable_snapshot_successor(source: str) -> str:
    """Reverse only the reviewed immutable-worker snapshot deltas to 44f5."""
    def once(old: str, new: str, label: str) -> None:
        nonlocal source
        assert source.count(old) == 1, ("snapshot reverse anchor", label, source.count(old))
        source = source.replace(old, new, 1)

    # 70789b12: freeze Maxwell register state used by translation workers.
    once(
        """void SetShaderTranslationSnapshotForThread(
    GPUVAddr texture_base, u32 texture_limit, const u8* texture_data,
    bool via_header_index, u32 viewport_transform_state,
    const u8* const* cbuf_data, const u32* cbuf_sizes, size_t cbuf_count) noexcept;""",
        """void SetShaderTranslationSnapshotForThread(
    GPUVAddr texture_base, u32 texture_limit, const u8* texture_data,
    const u8* const* cbuf_data, const u32* cbuf_sizes, size_t cbuf_count) noexcept;""",
        "707 declaration")
    once(
        """    const bool snapshot_via_header_index =
        maxwell3d->regs.sampler_binding == Maxwell::SamplerBinding::ViaHeaderBinding;
    const u32 snapshot_viewport_transform_state =
        maxwell3d->regs.viewport_scale_offset_enabled;
""", "", "707 register snapshot")
    once(
        """    if (parallel_translate_stages) {
        for (Shader::Environment* const env : envs) {
            // HLE replacement lookup still belongs to Maxwell3D::replace_table.
            // Keep those rare shaders on the GPU owner until that table has an
            // immutable per-environment representation too.
            if (env->HasHLEMacroState()) {
                parallel_translate_stages = false;
                break;
            }
        }
    }

""", "", "707 HLE serial fallback")
    once(
        """                 physical_stage, snapshot_texture_base, snapshot_texture_limit,
                 snapshot_via_header_index, snapshot_viewport_transform_state,
                 &parallel_texture_snapshot, &parallel_cbuf_ptrs,""",
        """                 physical_stage, snapshot_texture_base, snapshot_texture_limit,
                 &parallel_texture_snapshot, &parallel_cbuf_ptrs,""",
        "707 lambda capture")
    once(
        """                            const std::vector<u8>& texture, bool via_header_index,
                            u32 viewport_transform_state,
                            const std::array<const u8*, Maxwell::MaxConstBuffers>& cbuf_data,""",
        """                            const std::vector<u8>& texture,
                            const std::array<const u8*, Maxwell::MaxConstBuffers>& cbuf_data,""",
        "707 scope params")
    once(
        """                                texture_base, texture_limit, texture.data(),
                                via_header_index, viewport_transform_state,
                                cbuf_data.data(), cbuf_sizes.data(),""",
        """                                texture_base, texture_limit, texture.data(),
                                cbuf_data.data(), cbuf_sizes.data(),""",
        "707 setter args")
    once(
        """                        snapshot_texture_base, snapshot_texture_limit,
                        parallel_texture_snapshot, snapshot_via_header_index,
                        snapshot_viewport_transform_state,
                        parallel_cbuf_ptrs[physical_stage],""",
        """                        snapshot_texture_base, snapshot_texture_limit,
                        parallel_texture_snapshot, parallel_cbuf_ptrs[physical_stage],""",
        "707 scope invocation")

    # 4bd7eb17: immutable TIC/CBUF bytes replaced the earlier owner-flushed TIC path.
    once(
        """void SetShaderTranslationSnapshotForThread(
    GPUVAddr texture_base, u32 texture_limit, const u8* texture_data,
    const u8* const* cbuf_data, const u32* cbuf_sizes, size_t cbuf_count) noexcept;
void ClearShaderTranslationSnapshotForThread() noexcept;""",
        """void SetShaderTexturePoolPreflushedForThread(bool preflushed) noexcept;""",
        "4bd declaration")

    start = source.find("    // Worker translation must never traverse the live guest GMMU. Snapshot\\n")
    stop = source.find("    if (parallel_translate_stages) {\\n        size_t parallel_env_index{};", start)
    assert start >= 0 and stop > start, ("snapshot owner block anchors", start, stop)
    source = source[:start] + source[stop:]

    once(
        """                [this, env, stage_pools, cfg_offset, exits_to_dispatcher, index,
                 physical_stage, snapshot_texture_base, snapshot_texture_limit,
                 &parallel_texture_snapshot, &parallel_cbuf_ptrs,
                 &parallel_cbuf_sizes, &parallel_programs, &parallel_errors,
                 &parallel_stage_costs] {""",
        """                [this, env, stage_pools, cfg_offset, exits_to_dispatcher, index,
                 &parallel_programs, &parallel_errors, &parallel_stage_costs] {""",
        "4bd lambda capture")

    scope_start = source.find("                    struct ImmutableGuestSnapshotScope {")
    scope_stop = source.find("                    try {", scope_start)
    assert scope_start >= 0 and scope_stop > scope_start
    source = source[:scope_start] + """                    struct PreflushedTexturePoolScope {
                        PreflushedTexturePoolScope() {
                            VideoCommon::SetShaderTexturePoolPreflushedForThread(true);
                        }
                        ~PreflushedTexturePoolScope() {
                            VideoCommon::SetShaderTexturePoolPreflushedForThread(false);
                        }
                    } texture_pool_scope;
""" + source[scope_stop:]

    once(
        """        // The GPU owner intentionally waits here. Workers see only immutable
        // host snapshots plus each environment's already-copied shader code;
        // no worker traverses the live GMMU/PTE table.
""",
        """        // The GPU owner intentionally waits here. While it waits, the TIC pool
        // that it flushed cannot be made GPU-dirty by a later draw/dispatch.
""",
        "4bd wait comment")
    once(
        """                // Full TIC/CBUF byte snapshots are built inside
                // CreateGraphicsPipeline on the GPU owner before queueing work.
                parallel_translate_stages = true;""",
        """                // Flush once on the GPU owner. Translation workers use only
                // ReadBlockUnsafe for TICs until this owner joins them.
                gpu_memory->FlushRegion(pool_base, pool_bytes);
                parallel_translate_stages = true;""",
        "4bd owner TIC flush")
    return source


def normalize_for_historical_proof(source: str) -> tuple[str, bool]:
    """Return old exact source and whether reviewed diagnostic blocks existed.

    Reject ANY unrelated byte change, marker drift, or missing sentinel.
    The normalized output is only used by source-integrity comparison.
    It must NOT replace the compiled production vendor file.
    """
    current = git_blob(source)
    if current == REVIEWED_IMMUTABLE_SNAPSHOT_BLOB:
        source = reverse_immutable_snapshot_successor(source)
        current = git_blob(source)
        assert current == REVIEWED_PARALLEL_TIMING_BLOB, (
            "Immutable shader snapshot predecessor drift", current)
    if current == REVIEWED_PARALLEL_TIMING_BLOB:
        source = reverse_reviewed_source(
            source, PARALLEL_TIMING_REVERSES,
            "parallel graphics keyed shader timing")
        current = git_blob(source)
        assert current == REVIEWED_PARALLEL_TRANSLATION_BLOB, (
            "Parallel shader timing predecessor drift", current)
    if current == REVIEWED_PARALLEL_TRANSLATION_BLOB:
        source = reverse_reviewed_source(
            source, PARALLEL_TRANSLATION_REVERSES,
            "NS1 bounded parallel graphics IR translation")
        current = git_blob(source)
        assert current == REVIEWED_FC27_NONE_RT_BLOB, (
            "Parallel graphics translation predecessor drift", current)
    if current == REVIEWED_FC27_NONE_RT_BLOB:
        source = reverse_reviewed_source(source, NONE_RT_REVERSES,
                                         "FC27 unused render-target NONE guard")
        current = git_blob(source)
        assert current == REVIEWED_FC27_RECENT_128_BLOB, (
            "FC27 NONE guard predecessor drift", current)
    if current == REVIEWED_FC27_RECENT_128_BLOB:
        # Reconstruct only the reviewed 128-entry small-cache admission policy
        # before the established integer-output and original R23 receipts.
        source = reverse_reviewed_source(source, RECENT_128_PREWARM_REVERSES,
                                         "FC27 bounded recent pipeline preload")
        current = git_blob(source)
        assert current == REVIEWED_FRAGMENT_INTEGER_RT_BLOB, (
            "FC27 recent pipeline preload predecessor drift", current)
    if current == REVIEWED_FRAGMENT_INTEGER_RT_BLOB:
        source = reverse_reviewed_source(source, FRAGMENT_INTEGER_RT_REVERSES, "integer fragment RT")
        current = git_blob(source)
        assert current == REVIEWED_RECENT_PREWARM_BLOB, ("Integer RT predecessor drift", current)
    if current == REVIEWED_RECENT_PREWARM_BLOB:
        source = reverse_reviewed_source(source, RECENT_PREWARM_REVERSES, "recent shader prewarm")
        current = git_blob(source)
        assert current == REVIEWED_PIPELINE_DRAIN_BLOB, ("Prewarm predecessor drift", current)
    # Lichii 499e2e4 successor drains queued pipeline workers before teardown.
    # Reverse this exact shipping PS5-only hunk to reapply the existing R23 proof.
    if current == REVIEWED_PIPELINE_DRAIN_BLOB:
        new = """    // Lichii 499e2e4: queued builders capture pipeline objects by pointer.
    // Drain them while the cache still owns every pipeline; otherwise member
    // destruction can race a late builder during title teardown.
    workers.WaitForRequests();
    // First-use shader environments are serialized on this worker. Let all
    // accepted writes finish before destroying the worker and VkPipelineCache,
    // or a later launch re-translates shaders that were never persisted.
    // These are shutdown-only drains, never waits in the draw hot path.
"""
        old = """    // First-use shader environments are serialized on this worker. Let all
    // accepted writes finish before destroying the worker and VkPipelineCache,
    // or a later launch re-translates shaders that were never persisted.
    // This is a shutdown-only drain, never a wait in the draw hot path.
"""
        assert source.count(new) == 1, "Pipeline worker teardown successor drift"
        source = source.replace(new, old, 1)
        current = git_blob(source)
        assert current == REVIEWED_FRAGMENT_SHUFFLE_WITNESS_BLOB, (
            "Pipeline teardown predecessor drift", current)

    # Vendor #183 adds only a bounded standard-stderr witness around the
    # already-reviewed PS5 fragment-shuffle fallback. Reverse that exact block
    # first, then require the prior reviewed fallback blob before continuing
    # the immutable R23 normalization chain.
    if current == REVIEWED_FRAGMENT_SHUFFLE_WITNESS_BLOB:
        witness = """            static std::atomic<unsigned> fragment_shuffle_witness{};
            const unsigned fallback_witness =
                fragment_shuffle_witness.fetch_add(1, std::memory_order_relaxed) + 1;
            if (fallback_witness <= 8) {
                std::fprintf(stderr,
                             \"EDEN_FRAGMENT_SHUFFLE_FALLBACK count=%u hash=0x%016llx\\n\",
                             fallback_witness,
                             static_cast<unsigned long long>(key.unique_hashes[index]));
            }
"""
        assert source.count(witness) == 1, "Fragment-shuffle witness drift"
        source = source.replace(witness, "", 1)
        current = git_blob(source)
        assert current == REVIEWED_FRAGMENT_SHUFFLE_FALLBACK_BLOB, (
            "Fragment-shuffle witness predecessor drift", current)
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
