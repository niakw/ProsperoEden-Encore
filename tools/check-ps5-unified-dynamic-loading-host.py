#!/usr/bin/env python3
"""Focused contract for the continuous native loading compositor.

The shader is validated separately. This source gate rejects the old static
jacket/band and the R457 frozen-frame handoff: one retained GL context must
keep the shared scene moving through System::Load, then stop/join before
Vulkan takes VideoOut. No physical PS5 continuity is claimed.
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
display_h = (root / "headless/prosperoeden/pe/platform/display_egl.hpp").read_text()
display = (root / "headless/prosperoeden/pe/platform/display_egl.cpp").read_text()
handoff = (root / "headless/launch_handoff.hpp").read_text()
vulkan_cmake = (root / "headless/vulkan.cmake").read_text()
native_cmake = (root / "headless/CMakeLists.txt").read_text()

assert 'target_compile_definitions(video_core PRIVATE PS5_NATIVE=1)' in vulkan_cmake
assert "vulkan_renderer_r08.cpp" in vulkan_cmake
assert 'set(EDEN_NS2_SPARSE_BACKING OFF)' in native_cmake
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in native_cmake

# All three presentation phases use the same source-generated scene.
assert "kLoadingSceneGlsl" in frontend
assert "kLoadingSceneGlsl" in graphics
assert "kLoadingSceneGlsl" in display
assert '#include "loading_scene.glsl"' in shader
for source in (frontend, graphics, display):
    assert "loading_scene(gl_FragCoord.xy,size,seconds)" in source
assert "color = vec4(loading_scene(" in shader

assert "bool PresentUnifiedLoading(pe::ps5::Display& display, bool reduce_motion)" in frontend
assert "Eden::LaunchHandoff::LoadingSeconds(reduce_motion ? 1000.0 : 0.0)" in frontend
assert "Eden::LaunchHandoff::BeginLoading();" in frontend
assert "PresentUnifiedLoading(display, reduce_motion)" in frontend
assert "display.defer_scanout_close(reduce_motion)" in frontend
assert frontend.index("PresentUnifiedLoading(display, reduce_motion)") < frontend.index(
    "display.defer_scanout_close(reduce_motion)"
)
assert "bool defer_scanout_close(bool reduce_motion);" in display_h

# Native game selection enters the canonical compositor before the launcher
# can draw its preview-only jacket or wait for full media / a fixed timer.
launcher = (root / "headless/prosperoeden/pe/ui/launcher.cpp").read_text()
launcher_h = (root / "headless/prosperoeden/pe/ui/launcher.hpp").read_text()
assert "bool native_unified_loading = false" in launcher_h
assert "native_unified_loading_(native_unified_loading)" in launcher
launch = launcher.split("void Launcher::launch(", 1)[1].split("void Launcher::press(", 1)[0]
branch = launch.split("if (native_unified_loading_ && !selected_game_.empty()) {", 1)[1].split("}", 1)[0]
assert "done_ = true;" in branch and "return;" in branch
assert launch.index("services_.game_exists(file)") < launch.index("if (native_unified_loading_")
assert launch.index("selected_media_cancel_.store(true") < launch.index("if (native_unified_loading_")
assert launch.index("if (native_unified_loading_") < launch.index("textures_.clear_case_pages()")
assert launch.index("if (native_unified_loading_") < launch.index("launch_.start(theme::kLaunchSeconds)")
assert "pe::ui::Launcher launcher(services, textures, fonts, first_start, true);" in frontend
entry = frontend.split("if (launcher.done() && !launcher.selected_game().empty()) {", 1)[1].split("}", 1)[0]
assert entry.index("Eden::LaunchHandoff::BeginLoading();") < entry.index("PresentUnifiedLoading(display, reduce_motion)")
assert "reduce_motion = launcher.reduce_motion();" in entry
assert "break;" in entry
assert frontend.index("if (launcher.done() && !launcher.selected_game().empty()) {") < frontend.index("launcher.draw(list)")
assert "if (!loading_scene_started) {" in frontend
assert "if (!loading_scene_presented && !PresentUnifiedLoading(display, reduce_motion))" in frontend
print("PS5_NATIVE_SINGLE_LOADING_ENTRY_SOURCE_PASS preview_only_cinematic=1 no_fixed_dwell=1 first_present_before_teardown=1")

# R458: System::Load is no longer a frozen last GL frame.
assert "std::jthread deferred_loading_thread;" in display
assert "EGLContext deferred_context = EGL_NO_CONTEXT;" in display
loop = display.split("void deferred_loading_loop(", 1)[1].split("\n}", 1)[0]
assert "eglMakeCurrent(display, surface, surface, context)" in loop
assert "create_loading_program()" in loop
assert "Eden::LaunchHandoff::LoadingSeconds(reduce_motion ? 1000.0 : 0.0)" in loop
assert "while (!stop.stop_requested())" in loop
assert "eglSwapBuffers(display, surface)" in loop
assert "glViewport(0, 0, width, height)" in loop

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

handover = renderer.split("vk::SurfaceKHR CreateHandoffSurface(", 1)[1].split(
    "} // Anonymous namespace", 1
)[0]
assert handover.index("close_deferred_scanout()") < handover.index("CreateSurface(")

assert "LaunchHandoff::LoadingSeconds(LoadingCalm())" in graphics
assert "inline void BeginLoading() noexcept" in handoff
assert "inline void EndLoading() noexcept" in handoff
assert "inline double LoadingSeconds(double calm_offset = 0.0) noexcept" in handoff
assert "loading_started_ns" in handoff
shader_sha256 = hashlib.sha256(shader.encode()).hexdigest()
assert shader_sha256 == (
    "cec9e8b4323c573b5cb7ca17fe4f6831163df43be94602c781f8d0f82cf3d9df"
), ("vulkan_hud.frag sha256", shader_sha256)

print("PS5_CONTINUOUS_GL_VULKAN_LOADING_SOURCE_PASS shared_scene=1 shared_epoch=1 animated_system_load=1 single_videoout_owner=1 console_pending=1")
