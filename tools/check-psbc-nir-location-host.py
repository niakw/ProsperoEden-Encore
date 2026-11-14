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
assert 'amd/compiler/aco_lower_to_hw_instr.cpp' in build
assert 'compiler/nir/nir_unlower_io_to_vars.c' in build
assert 'amd/compiler/aco_spill_preserved.cpp' in build
assert 'amd/vulkan/nir/radv_nir_lower_descriptors.c' in build
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
    extras = []
    owner_patchers = [(module.ACO_PATH, module.patched_aco),
                      (module.NIR_MASK_PATH, module.patched_nir_mask)]
    owner_patchers.extend(
        (rel, lambda raw, rel=rel: module.patched_assert_warning(rel, raw))
        for rel in module.ASSERT_WARNING_OWNERS
    )
    for rel, fn in owner_patchers:
        stage = work / "src" / rel
        stage.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(vendor / "opengl-opengnm-psbc/src" / rel, stage)
        prior = stage.read_bytes()
        updated = fn(prior)
        assert prior != updated
        try:
            fn(prior + b"\n/* drift */\n")
        except ValueError:
            pass
        else:
            raise AssertionError("Unreviewed compiler owner admitted")
        extras.append((stage, prior, updated))
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
               'assert (p.parent.parent.parent/"amd/compiler/instruction_selection/aco_select_nir_intrinsics.cpp").read_bytes().count(b"static_cast<unsigned>(ffs(const_offset))")==2; '
               'assert b"nir_channels(&b, value, nir_component_mask(num_dwords))" in (p.parent.parent.parent/"amd/common/nir/ac_nir_meta_cs_clear_copy_buffer.c").read_bytes(); '
               'sys.exit(int(sys.argv[2]))',
               str(printer), str(rc)]
        assert module.compile_window(printer, cmd) == rc
        assert printer.read_bytes() == initial, "printer leaked after compile"
        assert header.read_bytes() == header_initial, "stub leaked after compile"
        for stage, prior, updated in extras:
            assert stage.read_bytes() == prior, "compiler owner leaked after compile"
    # Recreate the precise post-verification source state from the vendor's
    # official platform patch. Do not accept arbitrary alternate digests.
    import hashlib
    patch = vendor / "opengl-source/toolchain/opengnm-psbc-ps5.patch"
    assert hashlib.sha256(patch.read_bytes()).hexdigest() == "35967c8fef5aff9fa30928314093706597d5beaa1b7e378f37fb37367c03d0b9"
    changed = {
        module.ACO_PATH: "a73de0a574bea1cc6f421525047604bebe0be2e6",
        "amd/compiler/aco_lower_to_hw_instr.cpp": "3a6346cba427c411ae4cd839989a0b885770de06",
        "amd/vulkan/nir/radv_nir_lower_descriptors.c": "71ac6f6f01fc5e14102487812fb714e0abb93f99",
    }
    subprocess.run(["git", "init", "-q"], cwd=work, check=True, timeout=30)
    subprocess.run(["git", "apply", *["--include=src/"+rel for rel in changed],
                    str(patch)], cwd=work, check=True, timeout=30)
    staged = {stage: stage.read_bytes() for stage, _, _ in extras}
    for relative, digest in changed.items():
        assert module.gitblob((work/"src"/relative).read_bytes()) == digest
    for rc in (0, 7):
        cmd = [sys.executable, "-c",
               'import pathlib,sys; root=pathlib.Path(sys.argv[1]); '
               'assert b"ASSERTED bool non_linear_vgpr" in (root/"amd/compiler/aco_lower_to_hw_instr.cpp").read_bytes(); '
               'assert b"ASSERTED bool indirect" in (root/"amd/vulkan/nir/radv_nir_lower_descriptors.c").read_bytes(); '
               'sys.exit(int(sys.argv[2]))',
               str(work/"src"), str(rc)]
        assert module.compile_window(printer, cmd) == rc
        assert all(stage.read_bytes() == prior for stage, prior in staged.items())
        assert printer.read_bytes() == initial and header.read_bytes() == header_initial
    for stage, prior, _ in extras:
        stage.write_bytes(prior)
    print("PSBC_ASSERT_WARNING_STAGED_TREE_PASS exact_upstream_patch=1 postimages=3 restored=1")
    header.write_bytes(header_initial + b"\n/* drift */\n")
    try:
        module.compile_window(printer, [sys.executable, "-c", "raise AssertionError()"])
    except ValueError:
        pass
    else:
        raise AssertionError("Unreviewed RADV stub admitted")
    assert printer.read_bytes() == initial
    header.write_bytes(header_initial)
    for stage, prior, updated in extras:
        stage.write_bytes(prior + b"\n/* drift */\n")
        try:
            module.compile_window(printer, [sys.executable, "-c", "raise AssertionError()"])
        except ValueError:
            pass
        else:
            raise AssertionError("Drifted compiler owner passed compile window")
        assert printer.read_bytes() == initial and header.read_bytes() == header_initial
        stage.write_bytes(prior)
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

