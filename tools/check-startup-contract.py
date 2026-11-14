#!/usr/bin/env python3
"""Fast release gate for Encore's 13.60 startup/elevation/storage contract."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = (root / "headless/main.cpp").read_text()
elevation = (root / "headless/elevation/elevation.cpp").read_text()
helper = (root / "headless/elevation/helper/main.cpp").read_text()
packager = (root / "tools/package-headless-native.sh").read_text()
lifecycle = (root / "src/lifecycle.c").read_text()

body = main[main.index("int main("):]
boot = body.index("BootTrace::Begin")
request = body.index("elevation::request")
migrate_sandbox = body.index("MigrateSandboxData")
migrate_legacy = body.index("MigrateLegacyInstallAssets")
assert boot < request < migrate_sandbox < migrate_legacy
for forbidden in ("std::thread", "std::jthread", "pthread_create"):
    assert forbidden not in body[:request], f"{forbidden} starts before the one-shot helper"

assert "ProbeWritableRoot(Eden::kDataDir)" in body
assert body.index("MigrateLegacyInstallAssets") < body.index("PrepareStorageLayout();") < body.index("BootTrace::Ready")
assert "invalid_success_identity" not in body, "uid/gid inference must not kill a valid filesystem grant"
assert 'target_title_id[] = "PPSA99008"' in helper
assert 'sandbox-elevator.elf' in packager
assert 'PPSA99121' not in lifecycle, "stale lifecycle title ID"
assert 'PPSA99008' in lifecycle

# One authored loading state spans launcher, core load and Vulkan warm-up.
# The selected R08 overrides, not the historical vendor presenter, own the
# production transition. Physical PS5 continuity remains a hardware gate.
graphics = (root / "headless/graphics.cpp").read_text()
frontend = (root / "headless/prosperoeden/frontend.cpp").read_text()
display = (root / "headless/prosperoeden/pe/platform/display_egl.cpp").read_text()
active_renderer = (root / "headless/vulkan_renderer_r08.cpp").read_text()
active_presenter = (root / "headless/vulkan_window_adapt_r08.cpp").read_text()
assert "PresentVulkanLoading(renderer);" in graphics
assert "kLoadingSceneGlsl" in graphics
assert "kLoadingSceneGlsl" in frontend
assert "PresentUnifiedLoading(display)" in frontend
assert "display.defer_scanout_close()" in frontend
assert "close_deferred_scanout()" in active_renderer
assert "surface(CreateHandoffSurface(instance, render_window.GetWindowInfo()))" in active_renderer
assert "loading_jacket" not in active_renderer
assert "jacket_band" not in active_presenter
assert "hud.loading\n                ? VkRect2D{{0, 0}, size}" in active_presenter
# A black picture with a live stderr is not proof of a dead game process.
# Emit only bounded milestone signals: Core load, GPU start, guest run and
# two time thresholds while Vulkan still has no first guest frame.
for stage in ('stage=core_loaded', 'stage=gpu_started', 'stage=guest_run_begin'):
    assert stage in main, stage
assert 'EDEN_VULKAN_LOADING_WAIT stage=10s' in graphics
assert 'EDEN_VULKAN_LOADING_WAIT stage=30s' in graphics
assert 'vulkan_loading_diagnostic_stage = 0;' in graphics
assert 'guest_frame_handoff=0' in graphics
assert 'MakeLoadingSnapshot(1.0 + LoadingCalm())' in graphics
assert 'eglTerminate(display)' in display

for stage in (
    "elevation: request begin",
    "elevation: connect 127.0.0.1:9021",
    "elevation: helper stream complete",
    "elevation: prepare received",
    "elevation: final response",
):
    assert stage in elevation, f"missing startup trace stage: {stage}"

print("Startup contract: trace, single-threaded elevation, real filesystem proof and title identity PASS")
