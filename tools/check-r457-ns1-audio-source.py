#!/usr/bin/env python3
"""Current PS5 native AudioOut owner proof, without vendor revision allowlists."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"

pinned = subprocess.check_output(
    ["git", "rev-parse", "HEAD:vendor"], cwd=ROOT, text=True
).strip()
checkout = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=VENDOR, text=True
).strip()
assert pinned == checkout, ("vendor checkout differs from engine gitlink", checkout, pinned)
subprocess.check_call(["python3", "-B", "tools/check-source-tree-layout.py"], cwd=VENDOR)

cmake = (ROOT / "headless/CMakeLists.txt").read_text()
for marker in (
    'get_target_property(eden_ns1_audio_units audio_core SOURCES)',
    'list(REMOVE_ITEM eden_ns1_audio_units "device/device_session.cpp")',
    'list(APPEND eden_ns1_audio_units "${EDEN_NS1_AUDIO_SOURCE}")',
    'set_property(TARGET audio_core PROPERTY SOURCES "${eden_ns1_audio_units}")',
    'target_include_directories(audio_core BEFORE PRIVATE',
    'target_include_directories(core BEFORE PUBLIC',
    'memory_native_a32.cpp',
    'memory_native_standard.cpp',
):
    assert marker in cmake, ("missing active AudioOut source owner", marker)

start = cmake.index("# R457 NS1 AudioOut: ")
end = cmake.index("# Maintained service source:", start)
owner_block = cmake[start:end]
assert owner_block.count("if(PS5_NATIVE)") == 1
assert owner_block.count("list(APPEND eden_ns1_audio_units") == 1
assert owner_block.count("list(REMOVE_ITEM eden_ns1_audio_units") == 1

# Some headers still live in the eden-core migration-debt root; runtime TUs
# already use canonical encore-active/eden paths. Both are maintained owners,
# never sources/ copies.
memory_h = VENDOR / "encore-active/eden-core/overrides/core/memory.h"
audio = VENDOR / "encore-active/eden/src/audio_core/device/device_session.cpp"
backends = [
    VENDOR / "encore-active/eden/src/core/memory_native_a32.cpp",
    VENDOR / "encore-active/eden/src/core/memory_native_standard.cpp",
]
for path in (memory_h, audio, *backends):
    assert path.is_file(), path
    assert VENDOR / "encore-active" in path.parents

assert "ReadyForAudioRead() const noexcept" in memory_h.read_text()
assert "if (!handle || !handle->GetMemory().ReadyForAudioRead())" in audio.read_text()
for backend in backends:
    source = backend.read_text()
    assert source.count("bool Memory::ReadyForAudioRead() const noexcept") == 1
    assert "return impl && impl->current_page_table != nullptr;" in source

# Upstream snapshots remain dependency input only.
assert "ReadyForAudioRead" not in (
    VENDOR / "sources/eden/src/core/memory.h"
).read_text()
assert "ReadyForAudioRead" not in (
    VENDOR / "sources/eden/src/audio_core/device/device_session.cpp"
).read_text()

subprocess.run(
    [sys.executable, "-B", str(VENDOR / "tools/ns1/check_r457_audio_unready_host.py")],
    check=True,
)
subprocess.run(
    [sys.executable, "-B", str(VENDOR / "tools/ns1/check_c00_r457_unified_audio.py")],
    check=True,
)

print(
    "R457_AUDIO_SELECTED_NATIVE_SOURCE_PASS",
    "audio_tu=1",
    "memory_backends=2",
    "gitlink_match=1",
    "revision_allowlists=0",
)
