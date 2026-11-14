#!/usr/bin/env python3
"""Focused contract for the unified native loading compositor.

The shader is validated separately. This source gate rejects the old static
jacket + lower-band loader and requires one full-frame scene on GL and Vulkan.
No physical PS5 presentation continuity is claimed.
"""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[1]
renderer = (root / "headless/vulkan_renderer_r08.cpp").read_text()
header = (root / "headless/renderer_vulkan_r08.h").read_text()
shader = (root / "headless/vulkan_hud.frag").read_text()
window = (root / "headless/vulkan_window_adapt_r08.cpp").read_text()
graphics = (root / "headless/graphics.cpp").read_text()
frontend = (root / "headless/prosperoeden/frontend.cpp").read_text()
display = (root / "headless/prosperoeden/pe/platform/display_egl.cpp").read_text()
vulkan_cmake = (root / "headless/vulkan.cmake").read_text()
native_cmake = (root / "headless/CMakeLists.txt").read_text()

assert 'target_compile_definitions(video_core PRIVATE PS5_NATIVE=1)' in vulkan_cmake
assert "vulkan_renderer_r08.cpp" in vulkan_cmake
assert 'set(EDEN_NS2_SPARSE_BACKING OFF)' in native_cmake
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in native_cmake

assert "kLoadingSceneGlsl" in frontend
assert "kLoadingSceneGlsl" in graphics
assert '#include "loading_scene.glsl"' in shader
assert "loading_scene(gl_FragCoord.xy,size,seconds)" in frontend
assert "loading_scene(gl_FragCoord.xy,size,seconds)" in graphics
assert "color = vec4(loading_scene(" in shader

assert "1001.0f : 1.0f" in frontend
assert "now - loading_start + 1.0 + LoadingCalm()" in graphics
assert "MakeLoadingSnapshot(1.0 + LoadingCalm())" in graphics

loading = renderer.split("void RendererVulkan::PresentLoading()", 1)[1].split(
    "void RendererVulkan::Report()", 1
)[0]
assert "present_manager.SwapchainImageViewFormat(), true);" in loading
assert "Eden::GetVulkanHud()" in loading
assert "blit_swapchain.DrawHudOverlay(device, frame, live_loading);" in loading
assert loading.index("DrawHudOverlay") < loading.index("scheduler.Flush")
for retired in (
    "loading_jacket", "LaunchHandoff", "CopyBufferToImage",
    "VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL", "0x80000000u",
):
    assert retired not in loading
assert "loading_jacket_" not in header

overlay = window.split("void WindowAdaptPass::DrawHudOverlay", 1)[1].split(
    "VkDescriptorSetLayout WindowAdaptPass::GetDescriptorSetLayout", 1
)[0]
assert "hud.loading\n                ? VkRect2D{{0, 0}, size}" in overlay
assert "const VkViewport viewport{" in overlay
for retired in ("jacket_band", "band_height", "0x80000000u"):
    assert retired not in overlay
assert "cmdbuf.ClearAttachments" not in overlay

assert frontend.index("PresentUnifiedLoading(display)") < frontend.index(
    "display.defer_scanout_close()"
)
assert "else {\n        display.close();\n    }" in frontend
defer = display.split("bool Display::defer_scanout_close()", 1)[1].split(
    "bool Display::close_deferred_scanout()", 1
)[0]
assert "eglTerminate(" not in defer
handover = renderer.split("vk::SurfaceKHR CreateHandoffSurface(", 1)[1].split(
    "} // Anonymous namespace", 1
)[0]
assert handover.index("close_deferred_scanout()") < handover.index("CreateSurface(")

assert hashlib.sha256(shader.encode()).hexdigest() == (
    "3f5287326b7554164449f5f849f46aae3d2f69ff3a0b4c5c822055bd1877c6d6"
)

print("PS5_SINGLE_GL_VULKAN_LOADING_SOURCE_PASS shared_scene=1 fullscreen=1 deferred_videoout=1 console_pending=1")
