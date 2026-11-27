#!/usr/bin/env python3
"""Pin full A32/A64 emitters, shared RSB body and real CMake source selection."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
owned = root / "vendor/encore-active/eden/src/dynarmic/src/dynarmic/backend/x64"
upstream = root / "vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64"
read = lambda base, name: (base / name).read_text()
cm = read(root / "headless", "CMakeLists.txt")
macros = read(root / "headless/dynarmic", "shared-jit.cmake")
orig32 = read(upstream, "a32_emit_x64.cpp")
orig64 = read(upstream, "a64_emit_x64.cpp")
orig_h = read(upstream, "a64_emit_x64.h")
a32 = read(owned, "a32_emit_x64.cpp")
a64 = read(owned, "a64_emit_x64_standard.cpp")
shared = read(owned, "a64_emit_x64_shared.cpp")
normal_h = read(owned, "a64_emit_x64_standard.h")
shared_h = read(owned, "a64_emit_x64_shared.h")
old_lookup = (
    "        code.DisableWriting();\n"
    "        (*fast_dispatch_table_lookup)(location.Value()) = {};\n"
    "        code.EnableWriting();"
)
new_lookup = (
    "        // The prelude stays RX while dispatch entries change.\n"
    "        (*fast_dispatch_table_lookup)(location.Value()) = {};"
)
assert orig32.count(old_lookup) == orig64.count(old_lookup) == 1
assert a32 == orig32.replace(old_lookup, new_lookup), "A32 original-to-maintained parity"
original = orig64.replace(old_lookup, new_lookup)
sig = "A64EmitX64::Emit(IR::Block& block) noexcept"
publish_sig = "A64EmitX64::Emit(IR::Block& block, bool publish) noexcept"
ending = "    code.DisableWriting();\n    shared_labels.clear();"
publish_end = "    if (publish) code.DisableWriting();\n    shared_labels.clear();"
assert original.count(sig) == original.count(ending) == 1
# Replace complete declarations: directives cannot split return type/name
# or share the #endif line with the function's opening brace.
full_sig = "A64EmitX64::BlockDescriptor " + sig + " {"
full_publish_sig = "A64EmitX64::BlockDescriptor " + publish_sig + " {"
assert original.count(full_sig) == 1
expected_std = original.replace(
    full_sig, "#if defined(EDEN_JIT_A64_PUBLISH)\n" + full_publish_sig
    + "\n#else\n" + full_sig + "\n#endif"
).replace(
    ending, "#if defined(EDEN_JIT_A64_PUBLISH)\n" + publish_end + "\n#else\n" + ending + "\n#endif"
)
assert a64 == expected_std, "A64 standard original-to-maintained parity"
proto = "    BlockDescriptor Emit(IR::Block& block) noexcept;"
pub_proto = "    BlockDescriptor Emit(IR::Block& block, bool publish = true) noexcept;"
assert orig_h.count(proto) == 1
# P0: vendor #104 introduced a PS5_NATIVE-dependent A64EmitX64 array.
# The native graph compiles the owning a64_interface.cpp with PS5_NATIVE=1,
# but its a64_emit_x64.cpp and a64_emit_x64_memory.cpp methods without it.
# Therefore independent compiler passes accepted incompatible C++ layouts.
# Keep exactly ONE unconditional array size and hash mask across every TU.
dispatch_old = ("    static constexpr u64 fast_dispatch_table_mask = 0xFFFFF0;\n"
                "    static constexpr size_t fast_dispatch_table_size = 0x100000;")
expected_h = orig_h.replace(proto,
    "#if defined(EDEN_JIT_A64_PUBLISH)\n" + pub_proto
    + "\n#else\n" + proto + "\n#endif")
assert orig_h.count(dispatch_old) == expected_h.count(dispatch_old) == 1
assert normal_h == expected_h, "A64 dispatch class ABI drift from pinned stable layout"
assert normal_h.count(dispatch_old) == 1
assert "fast_dispatch_table_size = 0x10000;" not in normal_h
assert "fast_dispatch_table_size = 0x10000;" not in shared_h
assert "fast_dispatch_table_size = 0x10000;" not in orig_h

# Verify split compile ownership. Never change core PS5_NATIVE globally merely
# to mask this ABI mismatch; its other uses are intentionally source-scoped.
assert 'target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/a64_interface.cpp")' in cm
assert 'target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/a${bits}_emit_x64.cpp")' in cm
assert 'TARGET_DIRECTORY dynarmic APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"' in cm
dispatch_begin = normal_h.index(dispatch_old, normal_h.index(
    "static_assert(sizeof(FastDispatchEntry) == 0x10);"))
dispatch_end = normal_h.index("\n\n    void ClearFastDispatchTable();", dispatch_begin)
dispatch_selected = normal_h[dispatch_begin:dispatch_end]
assert "#if" not in dispatch_selected and "#else" not in dispatch_selected
compiler_dispatch = shutil.which("clang++") or shutil.which("g++")
assert compiler_dispatch, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-ps5-dispatch-abi-") as folder:
    src = Path(folder) / "dispatch.cpp"
    src.write_text(
        "#include <cstdint>\n"
        "#include <cstddef>\n"
        "using u64 = std::uint64_t;\n"
        "using std::size_t;\n"
        "struct A64Dispatch {\n" + dispatch_selected
        + "\nstruct Entry { u64 location; void* code; };\n"
        "Entry entries[fast_dispatch_table_size];\n};\n"
        "static_assert(A64Dispatch::fast_dispatch_table_mask == 0xFFFFF0);\n"
        "static_assert(A64Dispatch::fast_dispatch_table_size == 0x100000);\n"
        "static_assert(sizeof(A64Dispatch) == 16 * 1024 * 1024);\n")
    for flags in ([], ["-DPS5_NATIVE=1"]):
        result = subprocess.run(
            [compiler_dispatch, "-std=c++20", "-Werror", "-Wall", "-fsyntax-only",
             *flags, str(src)], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, (flags, result.stderr)
print("ENCORE_A64_PS5_DISPATCH_ABI_PASS all_TUs=16MiB stable_layout=1")

assert pub_proto in shared_h and proto not in shared_h
assert "JitGroup* eden_group = nullptr;" in shared_h
assert "eden_pending_sites" in shared_h
assert shared.count(publish_sig) == 1 and publish_end in shared
shared_root = root / "vendor/encore-active/eden/src/dynarmic/src/dynarmic/backend/x64"
assert read(shared_root, "jit_push_rsb.inc") in shared
assert read(shared_root, "jit_links.inc") in shared
assert "macro(eden_shared_jit_emitter_header)" not in macros
assert "macro(eden_shared_jit_emitter)" not in macros

# ABI contract: both caller and implementation must see publish signature.
# The unified PS5 target installs standard emitter/header unconditionally.
# Shared/Publish remain exact historical source+ABI host witnesses below;
# no caller-supplied DEV/JIT profile can alter the production source graph.
assert 'target_compile_definitions(dynarmic PRIVATE EDEN_JIT_A64_PUBLISH=1)' not in cm
assert 'if(EDEN_SHARED_JIT OR EDEN_JIT_COMPILE_BATCH)' not in cm
assert 'set(EDEN_A64_EMITTER_UNIT "${EDEN_MAINTAINED_EMIT_ROOT}/a64_emit_x64_standard.cpp")' in cm
assert 'set(EDEN_A64_EMITTER_HEADER "${EDEN_MAINTAINED_EMIT_ROOT}/a64_emit_x64_standard.h")' in cm
assert 'write_derived("${PORT_BUILD_DIR}/a${bits}_emit_x64.cpp"' not in cm
assert 'configure_file("${EDEN_EMITTER_UNIT}" "${PORT_BUILD_DIR}/a${bits}_emit_x64.cpp" COPYONLY)' in cm
assert shutil.which("cmake"), "CMake required"
start = cm.index('set(EDEN_MAINTAINED_EMIT_ROOT "')
stop = cm.index('foreach(bits 32 64)\n    if(bits EQUAL 64)', start)
selected_cmake = cm[start:stop]
with tempfile.TemporaryDirectory(prefix="encore-emitters-") as tmp:
    tmp = Path(tmp)
    for shared_mode in (False, True):
        for native in (False, True):
            for batch in (False, True):
                for dev in (False, True):
                    name = f"{int(shared_mode)}-{int(native)}-{int(batch)}-{int(dev)}"
                    output = tmp / name
                    output.mkdir()
                    script = tmp / (name + ".cmake")
                    script.write_text(
                        "cmake_minimum_required(VERSION 3.25)\n"
                        + f'set(PORT_ROOT "{root.as_posix()}")\n'
                        + f'set(PORT_BUILD_DIR "{output.as_posix()}")\n'
                        + f'set(EDEN_SHARED_JIT {"ON" if shared_mode else "OFF"})\n'
                        + f'set(PS5_NATIVE {"ON" if native else "OFF"})\n'
                        + f'set(EDEN_JIT_COMPILE_BATCH {"ON" if batch else "OFF"})\n'
                        + f'set(EDEN_DEV_PROFILE {"ON" if dev else "OFF"})\n'
                        + selected_cmake
                        + 'configure_file("${EDEN_A64_EMITTER_UNIT}" "${PORT_BUILD_DIR}/a64_emit_x64.cpp" COPYONLY)\n'
                        + 'configure_file("${EDEN_MAINTAINED_EMIT_ROOT}/a32_emit_x64.cpp" "${PORT_BUILD_DIR}/a32_emit_x64.cpp" COPYONLY)\n'
                    )
                    subprocess.run(["cmake", "-P", str(script)], check=True, timeout=30)
                    assert (output / "a32_emit_x64.cpp").read_text() == a32
                    assert (output / "a64_emit_x64.cpp").read_text() == a64
                    assert (output / "include/dynarmic/backend/x64/a64_emit_x64.h").read_text() == normal_h
print("ENCORE_EMITTER_OWNERS_PASS source=standard shared_source=reviewed profile_inputs_ignored=16")

# Compile actual header/implementation signature boundaries in both standard
# modes and the shared mode. Full-unit parity alone reproduced the malformed
# historical preprocessor placement and therefore could not detect this bug.
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
old_signature = "A64EmitX64::BlockDescriptor #if defined(EDEN_JIT_A64_PUBLISH)\n" + publish_sig + "\n#else\n" + sig + "\n#endif {\n"
normal_proto = "#if defined(EDEN_JIT_A64_PUBLISH)\n" + normal_h.split(
    "#if defined(EDEN_JIT_A64_PUBLISH)\n", 1)[1].split("#endif", 1)[0] + "#endif\n"
def signature(unit):
    return unit.split("A64EmitX64::~A64EmitX64() = default;", 1)[1].split(
        "    if (conf.very_verbose_debugging_output)", 1)[0]
with tempfile.TemporaryDirectory(prefix="encore-emit-signature-") as folder:
    folder = Path(folder)
    for mode, proto_text, implementation, flags in (
        ("old", normal_proto, old_signature, []),
        ("normal", normal_proto, signature(a64), []),
        ("publish", normal_proto, signature(a64), ["-DEDEN_JIT_A64_PUBLISH=1"]),
        ("shared", pub_proto, signature(shared), ["-DEDEN_JIT_A64_PUBLISH=1"]),
    ):
        path = folder / (mode + ".cpp")
        path.write_text("namespace IR { struct Block {}; }\n"
                        "struct A64EmitX64 { struct BlockDescriptor {};\n" + proto_text
                        + "\n};\n" + implementation + "    return {};\n}\n"
                        "int main() { IR::Block block; A64EmitX64 emitter; emitter.Emit(block); }\n")
        result = subprocess.run([compiler, "-std=c++20", "-Werror", "-fsyntax-only",
                                 *flags, str(path)], capture_output=True, text=True, timeout=30)
        if mode == "old":
            assert result.returncode != 0 and "#" in result.stderr, result.stderr
        else:
            assert result.returncode == 0, (mode, result.stderr)
print("EMITTER_SIGNATURE_COMPILE_PASS modes=normal,publish,shared old_signature=rejected")
