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
LEGACY_BACKPORT_SHA256 = "d617d9bd8882d6803fe885dd15302675b211a2e71e6c6faac18e549224aa1689"
SHIPPING_CANONICAL_BLOB = "71affe639ac03a38a9fe42d692efa6ffadf83764"
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
    legacy_max = "GpuFenceBehavior::Accurate,\n                                                                 \"gpu_fence_behavior\""
    canonical_max = "GpuFenceBehavior::Strict,\n                                                                 \"gpu_fence_behavior\""
    legacy_decl = "bool IsGPUFenceBehaviorAccurate();\n"
    canonical_decl = "bool IsGPUFenceBehaviorAccurate();\nbool IsGPUFenceBehaviorStrict();\n"
    canonical = text.count(canonical_max) == 1 and text.count(canonical_decl) == 1
    legacy = text.count(legacy_max) == 1 and text.count(legacy_decl) == 1 and "IsGPUFenceBehaviorStrict" not in text
    if canonical:
        return text
    if not legacy:
        raise RuntimeError("Unexpected reviewed PS5 fence ABI: header")
    return text.replace(legacy_max, canonical_max, 1).replace(legacy_decl, canonical_decl, 1)


def legacy_fence_header(text: str) -> str:
    canonical_max = "GpuFenceBehavior::Strict,\n                                                                 \"gpu_fence_behavior\""
    legacy_max = "GpuFenceBehavior::Accurate,\n                                                                 \"gpu_fence_behavior\""
    canonical_decl = "bool IsGPUFenceBehaviorAccurate();\nbool IsGPUFenceBehaviorStrict();\n"
    legacy_decl = "bool IsGPUFenceBehaviorAccurate();\n"
    if text.count(canonical_max) != 1 or text.count(canonical_decl) != 1:
        raise RuntimeError("Canonical PS5 fence header drift")
    return text.replace(canonical_max, legacy_max, 1).replace(canonical_decl, legacy_decl, 1)


def extend_fence_implementation(text: str) -> str:
    marker = (
        "bool IsGPUFenceBehaviorAccurate() {\n"
        "    return values.gpu_fence_behavior.GetValue() == GpuFenceBehavior::Accurate;\n"
        "}\n"
    )
    strict = (
        "\nbool IsGPUFenceBehaviorStrict() {\n"
        "    return values.gpu_fence_behavior.GetValue() == GpuFenceBehavior::Strict;\n"
        "}\n"
    )
    if text.count(marker + strict) == 1:
        return text
    if text.count(marker) != 1 or "bool IsGPUFenceBehaviorStrict() {" in text:
        raise RuntimeError("Unexpected reviewed PS5 fence ABI: implementation")
    return text.replace(marker, marker + strict, 1)


