#!/usr/bin/env python3
"""P1.2/N51: reverse only the audited pre-invalidation GPU memory diff.

A cache unmap must retire the previous backing before any PTE replacement.
The reviewed 4K/big-page source diff restores the exact predecessor blob;
changing both the code and this witness still requires predecessor parity.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools/ns2/p1_2_gpu_preinvalidate.patch"
PREVIOUS_SHA = "b43eae6863527b47b98892f5bfa68b7f685c0b28"
PATCH_SHA = "f778404d0de2bb98e1f68428113b4c4bffe1eafe"
SOURCE = Path("encore-active/eden-core/src/video_core/memory_manager.cpp")

def blob(content: str) -> str:
    data = content.encode()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def recover_prior_memory_manager(actual: str) -> str:
    assert blob(PATCH.read_text()) == PATCH_SHA, "unreviewed GPU pre-invalidation patch"
    assert actual.count("All old mappings have been evicted") == 1
    assert actual.count("Commit big-page backing only after the old cache owner") == 1
    assert actual.count("NeedsRasterizerUnmap(") == 2
    with tempfile.TemporaryDirectory(prefix="encore-preinvalidate-replay-") as tmp:
        target = Path(tmp) / SOURCE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(actual)
        result = subprocess.run(["git", "apply", "--reverse", str(PATCH)],
            cwd=tmp, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        previous = target.read_text()
    assert blob(previous) == PREVIOUS_SHA, "P1.2 predecessor bytes not recovered"
    return previous
