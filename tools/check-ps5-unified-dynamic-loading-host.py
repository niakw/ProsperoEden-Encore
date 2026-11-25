#!/usr/bin/env python3
"""Focused contract for the continuous native loading compositor.

The actual Encore jacket is projected per frame from shared geometry, and
three animated dots must survive GL -> retained EGL -> Vulkan/OpenGL.
Reject the old purple full-screen/band paths, and require the existing
stop/join ownership boundary. No physical PS5 continuity is claimed.
"""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
renderer = (root / "headless/vulkan_renderer_r08.cpp").read_text()
header = (root / "headless/renderer_vulkan_r08.h").read_text()
shader = (root / "headless/vulkan_hud.frag").read_text()
window = (root / "headless/vulkan_window_adapt_r08.cpp").read_text()
graphics = (root / "headless/graphics.cpp").read_text()
frontend = (root / "headless/prosperoeden/frontend.cpp").read_text()
display_h = (root / "headless/prosperoeden/pe/platform/display_egl.hpp").read_text()
display = (root / "headless/prosperoeden/pe/platform/display_egl.cpp").read_text()
handoff = (root / "headless/launch_handoff.hpp").read_text()
vulkan_cmake = (root / "headless/vulkan.cmake").read_text()
native_cmake = (root / "headless/CMakeLists.txt").read_text()
gl_art = (root / "headless/loading_artwork_gl.hpp").read_text()
scene = (root / "headless/loading_scene.glsl").read_text()
launcher = (root / "headless/prosperoeden/pe/ui/launcher.cpp").read_text()
launcher_h = (root / "headless/prosperoeden/pe/ui/launcher.hpp").read_text()
transfer = (root / "headless/loading_artwork_transfer.hpp").read_text()
wsi = (root / "vendor/encore-active/ps5-mesa/src/vulkan/wsi/wsi_common_videoout.c").read_text()

assert 'target_compile_definitions(video_core PRIVATE PS5_NATIVE=1)' in vulkan_cmake
assert "vulkan_renderer_r08.cpp" in vulkan_cmake
assert 'set(EDEN_NS2_SPARSE_BACKING OFF)' in native_cmake
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in native_cmake

# All presentation phases share actual composed artwork and one indicator.
for source in (frontend, graphics, display):
    assert '#include "loading_artwork_gl.hpp"' in source
    assert "loading_scene(gl_FragCoord.xy,size,seconds)" not in source
assert "kLoadingSceneGlsl" in gl_art
assert "loading_artwork_indicator(gl_FragCoord.xy,size,seconds)" in gl_art
assert "loading_scene(gl_FragCoord.xy,size,seconds)" not in gl_art
assert "vec4 loading_artwork_indicator" in scene
assert '#include "loading_scene.glsl"' in shader
assert "loading_artwork_indicator(" in shader
assert "color = vec4(loading_scene(" not in shader
assert "text.glyphs[0] == 1u ? dots" in shader

# The native launcher paints the original front/title, without the separate
# timed rear-hold cinematic; the preview retains that code for design QA.
assert "bool native_artwork_loading = false" in launcher_h
assert "pe::ui::Launcher launcher(services, textures, fonts, first_start, true)" in frontend
assert "native_launch_art_ready_ || std::chrono::steady_clock::now() >= native_launch_deadline_" in launcher
assert "std::chrono::milliseconds(750)" in launcher
assert "if (!native_artwork_loading_ || done_) prepare_case_page(true);" in launcher
assert "prepare_case_page(true);" in launcher
assert "!(native_artwork_loading_ && done_)" in launcher
assert "const float appear = native_artwork_loading_ ? 1.0f" in launcher