def legacy_fence_implementation(text: str) -> str:
    marker = (
        "bool IsGPUFenceBehaviorAccurate() {\n"
        "    return values.gpu_fence_behavior.GetValue() == GpuFenceBehavior::Accurate;\n"
        "}\n"
    )
    strict = (
        "\nbool IsGPUFenceBehaviorStrict() {\n"
        "    return values.gpu_fence_behavior.GetValue() == GpuFenceBehavior::Strict;\n"
        "}\n"
    )
    if text.count(marker + strict) != 1:
        raise RuntimeError("Canonical PS5 fence implementation drift")
    return text.replace(marker + strict, marker, 1)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_blob(value: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\\0" + value).hexdigest()


def extend_graphics_enums(base_text: str) -> str:
    legacy = all(base_text.count(before) == 1 and after not in base_text
                 for before, after in REPLACEMENTS)
    canonical = all(base_text.count(after) == 1 and before not in base_text
                    for before, after in REPLACEMENTS)
    if canonical:
        return base_text
    if not legacy:
        raise RuntimeError("Unexpected reviewed graphics enum source ABI")
    result = base_text
    for before, after in REPLACEMENTS:
        result = result.replace(before, after, 1)
    return result


def legacy_graphics_enums(canonical_text: str) -> str:
    if not all(canonical_text.count(after) == 1 and before not in canonical_text
               for before, after in REPLACEMENTS):
        raise RuntimeError("Canonical graphics enum ABI drift")
    result = canonical_text
    for before, after in REPLACEMENTS:
        result = result.replace(after, before, 1)
    return result


def approved_bytes() -> tuple[bytes, bytes]:
    original = ROOT / "vendor/sources/eden" / RELATIVE
    reviewed = ROOT / "vendor/encore-active/eden" / RELATIVE
    source = original.read_bytes()
    canonical = reviewed.read_bytes()
    if sha256(source) != PINNED_UPSTREAM_SHA256:
        raise RuntimeError("Pinned Eden enum input drift: immutable source was modified")
    if git_blob(canonical) != SHIPPING_CANONICAL_BLOB:
        raise RuntimeError("Canonical Encore graphics enum owner drift")
    legacy = legacy_graphics_enums(canonical.decode("utf-8")).encode("utf-8")
    if sha256(legacy) != LEGACY_BACKPORT_SHA256:
        raise RuntimeError("Canonical graphics enum reverse delta changed legacy audited owner")
    return source, canonical


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
    # Eden #4218 flattened recursive terminators and retained a diagnostic
    # stub that always returns the empty string. Its reference parameter
    # is intentionally unnamed in the native build copy; never alter
    # compilation flags, the frozen source, or guest terminal semantics.
    relative = Path("src/dynarmic/src/dynarmic/ir/basic_block.cpp")
    original = (ROOT / "vendor/sources/eden" / relative).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(original)).encode() + b"\0" + original).hexdigest()
    if blob != "4a7b2bf261562316d9060cf2464c9216807e3cf0":
        raise RuntimeError("Unreviewed Dynarmic terminal diagnostic owner")
    before = b"static std::string TerminalToString(const Term::Terminal& terminal_variant) noexcept {"
    after = b"static std::string TerminalToString(const Term::Terminal&) noexcept {"
    if original.count(before) != 1 or after in original:
        raise RuntimeError("Unexpected Dynarmic terminal diagnostic signature")
    body = original.split(before, 1)[1].split(b"\n}", 1)[0]
    executable = [line.strip() for line in body.splitlines()
                  if line.strip() and not line.lstrip().startswith(b"//")]
    if executable != [b'return "";']:
        raise RuntimeError("Dynarmic terminal diagnostic is no longer an empty stub")
    result.append((relative, original, original.replace(before, after, 1)))
    return result


def apply(stage: Path, check_only: bool = False) -> str:
    _, canonical_enums = approved_bytes()
    _ = validate_owned_stage(stage)

    canonical_enum_text = extend_graphics_enums(canonical_enums.decode("utf-8"))
    legacy_enum_bytes = legacy_graphics_enums(canonical_enum_text).encode("utf-8")

    canonical_h_bytes = (ROOT / "vendor/encore-active/eden" / FENCE_HEADER).read_bytes()
    canonical_cpp_bytes = (ROOT / "vendor/encore-active/eden" / FENCE_IMPL).read_bytes()
    canonical_h_text = extend_fence_header(canonical_h_bytes.decode("utf-8"))
    canonical_cpp_text = extend_fence_implementation(canonical_cpp_bytes.decode("utf-8"))

    targets = [
        (RELATIVE, legacy_enum_bytes, canonical_enum_text.encode("utf-8")),
        (FENCE_HEADER, legacy_fence_header(canonical_h_text).encode("utf-8"),
         canonical_h_text.encode("utf-8")),
        (FENCE_IMPL, legacy_fence_implementation(canonical_cpp_text).encode("utf-8"),
         canonical_cpp_text.encode("utf-8")),
    ]
    targets.extend(reviewed_warning_targets())

    pending = []
    for relative, legacy, expected in targets:
        dest = stage / relative
        if dest.is_symlink() or not dest.is_file() or not (
                dest.resolve().is_relative_to(stage.resolve())):
            raise RuntimeError("Unsafe PS5 graphics/fence owner: " + str(relative))
        current = dest.read_bytes()
        if current == expected:
            continue
        if current != legacy:
            raise RuntimeError("Unreviewed PS5 staged graphics/fence source: " + str(relative))
        pending.append((dest, legacy, expected))
    if not pending:
        return "already-applied"
    if check_only:
        raise RuntimeError("Canonical PS5 graphics/fence owners not yet staged")
    for dest, legacy, expected in pending:
        tmp = dest.with_name(dest.name + ".encore-" + str(os.getpid()))
        if tmp.exists() or tmp.is_symlink():
            raise RuntimeError("Unexpected PS5 staged graphics temporary file")
        try:
            tmp.write_bytes(expected)
            shutil.copymode(dest, tmp)
            if dest.read_bytes() != legacy:
                raise RuntimeError("PS5 staged graphics source changed during installation")
            tmp.replace(dest)
        finally:
            tmp.unlink(missing_ok=True)
    return "installed"


