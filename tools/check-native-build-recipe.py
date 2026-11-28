#!/usr/bin/env python3
"""Replay maintained, full native CMake and SCM files with repeat/rollback checks."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
script=root/"tools/install-vendored-eden-build-flags.py"
specs=(
    ("src/CMakeLists.txt",b"-Wno-error-all>",b"-Wno-error=all>"),
    ("src/common/scm_rev.cpp.in",b'#define BUILD_ID "@BUILD_ID@"',
     b'#ifdef BUILD_ID\n#undef BUILD_ID\n#endif\n#define BUILD_ID "@BUILD_ID@"'),
)
subprocess.run([sys.executable,"-B",str(script)],check=True,timeout=12)
with tempfile.TemporaryDirectory(prefix="eden-native-recipe-") as scratch:
    location=Path(scratch)
    original={}
    for relative,from_bytes,to_bytes in specs:
        source=root/"vendor/sources/eden"/relative
        active=root/"vendor/encore-active/eden"/relative
        old=source.read_bytes()
        assert old.count(from_bytes)==1
        expected=old.replace(from_bytes,to_bytes)
        assert active.read_bytes()==expected
        original[relative]=(old,expected)
        target=location/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(old)
    for iteration in range(2):
        subprocess.run([sys.executable,"-B",str(script),str(location)],check=True,timeout=12)
        for relative,(_old,expected) in original.items():
            assert (location/relative).read_bytes()==expected,(iteration,relative)
    target=location/"src/CMakeLists.txt"
    target.write_bytes(b"unrecognized revision")
    refused=subprocess.run([sys.executable,"-B",str(script),str(location)],
                           capture_output=True,text=True,timeout=12)
    assert refused.returncode!=0
    assert target.read_bytes()==b"unrecognized revision"
    # Compiler warning options MUST be recognized by the native Clang toolchain.
    assert b"-Wno-error-all" not in (location/"src/CMakeLists.txt").read_bytes()
    assert b"#undef BUILD_ID" in (location/"src/common/scm_rev.cpp.in").read_bytes()
# The FFmpeg compiler adapter must keep its existing third-party-only
# warning exclusions AFTER FFmpeg's own -Wall/-Wextra arguments. Earlier
# placement reenabled three warnings on the R457 native release.
ffmpeg = root/"tools/ffmpeg-ps5-cc.sh"
recipe = ffmpeg.read_text()
assert recipe.index('    "${arguments[@]}" \\') < recipe.index('    -Wno-unreachable-code-generic-assoc')
assert recipe.rstrip().endswith(
    '-Wno-unreachable-code-generic-assoc -Wno-unused-function -Wno-unused-label'
)
subprocess.run(["bash", "-n", str(ffmpeg)], check=True, timeout=10)
clang = shutil.which("clang-18") or shutil.which("clang")
if clang:
    with tempfile.TemporaryDirectory(prefix="encore-ffmpeg-warning-order-") as folder:
        src = Path(folder)/"unused.c"
        src.write_text("static void unused(void) {}\nvoid f(void) { unreferenced: ; }\n")
        compiled = subprocess.run([
            clang, "-fsyntax-only", "-Wall", "-Wunused-function", "-Wunused-label",
            "-Wno-unused-function", "-Wno-unused-label", str(src),
        ], capture_output=True, text=True, timeout=12)
        assert compiled.returncode == 0 and "warning:" not in compiled.stderr, compiled.stderr
print("PASS: full CMake & SCM sources installed byte-exact, idempotent, foreign revisions refused; FFmpeg warning flags retain precedence")
