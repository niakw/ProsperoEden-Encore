#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pair engine selection with vendor #192/#193 P0 source contracts."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text(encoding="utf-8")

tests = (
    ROOT / "vendor/tests/ns2_a64_v81_v85_source.py",
    ROOT / "vendor/tests/ns2_alias_64g_upstream_parity_host.py",
)
for test in tests:
    assert test.is_file(), test
    result = subprocess.run([sys.executable, str(test)], cwd=ROOT,
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        print(result.stdout[-3000:], file=sys.stderr)
        print(result.stderr[-5000:], file=sys.stderr)
        raise SystemExit(result.returncode)

assert 'set_property(SOURCE "${EDEN_MAINTAINED_SCALAR_TRANSLATOR}"' in CMAKE
scope = CMAKE.split('set_property(SOURCE "${EDEN_MAINTAINED_SCALAR_TRANSLATOR}"', 1)[1].split(')', 1)[0]
assert '"EDEN_NS2_A64_V81_V85=1"' in scope
assert 'target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85' not in CMAKE
assert 'EDEN_NS2_A64_EXPERIMENTAL' not in CMAKE

# Current-upstream parity from vendor #193: 64 GiB alias => upper-half 32 GiB VAMM.
addr = (ROOT / "vendor/encore-active/ns2-runtime/kernel/core/hle/kernel/k_address_space_info.cpp").read_text()
assert "0x1000000000" in addr or "64_GiB" in addr or "64 GiB" in addr
assert "0x2000000000" not in addr, "unmerged 128GiB alias propagation returned"

print("NS2_VENDOR_P0_PROMOTIONS_ENGINE_PAIR_PASS a64_v81_v85=1 alias64_vamm32=1")
print("Host/source proof only; PS5 first-frame and PC=0x4 remain unverified")
