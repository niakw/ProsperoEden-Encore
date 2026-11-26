#!/usr/bin/env python3
"""S01: compile actual per-key cold-shader phase timer and RAII attribution.

Host-only test. Native mode changes diagnostic attribution, not CPU scheduling,
Vulkan worker fences, shader outputs, or the quiet path.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
perf = (root / "headless/performance.h").read_text()
pipeline = (root / "vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp").read_text()
gen = (root / "tools/prepare-vulkan-port.py").read_text()
analyzer = (root / "tools/analyze-ps5-cold-shader-misses.py").read_text()
# GPU-23: a native Vulkan integer color attachment must receive a signed
# or unsigned integer SPIR-V output. This checks the shipping pipeline
# selection AND the pre-existing Sirit emitter, never a duplicate shader.
spirv_output = (root / "vendor/sources/eden/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp").read_text()
spirv_store = (root / "vendor/sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp").read_text()
fragment = pipeline.split("case Shader::Stage::Fragment: {", 1)[1].split("\n    default:", 1)[0]
assert "const bool require_typed_fragment_outputs =" in fragment
assert "#ifdef PS5_NATIVE\n            true;\n#else\n            device.IsMoltenVK();\n#endif" in fragment
none_guard = "if (format == Tegra::RenderTargetFormat::NONE)"
assert fragment.count(none_guard) == 1
assert "info.color_output_types[i] = Shader::AttributeType::Float;" in fragment
assert fragment.index(none_guard) < fragment.index("PixelFormatFromRenderTargetFormat(format)")
assert "Unused color slots are encoded as RenderTargetFormat::NONE" in gen
assert fragment.index("if (require_typed_fragment_outputs)") < fragment.index("IsPixelFormatInteger(pixel_format)")
assert "Shader::AttributeType::SignedInt" in fragment
assert "Shader::AttributeType::UnsignedInt" in fragment
assert "GPU-23 PS5 integer framebuffer fragment output numeric type" in gen
assert "GetAttributeType(*this, runtime_info.color_output_types[index])" in spirv_output
assert "ctx.OpBitcast(ctx.U32[1], value)" in spirv_store
assert "ctx.OpBitcast(ctx.S32[1], value)" in spirv_store
assert "spv::Decoration::Index, index" in spirv_output # dual-source blend preserved


stage_start = perf.index("struct ShaderMissStageCosts {")
stage_end = perf.index("inline thread_local ShaderMissStageCosts* shader_miss_stage_active{};", stage_start)
stage_end += len("inline thread_local ShaderMissStageCosts* shader_miss_stage_active{};")
stage_declarations = perf[stage_start:stage_end]
timer_start = perf.index("class CachePhaseTimer {")
timer_end = perf.index("\n};", timer_start) + len("\n};")
real_timer = perf[timer_start:timer_end]
trace_start = pipeline.index("struct ColdShaderMissTrace {")
trace_end = pipeline.index("\n};\n#endif", trace_start) + len("\n};")
real_trace = pipeline[trace_start:trace_end]

assert real_trace in gen
assert "shader_miss_stage_active" in real_trace
assert "if (!enabled) return;" in real_trace
assert "std::chrono::steady_clock::now()" in real_trace
assert "shader_miss_stage_active = previous;" in real_trace
assert "EDEN_VULKAN_SHADER_MISS kind=%s key=%016llx" in real_trace
assert "env_ns=%llu pool_ns=%llu" in real_trace
assert "cfg_ns=%llu ir_ns=%llu spirv_ns=%llu module_ns=%llu" in real_trace
assert "phase(phase)" in real_timer
assert "if (auto* const keyed = shader_miss_stage_active)" in real_timer
for name in ("GraphicsShaderEnvironment", "ShaderPoolReset", "ShaderCfg", "ShaderIr",
             "ShaderSpirv", "ShaderModule"):
    assert "case CachePhase::" + name + ":" in real_timer, name
assert "stats->total_ns.fetch_add(ns, std::memory_order_relaxed);" in real_timer
assert "std::chrono::steady_clock::time_point" in real_trace
assert "stages: tuple[int, int, int, int, int, int] | None = None" in analyzer

# Parallel graphics translation runs CFG/IR on dedicated workers, so the
# thread-local keyed owner must be transferred to private per-stage buckets
# and merged only after all workers have joined.
parallel_begin = pipeline.index(
    "std::array<::Eden::Performance::ShaderMissStageCosts, Maxwell::MaxShaderProgram>")
parallel_end = pipeline.index("\n#endif", parallel_begin)
parallel = pipeline[parallel_begin:parallel_end]
for token in (
    "parallel_stage_costs{}",
    "ShaderMissStageScope",
    "shader_miss_stage_active = current;",
    "shader_miss_stage_active = previous;",
    "shader_translation_workers.WaitForRequests();",
    "owner_stage_costs->cfg_ns += parallel_stage_costs[index].cfg_ns;",
    "owner_stage_costs->ir_ns += parallel_stage_costs[index].ir_ns;",
):
    assert token in parallel, token
assert parallel.index("shader_translation_workers.WaitForRequests();") < parallel.index(
    "owner_stage_costs->cfg_ns += parallel_stage_costs[index].cfg_ns;")
# Each worker owns a distinct array element; no atomic/keyed sharing between
# concurrent stage translations is introduced.
assert "&parallel_stage_costs[index]" in parallel
assert "std::array<::Eden::Performance::ShaderMissStageCosts, Maxwell::MaxShaderProgram>" in gen

cpp = r"""
#include <array>
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <cstdint>
#include <stdexcept>
#include <string>
using u64 = std::uint64_t;

