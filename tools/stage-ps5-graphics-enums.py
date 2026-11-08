#!/usr/bin/env python3
"""Apply PS5-only graphics enum extensions to an owner-stamped build copy.

Never patch vendor/sources/eden: its SHA-256 is an immutable input to the
83-source backport manifest, not an editable header. Preserve upstream enum
ordinals by appending Encore-only values after stock entries. Restore the
upstream Strict GPU-fence setting/handler consistently across the native
settings enum, declaration and implementation without editing the pinned
backport originals.
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
    ("ENUM(GpuFenceBehavior, Default, Immediate, Balanced, Accurate);", "ENUM(GpuFenceBehavior, Default, Immediate, Balanced, Accurate, Strict);"),
)

FENCE_HEADER = Path("src/common/settings.h")
FENCE_IMPL = Path("src/common/settings.cpp")


def exact_replace(text: str, before: str, after: str, what: str) -> str:
    if text.count(before) != 1 or after in text:
        raise RuntimeError("Unexpected reviewed PS5 fence ABI: " + what)
    return text.replace(before, after)


def extend_fence_header(text: str) -> str:
    text = exact_replace(
        text,
        "GpuFenceBehavior::Accurate,\n                                                                 \"gpu_fence_behavior\"",
        "GpuFenceBehavior::Strict,\n                                                                 \"gpu_fence_behavior\"",
        "maximum supported fence behavior",
    )
    return exact_replace(
        text,
        "bool IsGPUFenceBehaviorAccurate();\n",
        "bool IsGPUFenceBehaviorAccurate();\nbool IsGPUFenceBehaviorStrict();\n",
        "fence strict declaration",
    )


def extend_fence_implementation(text: str) -> str:
    marker = (
        "bool IsGPUFenceBehaviorAccurate() {\n"
        "    return values.gpu_fence_behavior.GetValue() == GpuFenceBehavior::Accurate;\n"
        "}\n"
    )
    return exact_replace(
        text, marker,
        marker + (
            "\nbool IsGPUFenceBehaviorStrict() {\n"
            "    return values.gpu_fence_behavior.GetValue() == GpuFenceBehavior::Strict;\n"
            "}\n"
        ), "real fence strict implementation")


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
    _ = validate_owned_stage(stage)
    targets = (
        (RELATIVE, approved, extend_graphics_enums(approved.decode("utf-8")).encode("utf-8")),
        (FENCE_HEADER,
         (ROOT / "vendor/encore-active/eden-backports" / FENCE_HEADER).read_bytes(),
         None),
        (FENCE_IMPL,
         (ROOT / "vendor/encore-active/eden-backports" / FENCE_IMPL).read_bytes(),
         None),
    )
    targets = list(targets)
    targets[1] = (targets[1][0], targets[1][1],
                  extend_fence_header(targets[1][1].decode("utf-8")).encode("utf-8"))
    targets[2] = (targets[2][0], targets[2][1],
                  extend_fence_implementation(targets[2][1].decode("utf-8")).encode("utf-8"))
    # Inspect every target before writing any, so an unfamiliar build-cache
    # change cannot partially install or bypass the reviewed source variant.
    pending = []
    for relative, original, expected in targets:
        dest = stage / relative
        if dest.is_symlink() or not dest.is_file() or not (
                dest.resolve().is_relative_to(stage.resolve())):
            raise RuntimeError("Unsafe PS5 fence/graphics owner: " + str(relative))
        current = dest.read_bytes()
        if current == expected:
            continue
        if current != original:
            raise RuntimeError("Unreviewed PS5 staged graphics/fence source: " + str(relative))
        pending.append((dest, original, expected))
    if not pending:
        return "already-applied"
    if check_only:
        raise RuntimeError("PS5 graphics/fence overlay not yet installed")
    for dest, original, expected in pending:
        tmp = dest.with_name(dest.name + ".encore-" + str(os.getpid()))
        if tmp.exists() or tmp.is_symlink():
            raise RuntimeError("Unexpected PS5 staged graphics temporary file")
        try:
            tmp.write_bytes(expected)
            shutil.copymode(dest, tmp)
            if dest.read_bytes() != original:
                raise RuntimeError("PS5 staged graphics source changed during installation")
            tmp.replace(dest)
        finally:
            tmp.unlink(missing_ok=True)
    return "installed"

def self_test() -> None:
    source, approved = approved_bytes()
    extended = extend_graphics_enums(approved.decode("utf-8"))
    # Strict already exists in the PINNED upstream Eden enum. The old
    # 83-source backport omitted it, while upstream fence_manager.h still
    # calls its real predicate. Only Encore's scaling/AA extras must be
    # absent from original upstream; Strict must be present there.
    upstream_enums = source.decode("utf-8")
    assert not any(after in upstream_enums for before, after in REPLACEMENTS
                   if "GpuFenceBehavior" not in before)
    assert "ENUM(GpuFenceBehavior, Default, Immediate, Balanced, Accurate, Strict);" in upstream_enums
    assert "ENUM(GpuFenceBehavior, Default, Immediate, Balanced, Accurate);" in approved.decode("utf-8")
    assert all(extended.count(after) == 1 for _,after in REPLACEMENTS)
    assert all(extended.count(before) == 0 for before,_ in REPLACEMENTS)
    assert extended.count("ENUM(ScalingFilter,") == 1
    assert extended.count("ENUM(AntiAliasing,") == 1
    assert extended.count("ENUM(GpuFenceBehavior,") == 1
    fence_h = (ROOT / "vendor/encore-active/eden-backports" / FENCE_HEADER).read_text()
    fence_cpp = (ROOT / "vendor/encore-active/eden-backports" / FENCE_IMPL).read_text()
    updated_h = extend_fence_header(fence_h)
    updated_cpp = extend_fence_implementation(fence_cpp)
    assert updated_h.count("bool IsGPUFenceBehaviorStrict();") == 1
    assert updated_h.count("GpuFenceBehavior::Strict,") == 1
    assert updated_cpp.count("bool IsGPUFenceBehaviorStrict() {") == 1
    assert "GpuFenceBehavior::Strict" in extended
    for source, extend in ((updated_h, extend_fence_header),
                           (updated_cpp, extend_fence_implementation)):
        try:
            extend(source)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Already-patched fence owner accepted")
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
