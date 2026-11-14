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

# These two source owners were corrected together in vendor 7386cd7bc01e.
# R457's native compiler still read the old archive/cache bytes. Admit only
# the exact reviewed vendor blob and its one reversible upstream hunk.
def reviewed_warning_targets() -> list[tuple[Path, bytes, bytes]]:
    specs = (
        (Path("externals/stb/stb_image_write.h"),
         "62f0d5d0c4d0b28dfbf1666b93a50239793281f0",
         '         /* FALLTHROUGH */\n'
         '      case 3:\n         stbiw__write3(s, d[1 - rgb_dir], d[1], d[1 + rgb_dir]);',
         '         // Preserve the intentional RGBA -> RGB fallthrough without relying on\n'
         '         // comments that Clang does not recognize as a compiler annotation.\n'
         '#if defined(__cplusplus) && __cplusplus >= 201703L\n'
         '         [[fallthrough]];\n'
         '#elif defined(__has_attribute)\n'
         '#if __has_attribute(fallthrough)\n'
         '         __attribute__((fallthrough));\n'
         '#endif\n'
         '#elif defined(__GNUC__) && __GNUC__ >= 7\n'
         '         __attribute__((fallthrough));\n'
         '#endif\n'
         '      case 3:\n         stbiw__write3(s, d[1 - rgb_dir], d[1], d[1 + rgb_dir]);'),
        (Path("src/video_core/renderer_vulkan/maxwell_to_vk.cpp"),
         "f9841c558db0cf89fc580abe2d63e64454b8037b",
         '    case Shader::Stage::Compute:\n        return VK_SHADER_STAGE_COMPUTE_BIT;\n'
         '    }\n    UNIMPLEMENTED_MSG("Unimplemented shader stage={}", stage);',
         '    case Shader::Stage::Compute:\n        return VK_SHADER_STAGE_COMPUTE_BIT;\n'
         '    case Shader::Stage::Task:\n'
         '    case Shader::Stage::Mesh:\n'
         '        // This Vulkan owner has no maintained Task/Mesh stage conversion.\n'
         '        // Keep the existing failure diagnostic rather than invent a mapping.\n'
         '        break;\n'
         '    }\n    UNIMPLEMENTED_MSG("Unimplemented shader stage={}", stage);'),
    )
    result = []
    for relative, blob, before, after in specs:
        maintained = ROOT / "vendor/sources/eden" / relative
        expected = maintained.read_bytes()
        actual_blob = hashlib.sha1(b"blob " + str(len(expected)).encode() + b"\0" +
                                   expected).hexdigest()
        if actual_blob != blob or expected.count(after.encode()) != 1:
            raise RuntimeError("Unreviewed vendor warning owner: " + str(relative))
        original = expected.replace(after.encode(), before.encode(), 1)
        if original.count(before.encode()) != 1 or original == expected:
            raise RuntimeError("Ambiguous vendor warning delta: " + str(relative))
        result.append((relative, original, expected))
    return result


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
    targets.extend(reviewed_warning_targets())
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
    assert "ENUM(GpuFenceBehavior, Default, Immediate, Balanced, Accurate, Strict);" in extended
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
    # Exercise actual owned-cache installation, a repeated invocation,
    # and refusal before modifying any target if one owner has drifted.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="ps5-eden-headless.warning-test.") as temp:
        cache = Path(temp)
        (cache / "owner").write_text(str(ROOT.resolve()) + "\n")
        stage = cache / "source"
        inputs = [(RELATIVE, approved, extended.encode()),
                  (FENCE_HEADER, fence_h.encode(), updated_h.encode()),
                  (FENCE_IMPL, fence_cpp.encode(), updated_cpp.encode())]
        inputs.extend(reviewed_warning_targets())
        for relative, original, expected in inputs:
            dest = stage / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(original)
        last = stage / inputs[-1][0]
        last.write_bytes(b"unreviewed source")
        try:
            apply(stage)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Unexpected warning owner accepted")
        assert (stage / RELATIVE).read_bytes() == approved
        last.write_bytes(inputs[-1][1])
        assert apply(stage) == "installed"
        assert apply(stage, check_only=True) == "already-applied"
        assert apply(stage) == "already-applied"
        for relative, original, expected in inputs:
            assert (stage / relative).read_bytes() == expected
    print("R457_WARNING_OWNER_STAGE_PASS owners=2 exact_vendor_blob=1 idempotent=1 failclosed=1")
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
