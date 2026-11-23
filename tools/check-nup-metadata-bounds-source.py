#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""NUP malformed-metadata classification: preserve safety while adding exact facts."""
from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"headless/nup_v1_vfs.cpp").read_text()
m=s.split("const auto meta_at = ReadLe<std::uint64_t>(toc, at + 0x20);",1)[1].split(
  "metadata_regions.emplace_back(meta_at, meta_at + meta_size);",1)[0]
for word in ("meta_size <= MaxMeta", "meta_at >= blob_at",
             "meta_at <= file_size", "meta_size <= file_size - meta_at",
             'meta_size > MaxMeta ? "size_limit"',
             'meta_at < blob_at ? "before_blob"',
             'meta_at > file_size ? "offset_outside_file"',
             '"range_outside_file"', "EDEN_NUP_METADATA_BOUNDS_REJECT",
             'Check(false, "metadata exceeds file");'):
    assert word in m,word
assert m.index("const bool metadata_bounded") < m.index("if (!metadata_bounded)") < m.index(
    'Check(false, "metadata exceeds file");') < len(m)
assert "metadata_regions.emplace_back" in s
print("NUP_METADATA_BOUNDS_SOURCE_PASS fail_closed=1 distinguished_failure_modes=4")
