#!/usr/bin/env python3
"""Exact reversible receipt for PS5 shader-cache admission diagnostics.

The historical Vulkan/R23 verified source must not change. This module
accepts ONLY the explicitly reviewed vendor diagnostic blob, removes seven
marked diagnostic-only additions in memory and recovers the prior raw Git blob.
Neither compiler inputs nor immutable R23/P24 receipt hashes are modified.
"""
from __future__ import annotations

import hashlib
import re

OWNER = "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp"
ORIGINAL_BLOB = "6efe1b10862135056c1df1b78007a1c9cb5a9610"
REVIEWED_DIAGNOSTIC_BLOB = "c79131ffafce0e2b33213051ae7a028c3c4ff33d"
OPEN = "ENCORE_PS5_CACHE_DIAG_BEGIN"
CLOSE = "ENCORE_PS5_CACHE_DIAG_END"
BLOCKS = 7
MARKED_BLOCK = re.compile(
    r"(?ms)^[ \t]*// ENCORE_PS5_CACHE_DIAG_BEGIN\n"
    r".*?^[ \t]*// ENCORE_PS5_CACHE_DIAG_END\n"
)


def git_blob(content: str) -> str:
    raw = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def normalize_for_historical_proof(source: str) -> tuple[str, bool]:
    """Return old exact source and whether reviewed diagnostic blocks existed.

    Reject ANY unrelated byte change, marker drift, or missing sentinel.
    The normalized output is only used by source-integrity comparison.
    It must NOT replace the compiled production vendor file.
    """
    current = git_blob(source)
    if OPEN not in source and CLOSE not in source:
        assert current == ORIGINAL_BLOB, (
            "Unknown native Vulkan pipeline owner without diagnostics", current)
        return source, False
    assert current == REVIEWED_DIAGNOSTIC_BLOB, (
        "Unreviewed PS5 shader-cache source; do not waive R23 checks", current)
    assert source.count(OPEN) == source.count(CLOSE) == BLOCKS
    for marker in ("EDEN_PS5_SHADER_CACHE_DISK",
                   "EDEN_PS5_SHADER_CACHE_ADMISSION",
                   "disk_graphics_admitted", "std::filesystem::file_size"):
        assert marker in source, ("Missing PS5 diagnostic contract", marker)
    normalized, count = MARKED_BLOCK.subn("", source)
    assert count == BLOCKS and OPEN not in normalized and CLOSE not in normalized, (
        "PS5 diagnostic boundaries changed", count)
    assert git_blob(normalized) == ORIGINAL_BLOB, (
        "PS5-only diagnostic removal changed original R23 owner")
    return normalized, True
