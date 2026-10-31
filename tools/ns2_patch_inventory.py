#!/usr/bin/env python3
"""Read-only inventory of an external Eden NS2 unified patch against Encore's pinned Eden tree.

This is NOT a patch applicator, an ABI test, a compiler test, or a PS5 compatibility proof.
No keys, firmware, executable game content, or network access are used.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

DIFF_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
PINNED_SOURCE = Path("vendor/sources/eden")


def classify(path: str) -> str:
    parts = path.split("/")
    if len(parts) >= 3 and parts[:3] == ["src", "core", "hle"]:
        return "HLE / kernel / services"
    if len(parts) >= 3 and parts[:3] == ["src", "dynarmic", "src"]:
        return "Dynarmic / ARM JIT"
    if len(parts) >= 2 and parts[:2] == ["src", "shader_recompiler"]:
        return "Shader recompiler"
    if len(parts) >= 2 and parts[:2] == ["src", "video_core"]:
        return "GPU / Vulkan / textures"
    if len(parts) >= 2 and parts[:2] == ["src", "audio_core"]:
        return "Audio"
    if len(parts) >= 2 and parts[:2] == ["src", "core"]:
        return "CPU / loader / other core"
    if len(parts) >= 2 and parts[:2] == ["src", "tests"]:
        return "Tests"
    return "Other / build / tools"


def read_inventory(patch_text: str, pinned_root: Path) -> dict:
    files: list[dict] = []
    current: dict | None = None
    for line in patch_text.splitlines():
        match = DIFF_RE.match(line)
        if match:
            old, new = match.groups()
            if old != new:
                raise ValueError(f"Rename requires manual review: {old} -> {new}")
            pure_path = Path(new)
            if (
                not new
                or pure_path.is_absolute()
                or any(part in ("..", ".", "") for part in pure_path.parts)
            ):
                raise ValueError(f"Invalid patch path: {new!r}")
            current = {
                "path": new,
                "category": classify(new),
                "change": "modified",
                "present_in_pinned_tree": (pinned_root / pure_path).is_file(),
            }
            files.append(current)
        elif current is not None and line == "--- /dev/null":
            current["change"] = "added"
        elif current is not None and line == "+++ /dev/null":
            current["change"] = "deleted"

    if not files:
        raise ValueError("No 'diff --git a/... b/...' headers found")
    duplicated = [path for path, count in Counter(x["path"] for x in files).items() if count > 1]
    if duplicated:
        raise ValueError(f"Duplicate path entries need manual review: {duplicated[:5]}")
    categories = Counter(item["category"] for item in files)
    changes = Counter(item["change"] for item in files)
    present = sum(1 for item in files if item["present_in_pinned_tree"])
    return {
        "total_changed_paths": len(files),
        "present_in_pinned_tree": present,
        "not_present_in_pinned_tree": len(files) - present,
        "changes": dict(sorted(changes.items())),
        "categories": dict(sorted(categories.items(), key=lambda item: (-item[1], item[0]))),
        "files": files,
        "interpretation": (
            "File-presence check ONLY. New files can be absent legitimately. "
            "Existing files can still reject patch hunks or conflict with Encore's "
            "compiled overrides; do NOT apply the patch automatically."
        ),
    }


def self_test() -> None:
    import tempfile

    example = (
        "diff --git a/src/core/hle/service.cpp b/src/core/hle/service.cpp\n"
        "--- a/src/core/hle/service.cpp\n"
        "+++ b/src/core/hle/service.cpp\n"
        "@@ -1 +1 @@\n-a\n+b\n"
        "diff --git a/src/video_core/new.cpp b/src/video_core/new.cpp\n"
        "--- /dev/null\n+++ b/src/video_core/new.cpp\n"
        "@@ -0,0 +1 @@\n+x\n"
    )
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "src/core/hle/service.cpp"
        path.parent.mkdir(parents=True)
        path.write_text("original", encoding="utf-8")
        data = read_inventory(example, root)
        assert data["total_changed_paths"] == 2
        assert data["present_in_pinned_tree"] == 1
        assert data["changes"] == {"added": 1, "modified": 1}
        assert data["files"][0]["category"] == "HLE / kernel / services"
        assert data["files"][1]["category"] == "GPU / Vulkan / textures"
    print("NS2 patch inventory self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch", type=Path, help="Locally downloaded upstream NS2 .patch")
    parser.add_argument("--root", type=Path, default=Path("."), help="Encore checkout root")
    parser.add_argument("--json", action="store_true", help="Print the complete JSON inventory")
    parser.add_argument("--self-test", action="store_true", help="Run standalone parser tests")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.patch is None:
        parser.error("--patch is required unless --self-test is given")
    try:
        patch = args.patch.read_text(encoding="utf-8")
        data = read_inventory(patch, args.root / PINNED_SOURCE)
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"NS2 inventory failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"NS2 patch paths: {data['total_changed_paths']}")
        print(f"Present in pinned Eden: {data['present_in_pinned_tree']}")
        print(f"Absent in pinned Eden: {data['not_present_in_pinned_tree']} (may be new files)")
        print("Change types:")
        for category, count in data["changes"].items():
            print(f"  {category:<10} {count}")
        print("Sub-systems:")
        for category, count in data["categories"].items():
            print(f"  {category:<30} {count}")
        print(data["interpretation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
