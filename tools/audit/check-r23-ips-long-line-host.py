#!/usr/bin/env python3
"""Compile and exercise actual IPSwitchRecord/EscapeStringSequences from PS5 owner.

Positive and negative host ASan/UBSan fixtures include >256-byte lines.
This is not a full IPSwitchParser, guest file, or native PS5 ELF proof.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "headless/r23_ips_layer_ps5.cpp"

def main() -> None:
    source = SOURCE.read_text()
    start = source.index("struct IPSwitchRecord {")
    end = source.index("\nstruct IPSwitchCompiler::IPSwitchPatch", start)
    record = source[start:end]
    start = source.index("static IPSwitchRecord EscapeStringSequences(")
    end = source.index("\nvoid IPSwitchCompiler::Parse", start)
    parser = source[start:end]
    for required in (
        "std::vector<uint8_t> data;",
        "r.data.push_back(",
        "r.data.resize(hs.size());",
        "auto replace_size = record.second.data.size();",
    ):
        assert required in source, "missing real source implementation " + required
    assert "r.data.push_back(*it);" in source, "unescaped characters must be emitted"
    for forbidden in ("r.count", "r.data[r.count]", "std::array<uint8_t, 256 - sizeof(size_t)>"):
        assert forbidden not in source, "unsafe legacy buffer in selected source " + forbidden
    fixture = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>
namespace FileSys {
""" + record + "\n" + parser + r"""
}
int main() {
    using namespace FileSys;
    assert(EscapeStringSequences("").data.empty());
    const std::string text(4096, 'A');
    const auto long_line = EscapeStringSequences(text);
    assert(long_line.data.size() == text.size());
    assert(std::all_of(long_line.data.begin(), long_line.data.end(),
                       [](std::uint8_t c){return c == 'A';}));
    const auto boundary = EscapeStringSequences(std::string(248, 'z'));
    assert(boundary.data.size() == 248);
    const auto over_boundary = EscapeStringSequences(std::string(249, 'x'));
    assert(over_boundary.data.size() == 249);
    const auto escapes = EscapeStringSequences("A\\nB\\tC\\eD\\?E\\");
    // The final single backslash is literal; escaped sequences collapse.
    const std::string expected({'A', '\n', 'B', '\t', 'C', '\x1b', 'D', '?', 'E', '\\'});
    assert(escapes.data.size() == expected.size());
    assert(std::memcmp(escapes.data.data(), expected.data(), expected.size()) == 0);

    std::vector<std::uint8_t> replacement(1024, 0x7a);
    IPSwitchRecord record{};
    record.data.resize(replacement.size());
    std::memcpy(record.data.data(), replacement.data(), replacement.size());
    std::vector<std::uint8_t> target(1032, 0xa5);
    const std::size_t offset = 4;
    const auto replace_size = std::min(record.data.size(), target.size() - offset);
    std::memcpy(target.data() + offset, record.data.data(), replace_size);
    assert(target[0] == 0xa5 && target[3] == 0xa5);
    assert(target[4] == 0x7a && target[1027] == 0x7a);
    assert(target[1028] == 0xa5 && target.back() == 0xa5);
}
"""
    with tempfile.TemporaryDirectory(prefix="ab-r23-ips-long-") as directory:
        src = Path(directory) / "ips_long.cpp"
        exe = Path(directory) / "ips_long"
        src.write_text(fixture)
        subprocess.run(
            ["clang++", "-std=c++20", "-O1", "-g", "-Wall", "-Wextra",
             "-Werror", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
             str(src), "-o", str(exe)],
            cwd=ROOT, check=True, timeout=90,
        )
        subprocess.run(
            [str(exe)], cwd=ROOT, check=True, timeout=15,
            env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
        )
    print("AB_NS1_R23_LONG_IPSWITCH_RECORD_ASAN_UBSAN_PASS",
          "4096-byte-string,249-boundary,1024-hex,escaping,guard-byte-copies",
          "PS5_untested=1")

if __name__ == "__main__":
    try:
        main()
    except (ValueError, AssertionError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        print("AB_NS1_R23_LONG_IPSWITCH_RECORD_FAIL", exc, file=sys.stderr)
        sys.exit(1)
