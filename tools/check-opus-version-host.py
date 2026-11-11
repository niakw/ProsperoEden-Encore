#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Guard the exact Opus snapshot identity without modifying bundled sources.

The PS5 OpenGL/native dependency configure is expensive. This check only
validates the early, PS5-specific CMake override and the metadata format.
It does not assert that a full native configure has executed.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "headless/inject.cmake").read_text(encoding="utf-8")
pin_path = (
    "vendor/sources/eden-cpm/opus/a3f0ec02b3/"
    "cmake/OpusPackageVersion.cmake"
)
version = "1.6.1-6-ga3f0ec02b342"

# PS5 only. The supplied variable must be scoped to the documented
# snapshot; if its path changes in a newer vendor, the override disappears.
assert text.count("if(PS5_NATIVE)") == 1
assert text.count(pin_path) == 1
assert text.count('set(OPUS_PACKAGE_VERSION "' + version + '")') == 1
ps5_start = text.index("if(PS5_NATIVE)")
opus_at = text.index("set(OPUS_PACKAGE_VERSION")
assert ps5_start < opus_at < text.index('set(EDEN_WEBP_ROOT')
assert 'set(OPUS_PACKAGE_VERSION "' + version + '" CACHE' not in text
assert "if(EXISTS " in text[ps5_start:opus_at]
assert "a3f0ec02b342" in text[ps5_start:opus_at]

# A pinned development snapshot must never falsely advertise itself as
# the v1.6.1 release, and project(VERSION) must still get 1.6.1.
assert re.fullmatch(r"1\.6\.1-[1-9]\d*-g[0-9a-f]{12}", version)
cmake = shutil.which("cmake")
assert cmake, "cmake is required on the Ubuntu host runner"
with tempfile.TemporaryDirectory(prefix="encore-opus-version-") as temp:
    script = Path(temp) / "test.cmake"
    script.write_text(
        'cmake_minimum_required(VERSION 3.16)\n'
        + f'set(OPUS_PACKAGE_VERSION "{version}")\n'
        + f'string(REGEX REPLACE "^([0-9]+[.][0-9]+([.][0-9]+)?).*" "\\\\1" OPUS_PROJECT_VERSION "{version}")\n'
        + 'if(NOT OPUS_PROJECT_VERSION STREQUAL "1.6.1")\n'
        + '  message(FATAL_ERROR "Opus numeric project version wrong")\n'
        + 'endif()\n',
        encoding="utf-8",
    )
    check = subprocess.run([cmake, "-P", str(script)], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
print("PASS pinned Opus git-describe identity and PS5-only CMake scope")
