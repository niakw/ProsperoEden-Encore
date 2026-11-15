#!/usr/bin/env python3
"""Render the real shared loading helper in two independent desktop GL contexts."""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="encore-loading-artwork-egl-") as tmp:
    out = Path(tmp)
    scene = (root / "headless/loading_wordmark.glsl").read_text() + (root / "headless/loading_scene.glsl").read_text()
    (out / "loading_scene_glsl.h").write_text(
        '#pragma once\ninline constexpr const char* kLoadingSceneGlsl = R"glsl(\n'
        + scene + ')glsl";\n')
    binary = out / "loading-artwork-egl"
    subprocess.run(["c++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-pthread", "-I", str(out), "-I", str(root / "headless"),
                    str(root / "tools/loading-artwork-egl-check.cpp"),
                    "-lEGL", "-lGL", "-o", str(binary)], check=True)
    env = dict(os.environ, EGL_PLATFORM="surfaceless", LIBGL_ALWAYS_SOFTWARE="1")
    subprocess.run([str(binary)], check=True, env=env, timeout=60)
