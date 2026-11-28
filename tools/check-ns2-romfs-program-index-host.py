#!/usr/bin/env python3
"""Verify both PS5-selected RomFSFactory variants and exercise upstream #159."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
vendor=ROOT/"vendor/encore-active/eden/src/core/file_sys/romfs_factory.cpp"
engine=ROOT/"headless/nup_v1_romfs_factory.cpp"
runtime=ROOT/"headless/nup_v1_runtime.cmake"
assert vendor.is_file() and engine.is_file() and runtime.is_file()
marker="VirtualFile RomFSFactory::OpenPatchedRomFSWithProgramIndex("
def extract(path):
    s=path.read_text()
    assert s.count(marker)==1, path
    begin=s.index(marker)
    return s[begin:s.index("\n}\n",begin)+2]
a,b=extract(vendor),extract(engine)
assert a==b, "vendor/engine selected RomFS ABI logic diverged"
for snippet in ("program_index == 0", "type == ContentRecordType::Program",
                "!updatable", "return file;", "OpenPatchedRomFS(res_title_id, type)"):
    assert snippet in a, snippet
cmake=runtime.read_text()
assert '"file_sys/romfs_factory.cpp|nup_v1_romfs_factory.cpp"' in cmake
assert '"hle/service/aoc/addon_content_manager.cpp|nup_v1_aoc_service.cpp"' in cmake
subprocess.run([sys.executable, "-B", str(ROOT/"vendor/tests/ns2_romfs_program_index_fallback_host.py")],
               check=True, timeout=180)
print("ENCORE_NS2_ROMFS_INDEX0_DUAL_SOURCE_PASS vendor_nup_parity=1")
