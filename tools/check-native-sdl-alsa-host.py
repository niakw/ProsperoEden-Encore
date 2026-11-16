#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Host-only contract: PS5 SDL does not probe irrelevant Unix host backends."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
injection = (root / "headless/inject.cmake").read_text(encoding="utf-8")
native = (root / "headless/CMakeLists.txt").read_text(encoding="utf-8")
builder = (root / "tools/build-headless-native.sh").read_text(encoding="utf-8")

before, sep, branch = injection.partition("if(PS5_NATIVE)")
assert sep and "set(SDL_ALSA OFF" not in before
disabled = {
    "SDL_ALSA", "SDL_JACK", "SDL_PIPEWIRE", "SDL_PULSEAUDIO", "SDL_SNDIO",
    "SDL_X11", "SDL_WAYLAND", "SDL_KMSDRM", "SDL_FRIBIDI", "SDL_LIBTHAI",
    "SDL_IBUS", "SDL_LIBUDEV", "SDL_HIDAPI_LIBUSB", "SDL_LIBURING",
}
for option in disabled:
    assert f"set({option} OFF CACHE BOOL " in branch, option
    assert f"set({option} OFF CACHE BOOL " not in before, option
assert branch.index("set(SDL_ALSA OFF") < branch.index('add_subdirectory("${EDEN_WEBP_ROOT}"')
sdl = (root / "vendor/sources/eden-cpm/sdl3/release-3.4.8/CMakeLists.txt").read_text(encoding="utf-8")
for option in disabled:
    assert option in sdl, f"pinned SDL option vanished: {option}"
assert "list(FILTER audio_sources EXCLUDE REGEX \"sink/sdl3_sink" in native
assert "list(REMOVE_ITEM audio_libraries SDL3::SDL3)" in native
assert "list(REMOVE_ITEM audio_definitions HAVE_SDL3)" in native
assert "-DPS5_NATIVE=ON" in builder
print("PASS PS5-only SDL Unix backend selection; native audio/input paths remain selected")
