#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile and link the complete selected JXR source graph on the host."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
JXR = VENDOR / "sources/jxrlib"
ADAPTER = VENDOR / "encore-active/ps5-jxr"
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
groups = ("image/sys", "image/decode", "image/encode", "jxrgluelib")
sources = []
for group in groups:
    assert ('"${EDEN_JXR_ROOT}/' + group + '/*.c"') in cmake
    group_sources = sorted((JXR / group).glob("*.c"))
    assert group_sources, group
    sources.extend(group_sources)
assert len(sources) == len(set(sources))
assert '"${EDEN_JXR_ADAPTER}/jxr_decoder.c")' in cmake
assert "target_link_libraries(eden-ps5-jxr PUBLIC webp)" in cmake
assert "target_link_libraries(eden-headless PRIVATE eden-ps5-jxr)" in cmake

harness = r"""
#include <assert.h>
#include <stdio.h>
#include <unistd.h>
#include "jxr_decoder.h"
int main(void) {
    assert(!encore_jxr_to_webp(NULL, "out.webp"));
    assert(!encore_jxr_to_webp("missing.jxr", "out.webp"));
    assert(!encore_jxr_to_webp("short.jxr", "out.webp"));
    assert(!encore_jxr_to_webp("oversized.jxr", "out.webp"));
    assert(!encore_jxr_to_webp("link.jxr", "out.webp"));
    assert(access("out.webp", F_OK) != 0);
    return 0;
}
"""
with tempfile.TemporaryDirectory(prefix="jxr-combined-host-") as temp:
    work = Path(temp)
    code = work / "harness.c"
    code.write_text(harness)
    (work / "short.jxr").write_bytes(b"JXR")
    with (work / "oversized.jxr").open("wb") as stream:
        stream.truncate(48 * 1024 * 1024 + 1)
    (work / "link.jxr").symlink_to("oversized.jxr")
    includes = [ADAPTER, JXR, JXR / "common/include", JXR / "image/sys",
                JXR / "jxrgluelib", JXR / "image/decode", JXR / "image/encode"]
    exe = work / "jxr-host"
    command = ["clang", "-std=gnu11", "-O1", "-g",
               "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
               "-D__ANSI__", "-DDISABLE_PERF_MEASUREMENT", "-msse2",
               "-Werror=implicit-function-declaration", "-Werror=incompatible-pointer-types",
               "-include", str(JXR / "jxr_compat.h")]
    command += ["-I" + str(path) for path in includes]
    command += [str(path) for path in sources + [ADAPTER / "jxr_decoder.c", code]]
    command += ["-o", str(exe), "-lwebp", "-lm"]
    subprocess.run(command, check=True, cwd=work, timeout=300)
    subprocess.run([str(exe)], check=True, cwd=work, timeout=30)
print(f"JXR_COMBINED_HOST_LINK_PASS codec_sources={len(sources)} rejected_inputs=5")