def self_test() -> None:
    source, canonical_enums = approved_bytes()
    canonical_text = canonical_enums.decode("utf-8")
    legacy_text = legacy_graphics_enums(canonical_text)
    assert extend_graphics_enums(canonical_text) == canonical_text
    assert extend_graphics_enums(legacy_text) == canonical_text

    upstream_enums = source.decode("utf-8")
    assert "Anime4K3D" not in upstream_enums and "FxaaPlus" not in upstream_enums
    assert "ENUM(GpuFenceBehavior, Default, Immediate, Balanced, Accurate, Strict);" in upstream_enums
    assert all(canonical_text.count(after) == 1 for _, after in REPLACEMENTS)
    assert sha256(legacy_text.encode("utf-8")) == LEGACY_BACKPORT_SHA256
    assert git_blob(canonical_enums) == SHIPPING_CANONICAL_BLOB

    canonical_h = (ROOT / "vendor/encore-active/eden" / FENCE_HEADER).read_text()
    canonical_cpp = (ROOT / "vendor/encore-active/eden" / FENCE_IMPL).read_text()
    assert extend_fence_header(canonical_h) == canonical_h
    assert extend_fence_implementation(canonical_cpp) == canonical_cpp
    legacy_h = legacy_fence_header(canonical_h)
    legacy_cpp = legacy_fence_implementation(canonical_cpp)
    assert extend_fence_header(legacy_h) == canonical_h
    assert extend_fence_implementation(legacy_cpp) == canonical_cpp

    import tempfile
    with tempfile.TemporaryDirectory(prefix="ps5-eden-headless.warning-test.") as temp:
        cache = Path(temp)
        (cache / "owner").write_text(str(ROOT.resolve()) + "\n")
        stage = cache / "source"
        inputs = [
            (RELATIVE, legacy_text.encode("utf-8"), canonical_enums),
            (FENCE_HEADER, legacy_h.encode("utf-8"), canonical_h.encode("utf-8")),
            (FENCE_IMPL, legacy_cpp.encode("utf-8"), canonical_cpp.encode("utf-8")),
        ]
        inputs.extend(reviewed_warning_targets())
        for relative, legacy, expected in inputs:
            dest = stage / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(legacy)

        last = stage / inputs[-1][0]
        last.write_bytes(b"unreviewed source")
        try:
            apply(stage)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Unexpected staged owner accepted")
        assert (stage / RELATIVE).read_bytes() == legacy_text.encode("utf-8")

        last.write_bytes(inputs[-1][1])
        assert apply(stage) == "installed"
        assert apply(stage, check_only=True) == "already-applied"
        assert apply(stage) == "already-applied"
        for relative, legacy, expected in inputs:
            assert (stage / relative).read_bytes() == expected

        import subprocess
        terminal = (stage / "src/dynarmic/src/dynarmic/ir/basic_block.cpp").read_text()
        signature = "static std::string TerminalToString(const Term::Terminal&) noexcept {"
        method = signature + terminal.split(signature, 1)[1].split("\n}", 1)[0] + "\n}\n"
        fixture = cache / "terminal-warning.cpp"
        fixture.write_text("#include <string>\nnamespace Term { struct Terminal {}; }\n" +
                           method + "int main() { return TerminalToString(Term::Terminal{}).empty() ? 0 : 1; }\n")
        compilers = [c for c in (shutil.which("clang++"), shutil.which("g++")) if c]
        if not compilers:
            raise RuntimeError("No C++ compiler for Dynarmic terminal warning host witness")
        for index, compiler in enumerate(compilers):
            binary = cache / ("terminal-warning-" + str(index))
            subprocess.run([compiler, "-std=c++20", "-Wall", "-Wextra",
                            "-Werror=unused-parameter", str(fixture), "-o", str(binary)],
                           check=True, timeout=40)
            subprocess.run([str(binary)], check=True, timeout=10)
    print("DYNARMIC_TERMINAL_WARNING_HOST_PASS actual_stub=1 unused_parameter=0 semantic_change=0")
    print("R457_WARNING_OWNER_STAGE_PASS owners=3 exact_vendor_blob=1 idempotent=1 failclosed=1")
    print("PS5_GRAPHICS_ENUM_CANONICAL_OWNER_PASS active_final=1 legacy_replay=1 abi=1 failclosed=1")


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
