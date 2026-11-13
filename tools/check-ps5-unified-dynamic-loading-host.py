#!/usr/bin/env python3
"""Review the single animated native EGL->Vulkan jacket handoff source contract.

The real GLSL is compiled and validated separately by the isolated HUD SPIR-V
CI. This source gate does NOT claim a seamless physical console swapchain.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
renderer = (root / "headless/vulkan_renderer_r08.cpp").read_text()
shader = (root / "headless/vulkan_hud.frag").read_text()
window = (root / "headless/vulkan_window_adapt_r08.cpp").read_text()
graphics = (root / "headless/graphics.cpp").read_text()
loading = renderer.split("void RendererVulkan::PresentLoading()", 1)[1].split(
    "void RendererVulkan::Report()", 1
)[0]
native = loading.split("#ifdef PS5_NATIVE", 2)[2].split("#endif", 1)[0]
assert "const bool jacket_ready = loading_jacket_buffer &&" in loading
assert "present_manager.SwapchainImageViewFormat(), !jacket_ready);" in loading
assert "Eden::LaunchHandoff::Peek()" in loading
assert "loading_jacket_buffer = std::move(buffer);" in loading
assert "loading_jacket_attempted = true;" in loading
assert "scheduler.Record([target, upload, copy]" in native
assert "Eden::HudSnapshot live_loading = Eden::GetVulkanHud();" in native
assert "live_loading.width |= 0x80000000u;" in native
assert "live_loading.loading |= 0x80000000u;" not in loading
assert "blit_swapchain.DrawHudOverlay(device, frame, live_loading);" in native
assert native.index("scheduler.Record([target, upload, copy]") < native.index(
    "blit_swapchain.DrawHudOverlay(device, frame, live_loading);"
)
assert loading.index("blit_swapchain.DrawHudOverlay(device, frame, live_loading);") < (
    loading.index("scheduler.Flush(*frame->render_ready);")
)
assert "if (live_loading.loading != 0u && live_loading.width != 0u)" in native
assert "const auto hud = draw_hud ? Eden::GetVulkanHud()" in window
assert "CreateWrappedCoverageBlendingPipeline" in window
overlay = window.split("void WindowAdaptPass::DrawHudOverlay", 1)[1].split(
    "VkDescriptorSetLayout WindowAdaptPass::GetDescriptorSetLayout", 1
)[0]
assert "BeginRenderPass(cmdbuf, rp, fb, size);" in overlay
assert "cmdbuf.ClearAttachments" not in overlay
assert "const bool jacket_band = hud.loading != 0u &&" in overlay
assert "(hud.width & 0x80000000u) != 0u;" in overlay
assert "const std::uint32_t band_height = std::max(1u, size.height / 5u);" in overlay
assert "VkRect2D{{0, static_cast<int32_t>(size.height - band_height)}," in overlay
assert "const VkViewport viewport = jacket_band" in overlay
assert "const VkRect2D scissor = hud.loading" in overlay
assert "cmdbuf.SetScissor(0, scissor);" in overlay
assert "cmdbuf.Draw(4, 1, 0, 0);" in overlay
assert "void RendererVulkan::PresentLoading()" in renderer
assert "vulkan_hud = MakeLoadingSnapshot" in graphics
# The production SPIR-V is pinned to this ORIGINAL source. The single-loader
# animation must not require a source-only shader variant that differs from
# the vendor's embedded, already validated binary.
import hashlib
assert hashlib.sha256(shader.encode()).hexdigest() == (
    "3f5287326b7554164449f5f849f46aae3d2f69ff3a0b4c5c822055bd1877c6d6"
)
assert "float(text.loading - 1u) * 0.001" in shader
assert "color = vec4(loading_scene(" in shader
assert "bool quick = (text.loading & 0xfff00000u) == 0xff100000u;" in shader
print("PS5_SINGLE_ANIMATED_VULKAN_JACKET_SOURCE_PASS native_only=1 shader_pinned=1 console_pending=1")
