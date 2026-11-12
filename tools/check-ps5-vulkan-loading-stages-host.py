#!/usr/bin/env python3
"""Bounded Vulkan loading diagnostics source witness (not a guest-frame proof).

The loader is allowed to display its own frames while an NS2 title is stuck
before its first guest SwapBuffers. Check the shipping callback owns exactly
two quiet diagnostics per title and resets the stage on window creation.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

source = (Path(__file__).resolve().parents[1] / "headless/graphics.cpp").read_text()
assert source.count("unsigned vulkan_loading_diagnostic_stage{};") == 1
assert source.count("vulkan_loading_diagnostic_stage = 0;") == 1
loading = source.split("bool LoadingTick(", 1)[1].split("GraphicsWindow::GraphicsWindow(", 1)[0]
assert loading.count("EDEN_VULKAN_LOADING_WAIT stage=10s") == 1
assert loading.count("EDEN_VULKAN_LOADING_WAIT stage=30s") == 1
assert 'vulkan_loading_diagnostic_stage == 0 && elapsed >= 10.0' in loading
assert 'vulkan_loading_diagnostic_stage == 1 && elapsed >= 30.0' in loading
assert 'vulkan_loading_diagnostic_stage = 1;' in loading
assert 'vulkan_loading_diagnostic_stage = 2;' in loading
assert 'guest_frame_handoff=0' in loading
assert 'const double elapsed = now - vulkan_loading_start;' in loading
assert 'if (first) sceSystemServiceHideSplashScreen();' in loading
assert 'return true;' in loading
constructor = source.split("GraphicsWindow::GraphicsWindow(", 1)[1]
assert constructor.index("vulkan_loading_diagnostic_stage = 0;") < constructor.index("vulkan_loading_pace = {};")
# OpenGL titles must drop launcher jacket pixels on window creation.
# Vulkan titles must retain the same mailbox until upload completes.
assert '#include "launch_handoff.hpp"' in source
assert constructor.count('if (!vulkan) LaunchHandoff::Clear();') == 1
assert constructor.index('if (!vulkan) LaunchHandoff::Clear();') < constructor.index("vulkan_loading = vulkan;")
print("ENCORE_OPENGL_JACKET_LIFETIME_SOURCE_PASS clear_only_opengl=1 vulkan_mailbox_preserved=1")
# Validate stage boundary behavior under monotonic time (not the real GPU).
def stages(elapsed_values):
    stage = 0
    events = []
    for elapsed in elapsed_values:
        if stage == 0 and elapsed >= 10:
            stage = 1
            events.append(10)
        elif stage == 1 and elapsed >= 30:
            stage = 2
            events.append(30)
    return events, stage
assert stages([0, 1, 9.999, 10, 10, 20, 29.999, 30, 30, 100]) == ([10, 30], 2)
assert stages([0, 31, 32]) == ([10, 30], 2)
assert stages([0, 1, 9.9]) == ([], 0)
# Continuous jacket-to-Vulkan loading must use the launcher frame itself,
# not the old purple scene, a black second interstitial, or fake guest frames.
root = Path(__file__).resolve().parents[1]
frontend = (root / "headless/prosperoeden/frontend.cpp").read_text()
handoff = (root / "headless/launch_handoff.hpp").read_text()
renderer = (root / "vendor/encore-active/eden-vulkan/vulkan_renderer.cpp").read_text()
active_renderer = (root / "headless/vulkan_renderer_r08.cpp").read_text()
native_selection = (root / "headless/vulkan.cmake").read_text()
oracle = (root / "vendor/encore-active/eden-vulkan-oracles/vulkan_loading.inc").read_text()
renderer_header = (root / "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/renderer_vulkan.h").read_text()
generator = (root / "tools/prepare-vulkan-port.py").read_text()
assert frontend.count("glReadPixels(") == 2  # dev BMP capture + one production handoff
assert "glReadPixels(0, 0, width, height, GL_RGBA,\n                                         GL_UNSIGNED_BYTE, snapshot.rgba.data());" in frontend
assert frontend.count("LaunchHandoff::Publish(") == 1
handoff_read = frontend.index("snapshot.rgba.data());")
# The final GL readback must not inherit a pixel-pack buffer (the pointer
# would be interpreted as a GPU offset) or nonzero row/skip (buffer overrun).
# Verify every altered state is restored before EGL swaps the final jacket.
pack_begin = frontend.index("glGetIntegerv(GL_PIXEL_PACK_BUFFER_BINDING, &old_pack_buffer);")
pack_end = frontend.index("static_cast<GLuint>(old_pack_buffer));", pack_begin)
pack = frontend[pack_begin:pack_end]
assert pack.index("glBindBuffer(GL_PIXEL_PACK_BUFFER, 0);") < pack.index("glReadPixels(")
assert pack.index("glReadPixels(") < pack.index("glPixelStorei(GL_PACK_ALIGNMENT, old_pack_alignment);")
for pname in ("ALIGNMENT", "ROW_LENGTH", "SKIP_ROWS", "SKIP_PIXELS"):
    assert f"glPixelStorei(GL_PACK_{pname}, 0);" in pack if pname != "ALIGNMENT" else "glPixelStorei(GL_PACK_ALIGNMENT, 1);" in pack
    assert f"glPixelStorei(GL_PACK_{pname}, old_pack_{pname.lower()});" in pack
assert pack_end < frontend.index("Eden::LaunchHandoff::Publish(", pack_begin)
# The first swap is the legitimate startup splash. Verify the swap AFTER
# the completed launcher readback, not the first swap in this source file.
assert frontend.index("display.swap()") < frontend.index("batch.draw(list, viewport,")
assert frontend.index("batch.draw(list, viewport,") < handoff_read < frontend.index("display.swap()", handoff_read)
assert "handoff_captured = true;" in frontend
# The production guard already contains the substring after its leading '!'.
# Check the *full* conditional, not an ambiguous substring.
assert frontend.count("if (!handoff_captured && launcher.done() &&") == 1
# The final case remains alive for at most three GPU-readback attempts.
# Stale GL errors must not turn a successful readback into a false failure.
assert "handoff_attempts < 3u" in frontend
assert "++handoff_attempts;" in frontend
assert "handoff_captured = true;" in frontend
assert "EDEN_LAUNCH_GL_PRIOR_ERROR" in frontend
assert frontend.index("EDEN_LAUNCH_GL_PRIOR_ERROR") < frontend.index("glReadPixels(0, 0, width, height, GL_RGBA", frontend.index("EDEN_LAUNCH_GL_PRIOR_ERROR"))
assert "mixer->active_voices()" not in frontend
assert "mixer->set_bus_gain(pe::audio::Bus::ui, 0.0f);" in frontend

assert "if (handoff_captured && launcher.done() &&" not in frontend
assert "if (!handoff_captured && launcher.done() &&" in frontend
launcher_scene = (root / "headless/prosperoeden/pe/ui/launcher.cpp").read_text()
assert "const float leave = 1.0f;" in launcher_scene
assert "if (fade > 0.0f)" not in launcher_scene
assert "LaunchHandoff::Clear()" in frontend
assert "inline bool Valid(const Frame& frame)" in handoff
assert "frame.width <= max_width && frame.height <= max_height" in handoff
assert "std::exchange(pending_frame, {})" in handoff
assert "inline std::shared_ptr<const Frame> Peek()" in handoff
for evidence in (
    '#include "launch_handoff.hpp"',
    "Eden::LaunchHandoff::Peek()",
    "Eden::LaunchHandoff::Clear();",
    "loading_jacket_attempts >= 3",
    "loading_jacket_attempted = true;",
    "loading_jacket_buffer = std::move(buffer);",
    "buffer.Flush();",
    "VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL",
    "cmdbuf.CopyBufferToImage(upload, target,",
    "loading_jacket_width == frame->width",
):
    assert evidence in renderer, evidence
# CMake compiles the extended R08 presenter, not vendor's Vulkan source.
# Both must implement the exact one-screen jacket handoff contract.
assert '"${EDEN_PORT_DIR}/vulkan_renderer_r08.cpp"' in native_selection
assert active_renderer.count("void RendererVulkan::PresentLoading() {") == 1
for evidence in (
    '#include "launch_handoff.hpp"',
    "Eden::LaunchHandoff::Peek()",
    "Eden::LaunchHandoff::Clear();",
    "loading_jacket_buffer = std::move(buffer);",
    "cmdbuf.CopyBufferToImage(upload, target,",
    "loading_jacket_width == frame->width",
    "loading_jacket_attempts >= 3",
    "EDEN_LOADER_JACKET_HANDOFF_VULKAN",
):
    assert evidence in active_renderer, ("selected R08 loader missing", evidence)
assert active_renderer.count("EDEN_LOADER_JACKET_HANDOFF_VULKAN") == 4
assert active_renderer.index("Eden::LaunchHandoff::Peek()") < active_renderer.index("loading_jacket_buffer = std::move(buffer);")
assert active_renderer.index("loading_jacket_buffer = std::move(buffer);") < active_renderer.index("Eden::LaunchHandoff::Clear();")
# The compiled R08 header is a separate Encore-maintained override.
# Checking only vendor's header misses compile-time member lookup failures.
active_header = (root / "headless/renderer_vulkan_r08.h").read_text()
assert 'configure_file("${EDEN_PORT_DIR}/renderer_vulkan_r08.h"' in native_selection
for member in (
    "vk::Buffer loading_jacket_buffer{};",
    "u32 loading_jacket_width{};",
    "u32 loading_jacket_height{};",
    "bool loading_jacket_attempted{};",
    "u32 loading_jacket_attempts{};",
):
    assert active_header.count(member) == 1, ("actual R08 header missing jacket member", member)
assert active_header.index("MemoryAllocator memory_allocator;") < active_header.index(
    "vk::Buffer loading_jacket_buffer{};") < active_header.index("StateTracker state_tracker;")
assert "vk::Buffer loading_jacket_buffer{};" in renderer_header
assert "u32 loading_jacket_attempts{};" in renderer_header
assert "loading_jacket_attempts{}" in generator
assert renderer.index("Eden::LaunchHandoff::Peek()") < renderer.index("loading_jacket_buffer = std::move(buffer);") < renderer.index("Eden::LaunchHandoff::Clear();")
assert "loading_jacket_buffer{}" in generator
assert "launch_handoff.hpp" in generator
assert "loading_jacket_buffer = std::move(buffer);" in oracle
assert "cmdbuf.CopyBufferToImage(upload, target," in oracle
assert renderer.count("EDEN_LOADER_JACKET_HANDOFF_VULKAN") == 4  # success + fallback + retries + unsupported format
# A native build can be requested explicitly; console qualification and
# publication are independent decisions, not compilation-time P5 gates.
research = (root / ".github/workflows/ns2-native-ps5-research.yml").read_text()
release = (root / ".github/workflows/build-040-zbic.yml").read_text()
assert "  workflow_dispatch:" in research
assert "  push:" not in research
assert "    if: ${{ false }}" in research
assert "if: >-\n      ${{ github.event_name == 'workflow_dispatch' ||" in release
assert "contains(github.event.head_commit.message || '', '[full-build]')" in release
assert "(github.event_name == 'workflow_dispatch' && inputs.publish)" in release
# Compile and execute the tiny mailbox owner in host mode: one transfer,
# bounded dimensions, no stale snapshot and no copied pixels on subsequent
# Vulkan warm-up ticks. Does not build the PS5 app or GPU runtime.
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "host C++20 compiler required for single-loader mailbox test"
with tempfile.TemporaryDirectory(prefix="encore-single-loader-") as directory:
    exe = Path(directory) / "test_launch_handoff"
    subprocess.run(
        [compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
         "-pthread", "-O2", "-I", str(root / "headless"),
         str(root / "tools/loader/test_launch_handoff.cpp"), "-o", str(exe)],
        check=True,
    )
    subprocess.run([str(exe)], check=True)
print("ENCORE_LOADER_MAILBOX_HOST_PASS single_use=1 bounded=1")
print("ENCORE_SINGLE_LOADER_HANDOFF_SOURCE_PASS build_ps5_operator_triggered=1")

print("ENCORE_VULKAN_LOADING_DIAGNOSTIC_PASS first_guest_frame_not_claimed=1 max_reports=2 reset_per_title=1")
