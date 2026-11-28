#!/usr/bin/env python3
"""Reject malformed Eden patch hunks and stale shipping receipts before long CI."""
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / "headless/backports"
PATTERN = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")


def check_hunks(text, name):
    old = new = expected_old = expected_new = 0
    active = False
    num = 0

    def flush():
        if active and (old != expected_old or new != expected_new):
            raise AssertionError(f"{name}: corrupt hunk #{num}: "
                                 f"old={old}/{expected_old} new={new}/{expected_new}")

    for line in text.splitlines():
        m = PATTERN.match(line)
        if m:
            flush()
            expected_old = int(m[1]) if m[1] is not None else 1
            expected_new = int(m[2]) if m[2] is not None else 1
            old = new = 0
            active = True
            num += 1
        elif line.startswith(("--- ", "+++ ", "diff --git ", "index ")):
            flush()
            active = False
        elif active:
            if line.startswith(" "):
                old += 1
                new += 1
            elif line.startswith("-"):
                old += 1
            elif line.startswith("+"):
                new += 1
            elif not line.startswith("\\ No newline at end of file"):
                raise AssertionError(f"{name}: unexpected hunk line {line!r}")
    flush()
    assert num != 0, f"{name}: no hunks"
    return num


def main():
    fixture = "--- a/x\n+++ b/x\n@@ -1 +1,2 @@\n keep\n+added\n"
    assert check_hunks(fixture, "valid") == 1
    try:
        check_hunks(fixture.replace("+1,2", "+1,3"), "broken")
    except AssertionError:
        pass
    else:
        raise AssertionError("broken patch must fail")
    patches = sorted(PATCHES.glob("*.patch"))
    assert len(patches) >= 50
    hunk_total = sum(check_hunks(p.read_text(), p.name) for p in patches)
    script = (ROOT / "tools/apply-eden-backports.sh").read_text()
    calls = dict(re.findall(
        r'apply_one "\$root/headless/backports/([^"]+)" "\$eden/([^"]+)"',
        script))
    shipping = {
        patch: receipt for patch, receipt in calls.items()
        if patch != "eden-dummy-thread-waits.patch"
    }
    assert len(shipping) >= 50
    assert len(set(shipping.values())) == len(shipping)
    patch_names = {p.name for p in patches}
    assert set(shipping).issubset(patch_names)
    for patch, receipt in shipping.items():
        assert receipt.startswith(".encore-backport-") and receipt.endswith(".sha256")
        digest = hashlib.sha256((PATCHES / patch).read_bytes()).hexdigest()
        assert len(digest) == 64
    print(f"EDEN_BACKPORT_PATCH_INTEGRITY_PASS patches={len(patches)} "
          f"hunks={hunk_total} derived_receipts={len(shipping)}")


if __name__ == "__main__":
    main()
