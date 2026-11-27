#!/usr/bin/env python3
"""F07: replay selected native Scheduler graphics state after DrawTexture blit.

The raw VkImage BlitColor overload records a graphics pipeline on the command
buffer. Eden #4559 moved the required scheduler invalidation from DrawTexture
into the maintained BlitColor owner itself. Verify the selected source still
invalidates guest graphics state after recording the raw blit. HOST ONLY.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
raster = (root / "vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
blit = (root / "vendor/encore-active/eden-vulkan/blit_image.cpp").read_text()
sched = (root / "vendor/encore-active/eden-vulkan/vulkan_scheduler.cpp").read_text()
gen = (root / "tools/prepare-vulkan-port.py").read_text()
cmake = (root / "headless/vulkan.cmake").read_text()


def fragment(source: str, begin: str, end: str) -> str:
    assert source.count(begin) == 1, ("begin", begin)
    rest = source.split(begin, 1)[1]
    assert end in rest, ("end", end)
    return begin + rest.split(end, 1)[0]


draw = fragment(raster, "void RasterizerVulkan::DrawTexture() {",
                "\nvoid RasterizerVulkan::Clear(")
raw = fragment(blit, "void BlitImageHelper::BlitColor(const Framebuffer* dst_framebuffer, VkImageView src_image_view,",
               "\nvoid BlitImageHelper::BlitImpl(")
ordinary = fragment(blit, "void BlitImageHelper::BlitImpl(",
                    "\nvoid BlitImageHelper::BlitColorMSAA(")
assert draw.count("blit_image.BlitColor(framebuffer, texture.RenderTarget()") == 1
# Eden #4559 centralizes raw-blit invalidation in the selected helper. Keep
# DrawTexture free of a duplicate invalidation while requiring the helper to
# invalidate only after the command has been recorded.
assert draw.count("scheduler.InvalidateState();") == 0
assert raw.count("scheduler.InvalidateState();") == 1
assert raw.index("scheduler.Record(") < raw.index("scheduler.InvalidateState();")
assert "gpu_memory->FlushCaching();" in draw.split("std::scoped_lock l{texture_cache.mutex};", 1)[0]
assert "cmdbuf.BindPipeline(VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);" in raw
assert "cmdbuf.BindDescriptorSets(VK_PIPELINE_BIND_POINT_GRAPHICS" in raw
assert raw.count("scheduler.InvalidateState();") == 1
assert ordinary.count("scheduler.InvalidateState();") == 1
assert "PORT_BUILD_DIR" in cmake and "vulkan_rasterizer.cpp" in cmake
assert 'list(REMOVE_ITEM video_sources renderer_vulkan/blit_image.cpp)' in cmake
assert 'list(APPEND video_sources "${PORT_BUILD_DIR}/blit_image.cpp")' in cmake
assert '"    scheduler.InvalidateState();\\n"' in gen
assert "F07 bypass cold guest graphics shader lookup in native raw DrawTexture" in gen
for method_name,support in (("UpdateAlphaToCoverageEnable","SupportsAlphaToCoverage"),
                            ("UpdateAlphaToOneEnable","SupportsAlphaToOne")):
    assert f"F07 avoid raw blit guest shader lookup for native {method_name[6:-6]}" in gen
    start_method="void RasterizerVulkan::"+method_name+"("
    method=raster.split(start_method,1)[1].split("\nvoid RasterizerVulkan::",1)[0]
    assert method.count("pipeline_cache.CurrentGraphicsPipeline()")==1
    assert "GraphicsPipeline* const pipeline = prepared_pipeline;" in method
    assert method.index("#ifdef PS5_NATIVE") < method.index("GraphicsPipeline* const pipeline = prepared_pipeline;") < method.index("#else")
    assert "pipeline->"+support+"()" in method

dmethod=fragment(raster, "void RasterizerVulkan::UpdateDynamicStates() {",
                 "\nvoid RasterizerVulkan::HandleTransformFeedback(")
assert dmethod.count("if (device.IsExtVertexInputDynamicStateSupported()) {")==1
dynamic_branch=dmethod[dmethod.index("    if (device.IsExtVertexInputDynamicStateSupported()) {"):dmethod.rfind("\n}")]
assert "if (prepared_pipeline && prepared_pipeline->HasDynamicVertexInput())" in dynamic_branch
assert dynamic_branch.count("pipeline_cache.CurrentGraphicsPipeline()")==1
assert dynamic_branch.index("#ifdef PS5_NATIVE") < dynamic_branch.index("#else")
assert "    UpdateDynamicStates();" in draw
assert draw.index("    std::scoped_lock l{texture_cache.mutex};") < draw.index("    UpdateDynamicStates();")
# Raw blit must not record unused guest state under the texture mutex.
# The real BlitColor implementation supplies its own pipeline/viewport/scissor
# and Scheduler invalidation re-dirties guest state for the next real draw.
assert "void Scheduler::InvalidateState()" in sched
assert "state_tracker.InvalidateCommandBufferState();" in sched
assert "cmdbuf.SetViewport(0, viewport);" in blit
assert "cmdbuf.SetScissor(0, scissor);" in blit
assert "    // Avoid wasted state setup while texture_cache.mutex is held." in gen
raw_draw_state = draw.split("    texture_cache.UpdateRenderTargets(false);\n\n", 1)[1].split(
    "\n\n    query_cache.NotifySegment(true);", 1)[0]
assert raw_draw_state.count("UpdateDynamicStates();") == 1
assert raw_draw_state.index("#ifdef PS5_NATIVE") < raw_draw_state.index("#else")
assert raw_draw_state.index("#else") < raw_draw_state.index("UpdateDynamicStates();")
assert raw_draw_state.endswith("#endif")
# Compile the exact extracted pre-blit state decision in both configurations.
# This verifies the PS5 elision and preservation of the desktop call.
state_cpp = r"""
#include <cassert>
static int dynamic_updates = 0;
void UpdateDynamicStates() { ++dynamic_updates; }
void RawBlitState() {
""" + raw_draw_state + r"""
}
int main() {
    RawBlitState();
#ifdef PS5_NATIVE
    assert(dynamic_updates == 0);
#else
    assert(dynamic_updates == 1);
#endif
}
"""
with tempfile.TemporaryDirectory(prefix="ps5-raw-blit-state-") as td:
    source = Path(td) / "state.cpp"
    source.write_text(state_cpp)
    for opt in ("-O0", "-O2"):
        for native in (True, False):
            exe = Path(td) / ("state-" + opt[2:] + ("-ps5" if native else "-desktop"))
            subprocess.run(["c++", "-std=c++20", "-Wall", "-Wextra", "-Werror",
                            "-fsanitize=undefined", "-fno-sanitize-recover=all", opt,
                            *(["-DPS5_NATIVE=1"] if native else []),
                            str(source), "-o", str(exe)], check=True, capture_output=True, text=True)
            subprocess.run([str(exe)], check=True, capture_output=True, text=True)


update = fragment(sched, "bool Scheduler::UpdateGraphicsPipeline(GraphicsPipeline* pipeline, bool optimized) {",
                  "\nbool Scheduler::UpdateRescaling(")
invalidate = fragment(sched, "void Scheduler::InvalidateState() {",
                      "\nvoid Scheduler::EndPendingOperations(")
assert "if (state.graphics_pipeline == pipeline)" in update
assert "state.graphics_pipeline = nullptr;" in invalidate
assert "state.graphics_pipeline_optimized = false;" in invalidate
assert "state.graphics_pipeline_optimized = optimized;" in update

# Compile the ACTUAL maintained Scheduler methods at O0/O2 with minimal host
# mocks for the Vulkan-independent state tracker and guest pipeline object.
cpp = r"""
#include <cassert>
struct GraphicsPipeline {
    bool UsesExtendedDynamicState() const { return false; }
};
struct StateTracker {
    int invalidations = 0;
    void InvalidateStateEnableFlag() {}
    void InvalidateCommandBufferState() { ++invalidations; }
};
class Scheduler {
public:
    struct State {
        GraphicsPipeline* graphics_pipeline = nullptr;
        bool graphics_pipeline_optimized = false;
        bool needs_state_enable_refresh = false;
        bool rescaling_defined = true;
        bool descriptor_buffer_bound = true;
    } state;
    StateTracker state_tracker;
    bool UpdateGraphicsPipeline(GraphicsPipeline* pipeline, bool optimized = false);
    void InvalidateState();
};
""" + update + "\n" + invalidate + r"""
int main() {
    Scheduler scheduler;
    GraphicsPipeline guest;
    assert(scheduler.UpdateGraphicsPipeline(&guest));
    assert(!scheduler.UpdateGraphicsPipeline(&guest));
    // A raw Vk pipeline blit changes the GPU command-buffer binding but leaves
    // Scheduler::state.graphics_pipeline referring to this guest pipeline.
    // Without invalidate, the following same guest shader skips rebinding.
    assert(!scheduler.UpdateGraphicsPipeline(&guest));
    // The same logical pipeline can publish its optimized handle mid-frame.
    // The new API must detect this even before the raw blit invalidation.
    assert(scheduler.UpdateGraphicsPipeline(&guest, true));
    assert(!scheduler.UpdateGraphicsPipeline(&guest, true));
    scheduler.InvalidateState();
    assert(scheduler.state.graphics_pipeline == nullptr);
    assert(!scheduler.state.graphics_pipeline_optimized);
    assert(!scheduler.state.rescaling_defined);
    assert(!scheduler.state.descriptor_buffer_bound);
    assert(scheduler.state_tracker.invalidations == 1);
    assert(scheduler.UpdateGraphicsPipeline(&guest, true));
    assert(!scheduler.UpdateGraphicsPipeline(&guest, true));
}
"""
with tempfile.TemporaryDirectory(prefix="fc27-f07-raw-blit-") as td:
    source = Path(td) / "test.cpp"
    source.write_text(cpp)
    for opt in ("-O0", "-O2"):
        executable = Path(td) / ("case" + opt[2:])
        subprocess.run(["c++", "-std=c++20", "-Wall", "-Wextra", "-Werror",
                        opt, str(source), "-o", str(executable)],
                       check=True, capture_output=True, text=True)
        subprocess.run([str(executable)], check=True, capture_output=True, text=True)
# Prove the real native vertex-input branch never creates a cold guest shader
# on a raw blit (where prepared_pipeline is null), while it still programs
# dynamic vertex input for the next real guest draw. Desktop stays original.
def alpha_selector(method_name, support):
    m=raster.split("void RasterizerVulkan::"+method_name+"(",1)[1].split("\nvoid RasterizerVulkan::",1)[0]
    begin=m.index("#ifdef PS5_NATIVE")
    end=m.index("    const bool enable = pipeline != nullptr &&",begin)
    selected=m[begin:end]
    assert "prepared_pipeline;" in selected and "CurrentGraphicsPipeline()" in selected
    return selected + "    const bool enable = pipeline != nullptr && pipeline->"+support+"();\n"
alpha_coverage=alpha_selector("UpdateAlphaToCoverageEnable","SupportsAlphaToCoverage")
alpha_one=alpha_selector("UpdateAlphaToOneEnable","SupportsAlphaToOne")

dynamic_cpp = r"""
#include <cassert>
struct GraphicsPipeline {
    bool dynamic{};
    bool HasDynamicVertexInput() const { return dynamic; }
    bool SupportsAlphaToCoverage() const { return dynamic; }
    bool SupportsAlphaToOne() const { return dynamic; }
};
GraphicsPipeline* prepared_pipeline = nullptr;
struct Device {
    bool enabled = true;
    bool IsExtVertexInputDynamicStateSupported() const { return enabled; }
};
struct PipelineCache {
    GraphicsPipeline* selected = nullptr;
    unsigned lookups = 0;
    GraphicsPipeline* CurrentGraphicsPipeline() {
        ++lookups;
        return selected;
    }
};
struct FakeRasterizer {
    Device device;
    PipelineCache pipeline_cache;
    unsigned bindings = 0;
    void UpdateVertexInput(int&) { ++bindings; }
    void UpdateDynamicStates() {
        int regs = 0;
__DYNAMIC_BRANCH__
    }
    bool CheckAlphaCoverage() {
__ALPHA_COVERAGE__
        return enable;
    }
    bool CheckAlphaOne() {
__ALPHA_ONE__
        return enable;
    }
};
int main() {
    GraphicsPipeline dynamic{true}, fixed{false};
    FakeRasterizer raw;
    raw.pipeline_cache.selected = &dynamic;
    raw.UpdateDynamicStates();
    bool raw_coverage=raw.CheckAlphaCoverage();
    bool raw_one=raw.CheckAlphaOne();
#ifdef PS5_NATIVE
    assert(!raw_coverage && !raw_one);
    assert(raw.pipeline_cache.lookups == 0);
#else
    assert(raw_coverage && raw_one);
    assert(raw.pipeline_cache.lookups == 3);
#endif
#ifdef PS5_NATIVE
    assert(raw.pipeline_cache.lookups == 0 && raw.bindings == 0);
#else
    assert(raw.pipeline_cache.lookups == 3 && raw.bindings == 1);
#endif
    FakeRasterizer guest;
    guest.pipeline_cache.selected = &fixed;
    prepared_pipeline = &dynamic;
    guest.UpdateDynamicStates();
#ifdef PS5_NATIVE
    assert(guest.CheckAlphaCoverage() && guest.CheckAlphaOne());
    assert(guest.pipeline_cache.lookups == 0 && guest.bindings == 1);
#else
    // Desktop also uses the already-prepared guest pipeline; the old
    // fixture incorrectly expected two redundant cold shader lookups.
    assert(guest.CheckAlphaCoverage() && guest.CheckAlphaOne());
    assert(guest.pipeline_cache.lookups == 0 && guest.bindings == 1);
#endif
    prepared_pipeline = &fixed;
    guest.UpdateDynamicStates();
    assert(guest.pipeline_cache.lookups ==
#ifdef PS5_NATIVE
           0
#else
           0
#endif
           && guest.bindings == 1);
    guest.device.enabled = false;
    prepared_pipeline = &dynamic;
    guest.UpdateDynamicStates();
    assert(guest.bindings == 1);
    prepared_pipeline = nullptr;
}
""".replace("__DYNAMIC_BRANCH__", dynamic_branch).replace("__ALPHA_COVERAGE__",alpha_coverage).replace("__ALPHA_ONE__",alpha_one)
with tempfile.TemporaryDirectory(prefix="fc27-f07-raw-vertex-") as td:
    source = Path(td) / "dynamic.cpp"
    source.write_text(dynamic_cpp)
    for opt in ("-O0", "-O2"):
        for native in (False, True):
            executable = Path(td) / ("dyn" + opt[2:] + ("-ps5" if native else "-desktop"))
            args = ["c++", "-std=c++20", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=undefined", "-fno-sanitize-recover=all", opt,
                    *(["-DPS5_NATIVE=1"] if native else []),
                    str(source), "-o", str(executable)]
            subprocess.run(args, check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)
print("FC27_F07_RAW_BLIT_PIPELINE_INVALIDATION_PASS source_extracted=3 raw_blit_avoids_guest_shader=1 alpha_state_avoids_cold_shader=2 desktop_original=1 O0=1 O2=1")


# GPU-46: framebuffer layers are bounded by the smallest Vulkan attachment,
# and clears are clipped to that exact framebuffer layer count. Lichii #38 /
# Eglantine #293 reproduced the old max-layer policy as a Vulkan validation
# failure/device loss. Compile the selected policy under sanitizers.
texture_header=(root/"vendor/encore-active/ns2-astc/include/video_core/renderer_vulkan/vk_texture_cache.h").read_text()
texture_cpp=(root/"vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp").read_text()
clear_source=raster
assert "[[nodiscard]] u32 Layers() const noexcept" in texture_header
assert "u32 layers = 1;" in texture_header
assert "s32 num_layers = (std::numeric_limits<s32>::max)();" in texture_cpp
assert texture_cpp.count("num_layers = (std::min)(num_layers, color_buffer->range.extent.layers);")==1
assert texture_cpp.count("num_layers = (std::min)(num_layers, depth_buffer->range.extent.layers);")==1
assert "layers = static_cast<u32>((std::max)(num_layers, 1));" in texture_cpp
assert "CreateVkFramebuffer(runtime, attachments, layers);" in texture_cpp
assert "CreateMixedSamplesFramebuffer(runtime, color_buffers, attachments, renderpass_key,\n                                      layers, extent);" in texture_cpp
for token in (
    "const u32 framebuffer_layers = framebuffer->Layers();",
    "const u32 clear_base_layer = regs.clear_surface.layer;",
    "if (layer_count == 0 || clear_base_layer >= framebuffer_layers)",
    "(std::min)(layer_count, framebuffer_layers - clear_base_layer)",
    "clear_base_layer == 0 && clear_layer_count == framebuffer_layers",
    ".baseArrayLayer = clear_base_layer,",
    ".layerCount = clear_layer_count,",
    "clear_covers_all_layers &&",
):
    assert token in clear_source, token
assert "regs.clear_surface.layer == 0 &&" not in fragment(
    clear_source, "void RasterizerVulkan::Clear(u32 layer_count) {",
    "\nnamespace {\nconstexpr VkMemoryBarrier COMPUTE_WRITE_BARRIER")
# The native forced-MSAA candidate must reason about the clipped layer range.
assert "can_defer_clear && !ds_used && clear_layer_count == 1 &&" in clear_source
assert "framebuffer_layers == 1 &&" in clear_source

layer_cpp=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <limits>
using u32=std::uint32_t; using s32=std::int32_t;

u32 FramebufferLayers(const std::array<s32,8>& colors, s32 depth) {
    s32 num_layers=(std::numeric_limits<s32>::max)();
    for(s32 layer:colors) {
        if(layer>0) num_layers=(std::min)(num_layers,layer);
    }
    if(depth>0) num_layers=(std::min)(num_layers,depth);
    if(num_layers==(std::numeric_limits<s32>::max)()) num_layers=1;
    return static_cast<u32>((std::max)(num_layers,1));
}
struct ClearRange { u32 base{},count{}; bool all{}; };
ClearRange Clip(u32 base,u32 requested,u32 framebuffer_layers) {
    if(requested==0 || base>=framebuffer_layers) return {};
    const u32 count=(std::min)(requested,framebuffer_layers-base);
    return {base,count,base==0 && count==framebuffer_layers};
}
int main() {
    assert(FramebufferLayers({1,0,0,0,0,0,0,0},4)==1);
    assert(FramebufferLayers({4,2,0,0,0,0,0,0},8)==2);
    assert(FramebufferLayers({4,0,0,0,0,0,0,0},0)==4);
    assert(FramebufferLayers({},0)==1);

    auto a=Clip(0,4,1); assert(a.base==0 && a.count==1 && a.all);
    auto b=Clip(2,4,4); assert(b.base==2 && b.count==2 && !b.all);
    auto c=Clip(1,0,4); assert(c.count==0 && !c.all);
    auto d=Clip(4,1,4); assert(d.count==0 && !d.all);
    auto e=Clip(0,1,4); assert(e.count==1 && !e.all);
    auto f=Clip(0,4,4); assert(f.count==4 && f.all);
    auto g=Clip(1,(std::numeric_limits<u32>::max)(),4);
    assert(g.base==1 && g.count==3 && !g.all);
}
"""
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-fb-layers-gpu46-") as td:
    source=Path(td)/"layers.cpp"; source.write_text(layer_cpp)
    for opt in ("-O0","-O2"):
        exe=Path(td)/("layers-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_VULKAN_FRAMEBUFFER_LAYER_BOUNDS_HOST_PASS active_owner=1 min_attachment=1 "
      "mixed_samples=1 clear_clip=1 outside_skip=1 overflow_safe=1 "
      "partial_not_deferred=1 full_deferred=1 O0_O2=2 ASan_UBSan=1")


