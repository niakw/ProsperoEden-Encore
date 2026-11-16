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
hud = read("headless/hud.h")
vulkan_cmake = read("headless/vulkan.cmake")
hud_builder = read("tools/graphics/build-vulkan-hud-shaders.py")
font_baker = read("tools/launcher/bake_vulkan_menu_font.py")
font_baker_cpp = read("tools/launcher/bake_vulkan_menu_font.cpp")
quick_font = read("headless/quick_overlay_font.cpp")

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
assert '#include "vulkan_menu_font.glsl"' in shader
assert "menuFontSlotAlpha(" in shader
assert "15-bit atlas slot" in shader
assert "EncodeMenuText(value, prefs.language)" in menu
assert "SystemFonts" in quick_font and "bidi::resolve" in quick_font
assert "stbtt_GetGlyphSDF" in font_baker_cpp
assert '#include "eden_vulkan_hud_shaders.h"' in vulkan
assert "eden-vulkan-hud-shaders" in vulkan_cmake
assert "bake_vulkan_menu_font.py" in vulkan_cmake
assert "build-vulkan-hud-shaders.py" in vulkan_cmake
assert "EDEN_HUD_SHADER_HEADER" in vulkan_cmake
assert "--output" in font_baker
assert "--spirv-val" in hud_builder and "0x07230203" in hud_builder
assert "HudCodepoints(std::string_view text)" not in hud
assert "HudCodepoints(" not in menu

# All five pages retain shoulder navigation, but category labels now come
# from the same 31 launcher catalogues instead of a French-only parallel UI.
assert "const std::array<std::string, kOverlayTabs> headings" in menu
for index in range(1, 6):
    assert f" {index}/5 / R1" in menu
for key in ("Game settings", "Renderer", "Controls", "Diagnostics", "Multiplayer"):
    assert f'Text("{key}")' in menu
assert "line(headings[static_cast<std::size_t>(tab)], kSelectedRow);" in menu

# Home must expose every other category as a selectable row, even if the
# user never presses a shoulder button. Circle returns to that home row.
for row in range(4, 8):
    assert f"case {row}:" in menu
assert "tab == 0 ? kHomeRows" in menu
assert "HomeCategoryTab(selected)" in menu
assert "selected = kHomeActionRows + previous - 1;" in menu
assert 'Text("Change")' in menu and 'Text("Back")' in menu
assert "kHomeRows <= kVisibleRows" in menu


# Settings are saved for this title; only FPS and detailed logs update live.
assert "SaveGameSettings(title_id, game)" in menu
assert "SavePreferences(prefs)" in menu
assert "bool restart_required{};" in menu
assert "restart_required = true;" in menu
assert 'restart_required ? Text("Game settings")' in menu
assert "restart_required ? kWarningRow : kRow" in menu
assert "SetHudEnabled(prefs.hud);" in menu
assert "NativeLogs::SetDetailed(prefs.detailed_logging);" in menu
assert "void SetHudEnabled(bool enabled)" in graphics
print("ENCORE_TOUCHPAD_OVERLAY_SOURCE_PASS input=touchpad gfx=next-launch diagnostics=live render=two-paths")

# The retired chord must never remain in either visible FPS guide.
guide = "Shows live FPS while playing. In Vulkan, open the touchpad menu to toggle it."
retired = "Touchpad + R1 toggles it at any time."
for name in ("settings.cpp", "switch_theme.cpp"):
    source = (root / "headless/prosperoeden/pe/ui" / name).read_text()
    assert guide in source and retired not in source
catalogs = sorted((root / "headless/prosperoeden/ui/lang").glob("*.po"))
assert len(catalogs) == 31
for catalog in catalogs:
    text = catalog.read_text()
    assert f'msgid "{guide}"' in text and retired not in text, catalog
print("FPS_TOUCHPAD_GUIDE_CATALOG_PARITY_PASS themes=2 locales=31")


