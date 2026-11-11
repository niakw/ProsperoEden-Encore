#!/usr/bin/env python3
"""Strict reconstruction of the reviewed NS2/R2 Vulkan vendor overlays.

The production R2 staging and GPU-retirement blocks stay enabled. This
isolated source oracle subtracts only fixed, byte-exact insertions from a
SHA-pinned live owner for historic F07 generator parity.
"""
import ast
from pathlib import Path
import subprocess

def normalized(root: Path, name: str) -> str:
    assert name in ("vk_buffer_cache_cost.cpp",
                    "include/video_core/renderer_vulkan/vk_buffer_cache.h")
    oracle = ast.parse((root / "tools/check-vendored-vulkan-fork.py").read_text())
    declarations = [
        n for n in ast.walk(oracle)
        if isinstance(n, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "r2_replacements"
            for target in n.targets
        )
    ]
    assert len(declarations) == 1, "R2 normalizer declaration drift"
    recipes = ast.literal_eval(declarations[0].value)
    assert set(recipes) == {
        "vk_buffer_cache_cost.cpp",
        "include/video_core/renderer_vulkan/vk_buffer_cache.h"
    }
    expected_sha, edits = recipes[name]
    assert len(edits) == (4 if name == "vk_buffer_cache_cost.cpp" else 5)
    owner = root / "vendor/encore-active/eden-vulkan" / name
    sha = subprocess.check_output(
        ["git", "hash-object", str(owner)], text=True).strip()
    assert sha == expected_sha, ("unreviewed production R2 owner drift", name, sha)
    content = owner.read_text()
    for start, terminator in edits:
        start = start.replace("\\n", "\n")
        terminator = terminator.replace("\\n", "\n")
        assert content.count(start) == 1, ("R2 delimiter drift", name, start)
        position = content.index(start)
        end = content.find(terminator, position)
        assert end >= 0, ("R2 terminator missing", name)
        end += len(terminator)
        content = content[:position] + content[end:]
    if name == "vk_buffer_cache_cost.cpp":
        inc = '#include "video_core/renderer_vulkan/vk_buffer_cache.h"\n'
        after = '#include "video_core/renderer_vulkan/maxwell_to_vk.h"'
        assert content.count(inc + after) == 1, "R2 include whitespace drift"
        content = content.replace(inc + after, inc + "\n" + after, 1)
    return content