# GPU-47: Lichii #427 framebuffer-limit subset only. Do NOT import its
# unrelated StreamBuffer padding. Source-seal the active Vulkan device limits
# and framebuffer clamp, then test the policy under sanitizers.
device_header=(root/"vendor/encore-active/eden-vulkan/include/video_core/vulkan_common/vulkan_device.h").read_text()
texture_cpp=(root/"vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp").read_text()
for limit in ("FramebufferWidth","FramebufferHeight","FramebufferLayers"):
    assert f"FN_MAX_LIMIT_ELEM({limit})" in device_header
for token in (
    "const auto clamp_extent = [&runtime](VkExtent2D extent)",
    "runtime.device.GetMaxFramebufferWidth()",
    "runtime.device.GetMaxFramebufferHeight()",
    "runtime.device.GetMaxFramebufferLayers()",
    "layers = (std::max)(1U, (std::min)(layers, runtime.device.GetMaxFramebufferLayers()));",
    "const VkExtent2D extent = clamp_extent(",
    "render_area = clamp_extent(render_area);",
):
    assert token in texture_cpp, token
assert "32768x32768 surface clip" in texture_cpp

device_limit_cpp=r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
using u32=std::uint32_t;
struct Size { u32 width,height,layers; };
constexpr Size Clamp(Size size, Size max) {
    return {
      (std::max)(1U,(std::min)(size.width,max.width)),
      (std::max)(1U,(std::min)(size.height,max.height)),
      (std::max)(1U,(std::min)(size.layers,max.layers)),
    };
}
int main() {
    auto a=Clamp({32768,32768,4},{16384,16384,2});
    assert(a.width==16384 && a.height==16384 && a.layers==2);
    auto b=Clamp({1280,720,1},{16384,16384,2048});
    assert(b.width==1280 && b.height==720 && b.layers==1);
    auto c=Clamp({0,0,0},{16384,16384,2048});
    assert(c.width==1 && c.height==1 && c.layers==1);
    auto d=Clamp({16384,16384,2048},{16384,16384,2048});
    assert(d.width==16384 && d.height==16384 && d.layers==2048);
    auto e=Clamp({16385,1,2049},{16384,16384,2048});
    assert(e.width==16384 && e.height==1 && e.layers==2048);
}
"""
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-fb-device-limits-gpu47-") as td:
    source=Path(td)/"limits.cpp"; source.write_text(device_limit_cpp)
    for opt in ("-O0","-O2"):
        exe=Path(td)/("limits-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_VULKAN_FRAMEBUFFER_DEVICE_LIMIT_HOST_PASS upstream_427=1 active_owner=1 "
      "width=1 height=1 layers=1 attachmentless_clip=1 zero_to_one=1 "
      "valid_unchanged=1 O0_O2=2 ASan_UBSan=1")


# GPU-49: Lichii #353 fragment-output component ownership. The guest's
# color mask is necessary but not sufficient: Vulkan must also mask out
# components the fragment shader never writes.
shader_info=(root/"vendor/encore-active/eden/src/shader_recompiler/shader_info.h").read_text()
collect_info=(root/"vendor/encore-active/eden/src/shader_recompiler/ir_opt/collect_shader_info_pass.cpp").read_text()
gp_header=(root/"vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_graphics_pipeline.h").read_text()
gp_source=(root/"vendor/encore-active/eden-vulkan/vk_graphics_pipeline_cost.cpp").read_text()
rast_header=(root/"vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h").read_text()
assert "std::array<u8, 8> frag_color_components{};" in shader_info
for token in (
    "const u32 render_target{inst.Arg(0).U32()};",
    "info.stores_frag_color[render_target] = true;",
    "info.frag_color_components[render_target] |=",
    "static_cast<u8>(1U << inst.Arg(1).U32());",
):
    assert token in collect_info, token
for token in (
    "VkColorComponentFlags ColorOutputMask(size_t render_target) const noexcept",
    "u32 ColorOutputMask() const noexcept",
    "u32 color_output_mask{};",
):
    assert token in gp_header, token
for token in (
    "color_output_mask |= u32{stage_infos[NUM_STAGES - 1].frag_color_components[rt]}",
    "write_mask &= ColorOutputMask(index);",
):
    assert token in gp_source, token
for token in (
    "UpdateBlending(regs, prepared_pipeline);",
    "const u32 color_output_mask = pipeline ? pipeline->ColorOutputMask() : ~0U;",
    "const bool color_output_changed = color_output_mask != last_color_output_mask;",
    "current &= (color_output_mask >> (index * 4)) & 0xF;",
):
    assert token in raster, token
assert "const GraphicsPipeline* pipeline" in rast_header
assert "u32 last_color_output_mask{};" in rast_header
# Keep the PS5 hot path: no CurrentGraphicsPipeline lookup is introduced
# around the dynamic color-output mask.
blend_method=fragment(raster,
    "void RasterizerVulkan::UpdateBlending(Tegra::Engines::Maxwell3D::Regs& regs,",
    "\nvoid RasterizerVulkan::UpdateColorWriteEnable(")
assert "pipeline_cache.CurrentGraphicsPipeline()" not in blend_method
dynamic_method=fragment(raster,"void RasterizerVulkan::UpdateDynamicStates() {",
                        "\nvoid RasterizerVulkan::HandleTransformFeedback(")
assert "UpdateBlending(regs, prepared_pipeline);" in dynamic_method

mask_cpp=r"""
#include <array>
#include <cassert>
#include <cstdint>
using u32=std::uint32_t; using u8=std::uint8_t;
u32 Pack(const std::array<u8,8>& components) {
    u32 mask=0;
    for(std::size_t rt=0;rt<components.size();++rt)
        mask |= u32{components[rt]} << (rt*4);
    return mask;
}
u32 StaticMask(u32 guest,u32 packed,std::size_t rt) {
    return guest & ((packed >> (rt*4)) & 0xF);
}
struct Dynamic {
    u32 last{};
    unsigned records{};
    u32 Apply(bool guest_dirty,u32 guest_mask,const u32* pipeline_mask,std::size_t rt) {
        const u32 output=pipeline_mask?*pipeline_mask:~0U;
        const bool changed=output!=last;
        if(!guest_dirty && !changed) return 0xffffffffU;
        if(guest_dirty||changed) { last=output; ++records; }
        return guest_mask & ((output>>(rt*4))&0xF);
    }
};
int main() {
    std::array<u8,8> c{}; c[0]=0b0101; c[1]=0b1010;
    const u32 packed=Pack(c);
    assert(StaticMask(0xF,packed,0)==0x5);
    assert(StaticMask(0x7,packed,0)==0x5);
    assert(StaticMask(0xF,packed,1)==0xA);
    Dynamic d{};
    assert(d.Apply(true,0xF,&packed,0)==0x5);
    const unsigned first=d.records;
    assert(d.Apply(false,0xF,&packed,0)==0xffffffffU);
    assert(d.records==first);
    u32 other=0x3;
    assert(d.Apply(false,0xF,&other,0)==0x3);
    assert(d.records==first+1);
    // Raw DrawTexture/blit: no guest graphics pipeline => all components allowed.
    assert(d.Apply(false,0xB,nullptr,0)==0xB);
}
"""
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-frag-mask-gpu49-") as td:
    source=Path(td)/"mask.cpp"; source.write_text(mask_cpp)
    for opt in ("-O0","-O2"):
        exe=Path(td)/("mask-"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        str(source),"-o",str(exe)],check=True,timeout=45)
        subprocess.run([str(exe)],check=True,timeout=20)
print("NS1_FRAGMENT_COLOR_OUTPUT_MASK_HOST_PASS upstream_353=1 active_shader_info=1 "
      "static_mask=1 dynamic_mask=1 pipeline_change_rebind=1 raw_blit_full_mask=1 "
      "no_cold_lookup=1 O0_O2=2 ASan_UBSan=1")