# Exercise the exact replacement expressions without linking the complete Mesa compiler.
# POSIX ffs is 0..32; preserve all 32-bit one-hot positions and 0.
aco_harness = r"""
#include <cassert>
#include <cstdint>
#include <strings.h>
bool old_semantics(uint32_t const_offset, unsigned req_lsb_zero) {
    return !const_offset || (static_cast<unsigned>(ffs(const_offset)) > req_lsb_zero);
}
bool fixed(uint32_t const_offset, unsigned req_lsb_zero) {
    return !const_offset || REPLACED;
}
int main() {
    uint32_t offset=0;
    for(unsigned n=0;n<3;++n) assert(fixed(offset,n));
    for(unsigned bit=0;bit<32;++bit) {
        offset=uint32_t{1}<<bit;
        for(unsigned n=0;n<3;++n) assert(fixed(offset,n)==old_semantics(offset,n) && fixed(offset,n)==(bit>=n));
    }
}
""".replace("REPLACED", module.ACO_AFTER.decode())
mask_harness = r"""
#include <assert.h>
#include <stdint.h>
typedef uint16_t nir_component_mask_t;
static inline nir_component_mask_t nir_component_mask(unsigned num_components) {
    assert(num_components>=1 && num_components<=3);
    return (1u << num_components)-1;
}
typedef struct {} nir_def;
static unsigned seen;
static nir_def *nir_channels(int *b,nir_def *value,nir_component_mask_t mask) {
    (void)b; seen=mask; return value;
}
int main(void) {
    int b=0; nir_def storage={}; nir_def *value=&storage;
    for(unsigned dwords_per_thread=1;dwords_per_thread<=4;++dwords_per_thread)
        for(unsigned bytes=1;bytes<dwords_per_thread*4;++bytes) {
            unsigned num_dwords=bytes/4;
            if (num_dwords) {
                assert(REPLACED==value);
                assert(seen==((1u<<num_dwords)-1));
            }
        }
}
""".replace("REPLACED", module.MASK_AFTER.decode())
with tempfile.TemporaryDirectory(prefix="psbc-warning-domain-") as td:
    work=Path(td)
    for compiler,src,ext,std in ((shutil.which("g++"),aco_harness,"cpp","c++17"),
                                  (shutil.which("clang++"),aco_harness,"cpp","c++17"),
                                  (shutil.which("clang"),mask_harness,"c","gnu11"),
                                  (shutil.which("gcc"),mask_harness,"c","gnu11")):
        if not compiler:
            continue
        path=work/("check."+ext)
        path.write_text(src)
        exe=work/"check"
        subprocess.run([compiler,"-std="+std,"-Wall","-Wextra","-Werror",
                        "-fsanitize=undefined","-fno-sanitize-recover=all",
                        str(path),"-o",str(exe)],check=True,timeout=30)
        subprocess.run([str(exe)],check=True,timeout=20)
print("PSBC_ACO_NIR_WARNING_DOMAINS_PASS all_ffs_bits=32 partial_store=1..3 source_restored=1")

print("PSBC_ASSERT_ONLY_WARNING_OWNERS_HOST_PASS count=4 exact_preimages=1 restoration=1")
