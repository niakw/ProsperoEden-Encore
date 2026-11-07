#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Keep native R09 launch-time SHA-256 inventories aligned with public hashes."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
NATIVE=(ROOT/"headless/nr_dll_tensor_digests.h").read_text()
VENDOR=(ROOT/"vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/nr_rdna2_model_manifest.h").read_text()
for name,size in (("Original",599),("Compact",255)):
    expected={}
    path=ROOT/f"tools/graphics/r09_weights_{name.lower()}.sha256"
    for raw in path.read_text().splitlines():
        raw=raw.strip()
        if not raw: continue
        m=re.fullmatch(r"([0-9a-f]{64})\s+(.+)",raw)
        assert m,(name,raw)
        assert m[2] not in expected,(name,m[2])
        expected[m[2]]=m[1]
    marker=f"R09{name}Manifest = {{"
    assert marker in VENDOR,name
    manifest=VENDOR.split(marker,1)[1].split("};",1)[0]
    names=re.findall(r'"([^"]+)"',manifest)
    marker=f"R09{name}TensorDigests = {{"
    assert marker in NATIVE,name
    values=re.findall(r'"([0-9a-f]{64})"',NATIVE.split(marker,1)[1].split("};",1)[0])
    assert len(names)==len(values)==len(expected)==size,(name,len(names),len(values),len(expected))
    for label,hash_value in zip(names,values):
        assert expected[label]==hash_value,(name,label)
    print(f"R09_{name.upper()}_TENSOR_SHA256_REFERENCE_SYNC_PASS {size}/{size}")
