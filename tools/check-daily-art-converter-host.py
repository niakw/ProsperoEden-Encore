#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Host-only ImageMagick 6/7 selection checks: no network, image SDK or PS5 build."""
from pathlib import Path
import runpy
import subprocess
import tempfile
from unittest.mock import patch
import shutil

module = runpy.run_path(str(Path(__file__).resolve().parent / "launcher/fetch_daily_switch.py"))
convert_art = module["convert_art"]

def exercise(programs, expected_convert, expected_identify):
    seen = []
    def which(name):
        return f"/fake/{name}" if name in programs else None
    def identify(command, **kwargs):
        seen.append(command)
        return "1280 720"
    def convert(command, **kwargs):
        seen.append(command)
        payload = b"VP8 " + b"X" * 4092
        Path(command[-1]).write_bytes(
            b"RIFF" + (len(payload) + 4).to_bytes(4, "little") + b"WEBP" + payload)
    with tempfile.TemporaryDirectory() as tmp:
        src, target = Path(tmp) / "source.jpg", Path(tmp) / "target.webp"
        src.write_bytes(b"fixture")
        with patch.object(shutil, "which", side_effect=which), \
             patch.object(subprocess, "check_output", side_effect=identify), \
             patch.object(subprocess, "run", side_effect=convert):
            convert_art(src, target)
        assert target.stat().st_size == 4096
    assert seen[0][:len(expected_identify)] == expected_identify, seen[0]
    assert seen[1][0] == expected_convert, seen[1]
    assert "-auto-orient" in seen[1] and "-strip" in seen[1], seen[1]
    assert "-flip" not in seen[1] and "-flop" not in seen[1], seen[1]
    assert "webp:method=5" in seen[1] and "webp:lossless=false" in seen[1]
    assert "-interlace" not in seen[1], "JPEG-only settings leaked into WebP"

exercise({"magick", "convert", "identify"}, "/fake/magick", ["/fake/magick", "identify"])
exercise({"convert", "identify"}, "/fake/convert", ["/fake/identify"])
with patch.object(shutil, "which", return_value=None):
    try:
        convert_art(Path("/missing"), Path("/also-missing"))
    except RuntimeError as e:
        assert "ImageMagick" in str(e)
    else:
        raise AssertionError("missing conversion tools accepted")
# No promotional game-art downloads or assets without explicit opt-in.
# The launcher preference is separately off by default and only the Daily
# background path schedules the asynchronous local catalog lookup.
root = Path(__file__).resolve().parents[1]
pack = (root / "tools/package-headless-native.sh").read_text()
settings = (root / "headless/settings_store.h").read_text()
launcher = (root / "headless/prosperoeden/pe/ui/launcher.cpp").read_text()
generator = (root / "tools/launcher/fetch_daily_switch.py").read_text()
service = (root / "headless/prosperoeden/eden_services.cpp").read_text()
assert 'EDEN_BAKE_DAILY_SWITCH_ART:-0' in pack
assert 'rm -rf "$app/ui/art/daily"' in pack
assert 'int background_style = 0;' in settings
assert 'if (value.background == 5)' in launcher
assert 'MAX_ITEMS = 8' in generator
assert 'if (candidates.size() > 8) candidates.resize(8);' in service
assert 'ext == ".tga" || ext == ".webp"' in service
print("PASS zero-default daily art, eight newest WebPs, user import exception")

print("PASS ImageMagick 7 and Ubuntu ImageMagick 6 conversion tool selection")
