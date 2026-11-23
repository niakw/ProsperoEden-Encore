#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression: NUP metadata in the TOC/blob gap is valid, malformed extents remain rejected."""
from pathlib import Path

s=(Path(__file__).resolve().parents[1]/"headless/nup_v1_vfs.cpp").read_text()
m=s.split("const auto meta_at = ReadLe<std::uint64_t>(toc, at + 0x20);",1)[1].split(
  "metadata_regions.emplace_back(meta_at, meta_at + meta_size);",1)[0]
for word in (
    "meta_size <= MaxMeta", "meta_at <= file_size",
    "meta_size <= file_size - meta_at",
    "meta_at >= toc_at + toc_size", "meta_at < blob_at",
    "meta_size <= blob_at - meta_at",
    "const bool metadata_after_blob = meta_at >= blob_at;",
    "metadata_inside_file && (metadata_in_toc_gap || metadata_after_blob)",
    '"overlaps_toc_or_header"', '"gap_crosses_blob"',
    "EDEN_NUP_METADATA_BOUNDS_REJECT", 'Check(false, "metadata exceeds file");',
):
    assert word in m, word
assert m.index("const bool metadata_inside_file") < m.index(
    "const bool metadata_bounded") < m.index("if (!metadata_bounded)") < m.index(
    'Check(false, "metadata exceeds file");')
assert "metadata_regions.emplace_back(meta_at, meta_at + meta_size);" in s
assert 'Check(it == regions.end() || it->first >= meta.second,' in s
assert 'Check(metadata_regions[i - 1].second <= metadata_regions[i].first,' in s
# Mirror the source's short-circuit bounds with synthetic offsets, including
# the historical 0x80 header, 0x100+ TOC and 16-byte aligned blob region.
def valid(meta_at, meta_size, *, toc_at=0x80, toc_size=0x100,
          blob_at=0x400, file_size=0x5000, max_meta=32*1024*1024):
    inside=meta_size <= max_meta and meta_at <= file_size and (
        meta_size <= file_size - meta_at)
    gap=meta_at >= toc_at+toc_size and meta_at < blob_at and (
        meta_size <= blob_at-meta_at)
    after=meta_at >= blob_at
    return inside and (gap or after)
assert valid(0x200,0x100) and valid(0x300,0x100)
assert valid(0x400,0x30) and valid(0x4fc0,0x40)
for address,size in (
    (0x100,0x10), # overlaps TOC
    (0x1ff,0x202), # gap crosses blob (0x401 > blob_at)
    (0x200,0x201), # gap crosses blob
    (0x5000,0x1), # outside file
    (0x5001,0x1), # starts outside file
    (0x400, 0x5000), # ends outside file
    (0x400, 32*1024*1024+1), # oversized metadata
):
    assert not valid(address,size),(hex(address),hex(size))
print("NUP_METADATA_GAP_SOURCE_PASS source_bound=1 before_blob_valid=1 malformed_rejected=7")
