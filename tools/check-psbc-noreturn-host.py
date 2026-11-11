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
assert "psbc_configs=()" in build
# P5 inputs must be restored on failures during the early PS5 SDK cross-file
# mutation, not only failures during the later PSBC/Mesa build.
assert build.index("trap cleanup EXIT") < build.index("if ! grep -q")
# The PSBC config backups must be per-process: a fixed ".backup.$" path can
# be overwritten by overlapping builds and silently restore the wrong input.
assert build.count('${cfg}.encore-backup.' + chr(36) * 2 + '"') == 4
assert build.count('${cfg}.encore-backup.' + chr(36) + '"') == 0
syntax = subprocess.run(["bash", "-n", str(root / "tools/build-opengl-sdk.sh")],
                        capture_output=True, text=True)
assert syntax.returncode == 0, syntax.stderr
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

# Exercise the real cleanup function against sandbox files on both early
# and late simulated failure. Never invokes SDK builder or modifies vendor.
import re
cleanup = re.search(r"(?ms)^cleanup\(\) \{\n.*?^\}\ntrap cleanup EXIT\n", build)
assert cleanup, "cleanup/trap must remain a contiguous shell function"
for scenario in ("early", "late"):
    with tempfile.TemporaryDirectory(prefix="encore-psbc-rollback-") as sandbox:
        harness = r"""
set -euo pipefail
root="$1"
stage="$root/stage"
cross_file="$root/cross.ini"
host_test="$root/host-test.c"
psbc_host="$root/host.mak"
psbc_ps5="$root/ps5.mak"
cross_backup=""
host_test_backup=""
psbc_configs=()
mkdir -p "$stage"
printf 'original cross\n' > "$cross_file"
printf 'original host test\n' > "$host_test"
printf 'original host config\n' > "$psbc_host"
printf 'original ps5 config\n' > "$psbc_ps5"
""" + cleanup.group() + r"""
cross_backup="${cross_file}.encore-backup.PIDTOKEN"
cp -p "$cross_file" "$cross_backup"
printf 'mutated cross\n' > "$cross_file"
if [[ "$2" == late ]]; then
    host_test_backup="${host_test}.encore-backup.PIDTOKEN"
    cp -p "$host_test" "$host_test_backup"
    printf 'mutated host test\n' > "$host_test"
    for cfg in "$psbc_host" "$psbc_ps5"; do
        cp -p "$cfg" "${cfg}.encore-backup.PIDTOKEN"
        psbc_configs+=("$cfg")
        printf 'mutated compiler config\n' > "$cfg"
    done
fi
exit 31
"""
        harness = harness.replace(".encore-backup.PIDTOKEN", ".encore-backup." + chr(36) * 2)
        observed = subprocess.run(["bash", "-c", harness, "rollback-host", sandbox, scenario],
                                  capture_output=True, text=True)
        assert observed.returncode == 31, (scenario, observed.stderr)
        expected = {"cross.ini": b"original cross\n",
                    "host-test.c": b"original host test\n",
                    "host.mak": b"original host config\n",
                    "ps5.mak": b"original ps5 config\n"}
        for filename, contents in expected.items():
            assert (Path(sandbox) / filename).read_bytes() == contents, (scenario, filename)
        assert not (Path(sandbox) / "stage").exists(), scenario
        assert not list(Path(sandbox).glob("*.encore-backup.*")), scenario

print("PASS PSBC host/PS5 noreturn attribute, compiler proof, guarded restoration")
