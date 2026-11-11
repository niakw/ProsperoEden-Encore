#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""PSBC noreturn compile proof, fail-closed config patch, source restoration."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
helper = root / "tools/ci/patch-psbc-noreturn-flags.py"
spec = importlib.util.spec_from_file_location("psbc_noreturn", helper)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original = b"SHARED_FLAGS=\\\n\t-DHAVE_FUNC_ATTRIBUTE_PACKED=1 \\\n\t-DBLAKE3_NO_SSE2\n"
patched = module.patched_bytes(original)
assert patched.count(b"-DHAVE_FUNC_ATTRIBUTE_NORETURN=1") == 1
for bad in (original.replace(b"-DHAVE_FUNC_ATTRIBUTE_PACKED=1", b"-DOTHER=1"),
            patched, original.replace(b"-DBLAKE3_NO_SSE2", b"-DHAVE_FUNC_ATTRIBUTE_PACKED=1")):
    try:
        module.patched_bytes(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid PSBC config accepted")
build = (root / "tools/build-opengl-sdk.sh").read_text()
assert build.count('python3 -B "$root/tools/ci/patch-psbc-noreturn-flags.py" "$cfg"') == 1
assert "toolchain/opengnm-psbc-host.mak" in build
assert "toolchain/opengnm-psbc-ps5.mak" in build
assert "psbc_configs=()" in build and "encore-backup.$$" in build
cc = shutil.which("gcc") or shutil.which("clang")
assert cc, "GCC or Clang required"
code = r"""
#ifdef HAVE_FUNC_ATTRIBUTE_NORETURN
#define NORETURN __attribute__((__noreturn__))
#else
#define NORETURN
#endif
NORETURN void fail_shader(void);
int translate_shader(int opcode) { if (opcode == 1) return 1; fail_shader(); }
void fail_shader(void) { __builtin_trap(); }
"""
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "flow.c"
    out = Path(tmp) / "flow.o"
    src.write_text(code)
    base = subprocess.run([cc, "-std=gnu11", "-O2", "-Wall", "-Werror=return-type",
                           "-c", str(src), "-o", str(out)], capture_output=True, text=True)
    assert base.returncode != 0 and "return" in base.stderr.lower(), base.stderr
    good = subprocess.run([cc, "-std=gnu11", "-O2", "-Wall", "-Werror=return-type",
                           "-DHAVE_FUNC_ATTRIBUTE_NORETURN=1",
                           "-c", str(src), "-o", str(out)], capture_output=True, text=True)
    assert good.returncode == 0, good.stderr
print("PASS PSBC host/PS5 noreturn attribute, compiler proof, guarded restoration")
