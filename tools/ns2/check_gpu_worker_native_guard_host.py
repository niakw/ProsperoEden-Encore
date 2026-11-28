#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Guard selected native GPU-worker diagnostic code against silent macro exclusion.

This is a source-ownership check, not a replacement for a genuine native link,
PS5 runtime reproduction or proof that an NS2 game reaches its first frame.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
cmake = (root / "headless/CMakeLists.txt").read_text(encoding="utf-8")
source = (root / "vendor/encore-active/eden/src/core/hle/service/am/service/gpu_worker.cpp").read_text(encoding="utf-8")

begin = cmake.index('set(EDEN_NS2_GPU_SESSION_ROOT ')
end = cmake.index('\nendif()', begin)
selected = cmake[begin:end]

# A global definition on core is forbidden: only the reviewed GPU worker TU
# uses these native-only receipts. The shared NS1 paths must remain identical.
guard = re.compile(
    r'set_property\(SOURCE "\$\{EDEN_NS2_GPU_WORKER_SOURCE\}"\s+'
    r'TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"\)'
)
assert len(guard.findall(selected)) == 1, "Native GPU worker TU lacks its own PS5_NATIVE flag"
assert selected.index('target_sources(core PRIVATE "${EDEN_NS2_GPU_SESSION_SOURCE}"') < selected.index('set_property(SOURCE "${EDEN_NS2_GPU_WORKER_SOURCE}"')
assert selected.count('set_property(SOURCE "${EDEN_NS2_GPU_SESSION_SOURCE}"') == 1
assert selected.count('set_property(SOURCE "${EDEN_NS2_GPU_WORKER_SOURCE}"') == 1
assert selected.count('COMPILE_DEFINITIONS "PS5_NATIVE=1"') == 2
assert 'target_compile_definitions(core PRIVATE PS5_NATIVE' not in selected

# The real vendor source is the only source of diagnostic strings. All these
# blocks are under PS5_NATIVE, so a syntax-only compilation without the flag
# can misleadingly pass with no counters in the built ELF.
for required in (
    'EDEN_NS2_IPC owner=gpu_worker',
    'EDEN_NS2_BLOCKING_BOUNDARY',
    'EDEN_NS2_GPU_WORKER_RESULT',
    'EDEN_NS2_GPU_214',
    'EDEN_NS2_GPU_216',
    'EDEN_NS2_GPU_102_SPARSE_RESTORE',
):
    assert required in source, ("Missing selected worker diagnostic", required)
assert source.count('#ifdef PS5_NATIVE') >= 7
assert 'u64 restored_sparse_ranges{};' in source
assert 'restored_sparse_ranges += batch.entries.size();' in source
assert '#ifdef PS5_NATIVE\n    if (restored_sparse_ranges)' in source

print("NS2_NATIVE_GPU_WORKER_GUARD_HOST_PASS source_scoped=1 guest_ns1_unchanged=1 markers=6")
print("No PS5 native binary or runtime gameplay validated by this source contract")
