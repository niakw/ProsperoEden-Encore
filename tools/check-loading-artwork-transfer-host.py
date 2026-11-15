#!/usr/bin/env python3
"""Host tests for the shared Encore artwork transfer; no GPU or native package."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    binary = Path(tmp) / "loading-artwork-transfer"
    for optimization in ("-O0", "-O2"):
        subprocess.run(["c++", "-std=c++20", optimization, "-Wall", "-Wextra",
                        "-Werror", "-pedantic", "-pthread", "-I", str(root / "headless"),
                        str(root / "tools/loading-artwork-transfer-check.cpp"),
                        "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
        print("ENCORE_LOADING_ARTWORK_TRANSFER_PASS", optimization, "host_only=1")
