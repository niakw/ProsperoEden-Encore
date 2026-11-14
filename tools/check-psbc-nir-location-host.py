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
assert 'nir_print_backup="${nir_print_source}.encore-backup.$$"' in build
assert 'cp -p "$nir_print_source" "$nir_print_backup"' in build
assert build.count('mv -f "$nir_print_backup" "$nir_print_source"') == 2
assert 'radv_stub_backup="${radv_stub_source}.encore-backup.$$"' in build
assert 'cp -p "$radv_stub_source" "$radv_stub_backup"' in build
assert build.count('mv -f "$radv_stub_backup" "$radv_stub_source"') == 2
assert build.index('cp -p "$radv_stub_source"') < build.index('patch-psbc-nir-build-hooks.py" "$script"')
assert 'ENCORE_PSBC_NIR_LOCATION_FIX' in build
assert 'export ENCORE_PSBC_NIR_PATCHER=' in build
assert 'python3 -B "$root/tools/ci/patch-psbc-nir-build-hooks.py" "$script"' in build
assert build.index('trap cleanup EXIT') < build.index('patch-psbc-nir-build-hooks.py" "$script"')
assert build.index('python3 "$source_dir/tools/fetch-sources.py"') < build.index(
    'patch-psbc-nir-build-hooks.py" "$script"')
# The base branch may install a Ninja jobserver wrapper before sdk-gl46.
# Match the concrete make invocation independently of its PATH prefix.
sdk_make = 'make -C "$source_dir" sdk-gl46'
assert build.count(sdk_make) == 1
assert build.index('patch-psbc-nir-build-hooks.py" "$script"') < build.index(sdk_make)
assert build.index(sdk_make) < build.index('python3 "$source_dir/tools/fetch-sources.py" --verify-psbc')
assert build.count('${script}.encore-backup.$$"') == 4
assert '${script}.encore-backup.$"' not in build
assert 'cp -p "$script" "${script}.encore-backup.$$"' in build
assert build.count('mv -f "${script}.encore-backup.$$" "$script"') == 2
assert 'python3 -B "$root/tools/ci/patch-psbc-nir-location-print.py" "$nir_print_source"' not in build
subprocess.run(["bash", "-n", str(ROOT / "tools/build-opengl-sdk.sh")], check=True)

# Exercise exact vendored script preimages and actual NIR source compile
# window. Neither a failing compiler command nor an ordinary exit may
# leave the tracked printer modified for the next upstream verifier.
import sys
hook_file = ROOT / "tools/ci/patch-psbc-nir-build-hooks.py"
hook_spec = importlib.util.spec_from_file_location("nir_hooks", hook_file)
assert hook_spec and hook_spec.loader
hook = importlib.util.module_from_spec(hook_spec)
hook_spec.loader.exec_module(hook)
vendor = ROOT / "vendor/sources"
with tempfile.TemporaryDirectory(prefix="psbc-verify-window-") as td:
    work = Path(td)
    for filename in hook.HOOKS:
        original = vendor / "opengl-source/toolchain" / filename
        stage = work / filename
        shutil.copyfile(original, stage)
        assert hook.gitblob(stage.read_bytes()) == hook.HOOKS[filename][0]
        hook.patched_script(stage)
        modified = stage.read_text()
        assert modified.count('--compile') == 1
        assert modified.index('--verify-psbc') < modified.index('--compile')
        subprocess.run(["bash", "-n", str(stage)], check=True)
        try:
            hook.patched_script(stage)
        except ValueError:
            pass
        else:
            raise AssertionError("Repeated hook injection accepted")
    printer = work / "src/compiler/nir/nir_print.c"
    header = work / "src/amd/vulkan/radv_instance.h"
    printer.parent.mkdir(parents=True)
    header.parent.mkdir(parents=True)
    shutil.copyfile(vendor / "opengl-opengnm-psbc/src/compiler/nir/nir_print.c", printer)
    shutil.copyfile(vendor / "opengl-opengnm-psbc/src/amd/vulkan/radv_instance.h", header)
    initial = printer.read_bytes()
    header_initial = header.read_bytes()
    assert module.gitblob(header_initial) == module.PINNED_RADV_STUB
    header_fixed = module.patched_radv_stub(header_initial)
    assert header_fixed.replace(module.RADV_FORWARD, b"", 1) == header_initial
    assert header_fixed.count(module.RADV_FORWARD) == 1
    # Compile the real header, not a hand-written approximation. The opaque
    # type in a C parameter list must agree with a later file-scope definition.
    stub_harness = work / "stub.c"
    stub_harness.write_text("""
#include "radv_instance.h"
#include <assert.h>
struct radv_physical_device { int unused; };
int main(void) {
    struct radv_physical_device device = {0};
    const struct radv_instance *(*fn)(const struct radv_physical_device *) =
        radv_physical_device_instance;
    assert(fn(&device) == fn(0));
    assert(fn(&device)->debug_flags == 0);
    return 0;
}
""")
    for cc in (shutil.which("gcc"), shutil.which("clang")):
        if not cc:
            continue
        exe = work / "stub"
        flags = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror",
                 "-I" + str(header.parent), str(stub_harness), "-o", str(exe)]
        header.write_bytes(header_initial)
        rejected = subprocess.run(flags, capture_output=True, text=True, timeout=30)
        assert rejected.returncode != 0 and "radv_physical_device" in rejected.stderr
        header.write_bytes(header_fixed)
        subprocess.run(flags, check=True, timeout=30)
        subprocess.run([str(exe)], check=True, timeout=20)
    header.write_bytes(header_initial)
    for rc in (0, 7):
        cmd = [sys.executable, "-c",
               'import pathlib,sys; p=pathlib.Path(sys.argv[1]); '
               'assert p.read_bytes().count(b"char buf[11];")==2; '
               'assert (p.parent.parent.parent/"amd/vulkan/radv_instance.h").read_bytes().count(b"struct radv_physical_device;")==1; '
               'sys.exit(int(sys.argv[2]))',
               str(printer), str(rc)]
        assert module.compile_window(printer, cmd) == rc
        assert printer.read_bytes() == initial, "printer leaked after compile"
        assert header.read_bytes() == header_initial, "stub leaked after compile"
    header.write_bytes(header_initial + b"\n/* drift */\n")
    try:
        module.compile_window(printer, [sys.executable, "-c", "raise AssertionError()"])
    except ValueError:
        pass
    else:
        raise AssertionError("Unreviewed RADV stub admitted")
    assert printer.read_bytes() == initial
    header.write_bytes(header_initial)
    printer.write_bytes(initial + b"\\n/* drift */\\n")
    try:
        module.compile_window(printer, [sys.executable, "-c", "raise AssertionError()"])
    except ValueError:
        pass
    else:
        raise AssertionError("Unreviewed printer admitted")

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
print("PSBC_RADV_STUB_FILE_SCOPE_HOST_PASS original_rejected=1 gcc_clang=1 restored=1")
