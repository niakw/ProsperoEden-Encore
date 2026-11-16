#!/usr/bin/env python3
"""Verify the exact staged typography inventory and its generation receipts."""
import hashlib
import json
from pathlib import Path

def digest(data):
    return hashlib.sha256(data).hexdigest()

def verify_fonts(root, app):
    spec = json.loads((root / "tools/launcher/noto_fallbacks.json").read_text())
    folder = app / "ui/fonts/fallback"
    names = {item["output"] for item in spec["fonts"]}
    assert len(names) == len(spec["fonts"]) == 7
    expected = names | {"Montserrat-Medium.ttf", "receipt.json"}
    assert folder.is_dir() and not folder.is_symlink()
    assert {p.name for p in folder.iterdir()} == expected, "incorrect staged font inventory"
    assert all((folder / name).is_file() and not (folder / name).is_symlink() for name in expected)
    receipt = json.loads((folder / "receipt.json").read_text())
    for key in ("schema", "source_repository", "source_commit", "max_total_bytes"):
        assert receipt[key] == spec[key], key
    by_name = {item["file"]: item for item in receipt["fonts"]}
    assert len(receipt["fonts"]) == len(by_name) == len(names) and set(by_name) == names
    total = 0
    for item in spec["fonts"]:
        entry = by_name[item["output"]]
        assert entry["id"] == item["id"] and entry["locales"] == item["locales"]
        assert entry["source_git_blob"] == item["git_blob"]
        data = (folder / entry["file"]).read_bytes()
        assert 0 < len(data) == entry["subset_bytes"] and digest(data) == entry["subset_sha256"]
        assert data[:4] in (b"\x00\x01\x00\x00", b"OTTO"), entry["file"]
        total += len(data)
    assert 0 < total == receipt["total_bytes"] <= spec["max_total_bytes"]
    primary = root / "third_party/fonts/Montserrat-Medium.ttf"
    assert (folder / primary.name).read_bytes() == primary.read_bytes()
    generated = root / "build/generated/noto-fallback"
    if generated.is_dir():
        for name in names | {"receipt.json"}:
            assert (folder / name).read_bytes() == (generated / name).read_bytes(), name
    return {"ui/fonts/fallback/" + name for name in expected}
