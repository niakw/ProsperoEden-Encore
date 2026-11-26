#!/usr/bin/env python3
"""Source/host contract for one continuous PS5 GL -> Vulkan loading state.

This does not prove physical scanout continuity. The same Encore artwork
and three-dot indicator are reused during core load, then the retained
GL owner is stopped/joined before Vulkan takes over. No purple band.
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
gl_art = (root / "headless/loading_artwork_gl.hpp").read_text()
wsi = (root / "vendor/encore-active/ps5-mesa/src/vulkan/wsi/wsi_common_videoout.c").read_text()
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

assert '#include "loading_artwork_gl.hpp"' in frontend
assert '#include "loading_artwork_gl.hpp"' in display
assert "bool PresentUnifiedLoading(pe::ps5::Display& display, bool reduce_motion)" in frontend
unified = frontend.split("bool PresentUnifiedLoading(", 1)[1].split("\n}", 1)[0]
assert "Eden::LoadingArtwork::GlPresenter presenter" in unified
assert "presenter.Draw(display.width(), display.height()" in unified
assert "loading_artwork_indicator(gl_FragCoord.xy,size,seconds)" in gl_art
assert "display.swap()" in unified
assert "Eden::LaunchHandoff::LoadingSeconds(reduce_motion ? 1000.0 : 0.0)" in unified
assert "Eden::LaunchHandoff::BeginLoading();" in frontend
assert "Eden::LoadingArtwork::Capture(" in frontend
assert "LaunchHandoff::Publish(std::move(frame), alternate)" in gl_art
assert "LaunchHandoff::PeekAlternate()" in gl_art
assert "Pose::back" in frontend and "Pose::front" in frontend
assert "Pose::background" in frontend
assert "PublishCase(std::move(scene))" in frontend
assert "handoff_captured" not in frontend
assert "handoff_attempts" not in frontend
assert frontend.index("PresentUnifiedLoading(display, reduce_motion)") < frontend.index(
    "display.defer_scanout_close(reduce_motion)"
)
assert "Display::close_deferred_scanout()" in frontend

assert "bool Display::defer_scanout_close(bool reduce_motion)" in display
assert "bool defer_scanout_close(bool reduce_motion);" in display_h
defer = display.split("bool Display::defer_scanout_close(bool reduce_motion)", 1)[1].split(
    "bool Display::close_deferred_scanout()", 1
)[0]
assert "std::jthread{deferred_loading_loop" in defer
assert "eglDestroyContext(" not in defer
assert "eglDestroySurface(" not in defer
assert "eglTerminate(" not in defer

presenter = display.split("void deferred_loading_loop(", 1)[1].split("\n}", 1)[0]
assert "Eden::LoadingArtwork::GlPresenter presenter" in presenter
assert "presenter.Draw(width, height, seconds)" in presenter
assert "while (!stop.stop_requested())" in presenter
assert "Eden::LaunchHandoff::LoadingSeconds(reduce_motion ? 1000.0 : 0.0)" in presenter
assert "eglSwapBuffers(display, surface)" in presenter

close_deferred = display.split("bool Display::close_deferred_scanout()", 1)[1].split(
    "bool Display::has_deferred_scanout()", 1
)[0]
assert close_deferred.index("presenter.request_stop();") < close_deferred.index("presenter.join();")
assert "Eden::LaunchHandoff::ClearAlternate();" not in close_deferred
assert close_deferred.index("presenter.join();") < close_deferred.index(
    "eglDestroyContext(display, context)"
)
assert close_deferred.index("eglDestroyContext(display, context)") < close_deferred.index(
    "eglDestroySurface(display, surface)"
)
assert close_deferred.index("eglDestroySurface(display, surface)") < close_deferred.index(
    "eglTerminate(display)"
)
for api in ("defer_scanout_close", "close_deferred_scanout", "has_deferred_scanout"):
    assert api in display_h

constructor = graphics.split("GraphicsWindow::GraphicsWindow(", 1)[1]
ogl_release = constructor.split("if (!vulkan) {", 1)[1].split("}", 1)[0]
assert "pe::ps5::Display::close_deferred_scanout()" in ogl_release
assert "LaunchHandoff::Clear();" not in ogl_release
assert "LaunchHandoff::Clear();" in graphics

draw_loading = graphics.split("bool DrawLoading(double seconds)", 1)[1].split(
    "void DrawHud(", 1
)[0]
assert "loading_artwork.Draw(width, height, seconds)" in draw_loading
assert "loading_scene(gl_FragCoord.xy,size,seconds)" not in draw_loading
assert "LaunchHandoff::LoadingSeconds(LoadingCalm())" in graphics
assert "LaunchHandoff::EndLoading();" in graphics

assert "vk::SurfaceKHR CreateHandoffSurface(" in renderer
handover = renderer.split("vk::SurfaceKHR CreateHandoffSurface(", 1)[1].split(
    "} // Anonymous namespace", 1
)[0]
assert "requested_hz.load(std::memory_order_relaxed) >= 120" in handover
assert "PrepareHandoffSwapchain(vk::SurfaceKHR& surface)" in handover
assert "boundary=create_surface reason=120hz" in handover
assert "boundary=create_swapchain reason=60hz" in handover
assert "surface(CreateHandoffSurface(instance, render_window.GetWindowInfo()))" in renderer
assert renderer.index("device(CreateDevice(instance, dld, *surface))") < renderer.index(
    "PrepareHandoffSwapchain(surface)"
)
modes = wsi.split("static uint32_t\nvideoout_modes(", 1)[1].split(
    "VKAPI_ATTR VkResult VKAPI_CALL\nwsi_GetDisplayModePropertiesKHR", 1)[0]
assert "if (videoout_title_declares_high_frame_rate()) {" in modes
assert modes.index("videoout_settle_modes();") < modes.index("modes[count++] = &videoout_high_mode;")
assert "modes[count++] = &videoout_mode;" in modes

present = renderer.split("void RendererVulkan::PresentLoading()", 1)[1].split(
    "void RendererVulkan::Report()", 1
)[0]
assert "LaunchHandoff::Peek()" in present
assert "Eden::LoadingArtwork::Repack" in present
assert "blit_swapchain.DrawLoadingArtwork(device, frame, format)" in present
assert "Eden::LaunchHandoff::PeekAlternate()" in window
assert present.index("CopyBufferToImage") < present.index("DrawHudOverlay")
assert "live_loading.glyphs[0] = has_artwork ? 1u : 0u" in present
for retired in ("loading_jacket", "EDEN_LOADER_JACKET_HANDOFF_VULKAN", "0x80000000u"):
    assert retired not in present, retired
assert "blit_swapchain.DrawHudOverlay(device, frame, live_loading);" in present
assert present.index("DrawHudOverlay") < present.index("scheduler.Flush")
assert "loading_jacket_" not in renderer_h
assert "loading_artwork_buffer" in renderer_h
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
assert "loading_artwork_indicator(" in shader
assert "color = vec4(loading_scene(" not in shader
assert "text.glyphs[0] == 1u ? dots" in shader

print("ENCORE_GL_VK_CONTINUOUS_LOADING_SOURCE_PASS presenter=1 shared_shader=1 shared_epoch=1 jacket_upload=1 bottom_band=0 purple_loader=0 console_pending=1")
print("ENCORE_VULKAN_LOADING_DIAGNOSTIC_PASS first_guest_frame_not_claimed=1 max_reports=2")
