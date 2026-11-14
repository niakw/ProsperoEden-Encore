#!/usr/bin/env python3
"""Host-only guard: all graphical extras are displayed and remain opt-in.

This checks the alternate Switch presentation against the real shared
settings dialog row contracts; the latter are not switched by theme.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
read = lambda name: (root / name).read_text(encoding="utf-8")
switch = read("headless/prosperoeden/pe/ui/switch_theme.cpp")
settings = read("headless/prosperoeden/pe/ui/settings.cpp")
game = read("headless/prosperoeden/pe/ui/library.cpp")
store = read("headless/settings_store.h")
service = read("headless/prosperoeden/pe/ui/services.hpp")
generated = read("headless/encore_overrides_generated.h")
policy = read("headless/neural_video_policy.h")

assert "return kVideoRows;" in settings
assert "video_neural_status" in settings and "video_neural_strength" in settings
assert "return services_.save_transfer_available() ? 16 : 15;" in settings
assert "row_save, // in builds that move saves" in game
assert "row_neural_status" in game and "row_neural_strength_preset" in game
assert 'TR("Neural Rendering"), TR("Intensité DLSS-NR")' in game

assert "const std::array<std::string,16> values={" in switch
assert "if(i<0||i>=16)continue;" in switch
assert 'fallback(g.neural_mode,NeuralModeName' in switch
assert 'fallback(g.neural_strength,std::to_string' in switch
assert 'option_==15?TR("Import"):' in switch
assert 'option_==14?TR("Open")' in switch
assert "case 9:value=NeuralModeName(prefs_.neural_mode)" in switch
assert 'case 10:value=std::to_string(prefs_.neural_strength)+"%"' in switch
assert 'case 11:value=prefs_.refresh' in switch

game_block = switch.split("void Launcher::draw_switch_game(", 1)[1].split(
    "void Launcher::draw_switch_mods(", 1
)[0]
names = re.search(r"static constexpr const char\* names\[\]\s*=\s*\{(.*?)\};", game_block, re.S)
assert names is not None, "Switch game row labels absent"
assert len(re.findall(r'TR\("', names.group(1))) == 16, "Switch game labels count drift"

global_block = switch.split("case Modal::video: {", 1)[1].split(
    "case Modal::controls:", 1
)[0]
labels = re.search(r"static constexpr const char\* labels\[\]\s*=\s*\{(.*?)\};", global_block, re.S)
assert labels is not None, "Switch global video row labels absent"
assert len(re.findall(r'TR\("', labels.group(1))) == 13, "Switch global labels count drift"
# All global video rows now retain their contextual guide, including extras.
assert "modal==Modal::video && option_>=0 && option_<=12" in switch
guide_block = switch.split("modal==Modal::video && option_>=0 && option_<=12", 1)[1].split("if (guides)", 1)[0]
for row in range(13):
    assert f"option_=={row})" in guide_block, f"Switch global guide missing row {row}"

assert "option_>=5 && option_<=11" in switch

assert 'int frame_generation = 0;' in store
assert "int neural_mode = NeuralVideo::kOff;" in store
assert "int neural_strength = 100;" in store
assert 'int frame_generation = 0;' in service
assert 'int neural_mode = 0;' in service
assert "kModeCount=6;" in policy
assert "int filter = Eden::EncoreOverrides::kGeneralProfiles[1].filter;" in service
assert "int texture_anisotropy = Eden::EncoreTextureProfiles::ForTitle(0,1);" in service
assert "{1, 1, 4, 1, 50, 1, 0, true}" in generated, "compiled Recommended FSR1 missing"
assert 'NeuralModeGuide' in switch and 'NeuralStrengthGuide' in switch
print("GRAPHICS_EXTRAS_UI_DEFAULTS_PASS global_rows=13 game_rows=15_or_16 NR=5 FG=3 defaults=off")
