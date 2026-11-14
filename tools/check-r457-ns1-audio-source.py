#!/usr/bin/env python3
"""Fail-closed source-owner proof for PS5 native AudioOut (host only).

This is not a PS5 firmware execution or a guest FC27 boot proof.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
# Both exact cross-repo graphs are reviewed. No arbitrary vendor SHA allowed.
KNOWN_VENDOR_GRAPH = {
    "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864": "original",
    "fe9edd661d6f0824c7339865d50aa9cf99cab150": "integrated",
    "c339fd06f02e42e67d5416ae82194ba619b7ee68": "integrated+jxr",
    "47568425c71d534b72cc966d1500412c9ae4fc16": "integrated+jxr-cache-page-table",
    "447e08718c9b6625508da6ce63796ed1f4285d2f": "integrated+jxr-cache-page-table-vfs",
    "97fdc316fcf5b42e08c26845887f298feac2a424": "integrated+jxr-cache-page-table-vfs-nca",
}
selected = subprocess.check_output(["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True).strip()
assert selected in KNOWN_VENDOR_GRAPH, f"Unexpected vendor submodule {selected}"

def git_blob(path: Path) -> str:
    body = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
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
# These four audio/guest-memory owners are byte-for-byte the same in the
# historical and integrated vendor SHAs (verified through raw Git blobs).
for owner, expected in (
    (h, "d4273c4539971285711a8e26c39bae046ccbbad6"),
    (audio, "893e5e5352149555ac15895d86e79068ab0ee7ae"),
    (backends[0], "1b506bac747a3c492d4393016ca2b7dc29bfcc57"),
    (backends[1], "c8f197810af244c3f2d66413352533734d031620"),
):
    assert git_blob(owner) == expected, ("Unreviewed audio owner drift", owner)
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
print("R457_AUDIO_SELECTED_NATIVE_SOURCE_PASS audio_tu=1 memory_backends=2 vendor_pin=exact reviewed="+KNOWN_VENDOR_GRAPH[selected])
