#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""For the isolated Linux R09 CI only: replace unreliable Github mirror+file.

Preserves Ubuntu apt package signing, package suites and components.
Does not modify any sources outside the expressly supplied CI .sources file.
"""
from pathlib import Path
import re
import sys

def replace_mirrors(source: str) -> tuple[str, int]:
    blocks = source.split("\n\n")
    changed = 0
    for i, block in enumerate(blocks):
        if "URIs: mirror+file:" not in block:
            continue
        endpoint = ("http://security.ubuntu.com/ubuntu"
                    if re.search(r"^Suites:.*noble-security", block, re.M)
                    else "http://archive.ubuntu.com/ubuntu")
        rewritten, matched = re.subn(
            r"^URIs: mirror\+file:/etc/apt/apt-mirrors\.txt$",
            "URIs: " + endpoint, block, flags=re.M)
        if matched != 1:
            raise ValueError("R09_APT_UNKNOWN_MIRROR_FORMAT")
        blocks[i] = rewritten
        changed += 1
    return "\n\n".join(blocks), changed

def test() -> None:
    original = (
        "Types: deb\nURIs: mirror+file:/etc/apt/apt-mirrors.txt\n"
        "Suites: noble noble-updates noble-backports\n"
        "Components: main universe\nSigned-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n\n"
        "Types: deb\nURIs: mirror+file:/etc/apt/apt-mirrors.txt\n"
        "Suites: noble-security\nComponents: main universe\n"
        "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n"
    )
    rewritten, count = replace_mirrors(original)
    assert count == 2
    assert rewritten.count("http://archive.ubuntu.com/ubuntu") == 1
    assert rewritten.count("http://security.ubuntu.com/ubuntu") == 1
    assert rewritten.count("Signed-By:") == 2
    assert replace_mirrors(rewritten) == (rewritten, 0)
    try:
        replace_mirrors("URIs: mirror+file:/different/repo\n")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown mirror unexpectedly accepted")
    print("R09_APT_SIGNED_OFFICIAL_MIRROR_REWRITE_TEST_PASS")

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        test()
        return 0
    if len(sys.argv) != 2:
        print("usage: r09_official_apt_mirrors.py <ubuntu.sources>", file=sys.stderr)
        return 64
    p = Path(sys.argv[1])
    if p.is_symlink() or not p.is_file() or p.name != "ubuntu.sources":
        print("R09_APT_SOURCES_UNSAFE_PATH", file=sys.stderr)
        return 65
    try:
        output, changed = replace_mirrors(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 66
    if changed:
        p.write_text(output, encoding="utf-8")
    print(f"R09_APT_SIGNED_OFFICIAL_MIRRORS selected={changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
