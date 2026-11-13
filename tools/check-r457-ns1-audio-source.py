#!/usr/bin/env python3
"""Fail-closed source-owner proof for PS5 native AudioOut (host only).

This is not a PS5 firmware execution or a guest FC27 boot proof.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
PIN = "3c08dc54334a30889acea7d0eb38753bcabe4ce6"
selected = subprocess.check_output(["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True).strip()
assert selected == PIN, f"Unexpected vendor submodule {selected}"
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
checks = (
    'get_target_property(eden_ns1_audio_units audio_core SOURCES)',
    'list(REMOVE_ITEM eden_ns1_audio_units "device/device_session.cpp")',
    'list(APPEND eden_ns1_audio_units "${EDEN_NS1_AUDIO_SOURCE}")',
    'set_property(TARGET audio_core PROPERTY SOURCES "${eden_ns1_audio_units}")',
    'target_include_directories(audio_core BEFORE PRIVATE',
    'target_include_directories(core BEFORE PUBLIC',
    'APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"',
    'memory_native_a32.cpp',
    'memory_native_standard.cpp',
)
for check in checks:
    assert check in cmake, f"Missing active AudioOut source owner: {check}"
start = cmake.index('# R457 NS1 AudioOut: ')
end = cmake.index('# Maintained service source:', start)
owner = cmake[start:end]
assert owner.count('if(PS5_NATIVE)') == 1
assert owner.count("list(APPEND eden_ns1_audio_units") == 1
assert owner.count("list(REMOVE_ITEM eden_ns1_audio_units") == 1
h = VENDOR / "encore-active/eden-core/overrides/core/memory.h"
audio = VENDOR / "encore-active/eden-core/src/audio_core/device/device_session.cpp"
backends = [VENDOR / f"encore-active/eden-core/src/core/memory_native_{name}.cpp"
            for name in ("a32", "standard")]
assert 'ReadyForAudioRead() const noexcept' in h.read_text()
assert 'if (!handle || !handle->GetMemory().ReadyForAudioRead())' in audio.read_text()
for b in backends:
    source = b.read_text()
    assert source.count('bool Memory::ReadyForAudioRead() const noexcept') == 1
    assert 'return impl && impl->current_page_table != nullptr;' in source
# Pinned original source tree must remain unchanged for downstream vendored checks.
assert 'ReadyForAudioRead' not in (VENDOR / "sources/eden/src/core/memory.h").read_text()
assert 'ReadyForAudioRead' not in (VENDOR / "sources/eden/src/audio_core/device/device_session.cpp").read_text()
subprocess.run([sys.executable, "-B", str(VENDOR / "tools/ns1/check_r457_audio_unready_host.py")], check=True)
subprocess.run([sys.executable, "-B", str(VENDOR / "tools/ns1/check_c00_r457_unified_audio.py")], check=True)
print("R457_AUDIO_SELECTED_NATIVE_SOURCE_PASS audio_tu=1 memory_backends=2 vendor_pin=exact")
