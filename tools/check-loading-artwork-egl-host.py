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
    # Link a second TU which resolves glCreateProgram through a GLAD-like
    # nullable pointer. Before the loading dispatch fix, its weak inline
    # Build() could be selected for the direct-GL launcher at link time.
    mock = out / "loading-mock-glad.cpp"
    mock.write_text(r'''#define GL_GLEXT_PROTOTYPES 1
#include <GL/glcorearb.h>
namespace { PFNGLCREATEPROGRAMPROC mock_glad_create_program = nullptr; }
#define glCreateProgram mock_glad_create_program
#include "loading_artwork_gl.hpp"
#undef glCreateProgram
extern "C" bool LoadingMockGladDraw(int width, int height, double seconds) {
    mock_glad_create_program = &glCreateProgram;
    Eden::LoadingArtwork::GlPresenter presenter;
    const bool drawn = presenter.Draw(width, height, seconds);
    presenter.Release();
    mock_glad_create_program = nullptr;
    return drawn;
}
''')
    binary = out / "loading-artwork-egl"
    subprocess.run(["c++", "-std=c++20", "-O0", "-fno-inline", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-pthread", "-I", str(out), "-I", str(root / "headless"),
                    str(mock), str(root / "tools/loading-artwork-egl-check.cpp"),
                    "-lEGL", "-lGL", "-o", str(binary)], check=True)
    env = dict(os.environ, EGL_PLATFORM="surfaceless", LIBGL_ALWAYS_SOFTWARE="1")
    subprocess.run([str(binary)], check=True, env=env, timeout=60)