# Composition is read only from the explicitly owned offscreen target.
assert "Eden::LoadingArtwork::Capture(" in frontend
assert "int width=1920,int height=1080" in gl_art
assert gl_art.index("glFramebufferTexture2D") < gl_art.index("glReadPixels")
assert "glBindFramebuffer(GL_READ_FRAMEBUFFER, fbo)" in gl_art
assert "glBindBuffer(GL_PIXEL_PACK_BUFFER, 0)" in gl_art
assert "glPixelStorei(GL_PACK_ROW_LENGTH, 0)" in gl_art
assert "std::swap_ranges" in gl_art
assert "LaunchHandoff::Publish(std::move(frame), alternate)" in gl_art
assert "LaunchHandoff::PeekAlternate()" in gl_art
assert "alternate_texture_" in gl_art
assert "has_alternate" not in gl_art
assert "abs(cos(turn" not in gl_art + shader
assert "Pose::front" in frontend and "Pose::back" in frontend
assert "Pose::background" in frontend and "paper.image(run.texture" in frontend
assert "PublishCase(std::move(scene))" in frontend
assert "LoadingCase::MakeBatch" in gl_art and "LoadingCase::MakeBatch" in window
assert "EDEN_LOADING_CASE_VERT_SPV" in window and "EDEN_LOADING_CASE_FRAG_SPV" in window
assert "LaunchHandoff::Peek()" in gl_art
assert "LaunchHandoff::Valid(*artwork)" in gl_art
assert "Eden::LaunchHandoff::LoadingSeconds(reduce_motion ? 1000.0 : 0.0)" in frontend
assert "Eden::LaunchHandoff::BeginLoading();" in frontend
assert "display.defer_scanout_close(reduce_motion)" in frontend
assert frontend.index("Eden::LoadingArtwork::Capture(") < frontend.index("textures.release();", frontend.index("Eden::LoadingArtwork::Capture("))
assert frontend.index("PresentUnifiedLoading(display, reduce_motion)") < frontend.index("display.defer_scanout_close(reduce_motion)")
assert "bool defer_scanout_close(bool reduce_motion);" in display_h

# R458: System::Load is no longer a frozen last GL frame.
assert "std::jthread deferred_loading_thread;" in display
assert "EGLContext deferred_context = EGL_NO_CONTEXT;" in display
loop = display.split("void deferred_loading_loop(", 1)[1].split("\n}", 1)[0]
assert "eglMakeCurrent(display, surface, surface, context)" in loop
assert "Eden::LoadingArtwork::GlPresenter presenter;" in loop
assert "presenter.Draw(width, height, seconds)" in loop
assert "presenter.Release();" in loop
assert "Eden::LaunchHandoff::LoadingSeconds(reduce_motion ? 1000.0 : 0.0)" in loop
assert "while (!stop.stop_requested())" in loop
assert "eglSwapBuffers(display, surface)" in loop
assert "glViewport(0, 0, width, height)" in gl_art

defer = display.split("bool Display::defer_scanout_close(bool reduce_motion)", 1)[1].split(
    "bool Display::close_deferred_scanout()", 1
)[0]
assert "eglMakeCurrent(display_, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT)" in defer
assert "std::jthread{deferred_loading_loop" in defer
assert "deferred_context = context_;" in defer
assert "eglDestroyContext(" not in defer
assert "eglDestroySurface(" not in defer
assert "eglTerminate(" not in defer

close_deferred = display.split("bool Display::close_deferred_scanout()", 1)[1].split(
    "bool Display::has_deferred_scanout()", 1
)[0]
for required in (
    "presenter.request_stop();",
    "presenter.join();",
    "eglDestroyContext(display, context)",
    "eglDestroySurface(display, surface)",
    "eglTerminate(display)",
):
    assert required in close_deferred
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

