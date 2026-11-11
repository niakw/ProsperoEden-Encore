#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Host-only audit of all migrated checkout actions and safety triggers."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
pin = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
old = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
files = {
    "prepare-encore-r2-draft.yml": 2,
    "encore-overrides-source-integrity.yml": 1,
    "r09-host-link.yml": 1,
    "r09-vit-boundary-qualification.yml": 3,
}
texts = {}
for name, count in files.items():
    body = (root / ".github/workflows" / name).read_text()
    assert body.count(pin) == count, (name, "wrong checkout pin count")
    assert old not in body, (name, "checkout v4 returned")
    texts[name] = body
assert sum(text.count(pin) for text in texts.values()) == 7

draft = texts["prepare-encore-r2-draft.yml"]
assert "release/encore-r2-draft-20261109" in draft
assert "release_id=438869174" in draft
assert draft.count(".draft == true and .prerelease == true and (.assets | length) == 0") == 2
assert "-F draft=true -F prerelease=true" in draft
assert "gh release publish" not in draft
assert "gh release create" not in draft

overrides = texts["encore-overrides-source-integrity.yml"]
assert "submodules: recursive" in overrides
assert "  pull_request:" in overrides

link = texts["r09-host-link.yml"]
assert "workflow_dispatch:" in link
assert "branches: [main]" in link
assert "'tools/graphics/r09-host-link-request.txt'" in link
assert "submodules: recursive" in link

vit = texts["r09-vit-boundary-qualification.yml"]
assert "workflow_dispatch:" in vit
assert "branches: [main]" in vit

print("PASS 7 Node24 checkout pins in 4 workflows, R2 hidden draft and R09 triggers unchanged")
