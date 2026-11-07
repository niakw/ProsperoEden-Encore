#!/usr/bin/env python3
"""Apply PS5-only graphics enum extensions to an owner-stamped build copy.

Never patch vendor/sources/eden: its SHA-256 is an immutable input to the
83-source backport manifest, not an editable header. Preserve upstream enum
ordinals by appending the eight Encore-only enum values after stock entries.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PINNED_UPSTREAM_SHA256 = "f2a3ae93b4257611958fab5a0c652f89c8158d2e16da31fb196a27960cf467ba"
SHIPPING_BACKPORT_SHA256 = "d617d9bd8882d6803fe885dd15302675b211a2e71e6c6faac18e549224aa1689"
RELATIVE = Path("src/common/settings_enums.h")
REPLACEMENTS = (
    ("ENUM(ScalingFilter, NearestNeighbor, Bilinear, Bicubic, Gaussian, Lanczos, ScaleForce, Fsr, Area, ZeroTangent, BSpline, Mitchell, Spline1, Mmpx, Sgsr, SgsrEdge);", "ENUM(ScalingFilter, NearestNeighbor, Bilinear, Bicubic, Gaussian, Lanczos, ScaleForce, Fsr, Area, ZeroTangent, BSpline, Mitchell, Spline1, Mmpx, Sgsr, SgsrEdge, Anime4K3D, Anime4KSoft, Anime4KDenoise);"),
    ("ENUM(AntiAliasing, None, Fxaa, Smaa);", "ENUM(AntiAliasing, None, Fxaa, Smaa, FxaaPlus, Msaa2, Msaa4, Msaa8, Msaa16);"),
)

def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def approved_bytes() -> tuple[bytes, bytes]:
    original = ROOT / "vendor/sources/eden" / RELATIVE
    reviewed = ROOT / "vendor/encore-active/eden-backports" / RELATIVE
    source = original.read_bytes()
    base = reviewed.read_bytes()
    if sha256(source) != PINNED_UPSTREAM_SHA256:
        raise RuntimeError("Pinned Eden enum input drift: immutable source was modified")
    if sha256(base) != SHIPPING_BACKPORT_SHA256:
        raise RuntimeError("Audited 83-source Eden backport header drift")
    return source, base

def extend_graphics_enums(base_text: str) -> str:
    result = base_text
    for before, after in REPLACEMENTS:
        if result.count(before) != 1 or after in result:
            raise RuntimeError("Unexpected reviewed graphics enum source ABI")
        result = result.replace(before, after)
    return result

def validate_owned_stage(stage: Path) -> Path:
    if stage.is_symlink() or stage.name != "source":
        raise RuntimeError("Only an owned build-cache source is writable")
    cache = stage.parent
    owner = cache / "owner"
    if (cache.is_symlink() or not cache.name.startswith("ps5-eden-headless.") or
        owner.is_symlink() or not owner.is_file() or
        owner.read_text().strip() != str(ROOT.resolve())):
        raise RuntimeError("Build-cache source is not owner-stamped for this checkout")
    if not stage.is_dir() or stage.resolve() != cache.resolve() / "source":
        raise RuntimeError("Unexpected or escaping Eden build directory")
    target = stage / RELATIVE
    if (target.is_symlink() or not target.is_file() or
        not target.resolve().is_relative_to(stage.resolve())):
        raise RuntimeError("Unsafe graphics enum destination")
    return target

def apply(stage: Path, check_only: bool = False) -> str:
    _, approved = approved_bytes()
    expected = extend_graphics_enums(approved.decode("utf-8")).encode("utf-8")
    target = validate_owned_stage(stage)
    current = target.read_bytes()
    if current == expected:
        return "already-applied"
    if current != approved:
        raise RuntimeError("Unknown graphics enum build source; refusing replacement")
    if check_only:
        raise RuntimeError("PS5 graphics enum overlay not yet installed")
    tmp = target.with_name(target.name + ".encore-" + str(os.getpid()))
    if tmp.exists() or tmp.is_symlink():
        raise RuntimeError("Unexpected staged graphics enum temporary file")
    try:
        tmp.write_bytes(expected)
        shutil.copymode(target, tmp)
        if target.read_bytes() != approved:
            raise RuntimeError("Graphics enum source changed during staging")
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return "installed"

def self_test() -> None:
    source, approved = approved_bytes()
    extended = extend_graphics_enums(approved.decode("utf-8"))
    assert not any(new in source.decode("utf-8") for _,new in REPLACEMENTS)
    assert all(extended.count(after) == 1 for _,after in REPLACEMENTS)
    assert all(extended.count(before) == 0 for before,_ in REPLACEMENTS)
    assert extended.count("ENUM(ScalingFilter,") == 1
    assert extended.count("ENUM(AntiAliasing,") == 1
    assert sha256(approved) == SHIPPING_BACKPORT_SHA256
    try:
        extend_graphics_enums(extended)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Already-patched enums accepted as a new baseline")
    print("PS5_GRAPHICS_ENUM_OVERLAY_PASS pinned=1 backport=1 abi=1 failclosed=1")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.stage is None and not args.self_test:
        parser.error("provide an owned build source or --self-test")
    if args.stage is not None:
        print("PS5_GRAPHICS_ENUM_OVERLAY_" + apply(args.stage, args.check).upper())
