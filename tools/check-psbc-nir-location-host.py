#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail-closed Mesa NIR location-print truncation and source restoration fixture."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
patcher = ROOT / "tools/ci/patch-psbc-nir-location-print.py"
spec = importlib.util.spec_from_file_location("nir_print_patch", patcher)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
raw = (b"static char *print_location(unsigned location, char *buf) {\n"
       b'  snprintf(buf, 4, "%u", location);\n'
       b'  return buf;\n'
       b'}\n'
       b'  char buf[4];\n'
       b'  char buf[4];\n')
fixed = module.patched_bytes(raw)
assert fixed.count(b'char buf[11];') == 2
assert fixed.count(b'snprintf(buf, 11, "%u", location);') == 1
for bad in (
    raw.replace(b'char buf[4];', b'char buf[3];', 1),
    raw.replace(b'snprintf(buf, 4, "%u", location);',
                b'snprintf(buf, 5, "%u", location);'),
    fixed,
    raw + b'  char buf[4];\n',
):
    try:
        module.patched_bytes(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("NIR location buffer source drift accepted")

build = (ROOT / "tools/build-opengl-sdk.sh").read_text()
assert 'nir_print_source="$source_dir/third_party/opengnm-psbc/src/compiler/nir/nir_print.c"' in build
assert 'python3 -B "$root/tools/ci/patch-psbc-nir-location-print.py" "$nir_print_source"' in build
assert 'nir_print_backup="${nir_print_source}.encore-backup.$$"' in build
assert 'cp -p "$nir_print_source" "$nir_print_backup"' in build
assert build.count('mv -f "$nir_print_backup" "$nir_print_source"') == 2
assert build.index('trap cleanup EXIT') < build.index('python3 -B "$root/tools/ci/patch-psbc-nir-location-print.py"')
assert build.index('python3 "$source_dir/tools/fetch-sources.py"') < build.index(
    'python3 -B "$root/tools/ci/patch-psbc-nir-location-print.py"')
assert build.index('python3 -B "$root/tools/ci/patch-psbc-nir-location-print.py"') < build.index(
    'PATH="$opengl_host_path" make -C "$source_dir" sdk-gl46')
script = subprocess.run(["bash", "-n", str(ROOT / "tools/build-opengl-sdk.sh")],
                        text=True, capture_output=True)
assert script.returncode == 0, script.stderr

# Shader reflection/debug location indices are unsigned 32-bit: decimal max
# is ten characters. Verify the actual count including NUL, both callers,
# and surrounding guards with the C compiler, not just a string match.
c_source = r"""
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static const char *get_location_str(unsigned location, char *buf) {
    snprintf(buf, 11, "%u", location);
    return buf;
}
static void first_caller(unsigned loc) {
    struct {char before; char buf[11]; char after;} guard = {'A', {0}, 'Z'};
    const char *text = get_location_str(loc, guard.buf);
    assert(text == guard.buf && guard.before == 'A' && guard.after == 'Z');
    assert(strlen(text) == (loc == UINT_MAX ? 10u : 1u));
}
static void second_caller(unsigned loc) {
    struct {char before; char buf[11]; char after;} guard = {'A', {0}, 'Z'};
    assert(get_location_str(loc, guard.buf) == guard.buf);
    assert(strcmp(guard.buf, "4294967295") == 0);
    assert(guard.before == 'A' && guard.after == 'Z');
}
int main(void) {
    first_caller(0);
    first_caller(UINT_MAX);
    second_caller(UINT_MAX);
}
"""
compilers = [c for c in (shutil.which("gcc"), shutil.which("clang")) if c]
assert compilers
with tempfile.TemporaryDirectory(prefix="psbc-nir-print-") as tmpdir:
    work = Path(tmpdir)
    file = work / "loc.c"
    file.write_text(c_source)
    for compiler in compilers:
        exe = work / (Path(compiler).name + "-loc")
        flags = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                 "-fsanitize=undefined", "-fno-sanitize-recover=all"]
        # GCC supports the extra static printf-truncation diagnostic; Clang
        # instead checks the concrete guarded max-uint32 output at runtime.
        if "gcc" in Path(compiler).name:
            flags.append("-Wformat-truncation=2")
        subprocess.run(flags + [str(file), "-o", str(exe)],
                       check=True, timeout=30)
        subprocess.run([str(exe)], check=True, timeout=20)
print("PSBC_NIR_LOCATION_11_BYTE_HOST_PASS callers=2 max_u32=4294967295 "
      "drift_rejected=1 original_restored=1")
