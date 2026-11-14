#!/usr/bin/env python3
"""Source geometry contract for original-drawn Switch-style console shell."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
src=(root/"headless/prosperoeden/pe/ui/switch_theme.cpp").read_text()
for line in (
    "kSwitchHomeTileSize = 384.0f;",
    "kSwitchHomeTilePitch = 405.0f;",
    "kSwitchHomeTileX = 160.5f;",
    "kSwitchHomeTileY = 291.0f;",
    "kSwitchLibraryTileSize = 261.0f;",
    "kSwitchLibraryTilePitch = 276.0f;",
    "kSwitchLibraryTileX = 138.0f;",
    "kSwitchLibraryTileY = 278.0f;",
    "constexpr int kHomeShortcuts = 6;",
    "555.0f+162.0f*float(i),y=816.0f;",
    "void Launcher::draw_switch_header",
    "constexpr float px=136.5f,py=98.0f;",
    "void Launcher::draw_switch_footer",
    "void Launcher::draw_switch_library",
    "void Launcher::draw_switch_settings",
    "void Launcher::draw_switch_dialog",
):
    assert line in src, f"reference console geometry missing: {line}"
assert "switch_game_tile(c,item.tile_icon.empty()?item.cover:item.tile_icon,item.title,box,i)" in src
assert "const Cover avatar=profile_avatar_path_.empty()?Cover{}:" in src
assert "case 5: { // Power glyph" in src
assert "std::clamp(current+delta,kHomeShortcutFirst," in src
assert "switch_home_last_tile_=current;" in src
assert "switch_home_focus_=last==kHomeAllSoftware||last>=count?" in src
assert "press_library(key);" in src, "Switch game launch must respect core validation"
# P3: the alternate theme must not display an empty-ROM error while the
# initial asynchronous scan is still pending (same rule as standard shell).
switch_library = src.split("void Launcher::draw_switch_library(Canvas& c) {", 1)[1].split(
    "void Launcher::draw_switch_game(", 1
)[0]
assert switch_library.index("if(!games_loaded_) {") < switch_library.index("if(count==0) {")
assert switch_library.index('tr("Loading game library...")') < switch_library.index(
    'tr("No ROM files found.")'
)
assert "void Launcher::draw_switch_confirmation" in src
assert "switch_value(services_.resolution_labels(),prefs_.resolution)" in src
assert "switch_value(services_.filter_labels(),prefs_.filter)" in src
assert "switch_value(services_.anti_aliasing_labels(),prefs_.anti_aliasing)" in src
assert "switch_value(services_.performance_profile_labels(),prefs_.performance_profile)" in src
preview=(root/"headless/prosperoeden/host/preview_main.cpp").read_text()
assert "06-switch-exit-confirm" in preview
assert "Key::right, Key::right, Key::right, Key::right," in preview
assert "if(modal_==Modal::none && confirmation_==Confirmation::none && !message_.empty())" in src
assert "if(modal_==Modal::none && confirmation_==Confirmation::none && !feedback.empty())" in src
assert "void Launcher::draw_switch_confirmation" in src, "native confirmation must be themed"
assert "stock_assets.hpp" not in src, "firmware-extracted UI atlas must not be imported"
print("SWITCH_UI_GEOMETRY_AND_ASSET_ISOLATION: PASS")

assert "void Launcher::draw_switch_game(Canvas& c,float opened)" in src
assert "void Launcher::draw_switch_mods(Canvas& c,float opened)" in src
assert "void Launcher::draw_switch_mapping(Canvas& c,float opened)" in src
assert "VideoPresetForTitle(id" in src

preview=(root/"headless/prosperoeden/host/preview_main.cpp").read_text()
for filename in ("07-switch-game-options","08-switch-game-mods","09-switch-button-mapping"):
    assert filename in preview

assert '!message.empty()&&warn?' in src, "stale confirmation must not tint normal modal hint red"
assert 'text_shrink(c,tr("Back"),1230.0f' in src

# The visual mapping must use the effective mapped pad (not a fixed platform
# face glyph), and custom profiles must not be mislabeled as defaults.
assert "switch_profile_name(int layout,const ButtonMapping& mapping)" in src
assert "switch_profile_name(g.controller_layout" in src
assert "switch_physical_pad(mapped)" in src
assert "const Pad icon=switch_physical_pad(mapped);" in src
assert "draw_pad(c,icon,1035.0f" in src
assert "if(mapped>=4)" in src, "shoulder/system glyphs need a dark backing on white"
assert "settings_.wrap=false;" in src
assert "settings_.wrap=original_wrap;" in src
assert 'text_shrink(c,tr("Select"),1024.0f' in src

mapping=(root/"headless/prosperoeden/pe/ui/mapping.cpp").read_text()
assert "screen_ == Screen::home" in mapping
assert "close_modal();" in mapping
assert "10-switch-mods-installed" in preview
assert "11-switch-mod-enabled" in preview

assert "text_block(c,message.empty()?tr(fallback):message" in src
assert "418.0f,2,kShrink" in src

# R457: contextual help survives ordinary save feedback in both themes.
settings=(root/"headless/prosperoeden/pe/ui/settings.cpp").read_text()
dialog=settings.split("void Launcher::draw_dialog(",1)[1]
assert "const bool compact_success = contextual_guide &&" in dialog
assert "(message_.empty() || compact_success)" in dialog
assert "if (modal == Modal::video && show_contextual_guide)" in dialog
assert "if (show_contextual_guide && (modal == Modal::controls ||" in dialog
assert "if (!message_.empty() && !compact_success)" in dialog
switch_dialog=src.split("void Launcher::draw_switch_dialog(",1)[1].split("void Launcher::press_switch_settings(",1)[0]
assert "if (modal==Modal::video && option_>=0 && option_<=12)" in switch_dialog
assert "switch_video_help(c,tr(labels[option_]),guides,inactive,744.0f)" in switch_dialog
assert "text_block(c,message_,493.0f,213.0f" in switch_dialog
assert "total-visible" in switch_dialog
assert 'TR("Panel opacity"), TR("Background motion")' in switch_dialog
assert 'case 16: value = std::to_string(prefs_.panel_opacity)+"%";' in switch_dialog
assert 'case 19: value = prefs_.show_game_background?' in switch_dialog
print("R457_SETTINGS_GUIDE_SOURCE_PASS")

# R457: per-title row descriptions must not depend on an empty success toast.
library=(root/"headless/prosperoeden/pe/ui/library.cpp").read_text()
game=library.split("void Launcher::draw_game(",1)[1].split("// ---------------------------------------------------------------- a game's mods",1)[0]
assert "const bool compact_game_success = !message_.empty() && !message_warning_ &&" in game
assert "option_ >= row_mode && option_ < row_controls;" in game
assert "if (!message_.empty() && !compact_game_success)" in game
assert "compact_game_success ? 405.0f : 736.0f" in game
assert "if (compact_game_success)" in game
assert "DrawVideoGuide(c, tr(kLabels[option_]), explanation," in game
per_game=src.split("void Launcher::draw_switch_game(",1)[1].split("void Launcher::draw_switch_mods(",1)[0]
assert "(message_.empty() || !message_warning_) && option_>=0 && option_<14" in per_game
assert "constexpr Rect kGameClip{530.0f,302.0f,861.0f,402.0f};" in per_game
assert "d.push_clip(kGameClip);" in per_game
assert "switch_video_help(c,tr(names[option_]),guide,inactive,708.0f)" in per_game
assert "advanced_status(c,message_,message_warning_" in per_game
import re
def guide_keys(source):
    body=source.split("kGameAbout = {{",1)[1].split("}};",1)[0]
    return re.findall(r'TR\("([^"]+)"\)',body)
assert len(guide_keys(game))==14
assert guide_keys(game)==guide_keys(per_game)
# Four rows fit the reserved clip; the guide sits after it and before
# the footer text baseline. The actual preview separately renders both skins.
assert 318 + 3*96 + 92 <= 302 + 402 <= 708
assert 708 + 124 <= 831 + (39-18)/2
print("R457_PER_GAME_GUIDANCE_SOURCE_PASS rows=14 routine_feedback=independent clip=separate")
