#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Host-only contract: native PS5 never probes ALSA, other targets unchanged."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
injection = (root / "headless/inject.cmake").read_text(encoding="utf-8")
native = (root / "headless/CMakeLists.txt").read_text(encoding="utf-8")
builder = (root / "tools/build-headless-native.sh").read_text(encoding="utf-8")

before, sep, branch = injection.partition("if(PS5_NATIVE)")
assert sep and "set(SDL_ALSA OFF" not in before
assert 'set(SDL_ALSA OFF CACHE BOOL "PS5 uses the native audio backend, not Linux ALSA" FORCE)' in branch
assert branch.index("set(SDL_ALSA OFF") < branch.index('add_subdirectory("${EDEN_WEBP_ROOT}"')
assert "list(FILTER audio_sources EXCLUDE REGEX \"sink/sdl3_sink" in native
assert "list(REMOVE_ITEM audio_libraries SDL3::SDL3)" in native
assert "list(REMOVE_ITEM audio_definitions HAVE_SDL3)" in native
assert "-DPS5_NATIVE=ON" in builder
print("PASS PS5-only SDL ALSA selection; native sink remains installed")
