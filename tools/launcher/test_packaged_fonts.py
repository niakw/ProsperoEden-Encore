#!/usr/bin/env python3
"""Offline synthetic fixtures for the staged font receipt and inventory gate."""
import hashlib
import json
import tempfile
from pathlib import Path
from check_packaged_fonts import verify_fonts

spec_path = Path(__file__).resolve().parent / "noto_fallbacks.json"
spec = json.loads(spec_path.read_text())
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "tools/launcher").mkdir(parents=True)
    (root / "tools/launcher/noto_fallbacks.json").write_bytes(spec_path.read_bytes())
    primary = root / "third_party/fonts/Montserrat-Medium.ttf"
    primary.parent.mkdir(parents=True)
    primary.write_bytes(b"synthetic primary")
    app = root / "PPSA99008"
    folder = app / "ui/fonts/fallback"
    folder.mkdir(parents=True)
    (folder / primary.name).write_bytes(primary.read_bytes())
    entries = []
    for item in spec["fonts"]:
        data = b"\x00\x01\x00\x00" + item["id"].encode()
        (folder / item["output"]).write_bytes(data)
        entries.append(dict(id=item["id"], file=item["output"], locales=item["locales"],
                            source_git_blob=item["git_blob"], subset_bytes=len(data),
                            subset_sha256=hashlib.sha256(data).hexdigest()))
    receipt = {key: spec[key] for key in ("schema", "source_repository", "source_commit", "max_total_bytes")}
    receipt.update(fonts=entries, total_bytes=sum(entry["subset_bytes"] for entry in entries))
    (folder / "receipt.json").write_text(json.dumps(receipt))
    assert len(verify_fonts(root, app)) == 9
    path = folder / entries[0]["file"]
    good = path.read_bytes()
    def rejected():
        try:
            verify_fonts(root, app)
        except (AssertionError, OSError, ValueError, KeyError):
            return
        raise AssertionError("bad staged font accepted")
    path.write_bytes(good + b"x")
    rejected()
    path.unlink()
    rejected()
    path.write_bytes(good)
    extra = folder / "unexpected.ttf"
    extra.write_bytes(good)
    rejected()
    extra.unlink()
    original = entries[0]["source_git_blob"]
    entries[0]["source_git_blob"] = "0" * 40
    (folder / "receipt.json").write_text(json.dumps(receipt))
    rejected()
    entries[0]["source_git_blob"] = original
    (folder / "receipt.json").write_text(json.dumps(receipt))
    assert len(verify_fonts(root, app)) == 9
print("STAGED_FONT_RECEIPT_HOST_PASS inventory=9 missing=reject modified=reject unknown=reject pin=reject")
