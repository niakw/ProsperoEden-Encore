#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check strict NUP payload/TOC validation alongside upstream optional metadata tolerance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cpp = (ROOT / "headless/nup_v1_vfs.cpp").read_text()
py = (ROOT / "tools/check-nup-v1-host.py").read_text()
host = (ROOT / "tools/check-nup-v1-vfs-host.py").read_text()
start = cpp.index("const auto meta_at = ReadLe<std::uint64_t>(toc, at + 0x20);")
end = cpp.index("package_metadata_.push_back", start)
meta = cpp[start:end]
for token in (
    "meta_size <= MaxMeta",
    "meta_at >= toc_at + toc_size",
    "meta_size <= file_size - meta_at",
    "const bool metadata_bounded",
    "const bool optional_metadata_outside_file",
    "meta_at == 0 || meta_at > file_size ||",
    "meta_size > file_size - meta_at;",
    "EDEN_NUP_OPTIONAL_METADATA_SKIPPED",
    "EDEN_NUP_METADATA_BOUNDS_REJECT",
    'Check(false, "metadata exceeds file");',
    "if (metadata_bounded) {",
    "metadata_regions.emplace_back(meta_at, meta_at + meta_size);",
    "const auto meta = ReadChunk(source_, meta_at, meta_size);",
):
    assert token in meta, token
assert meta.index("const bool optional_metadata_outside_file") < meta.index(
    "if (metadata_bounded) {") < meta.index(
    "ReadChunk(source_, meta_at, meta_size)")
assert meta.index("if (optional_metadata_outside_file)") < meta.index(
    "if (metadata_bounded) {")
assert 'if meta_offset == 0 or meta_offset > total or meta_size > total - meta_offset:' in py
assert "metadata_record = 0x80 + 0x30 + 0x20" in host
assert 'execute(bytes(invalid_optional), "@effective/romfs/state.bin", b"latest-v3")' in host
assert 'execute(bytes(invalid_overlap), "@effective/romfs/state.bin", None)' in host
print("NUP_OPTIONAL_METADATA_SOURCE_PASS skip_oob=1 reject_alias=1 retain_toc_and_payload=1")
