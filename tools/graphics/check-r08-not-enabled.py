#!/usr/bin/env python3
"""Fail-closed R08 packaging guard until native GPU / HUD / licensing signoff.

This is intentionally a source-level assertion, not proof of GPU correctness.
Change this check only together with an actual approved native runtime test.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
cmake = (root / "headless/vulkan.cmake").read_text()
settings = (root / "headless/prosperoeden/pe/ui/settings.cpp").read_text()
game_settings = (root / "headless/prosperoeden/pe/ui/library.cpp").read_text()
roadmap = (root / "docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md").read_text()
contract = (root / "extras/graphics/mihawk_native_surface_contract.h").read_text()
encoder = (root / "headless/mihawk_vulkan_encoder.cpp").read_text()

assert re.search(
    r'option\(EDEN_BUILD_MIHAWKGEN_CORE\s+"[^"]*"\s+OFF\)',
    cmake), "Unreviewed MihawkGen build setting default changed"
assert "add_library(eden-mihawkgen-core OBJECT" in cmake
assert "target_link_libraries(video_core PRIVATE eden-mihawkgen-core)" not in cmake
assert "target_link_libraries(eden-headless PRIVATE eden-mihawkgen-core)" not in cmake
assert "target_sources(video_core PRIVATE $<TARGET_OBJECTS:eden-mihawkgen-core>)" not in cmake
assert "kFramegenUnavailable" in settings
assert 'TR("Frame generation")' in settings
assert 'tr("Off")' in settings
assert "option_ == video_frame_generation" in settings
assert "row_frame_generation" in game_settings
assert "if (option_ == row_frame_generation)" in game_settings
assert "say(tr(kFramegenUnavailable), true);" in game_settings
assert 'TR("Frame generation")' in game_settings
assert "if (!x.hud_isolated)" in contract
assert "if (!x.history_descriptor_slots_fenced)" in contract
assert "ValidateNativeMihawkPair(generate)" in encoder
assert "C / R08" in roadmap or "**R08**" in roadmap
print("R08 RELEASE GATE PASS: no runtime link, no selectable frame generation")