loading = renderer.split("void RendererVulkan::PresentLoading()", 1)[1].split(
    "void RendererVulkan::Report()", 1
)[0]
assert "present_manager.SwapchainImageViewFormat(), false);" in loading
assert "Eden::GetVulkanHud()" in loading
assert "Eden::LoadingArtwork::Repack" in loading
assert "blit_swapchain.DrawLoadingArtwork(device, frame, format)" in loading
assert "if (!animated_artwork && has_artwork)" in loading
assert "Eden::LaunchHandoff::PeekAlternate()" in window
assert "EDEN_LOADING_ARTWORK_FRAG_SPV" in window
assert "blit_swapchain.RetireLoadingArtwork();" in renderer
assert "layout(std430, set = 0, binding = 0)" in shader
assert "loading_artwork_attempts >= 3" in loading
assert "loading_artwork_format == format" in loading
assert "VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL" in loading
assert "VK_ACCESS_TRANSFER_WRITE_BIT" in loading
assert "VK_ACCESS_COLOR_ATTACHMENT_READ_BIT" in loading
assert "to_present.newLayout = VK_IMAGE_LAYOUT_GENERAL;" in loading
assert loading.index("CopyBufferToImage") < loading.index("DrawHudOverlay") < loading.index("scheduler.Flush")
assert "live_loading.glyphs[0] = has_artwork ? 1u : 0u" in loading
assert "vk::Buffer loading_artwork_buffer" in header
assert "scheduler.IsFree(loading_artwork_tick)" in renderer
assert "loading_artwork_tick = std::numeric_limits<u64>::max()" in loading
assert "if (postprocess_hud.loading) postprocess_hud = {};" in renderer
assert "if (hud.loading && !configs.empty()) hud = {};" in window
for retired in ("loading_jacket", "0x80000000u", "band_height", "loading_scene("):
    assert retired not in loading

overlay = window.split("void WindowAdaptPass::DrawHudOverlay", 1)[1].split(
    "VkDescriptorSetLayout WindowAdaptPass::GetDescriptorSetLayout", 1
)[0]
assert "hud.loading\n                ? VkRect2D{{0, 0}, size}" in overlay
assert "const VkViewport viewport{" in overlay
for retired in ("jacket_band", "band_height", "0x80000000u"):
    assert retired not in overlay
assert "cmdbuf.ClearAttachments" not in overlay

handover = renderer.split("vk::SurfaceKHR CreateHandoffSurface(", 1)[1].split(
    "} // Anonymous namespace", 1
)[0]
assert "requested_hz.load(std::memory_order_relaxed) >= 120" in handover
assert "PrepareHandoffSwapchain(vk::SurfaceKHR& surface)" in handover
assert "boundary=create_surface reason=120hz" in handover
assert "boundary=create_swapchain reason=60hz" in handover
assert renderer.index("device(CreateDevice(instance, dld, *surface))") < renderer.index(
    "PrepareHandoffSwapchain(surface)"
)
assert "if (videoout_title_declares_high_frame_rate()) {" in wsi
modes = wsi.split("static uint32_t\nvideoout_modes(", 1)[1].split(
    "VKAPI_ATTR VkResult VKAPI_CALL\nwsi_GetDisplayModePropertiesKHR", 1)[0]
assert modes.index("if (videoout_title_declares_high_frame_rate())") < modes.index(
    "videoout_settle_modes();"
)
assert modes.index("videoout_settle_modes();") < modes.index(
    "modes[count++] = &videoout_high_mode;"
)
assert "modes[count++] = &videoout_mode;" in modes

assert "LaunchHandoff::LoadingSeconds(LoadingCalm())" in graphics
assert "inline void BeginLoading() noexcept" in handoff
assert "inline void EndLoading() noexcept" in handoff
assert "inline double LoadingSeconds(double calm_offset = 0.0) noexcept" in handoff
assert "loading_started_ns" in handoff
# Updated exact shader source receipt; preserve historical source reviews.
assert subprocess.check_output(["git", "hash-object", "headless/vulkan_hud.frag"], cwd=root, text=True).strip() == "9fde027ac8dbbd9bca6bfd133e7415bab014e7f8"
subprocess.run([sys.executable, "-B", str(root / "tools/check-loading-artwork-transfer-host.py")], check=True)

print("PS5_CONTINUOUS_GL_VULKAN_LOADING_SOURCE_PASS shared_artwork=1 shared_epoch=1 animated_system_load=1 single_videoout_owner=1 purple_loader=0 console_pending=1")
