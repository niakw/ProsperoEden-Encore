#!/usr/bin/env python3
"""Reverse ONLY the exact reviewed native GPU range-cache diff.

The previous N51/P1.2 reviewers must still recover the identical pre-cache
memory manager. No history is rewritten and no unrelated drift is ignored.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools/ns2/p1_2_gpu_contiguous_range_cache.patch"
SOURCE = Path("encore-active/eden-core/src/video_core/memory_manager.cpp")
BEFORE = "b018babb791e0a72a042abeb56dc6f4587ba557b"
AFTER = "f36837c70435a919fd8d51b46983707c634039cc"

def blob(text: str) -> str:
    content = text.encode()
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()

def recover_before_contiguous_cache(actual: str) -> str:
    assert blob(actual) == AFTER, "unreviewed native GPU memory source drift"
    assert actual.count("gpu_page_table_revision.fetch_add(1, std::memory_order_release)") == 4
    assert actual.count("thread_local std::array<Entry, 64> cache{};") == 1
    with tempfile.TemporaryDirectory(prefix="eden-gpu-range-reverse-") as tmp:
        target = Path(tmp) / SOURCE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(actual)
        result = subprocess.run(["git", "apply", "--reverse", str(PATCH)],
                                cwd=tmp, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        original = target.read_text()
    assert blob(original) == BEFORE, "native GPU cache patch changed unrelated source"
    return original
