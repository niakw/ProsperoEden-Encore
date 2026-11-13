#!/usr/bin/env python3
"""Fail on regressions reported by the 13 Nov native PS5 UI test.

Source-only gates; they cannot prove the PS5 Media Gallery mount is readable.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda name: (ROOT / name).read_text(encoding="utf-8")
service = read("headless/prosperoeden/eden_services.cpp")
widgets = read("headless/prosperoeden/pe/ui/widgets.cpp")
launcher = read("headless/prosperoeden/pe/ui/launcher.cpp")

capture = service.split("std::vector<SystemWallpaper> SystemCaptureWallpapers()", 1)[1].split("#endif", 1)[0]
gallery = service.split("std::vector<std::string> EdenServices::wallpapers()", 1)[1].split("std::string EdenServices::wallpaper_path(", 1)[0]
caption = service.split("std::string EdenServices::daily_wallpaper_caption(", 1)[1].split("const std::vector<std::string>& EdenServices::resolution_labels()", 1)[0]
chooser = widgets.split("float chooser(Canvas &c,", 1)[1].split("// ---------------------------------------------------------------- controller hints", 1)[0]
nav = launcher.split("void Launcher::draw_top_nav(", 1)[1].split("void Launcher::", 1)[0]
draw = launcher.split("void Launcher::draw(gfx::DrawList &list)", 1)[1]
pre_modal = draw.split("if (modal_shown_ != Modal::none)", 1)[0]
post_modal = draw.split("if (modal_shown_ != Modal::none)", 1)[1]

assert "kMaxEntries = 32768" in capture and "kMaxDepth = 8" in capture
assert "S_ISLNK(native.st_mode)" in capture and "ReadNativeDirectory" in capture
assert "for (const auto& capture : captures)" in gallery
assert "i < 64u" not in gallery
assert "names.size() - captures.size()" in gallery
assert "CheckedWallpaper(capture.photo.parent_path()" in service
assert "text_shrink(c, value, right - arrow, baseline, size" in chooser
assert "285.0f - arrow, Align::right" in chooser
assert "nav_opacity = std::clamp(look().panel_opacity" in nav
assert "theme::kPanel.with_alpha(nav_opacity)" in nav
assert "Color::rgb(0x301446, nav_opacity)" in nav
assert "Unknown" not in caption
assert "(source.empty() ? \"\" : \" · \" + source)" in caption
assert "cached_daily_wallpaper_caption_" in pre_modal
assert "(screen_ != Screen::home || !prefs_.show_game_background)" in pre_modal
assert "text_shrink(c, cached_daily_wallpaper_caption_" not in post_modal
print("PS5_GALLERY_OPACITY_CREDIT_HOST_PASS no_gallery_64_cap=1 caption_behind_modal=1 chooser_bounded=1")
