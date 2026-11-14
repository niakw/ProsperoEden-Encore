#!/usr/bin/env python3
"""Strict source receipt for the reviewed PS5 G21 GPU shutdown lifetime fix.

The five historical G21 CMake/source parity oracles are kept immutable.
A vendor PR #112 candidate is normalized IN MEMORY solely for historical
source comparison, never for production native C++ compilation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

OLD = {
    "gpu_vulkan.cpp": "8d43de2a7176f90c294e91a9dfcd6c0647292211",
    "gpu_gl_native.cpp": "ccd81a7930d129b2f3b35fd0a21217e4fd9d78f9",
    "gpu_gl_host.cpp": "0a1585073fa44e2500269ea275bac4f1b6002dbb",
    "gpu_gl_native_dev.cpp": "8ce31eb1c997c88b46a35be501e8c171d6473073",
    "gpu_gl_host_dev.cpp": "7beae3b46e921f160e7bbc8fd43b9d97d333106b",
}
REVIEWED = {
    "gpu_vulkan.cpp": "186be29abbb51e199cc52bf85e5bad938587b89e",
    "gpu_gl_native.cpp": "87edefe7cc5d8da45ca0797257e71e81f87175a9",
    "gpu_gl_host.cpp": "33fc3039d52a568585b7aa84cdf7e097aa339def",
    "gpu_gl_native_dev.cpp": "856f3259bb29cb07822c14f83819ebd10aaba647",
    "gpu_gl_host_dev.cpp": "848ead02e3b128c498e0ac08232d391f6b8b4085",
}
OLD_VULKAN = "    ~Impl() = default;\n\n"
OLD_OPENGL = (
    "    ~Impl() { gpu_thread.Stop(); if (renderer && Settings::IsOpenGL()) "
    "{ renderer->Context().MakeCurrent(); glFinish(); } }\n\n"
)
START = "    ~Impl() {"
NEXT_OWNER = "    std::shared_ptr<Control::ChannelState> CreateChannel("

def git_blob(source: str) -> str:
    raw = source.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

def normalize_g21_shutdown_source(filename: str, source: str) -> tuple[str, bool]:
    """Accept EXACT old or new Git blob and reconstruct prior byte-for-byte."""
    if filename not in OLD:
        raise AssertionError(("Unrecognized G21 source owner", filename))
    current = git_blob(source)
    if current == OLD[filename]:
        return source, False
    assert current == REVIEWED[filename], (
        "Unreviewed selected G21 source drift; never relax old oracle",
        filename, current)
    assert source.count(START) == 1 and source.count(NEXT_OWNER) == 1
    first = source.index(START)
    last = source.index(NEXT_OWNER, first)
    updated_destructor = source[first:last]
    for marker in ("NotifyShutdown();", "gpu_thread.Stop();", "renderer.reset();"):
        assert updated_destructor.count(marker) == 1, (filename, marker)
    assert updated_destructor.index("NotifyShutdown();") < updated_destructor.index(
        "gpu_thread.Stop();") < updated_destructor.index("renderer.reset();")
    if filename != "gpu_vulkan.cpp":
        for marker in ("renderer->Context().MakeCurrent();", "glFinish();"):
            assert updated_destructor.count(marker) == 1, (filename, marker)
        assert updated_destructor.index("glFinish();") < updated_destructor.index(
            "renderer.reset();")
    else:
        assert "glFinish();" not in updated_destructor
    assert source.index("std::unique_ptr<VideoCore::RendererBase> renderer;") < source.index(
        "::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;")
    assert source.index("::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;") < source.index(
        "VideoCommon::GPUThread::ThreadManager gpu_thread;")
    historic = OLD_VULKAN if filename == "gpu_vulkan.cpp" else OLD_OPENGL
    restored = source[:first] + historic + source[last:]
    assert git_blob(restored) == OLD[filename], (
        "Reviewed GPU shutdown normalization changed historical G21 owner", filename)
    return restored, True
