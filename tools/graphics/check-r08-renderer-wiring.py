#!/usr/bin/env python3
"""R08 source/packaging invariants; NOT a native PS5 compilation or GPU test."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[2]
read = lambda p: (root / p).read_text()
fork = read("headless/vulkan_renderer_r08.cpp")
header = read("headless/renderer_vulkan_r08.h")
present_header = read("headless/vk_present_manager_r08.h")
cmake = read("headless/vulkan.cmake")
pack = read("tools/package-headless-native.sh")
session = read("headless/mihawk_native_session.cpp")
volk = read("headless/mihawk_volk.h")
model = root / "vendor/sources/ps5-mihawkgen/framegen/models/network.fgw"

def between(pattern, start=0):
    return fork.index(pattern, start)

# The actual compositor draws the real source before any copy/dispatch.
composite = between("void RendererVulkan::Composite(")
draw = between("    blit_swapchain.DrawToFrame(device, rasterizer, frame, framebuffers,", composite)
copy = between("RecordOwnedSnapshot(source);", draw)
neural = between("RecordNativeMihawkPair(neural);", copy)
gpu_synthetic = between("const u64 generated_tick = scheduler.Flush(*r08_synthetic->render_ready);", neural)
present_synthetic = between("present_manager.Present(r08_synthetic);", gpu_synthetic)
gpu_real = between("const u64 real_tick = scheduler.Flush(*frame->render_ready);", present_synthetic)
present_real = between("present_manager.Present(frame);", gpu_real)
assert composite < draw < copy < neural < gpu_synthetic < present_synthetic < gpu_real < present_real
# FSR3 optical-flow must use a private source pair and actual GPU serials,
# never guest MV placeholders; original REAL frame always follows synthetic.
assert "Fsr3OpticalSession" in header
assert "fsr3_last_capture_tick" in header
assert "fsr3_last_capture_id" in header
assert "fsr3_optical->Create(" in fork
assert "fsr3_optical->Ready()" in fork
assert "fsr3_present_gate.OnRealFrame(" in fork
assert "FrameGeneration::Fsr3Vulkan" in fork
assert "fsr3_last_capture_tick = std::numeric_limits<u64>::max()" in fork
assert "fsr3_synthetic = present_manager.TryReserveRenderFrame()" in fork
assert "present_manager.CancelReservedRenderFrame(fsr3_synthetic)" in fork
assert "present_manager.ConfirmReservedRenderFrame(fsr3_synthetic)" in fork
assert "present_manager.Present(fsr3_synthetic)" in fork
assert "blit_swapchain.DrawHudOverlay(device, fsr3_synthetic, postprocess_hud)" in fork
assert "fsr3_optical.reset()" in fork
assert "fsr3_optical_session.cpp" in cmake
assert 'vendor/sources/ps5-fsr3-optical-flow' in cmake
assert fork.index("present_manager.Present(fsr3_synthetic)") < fork.index(
    "const u64 real_tick = scheduler.Flush(*frame->render_ready)")
assert "guest_motion_vectors = true" not in fork
assert "    ::Eden::FrameMetrics::OnRealQueued();" in fork
assert "    ::Eden::FrameMetrics::OnGeneratedQueued();" in fork
assert "r08_generated" in fork
assert "ValidateNativeMihawkPairInput(neural)" in fork
assert "ValidateOwnedSnapshotInput(source)" in fork
assert "reinterpret_cast<VkCommandBuffer>(1)" not in fork
assert "mihawk_capture_fences.CanGenerate(" in fork
assert "mihawk_capture_fences.Commit(" in fork
assert "mihawk_native->MarkOutputBlitted();" in fork
assert "mihawk_present_gate.Reset();" in fork
assert "Eden::Display::output_millihertz.load" in fork
assert "std::chrono::steady_clock::now()" in fork
assert "postprocess_hud_required ? Eden::GetVulkanHud()" in fork
assert "blit_swapchain.DrawHudOverlay(device, r08_synthetic, postprocess_hud);" in fork
assert "blit_swapchain.DrawHudOverlay(device, frame, postprocess_hud);" in fork
assert ".native_hud_absent = true" in fork
overlay_src = read("headless/vulkan_window_adapt_r08.cpp")
overlay_hdr = read("headless/window_adapt_pass_r08.h")
blit_src = read("headless/vulkan_blit_screen_r08.cpp")
assert "CreateWrappedRenderPass(device, frame_format, VK_IMAGE_LAYOUT_GENERAL)" in overlay_src
assert "hud_overlay_render_pass" in overlay_src and "hud_overlay_pipeline" in overlay_hdr
assert "DrawHudOverlay" in blit_src
assert "vulkan_window_adapt_r08.cpp" in cmake
assert "vulkan_blit_screen_r08.cpp" in cmake
assert "window_adapt_pass_r08.h" in cmake
assert "vk_blit_screen_r08.h" in cmake
assert "const bool mihawk_selected" in fork
assert "present_manager.Present(r08_synthetic);" in fork
assert "present_manager.Present(frame);" in fork
assert "DrawToFrame(device, rasterizer, frame, framebuffers," in fork
assert "present_manager.SwapchainImageViewFormat(), !postprocess_hud_required" in fork
assert "VK_IMAGE_LAYOUT_GENERAL);" in overlay_src
assert "BeginRenderPass(cmdbuf, rp, fb, size);" in overlay_src
assert "cmdbuf.EndRenderPass();" in overlay_src
assert "cmdbuf.ClearAttachments" not in overlay_src[overlay_src.index("void WindowAdaptPass::DrawHudOverlay("):overlay_src.index("VkDescriptorSetLayout WindowAdaptPass::GetDescriptorSetLayout()")]


assert ".native_hud_absent = true" in fork
assert "Eden::Display::game_millihertz.load" not in fork
assert "scheduler.Finish();" in fork and "mihawk_native.reset();" in fork
assert "ChooseMihawkSessionAction(" in fork
assert "MihawkSessionAction::RecreateAfterGpuIdle" in fork
assert "present_manager.WaitPresent();" in fork
assert "mihawk_capture_fences.ResetAfterDeviceIdle();" in fork
assert "std::unique_ptr<Eden::FeatureLab::MihawkNativeSession>" in header

# Synthetic reservation must NOT block on frame condition variables, and it
# must not reset its fence until commands are confirmed for submission.
reserve = present_header.index("Frame* TryReserveRenderFrame()")
cancel = present_header.index("void CancelReservedRenderFrame(")
confirm = present_header.index("void ConfirmReservedRenderFrame(")
assert reserve < cancel < confirm
assert "free_queue.empty()" in present_header[reserve:cancel]
assert "present_done.GetStatus()" in present_header[reserve:cancel]
assert "free_queue.erase(it)" in present_header[reserve:cancel]
assert "free_cv.wait(" not in present_header[reserve:cancel]
assert "present_done.Reset()" not in present_header[reserve:cancel]
assert "free_queue.push_front(frame)" in present_header[cancel:confirm]
assert "frame->present_done.Reset()" in present_header[confirm:]
assert "TryReserveRenderFrame()" in fork
assert "CancelReservedRenderFrame(r08_synthetic)" in fork
assert "ConfirmReservedRenderFrame(r08_synthetic)" in fork

# The complete renderer, present header and own source are versioned in
# Encore; the pinned vendor submodule is not edited/rewritten by CMake.
assert 'vulkan_renderer_r08.cpp' in cmake
assert 'renderer_vulkan_r08.h' in cmake
assert 'vk_present_manager_r08.h' in cmake
assert "target_sources(video_core PRIVATE $<TARGET_OBJECTS:eden-mihawkgen-native>)" in cmake
assert "EDEN_BUILD_MIHAWKGEN_CORE" not in cmake
assert "mihawk_native_session.cpp" in cmake
assert "#define VOLK_NAMESPACE 1" in volk
assert "using namespace volk;" in volk
assert "volkInitializeCustom(setup.instance_proc)" in session
assert "volkLoadDevice(setup.device)" in session
assert 'Eden::AppResourceFile("mihawkgen/network.fgw")' in fork

# The packaged model is content-verified, with the available notices.
assert '$app/mihawkgen/network.fgw' in pack
assert 'MIHAWKGEN_LICENSE.md' in pack
assert 'MIHAWKGEN_THIRD_PARTY_NOTICES.txt' in pack
assert model.is_file() and model.stat().st_size == 1_757_240
assert hashlib.sha256(model.read_bytes()).hexdigest() == (
    "31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b"
)

print("R08 RENDERER SOURCE PASS: native synthesis recorded, synthetic->real FIFO, nonblocking reserve, real GPU ticks")
