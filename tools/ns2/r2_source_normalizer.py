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
    owner = root / "vendor/encore-active/eden/src/video_core/renderer_vulkan" / name
    sha = subprocess.check_output(
        ["git", "hash-object", str(owner)], text=True).strip()
    content = owner.read_text()
    if name == "include/video_core/renderer_vulkan/vk_buffer_cache.h":
        # R23 #49's guarded descriptor-buffer texel view follows the
        # historical R2 ABI. Reverse this single exact checked source
        # addition before reconstructing R2's frozen generator parity.
        assert sha == "76228c0ed7cdb2c2cfa02a473c59365c46e9a466", (
            "unreviewed R23 production texel owner drift", name, sha)
        updated = (
            "        // In descriptor-buffer mode there is no VkBufferView: creating one\n"
            "        // before checking a missing address can attempt SurfaceFormat(255).\n"
            "        // Match Eden upstream 3e6a5566 while keeping legacy views intact.\n"
            "        if (guest_descriptor_queue.UsesDescriptorBuffer()) {\n"
            "            const VkDeviceAddress address = buffer.DeviceAddress();\n"
            "            const VkFormat vk_format = address == 0 ? VK_FORMAT_UNDEFINED : TexelBufferFormat(format);\n"
            "            guest_descriptor_queue.AddTexelBuffer(VK_NULL_HANDLE, address, offset, size, vk_format);\n"
            "        } else {\n"
            "            guest_descriptor_queue.AddTexelBuffer(buffer.View(offset, size, format));\n"
            "        }")
        former = (
            "        guest_descriptor_queue.AddTexelBuffer(buffer.View(offset, size, format),\n"
            "                                              buffer.DeviceAddress(), offset, size,\n"
            "                                              TexelBufferFormat(format));")
        assert content.count(updated) == 1
        content = content.replace(updated, former, 1)
        import hashlib
        raw = content.encode("utf-8")
        sha = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    if name == "vk_buffer_cache_cost.cpp" and sha == (
        "873b5552b429f42294c8d410070df0572b4ff84c"
    ):
        lut_candidates = []
        for node in ast.walk(oracle):
            if not isinstance(node, ast.For) or not isinstance(node.target, ast.Tuple):
                continue
            if [t.id if isinstance(t, ast.Name) else None for t in node.target.elts] != [
                "after", "before"
            ]:
                continue
            try:
                inverses = ast.literal_eval(node.iter)
            except (ValueError, SyntaxError, TypeError):
                continue
            if (isinstance(inverses, list) and len(inverses) == 3 and
                    all(isinstance(p, list) and len(p) == 2 and
                        all(isinstance(v, str) for v in p) for p in inverses) and
                    "Lichii #414" in inverses[1][0] and
                    "retired_buffers" in inverses[2][0]):
                lut_candidates.append(inverses)
        assert len(lut_candidates) == 1, "Quad LUT provenance recipe drift"
        for revised, historical in lut_candidates[0]:
            assert content.count(revised) == 1, "Selected quad LUT source hunk drift"
            content = content.replace(revised, historical, 1)
        import hashlib
        raw = content.encode("utf-8")
        sha = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw
        ).hexdigest()
        assert sha == expected_sha, (
            "Selected quad LUT predecessor is not frozen R2 owner", sha)
    assert sha == expected_sha, ("unreviewed production R2 owner drift", name, sha)
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