# Exercise the actual published model rather than a parallel simulation.
# The 112-byte shader push-constant ABI and legacy row are still unchanged.
import subprocess
import tempfile
assert "result.text[index].Assign(value);" in menu
assert "dst.glyphs = EncodeMenuText(value, prefs.language);" in menu
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "overlay_text.cpp"
    binary = Path(directory) / "overlay_text"
    source.write_text(r'''
#include "in_game_overlay.h"
#include <cassert>
#include <string>
#include <type_traits>
using namespace Eden::QuickOverlay;
int main() {
    static_assert(sizeof(Eden::HudSnapshot) == 112);
    static_assert(kHomeRows == 8 && kOverlayTabs == 5);
    static_assert(HomeCategoryTab(-1) == 0 && HomeCategoryTab(8) == 0);
    for (int row = 0; row < kHomeActionRows; ++row)
        assert(HomeCategoryTab(row) == 0);
    for (int tab = 1; tab < kOverlayTabs; ++tab) {
        const int row = kHomeActionRows + tab - 1;
        assert(HomeCategoryTab(row) == tab);
    }
    static_assert(std::is_trivially_copyable_v<Frame>);
    Frame visible{};
    visible.visible = true;
    visible.count = 2;
    visible.text[0].Assign("Full-length label beyond twenty-four characters");
    visible.rows[0].glyphs = Eden::HudText("FPS");
    const std::string prefix(MenuText::kCapacity - 1, 'x');
    const std::string accented = prefix + "\xc3\xa9";
    visible.text[1].Assign(accented);
    Publish(visible);
    auto got = Snapshot();
    assert(got.visible && got.count == 2);
    assert(got.text[0].View() == "Full-length label beyond twenty-four characters");
    assert(!got.text[0].truncated);
    assert(got.rows[0].glyphs == visible.rows[0].glyphs);
    assert(got.text[1].View() == prefix && got.text[1].truncated);
    MenuText text{};
    text.Assign(std::string(MenuText::kCapacity - 3, 'x') + "\xe2\x82\xac");
    assert(text.View().size() == MenuText::kCapacity && !text.truncated);
    text.Assign("short");
    assert(text.View() == "short" && !text.truncated);
    text.Assign("");
    assert(text.View().empty() && !text.truncated);
    Reset();
    got = Snapshot();
    assert(!got.visible && got.count == 0 && got.text[0].View().empty());
}
''', encoding="utf-8")
    subprocess.run(["c++", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-pthread", "-I", str(root / "headless"), str(source),
                    "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("OVERLAY_MENU_TEXT_MODEL_HOST_PASS utf8_boundary=1 immutable=1 legacy_abi=112 shaped_quick_menu_separate=1")


# Compile the actual Menu::Handle body and Count() into a controlled host
# harness. Persistence/render calls are spies: the test exercises navigation
# logic without writing real user configuration or starting a GPU.
handle = menu.split("    Outcome Handle(std::uint32_t actions) {", 1)[1].split("\nprivate:", 1)[0]
count = menu.split("    int Count() const {", 1)[1].split("\n    }", 1)[0]
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "overlay_navigation.cpp"
    binary = Path(directory) / "overlay_navigation"
    source.write_text(r'''
#include "in_game_overlay.h"
#include <cassert>
#include <string>
namespace Eden::QuickOverlay {
struct MenuProbe {
    enum class Outcome { none, close, library, multiplayer };
    bool visible = true;
    bool multiplayer_confirm = false;
    int tab = 0;
    int selected = 0;
    int writes = 0;
    std::string notice;
    static constexpr int kGraphicsRows = 12;
    static constexpr int kMappingRows = 12;
    void Show(bool next) { visible = next; }
    void Rebuild() {}
    void ToggleFps() { ++writes; }
    void ToggleLogs() { ++writes; }
    void EditGraphics(int) { ++writes; }
    void EditMapping(int) { ++writes; }
    static std::string Text(const char* english) { return std::string{english}; }
    int Count() const {''' + count + r'''
    }
    Outcome Handle(std::uint32_t actions) {''' + handle + r'''
};
} // namespace Eden::QuickOverlay
int main() {
    using namespace Eden::QuickOverlay;
    using O = MenuProbe::Outcome;
    for (int target = 1; target < kOverlayTabs; ++target) {
        MenuProbe probe;
        const int row = kHomeActionRows + target - 1;
        for (int i = 0; i < row; ++i)
            assert(probe.Handle(down) == O::none);
        assert(probe.selected == row);
        assert(probe.Handle(Eden::QuickOverlay::select) == O::none);
        assert(probe.tab == target && probe.selected == 0 && probe.writes == 0);
        assert(probe.Handle(back) == O::none);
        assert(probe.visible && probe.tab == 0 && probe.selected == row && probe.writes == 0);
        assert(probe.Handle(back) == O::close && !probe.visible);
    }
    MenuProbe shoulder;
    assert(shoulder.Handle(next_tab) == O::none && shoulder.tab == 1);
    assert(shoulder.Handle(previous_tab) == O::none && shoulder.tab == 0);
    assert(shoulder.Handle(previous_tab) == O::none && shoulder.tab == 4);
    assert(shoulder.Handle(Eden::QuickOverlay::select) == O::none && shoulder.multiplayer_confirm);
    assert(shoulder.Handle(back) == O::none && !shoulder.multiplayer_confirm);
    assert(shoulder.Handle(Eden::QuickOverlay::select) == O::none && shoulder.tab == 4);
    assert(shoulder.Handle(Eden::QuickOverlay::select) == O::none && shoulder.multiplayer_confirm);
    assert(shoulder.Handle(Eden::QuickOverlay::select) == O::multiplayer && !shoulder.visible);
    MenuProbe old_actions;
    assert(old_actions.Handle(down) == O::none);
    assert(old_actions.Handle(Eden::QuickOverlay::select) == O::none && old_actions.writes == 1);
    assert(old_actions.Handle(down) == O::none);
    assert(old_actions.Handle(Eden::QuickOverlay::select) == O::none && old_actions.writes == 2);
    assert(old_actions.Handle(down) == O::none);
    assert(old_actions.Handle(Eden::QuickOverlay::select) == O::library && !old_actions.visible);
    MenuProbe resume;
    assert(resume.Handle(Eden::QuickOverlay::select) == O::close && !resume.visible);
}
''', encoding="utf-8")
    subprocess.run(["c++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-pthread", "-I", str(root / "headless"),
                    str(source), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("OVERLAY_DIRECT_CATEGORY_NAVIGATION_HOST_PASS all_pages=4 home_return=1 shoulder=1 legacy_actions=1 multiplayer_confirm=1")
