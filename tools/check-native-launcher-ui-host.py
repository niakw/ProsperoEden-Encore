#!/usr/bin/env python3
"""Catch native launcher namespace and AppUpdateInfo aggregate failures on host.

Uses actual checked-in C++ declarations and initializer expressions. The
freestanding host syntax check does not need a PS5 SDK or a complete build.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "headless/main.cpp").read_text()
SERVICES = (ROOT / "headless/prosperoeden/pe/ui/services.hpp").read_text()
LAUNCHER = (ROOT / "headless/prosperoeden/pe/ui/launcher.cpp").read_text()
LIBRARY = (ROOT / "headless/prosperoeden/pe/ui/library.cpp").read_text()

for symbol, header in (
    ("EncoreOverrides", "headless/encore_overrides_generated.h"),
    ("EncoreTextureProfiles", "headless/encore_texture_profiles.h"),
):
    assert f"namespace Eden::{symbol}" in (ROOT / header).read_text()
    assert not re.search(rf"(?<!Eden::)\b{symbol}::", MAIN), (
        "Unqualified native main.cpp namespace", symbol
    )
assert "Eden::EncoreTextureProfiles::ForTitle(launch_title_id, aniso_tier)" in MAIN
assert "Eden::EncoreOverrides::kAuthoredProfileCount" in MAIN

assert "const int base_filter =" not in LIBRARY, "Unused filter snapshot in native UI"
assert "EffectiveGameUpscalingFilter(game_settings_, prefs_, title_id)" in LIBRARY

decl = re.search(r"struct AppUpdateInfo\s*\{[\s\S]*?\n\};", SERVICES)
assert decl, "Native updater aggregate declaration disappeared"
fallbacks = re.findall(
    r"return\s+(\{\s*AppUpdateInfo::State::incompatible[\s\S]*?\});",
    SERVICES,
)
assert len(fallbacks) == 2, "Expected both disconnected updater fallbacks"
offline = re.findall(
    r"state->result\s*=\s*(\{\s*AppUpdateInfo::State::offline[\s\S]*?\});",
    LAUNCHER,
)
assert len(offline) == 1, "Expected detached update worker fallback"

source = (
    "#include <string>\n#include <cstdint>\nnamespace pe::ui {\n"
    + decl.group(0)
    + "\n"
    + "\n".join(
        f"AppUpdateInfo CheckFallback{i}(const std::string& current) "
        f"{{ return {initializer}; }}"
        for i, initializer in enumerate(fallbacks)
    )
    + "\nAppUpdateInfo CheckOffline() { AppUpdateInfo state; "
    f"state = {offline[0]}; return state; }}\n"
    + "}\n"
)
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "Host C++ compiler unavailable"
with tempfile.TemporaryDirectory(prefix="encore-updater-cxx-") as tmp:
    path = Path(tmp) / "check.cpp"
    path.write_text(source)
    done = subprocess.run(
        [compiler, "-std=c++20", "-Wall", "-Wextra",
         "-Wmissing-field-initializers", "-Werror",
         "-fsyntax-only", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    if done.returncode:
        raise AssertionError(done.stderr[-5000:])
print("NATIVE_LAUNCHER_CXX_HOST_PASS actual AppUpdateInfo aggregate, namespaces, filter")
