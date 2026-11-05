#!/usr/bin/env python3
"""Verify actual compiled native release experiments (never claim console FPS).

Run after build-package.sh release-stage, before release distribution uploads.
The marker strings in eboot.bin alone do not prove CMake conditionals are ON.
"""
from __future__ import annotations
import sys
import tempfile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "build/headless-native/CMakeCache.txt"
RELEASE = ROOT / "build/release/PPSA99008"
REQUIRED = {
    # One native PS5 product irrespective of guest platform; release is
    # a packaging decision, not a different CPU/GPU feature profile.
    "CMAKE_BUILD_TYPE:STRING": "Release",
    "EDEN_PS5_VULKAN:BOOL": "ON",
    "EDEN_VULKAN_DRIVER:STRING": "RADV",
    "EDEN_PS5_OPENGL:BOOL": "ON",
}
NATIVE_SETTING = "PS5_NATIVE"
# These old diagnostic selectors are not the product configuration. The
# unselected CMake modules must not be activated by an inherited build cache.
DISALLOWED_ACTIVE = ("EDEN_GUEST_WRITE_BRIDGE_DEV", "EDEN_UNQUALIFIED_FERMI2D_COPY")
OFF_VALUES = {"OFF", "FALSE", "0", ""}

# Sparse fallback diagnostics may be linked from maintained JIT source even
# when runtime sparse selection is OFF. Strings alone are not activation proof.
# The compiled CMakeCache policy is checked fail-closed below.
MARKERS = (
    b"EDEN_EXPERIMENT_DEFAULTS sparse=%u logical_cpu=%u frame_probe=%u safe=%u",
    b"EDEN_JIT_SPARSE_TRIM released=",
    b"EDEN_PS5_JIT_POLICY scope=all_titles",
    b"EDEN_GPU_REPORT_STALLED age_ms=",
)

def verify(cache: str, eboot: bytes) -> None:
    config = {}
    for line in cache.splitlines():
        if line and not line.startswith(("#", "//")) and "=" in line:
            k, v = line.split("=", 1)
            config[k] = v
    mismatches = [
        f"{k}={config.get(k)!r} (expected {want!r})"
        for k, want in REQUIRED.items() if config.get(k) != want
    ]
    # The native toolchain can declare this -D switch BOOL or leave it as
    # UNINITIALIZED. Validate its value independently of CMake's type.
    native = [value for key, value in config.items()
              if key.split(':', 1)[0] == NATIVE_SETTING]
    if len(native) != 1 or native[0] != "ON":
        mismatches.append(f"{NATIVE_SETTING}={native!r} (expected one ON)")
    # Reject active deprecated research flags and diagnostic subsystems.
    # The old DEV/release profile names are intentionally NOT REQUIRED.
    for key, value in config.items():
        selector = key.split(':', 1)[0]
        if (re.fullmatch(r"EDEN_NS2_.*_EXPERIMENTAL", selector) or
                selector in DISALLOWED_ACTIVE):
            if value.upper() not in OFF_VALUES:
                mismatches.append(f"{key}={value!r} (must be inactive)")
    if mismatches:
        raise ValueError("release compile profile mismatch: " + ", ".join(mismatches))
    missing = [value.decode() for value in MARKERS if value not in eboot]
    if missing:
        raise ValueError("release binary lacks runtime markers: " + ", ".join(missing))

def self_test() -> None:
    valid = "\n".join([*(f"{k}={v}" for k, v in REQUIRED.items()),
                       "PS5_NATIVE:UNINITIALIZED=ON"])
    eboot = b"".join(MARKERS)
    verify(valid, eboot)
    for key, value in REQUIRED.items():
        incorrect = valid.replace(f"{key}={value}", f"{key}=INVALID")
        try:
            verify(incorrect, eboot)
        except ValueError as exc:
            assert key in str(exc)
        else:
            raise AssertionError(f"unnoticed compiler flag mismatch: {key}")
    for injected in (
        "EDEN_NS2_FUTURE_UNREVIEWED_EXPERIMENTAL:BOOL=ON",
        "EDEN_NS2_EXEFS_EXPERIMENTAL:BOOL=ON",
        "EDEN_GUEST_WRITE_BRIDGE_DEV:BOOL=ON",
        "EDEN_UNQUALIFIED_FERMI2D_COPY:BOOL=ON",
    ):
        try:
            verify(valid + "\n" + injected, eboot)
        except ValueError as exc:
            assert injected.split("=", 1)[0] in str(exc)
        else:
            raise AssertionError(f"unreviewed NS2 release selector accepted: {injected}")
    for wrong_native in ("OFF", "FALSE", "INVALID"):
        try:
            verify(valid.replace("PS5_NATIVE:UNINITIALIZED=ON",
                                 f"PS5_NATIVE:UNINITIALIZED={wrong_native}"), eboot)
        except ValueError as exc:
            assert "PS5_NATIVE" in str(exc)
        else:
            raise AssertionError("non-native PS5 configuration accepted")
    verify(valid.replace("PS5_NATIVE:UNINITIALIZED=ON", "PS5_NATIVE:BOOL=ON"), eboot)
    # A non-NS2 flag must not accidentally match the catch-all checker.
    verify(valid + "\nEDEN_UNRELATED_FEATURE:BOOL=ON", eboot)
    for marker in MARKERS:
        try:
            verify(valid, eboot.replace(marker, b""))
        except ValueError as exc:
            assert marker.decode() in str(exc)
        else:
            raise AssertionError(f"missing binary marker accepted: {marker!r}")
    print("PASS: one native compiled application, independently controlled publishing, strict GPU configuration and markers")

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return 0
    if len(sys.argv) != 2:
        print("usage: check-release-experiments.py build/release/PPSA99008", file=sys.stderr)
        return 2
    app = Path(sys.argv[1]).resolve()
    if app != RELEASE.resolve():
        print(f"REJECTED: expected native release staging path {RELEASE}", file=sys.stderr)
        return 1
    try:
        if not CACHE.is_file() or not (app / "eboot.bin").is_file():
            raise ValueError("compiled CMake cache or staged native executable missing")
        verify(CACHE.read_text("utf-8"), (app / "eboot.bin").read_bytes())
    except (OSError, ValueError) as exc:
        print(f"EDEN_RELEASE_EXPERIMENTS_REJECTED: {exc}", file=sys.stderr)
        return 1
    print("EDEN_RELEASE_EXPERIMENTS_COMPILED: sparse=on native_profile=release "
          "cross_core_shared_jit=off batch=off alias_runtime_probe=pending hardware=untested")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
