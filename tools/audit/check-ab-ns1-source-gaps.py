#!/usr/bin/env python3
"""Read-only static NS1 source-gap triage for Eden Encore PR #45.

Does not build, modify, or validate the PS5 binary. Requires initialized vendor.
Default exit zero reports debt; --fail-on-gap is an opt-in diagnostic only.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    file = ROOT / path
    if not file.is_file():
        raise FileNotFoundError(f"Missing audited input: {path}")
    return file.read_text(encoding="utf-8", errors="replace")


def body(src: str, symbol: str) -> str | None:
    matches = list(re.finditer(r"\b" + re.escape(symbol) +
        r"\s*\([^;{}]*\)(?:\s+(?:const|override|final|noexcept))*\s*\{", src))
    if len(matches) != 1:
        return None
    start = matches[0].end() - 1
    depth = 0
    for n in range(start, len(src)):
        if src[n] == "{":
            depth += 1
        elif src[n] == "}":
            depth -= 1
            if not depth:
                return src[start + 1:n]
    return None


def triage() -> dict:
    cmake = read("headless/CMakeLists.txt")
    shader = read("vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp")
    radv = read("vendor/encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c")
    meta_base = "vendor/sources/ps5-mesa/src/amd/vulkan/meta/"
    meta = read(meta_base + "radv_meta_buffer.c") + "\n" + read(meta_base + "radv_meta_copy.c")
    romfs = read("vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp")
    audio = read("headless/audio.cpp")
    null = read("vendor/sources/eden/src/audio_core/sink/null_sink.h")
    device = read("vendor/sources/eden/src/audio_core/device/device_session.cpp")
    main = read("headless/main.cpp")
    installer = read("tools/install-vendored-radv.py")

    # This owner is selected only when the shared native SPIR-V path is enabled.
    frag = body(shader, "EmitSetFragColor")
    shader_selected = ('EDEN_NS2_QMD_CBUF_DIRECT_SPIRV' in cmake and
                       'set_property(TARGET shader_recompiler PROPERTY SOURCES' in cmake)
    nan_guard = frag is not None and "OpIsNan" in frag and "OpSelect" in frag

    barrier = body(radv, "radv_CmdPipelineBarrier2")
    commands = ("radv_CmdFillBuffer", "radv_CmdCopyBuffer2",
                "radv_CmdUpdateBuffer", "radv_CmdCopyBufferToImage2",
                "radv_CmdCopyImageToBuffer2")
    direct = {name: None if body(meta, name) is None else
              "radv_split_cmd_stream_if_due" in body(meta, name)
              for name in commands}
    barrier_split = None if barrier is None else "radv_split_cmd_stream_if_due" in barrier
    radv_gap = barrier_split is False or any(x is False for x in direct.values())

    destructor = body(romfs, "~RomFSBuildContext")
    romfs_default = "RomFSBuildContext::~RomFSBuildContext() = default;" in romfs
    romfs_unlink = destructor is not None and all(
        x in destructor for x in ("sibling.reset()", "child.reset()", "file.reset()"))

    null_body = body(null, "ReleaseBuffer")
    device_body = body(device, "ReleaseBuffer")
    null_input = bool(re.search(
        r"StreamType::In\s*\?\s*SinkStreamPtr\s*\{\s*std::make_unique<NullSinkStreamImpl>", audio))
    empty_release = null_body is not None and "return {};" in null_body
    unchecked_copy = (device_body is not None and
        "WriteBlockUnsafe(buffer.samples, samples.data(), buffer.size)" in device_body)

    return {
        "AB-01-shader-NaN": {
            "classification": "unknown" if frag is None or not shader_selected else
                "guard-present-in-source" if nan_guard else "source-gap",
            "conditional_shared_source_selected": shader_selected,
            "float_output_nan_guard": nan_guard,
        },
        "AB-02-RADV-transfer": {
            "classification": "source-gap" if radv_gap else "unknown" if
                barrier_split is None or any(x is None for x in direct.values()) else
                "direct-guards-present",
            "pipeline_barrier_direct_guard": barrier_split,
            "transfer_direct_guards": direct,
            "meta_units_part_of_active_12_override_list": (
                "src/amd/vulkan/meta/radv_meta_buffer.c" in installer or
                "src/amd/vulkan/meta/radv_meta_copy.c" in installer),
        },
        "AB-03-RomFS": {
            "classification": "source-gap" if romfs_default else
                "unlink-present" if romfs_unlink else "unknown",
            "maintained_source_selected": "EDEN_MAINTAINED_ROMFS_BUILDER" in cmake,
            "default_destructor": romfs_default,
        },
        "AB-04-AudioIn": {
            "classification": "source-gap" if null_input and empty_release and unchecked_copy
                else "unknown",
            "input_uses_null_sink": null_input,
            "null_sink_returns_empty": empty_release,
            "device_copies_requested_byte_count": unchecked_copy,
            "ps5_input_device_explicitly_selected": (
                'Settings::values.audio_input_device_id = "ps5"' in main),
        },
    }


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--fail-on-gap", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        assert body("void f(int i) { if (i) { i++; } }", "f") == " if (i) { i++; } "
        assert body("void f(int);", "f") is None
        assert body("void f() {} void f() {}", "f") is None
        # Concrete pinned NullSink signature: "override" follows the argument list.
        assert "return {};" in body("std::vector<s16> ReleaseBuffer(u64) override { return {}; }", "ReleaseBuffer")
        assert body("void f() const override { int x = 1; }", "f") == " int x = 1; "
        assert body("void f() noexcept { return; }", "f") == " return; "
        assert body("void f() override;", "f") is None
        print("AB_NS1_SOURCE_TRIAGE_SELFTEST_OK")
        return 0
    try:
        report = triage()
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "incomplete-inputs", "error": str(error)}))
        return 2
    print(json.dumps({
        "mode": "static-source-only",
        "no_device_or_binary_proof": True,
        "results": report,
    }, indent=2, sort_keys=True))
    return int(args.fail_on_gap and any(
        x["classification"] == "source-gap" for x in report.values()))


if __name__ == "__main__":
    sys.exit(main_cli())
