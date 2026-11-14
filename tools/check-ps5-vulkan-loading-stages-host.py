#!/usr/bin/env python3
"""Source/host contract for one PS5 GL -> Vulkan loading state.

This does not prove physical scanout continuity. It proves the selected source
keeps the last OpenGL loading frame through core load, relinquishes VideoOut
at the Vulkan surface boundary, and uses the same loading_scene.glsl on both
renderers without the retired jacket screenshot/bottom-band path.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
graphics = (root / "headless/graphics.cpp").read_text()
frontend = (root / "headless/prosperoeden/frontend.cpp").read_text()
display_h = (root / "headless/prosperoeden/pe/platform/display_egl.hpp").read_text()
display = (root / "headless/prosperoeden/pe/platform/display_egl.cpp").read_text()
renderer = (root / "headless/vulkan_renderer_r08.cpp").read_text()
renderer_h = (root / "headless/renderer_vulkan_r08.h").read_text()
window = (root / "headless/vulkan_window_adapt_r08.cpp").read_text()
shader = (root / "headless/vulkan_hud.frag").read_text()
vulkan_cmake = (root / "headless/vulkan.cmake").read_text()
vendor_egl = (root / "vendor/sources/opengl-source/src/egl/ps5_egl.c").read_text()
vendor_present = (
    root / "vendor/sources/opengl-source/src/platform/ps5_agc_native_runtime.c"
).read_text()

assert graphics.count("unsigned vulkan_loading_diagnostic_stage{};") == 1
assert graphics.count("vulkan_loading_diagnostic_stage = 0;") == 1
loading_tick = graphics.split("bool LoadingTick(", 1)[1].split(
    "GraphicsWindow::GraphicsWindow(", 1
)[0]
for milestone in ("10s", "30s"):
    assert loading_tick.count(f"EDEN_VULKAN_LOADING_WAIT stage={milestone}") == 1
assert "guest_frame_handoff=0" in loading_tick

terminate = vendor_egl.split("eglTerminate(EGLDisplay display)", 1)[1].split(
    "EGLAPI EGLint EGLAPIENTRY", 1
)[0]
shutdown = vendor_present.split("int ps5_agc_gate2_shutdown_present(void)", 1)[1].split(
    "static int runtime_video_acquire(", 1
)[0]
assert "ps5_agc_gate2_shutdown_present()" in terminate
assert "close(runtime_video_handle)" in shutdown
assert "runtime_video_registered = 0;" in shutdown

assert '#include "loading_scene_glsl.h"' in frontend
assert "bool PresentUnifiedLoading(pe::ps5::Display& display)" in frontend
unified = frontend.split("bool PresentUnifiedLoading(", 1)[1].split("\n}", 1)[0]
assert "kLoadingSceneGlsl" in unified
assert "loading_scene(gl_FragCoord.xy,size,seconds)" in unified
assert "display.swap()" in unified
assert "1001.0f : 1.0f" in unified
assert "LaunchHandoff::Publish(" not in frontend
assert "handoff_captured" not in frontend
assert "handoff_attempts" not in frontend
assert frontend.index("PresentUnifiedLoading(display)") < frontend.index(
    "display.defer_scanout_close()"
)
assert "Display::close_deferred_scanout()" in frontend

assert "bool Display::defer_scanout_close()" in display
defer = display.split("bool Display::defer_scanout_close()", 1)[1].split(
    "bool Display::close_deferred_scanout()", 1
)[0]
assert "eglDestroyContext" in defer and "eglDestroySurface" in defer
assert "eglTerminate(display_)" not in defer
close_deferred = display.split("bool Display::close_deferred_scanout()", 1)[1].split(
    "bool Display::has_deferred_scanout()", 1
)[0]
assert "eglTerminate(display)" in close_deferred
for api in ("defer_scanout_close", "close_deferred_scanout", "has_deferred_scanout"):
    assert api in display_h

constructor = graphics.split("GraphicsWindow::GraphicsWindow(", 1)[1]
ogl_release = constructor.split("if (!vulkan) {", 1)[1].split("}", 1)[0]
assert "pe::ps5::Display::close_deferred_scanout()" in ogl_release
assert "LaunchHandoff::Clear();" in ogl_release

draw_loading = graphics.split("bool DrawLoading(double seconds)", 1)[1].split(
    "void DrawHud(", 1
)[0]
assert "kLoadingSceneGlsl" in draw_loading
assert "loading_scene(gl_FragCoord.xy,size,seconds)" in draw_loading
assert "now - loading_start + 1.0 + LoadingCalm()" in graphics
assert "MakeLoadingSnapshot(now - vulkan_loading_start + 1.0 + LoadingCalm())" in graphics
assert "MakeLoadingSnapshot(1.0 + LoadingCalm())" in graphics

assert "vk::SurfaceKHR CreateHandoffSurface(" in renderer
handover = renderer.split("vk::SurfaceKHR CreateHandoffSurface(", 1)[1].split(
    "} // Anonymous namespace", 1
)[0]
assert handover.index("close_deferred_scanout()") < handover.index(
    "CreateSurface(instance, window_info)"
)
assert "EDEN_GL_VK_SCANOUT_HANDOFF release=1 boundary=create_surface" in handover
assert "surface(CreateHandoffSurface(instance, render_window.GetWindowInfo()))" in renderer

present = renderer.split("void RendererVulkan::PresentLoading()", 1)[1].split(
    "void RendererVulkan::Report()", 1
)[0]
for retired in (
    "LaunchHandoff::Peek", "loading_jacket", "CopyBufferToImage",
    "EDEN_LOADER_JACKET_HANDOFF_VULKAN", "0x80000000u",
):
    assert retired not in present, retired
assert "blit_swapchain.DrawHudOverlay(device, frame, live_loading);" in present
assert present.index("DrawHudOverlay") < present.index("scheduler.Flush")
assert "loading_jacket_" not in renderer_h
assert "vulkan_renderer_r08.cpp" in vulkan_cmake

overlay = window.split("void WindowAdaptPass::DrawHudOverlay", 1)[1].split(
    "VkDescriptorSetLayout WindowAdaptPass::GetDescriptorSetLayout", 1
)[0]
assert "hud.loading\n                ? VkRect2D{{0, 0}, size}" in overlay
for retired in ("jacket_band", "band_height", "0x80000000u"):
    assert retired not in overlay
assert "cmdbuf.SetViewport(0, viewport);" in overlay
assert "cmdbuf.SetScissor(0, scissor);" in overlay

assert '#include "loading_scene.glsl"' in shader
assert "color = vec4(loading_scene(" in shader

print("ENCORE_GL_VK_SINGLE_LOADING_SOURCE_PASS deferred_scanout=1 shared_shader=1 jacket_upload=0 bottom_band=0 console_pending=1")
print("ENCORE_VULKAN_LOADING_DIAGNOSTIC_PASS first_guest_frame_not_claimed=1 max_reports=2")
