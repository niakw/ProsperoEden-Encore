#!/usr/bin/env python3
"""Host-only source contracts for the PS5 DualSense touchpad quick overlay.

No PS5 screenshot, runtime output or console-build claim. The independent
source-extracted Pad::Consume test exercises native input at O0 and O2.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
read = lambda path: (root / path).read_text(encoding="utf-8")
pad = read("headless/pad.cpp")
devices = read("headless/devices.h")
main = read("headless/main.cpp")
quick = read("headless/in_game_overlay.h")
menu = read("headless/in_game_overlay_menu.h")
vulkan = read("headless/vulkan_window_adapt_r08.cpp")
shader = read("headless/vulkan_hud.frag")
graphics = read("headless/graphics.cpp")

# Click the physical touchpad, never the reserved console system button; legacy shortcuts
# and OpenGL guest Minus remain unchanged.
assert "overlay_enabled.load(std::memory_order_acquire)" in pad
assert "overlay_open.store(opening, std::memory_order_release)" in pad
assert "slot.select_pulse = kSelectTapPolls + 1;" in pad
assert "constexpr ButtonMask menu_chord = kButtonTouchPad | kButtonL1;" in pad
assert "const bool guest_home = slot.guest_home.Observe(" in pad
assert "const bool intercept_overlay = overlay_open.load(std::memory_order_acquire);" in pad
assert "mapped_buttons = 0;" in pad
assert "intercept_overlay ? 0.0f" in pad
assert "constexpr ButtonMask hud_chord" not in pad
assert "TakeHudToggle" not in devices + main
assert "pad->TakeOverlayActions()" in main
assert "game && backend == Eden::GraphicsBackend::Vulkan" in main
assert "pad->EnableOverlay(false)" in main
assert "void EnableOverlay(bool enabled)" in devices

# Render-path guards: both normal present and generated frames.
assert "frame_visible.load(std::memory_order_acquire)" in quick
assert "std::lock_guard lock(frame_mutex);" in quick
assert vulkan.count("DrawQuickOverlay(cmdbuf,") == 2
assert "Eden::QuickOverlay::Snapshot()" in vulkan
assert "hud_pipeline ? *hud_pipeline : VK_NULL_HANDLE" in vulkan
assert "hud_layout ? *hud_layout : VK_NULL_HANDLE" in vulkan
assert "kWarningRow=kStyleTag|4u;" in read("headless/in_game_overlay_style.h")
assert "bool warning_row = quick && kind == 4u;" in shader
assert "result.style = StyleId(prefs.color_palette,prefs.accent_color," in menu
assert "dst.loading = StyledMode(mode,result.style);" in menu
assert "StyledMode(" in vulkan
assert "menuAccent(uint palette,uint accent)" in shader
assert "menuPanel(uint palette)" in shader
assert "prefs = LoadPreferences();" in menu

# Every tab displays its accessible page index and both shoulder controls,
# with the fifth Multiplayer tab visible even on initial opening.
import re
headings = menu.split("static constexpr std::string_view headings[] = {", 1)[1].split("};", 1)[0]
labels = re.findall(r'"([^"]+)"', headings)
assert len(labels) == 5
for idx, (label, category) in enumerate(zip(labels, ("JEU", "GRAPH", "PAD", "DIAG", "MULTI")), 1):
    assert label == f"L1 / {category} {idx}/5 / R1"
    assert len(label) <= 24
assert 'line(headings[tab], kSelectedRow);' in menu
assert 'line("JEU GRAPH PAD DIAG MULTI", kRow);' in menu
assert len("JEU GRAPH PAD DIAG MULTI") <= 24
assert len("EDEN ENCORE / PAD FERMER") <= 24
assert 'line("EDEN ENCORE / PAD FERMER", kRow);' in menu


# Settings are saved for this title; only FPS and detailed logs update live.
assert "SaveGameSettings(title_id, game)" in menu
assert "SavePreferences(prefs)" in menu
assert "bool restart_required{};" in menu
assert "restart_required = true;" in menu
assert "RELANCER LE JEU REQUIS" in menu
assert "restart_required ? kWarningRow : kRow" in menu
assert "SetHudEnabled(prefs.hud);" in menu
assert "NativeLogs::SetDetailed(prefs.detailed_logging);" in menu
assert "void SetHudEnabled(bool enabled)" in graphics
print("ENCORE_TOUCHPAD_OVERLAY_SOURCE_PASS input=touchpad gfx=next-launch diagnostics=live render=two-paths")
