#!/usr/bin/env python3
"""Host proof for PS5 OpenGL Mesa optional-feature selection."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PINNED = ROOT / "vendor/sources/opengl-source/toolchain/build-mesa-ps5.sh"
PATCHER = ROOT / "tools/ci/patch-ps5-opengl-mesa-options.py"
BUILDER = (ROOT / "tools/build-opengl-sdk.sh").read_text(encoding="utf-8")
MESA_OPTIONS = (ROOT / "vendor/sources/opengl-mesa-26-2/meson.options").read_text(encoding="utf-8")
MESA_BUILD = (ROOT / "vendor/sources/opengl-mesa-26-2/meson.build").read_text(encoding="utf-8")

flags = ("display-info", "spirv-tools", "lmsensors")
raw = PINNED.read_bytes()
for opt in flags:
    assert f"'{opt}'" in MESA_OPTIONS, opt
assert "with_spirv_tools = get_option('spirv-tools')" in MESA_BUILD
assert "required : get_option('display-info')" in MESA_BUILD
assert "required : get_option('lmsensors')" in MESA_BUILD
assert 'patch-ps5-opengl-mesa-options.py" "$mesa_build_script"' in BUILDER
assert 'mv -f "$mesa_build_script_backup" "$mesa_build_script"' in BUILDER
assert 'mesa_build_script_backup="${mesa_build_script}.encore-backup.$"' in BUILDER
assert 'legacy_mesa_backup="$source_dir/toolchain/build-mesa-ps5.sh.encore-backup.$"' in BUILDER
assert 'backup_mesa_sha' in BUILDER and 'expected_mesa_sha' in BUILDER

with tempfile.TemporaryDirectory(prefix="encore-mesa-options-") as td:
    p = Path(td) / "build-mesa-ps5.sh"
    p.write_bytes(raw)
    subprocess.run(["python3", "-B", str(PATCHER), str(p)], cwd=ROOT, check=True)
    out = p.read_text(encoding="utf-8")
    for opt in flags:
        assert out.count(f"-D{opt}=disabled") == 1
    for language in ("c_args", "cpp_args"):
        line = next(line for line in out.splitlines() if line.startswith(f"-D{language}="))
        assert "-Wno-thread-safety-analysis" in line
        assert "-Wno-unreachable-code-generic-assoc" in line
        assert "-Wno-unused-parameter" in line
        assert line.count("-Wno-") == 3
    assert p.read_bytes() != raw
    subprocess.run(["python3", "-B", str(PATCHER), str(p)], cwd=ROOT, check=True)
    assert p.read_text(encoding="utf-8") == out
    # Exact rollback model used by the outer build trap.
    p.write_bytes(raw)
    assert p.read_bytes() == raw
    # Partial selection must fail rather than silently invent a new profile.
    p.write_text(out.replace("-Dlmsensors=disabled\n", ""), encoding="utf-8")
    bad = subprocess.run(["python3", "-B", str(PATCHER), str(p)], cwd=ROOT)
    assert bad.returncode != 0

print("PASS PS5 OpenGL Mesa feature selection + scoped PS5 SDK diagnostic exclusions")