namespace Common {
struct FakeClock {
    std::chrono::nanoseconds now{};
    [[nodiscard]] std::chrono::nanoseconds GetTimeNS() const { return now; }
};
inline FakeClock g_wall_clock;
}
namespace Eden::Performance {
enum class CachePhase : unsigned {
    GraphicsShaderEnvironment, ShaderPoolReset, ShaderCfg, ShaderIr,
    ShaderSpirv, ShaderModule, Other, Count
};
struct CachePhaseTotal {
    std::atomic<unsigned long long> samples{}, total_ns{}, max_ns{};
};
inline std::array<CachePhaseTotal, static_cast<unsigned>(CachePhase::Count)> cache_phase_totals{};
inline thread_local bool cache_draw_sample_active = false;
inline std::atomic<bool> detailed_gpu_profile{false};
__STAGE_DECLARATIONS__
__REAL_TIMER__
}

#ifdef PS5_NATIVE
__REAL_TRACE__
#endif
void Stage(Eden::Performance::CachePhase phase, unsigned long long nanos) {
    Eden::Performance::CachePhaseTimer timer{phase, true};
    Common::g_wall_clock.now += std::chrono::nanoseconds(nanos);
    timer.Stop();
}
int main() {
    using namespace Eden::Performance;
#ifdef PS5_NATIVE
    // No session owner with quiet logging, even though the hot shader is
    // created. Unkeyed sampled phases must continue to work independently.
    {
        ColdShaderMissTrace quiet{"graphics", 1, false};
        assert(shader_miss_stage_active == nullptr);
        Stage(CachePhase::ShaderCfg, 2);
        quiet.Complete(true);
    }
    detailed_gpu_profile.store(true);
    {
        ColdShaderMissTrace cold{"graphics", 2, false};
        assert(shader_miss_stage_active == &cold.stages);
        Stage(CachePhase::GraphicsShaderEnvironment, 3);
        Stage(CachePhase::ShaderPoolReset, 5);
        Stage(CachePhase::ShaderCfg, 7);
        Stage(CachePhase::ShaderIr, 11);
        Stage(CachePhase::ShaderSpirv, 13);
        Stage(CachePhase::ShaderModule, 17);
        Stage(CachePhase::Other, 19);
        assert(cold.stages.env_ns == 3 && cold.stages.pool_ns == 5);
        assert(cold.stages.cfg_ns == 7 && cold.stages.ir_ns == 11);
        assert(cold.stages.spirv_ns == 13 && cold.stages.module_ns == 17);
        // Model the exact worker contract: a worker gets a private keyed bucket,
        // then the GPU owner merges it after the join. The owner's thread-local
        // pointer remains its ColdShaderMissTrace throughout.
        ShaderMissStageCosts worker_cfg{}, worker_ir{};
        {
            auto* const owner = shader_miss_stage_active;
            shader_miss_stage_active = &worker_cfg;
            Stage(CachePhase::ShaderCfg, 41);
            shader_miss_stage_active = owner;
        }
        {
            auto* const owner = shader_miss_stage_active;
            shader_miss_stage_active = &worker_ir;
            Stage(CachePhase::ShaderIr, 43);
            shader_miss_stage_active = owner;
        }
        assert(cold.stages.cfg_ns == 7 && cold.stages.ir_ns == 11);
        cold.stages.cfg_ns += worker_cfg.cfg_ns;
        cold.stages.ir_ns += worker_ir.ir_ns;
        assert(cold.stages.cfg_ns == 48 && cold.stages.ir_ns == 54);
        {
            ColdShaderMissTrace nested{"compute", 3, true};
            assert(shader_miss_stage_active == &nested.stages);
            Stage(CachePhase::ShaderCfg, 23);
            assert(nested.stages.cfg_ns == 23);
            assert(cold.stages.cfg_ns == 48);
            nested.Complete(false);
        }
        assert(shader_miss_stage_active == &cold.stages);
        Stage(CachePhase::ShaderCfg, 29);
        assert(cold.stages.cfg_ns == 77);
        cold.Complete(true);
        assert(shader_miss_stage_active == nullptr);
        Stage(CachePhase::ShaderModule, 31); // not part of the completed miss
        assert(cold.stages.module_ns == 17);
    }
    {
        ColdShaderMissTrace retry{"graphics", 4, true};
        Stage(CachePhase::ShaderModule, 37);
        retry.Complete(true);
        assert(retry.stages.module_ns == 37);
    }
    assert(shader_miss_stage_active == nullptr);
    try {
        ColdShaderMissTrace error{"compute", 5, false};
        Stage(CachePhase::ShaderIr, 41);
        throw std::runtime_error("exception within a cold translation");
    } catch (const std::runtime_error&) {
        assert(shader_miss_stage_active == nullptr);
    }
    detailed_gpu_profile.store(false);
    {
        ColdShaderMissTrace quiet_again{"compute", 6, true};
        assert(shader_miss_stage_active == nullptr);
        quiet_again.Complete(false);
    }
#else
    Stage(CachePhase::ShaderCfg, 2);
    assert(shader_miss_stage_active == nullptr);
#endif
    assert(cache_phase_totals[static_cast<unsigned>(CachePhase::ShaderCfg)]
               .samples.load() >= 1);
}
"""
cpp = cpp.replace("__STAGE_DECLARATIONS__", stage_declarations)
cpp = cpp.replace("__REAL_TIMER__", real_timer)
cpp = cpp.replace("__REAL_TRACE__", real_trace)

compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="f07-keyed-shader-stages-") as temp:
    src = Path(temp) / "probe.cpp"
    src.write_text(cpp)
    for native in (False, True):
        for opt in ("-O0", "-O2"):
            exe = Path(temp) / ("ps5" if native else "desktop") / opt[1:]
            exe.parent.mkdir(exist_ok=True)
            build = subprocess.run(
                [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                 "-fsanitize=undefined", "-fno-sanitize-recover=all",
                 *(["-DPS5_NATIVE=1"] if native else []),
                 str(src), "-o", str(exe)], capture_output=True, text=True, timeout=45
            )
            assert build.returncode == 0, (native, opt, build.stderr[-6000:])
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
            assert run.returncode == 0, (native, opt, run.stdout, run.stderr[-4000:])
            if native:
                assert run.stdout.count("EDEN_VULKAN_SHADER_MISS") == 3
                assert "key=0000000000000002" in run.stdout
                assert "env_ns=3 pool_ns=5 cfg_ns=77 ir_ns=54 spirv_ns=13 module_ns=17" in run.stdout
                assert "key=0000000000000003" in run.stdout
                assert "cfg_ns=23" in run.stdout
                assert "key=0000000000000004" in run.stdout
                assert "module_ns=37" in run.stdout
                assert "key=0000000000000001" not in run.stdout
                assert "key=0000000000000005" not in run.stdout
                assert "key=0000000000000006" not in run.stdout
            else:
                assert "EDEN_VULKAN_SHADER_MISS" not in run.stdout
            print(f"F07_KEYED_SHADER_STAGES_PASS mode={'PS5' if native else 'desktop'} {opt}")
print("HOST_ONLY no shader output, Vulkan worker, FPS or console measurements")

# GPU-owner participation keeps the same snapshot and stage-local attribution.
assert "const size_t parallel_stage_count = envs.size();" in pipeline
assert "if (parallel_env_index == parallel_stage_count) {" in pipeline
assert pipeline.index("translate_stage();") < pipeline.index("shader_translation_workers.QueueWork(std::move(translate_stage));")
assert pipeline.index("shader_translation_workers.QueueWork(std::move(translate_stage));") < pipeline.index("shader_translation_workers.WaitForRequests();", pipeline.index("translate_stage();"))
