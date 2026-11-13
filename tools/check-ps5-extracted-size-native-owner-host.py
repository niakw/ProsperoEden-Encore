#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Execute the actual PS5 extracted title-size scanner with native directory semantics.

The C++ owner body is extracted verbatim from eden_services.cpp; the only
injected element is an enumerator using a host directory_iterator. This is
a host regression, NOT evidence of PS5 mounted-drive behavior.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
library = (ROOT / "headless/prosperoeden/eden_services.cpp").read_text()
header = (ROOT / "headless/game_files.h").read_text()
begin = library.index("std::optional<std::uint64_t> ExtractedBaseBytes(")
end = library.index("\n// Local user-supplied covers", begin)
real_owner = library[begin:end]
assert '#if defined(PS5_NATIVE)' in real_owner
native = real_owner.split('#if defined(PS5_NATIVE)', 1)[1].split('#else', 1)[0]
assert "Eden::ReadNativeDirectory(current.path, listing_error)" in native
assert "fs::recursive_directory_iterator" not in native
assert "Eden::IsReservedAddOnPackageStem" in native
assert "::lstat(entry.path().c_str(), &info)" in native
assert "if (info.st_size < 0)" in native
assert 'return fail("getdents"' in native
assert "kMaxExtractedFiles = 1000000" in real_owner
assert "kMaxExtractedDepth = 64" in real_owner
assert 'inline bool IsReservedAddOnPackageStem(' in header

prefix = r"""
#include <algorithm>
#include <atomic>
#include <cassert>
#include <cerrno>
#include <cstdio>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <sys/stat.h>
#include <system_error>
#include <utility>
#include <vector>
#include "game_files.h"
namespace fs = std::filesystem;
namespace Eden {
// Exercise the real size-collector code with a controllable host equivalent
// of the native PS5 getdents reader. Inject incomplete directory errors.
std::vector<fs::directory_entry> ReadNativeDirectory(const fs::path& path,
                                                     std::error_code& ec) {
    if (path.filename() == "readerr") {
        ec = std::make_error_code(std::errc::io_error);
        return {};
    }
    std::vector<fs::directory_entry> entries;
    for (fs::directory_iterator it(path, fs::directory_options::none, ec), end;
         it != end && !ec; it.increment(ec))
        entries.push_back(*it);
    return ec ? std::vector<fs::directory_entry>{} : entries;
}
}
"""
suffix = r"""
int main(int argc, char** argv) {
    assert(argc == 2);
    const fs::path tmp = argv[1];
    const auto game = tmp / "Mario Kart World";
    const auto exefs = game / "base" / "exefs";
    const auto romfs = game / "base" / "romfs";
    fs::create_directories(exefs);
    fs::create_directories(romfs);
    auto fill = [](const fs::path& p, std::size_t n) {
        std::ofstream output{p, std::ios::binary};
        assert(output);
        std::string bytes(n, 'X');
        output.write(bytes.data(), bytes.size());
        assert(output);
    };
    fill(exefs / "main", 32768);
    fill(exefs / "main.npdm", 12288);
    fill(romfs / "sprite.bin", 256);
    // A sparse >2GiB file catches 32-bit size truncation without occupying RAM.
    const auto big = romfs / "content.dat";
    fill(big, 1);
    constexpr std::uint64_t huge = 3ULL * 1024 * 1024 * 1024 + 17;
    fs::resize_file(big, huge);
    fs::create_directories(game / "update_450" / "romfs");
    fs::create_directories(game / "DLC" / "romfs");
    fill(game / "update_450" / "romfs" / "exclude.bin", 1200);
    fill(game / "DLC" / "romfs" / "exclude.bin", 1300);
    // A symlink to a large file is not additional game content.
    fs::create_symlink(big, game / "linked_contents");
    const auto bytes = ExtractedBaseBytes(game, nullptr);
    assert(bytes.has_value());
    assert(*bytes == huge + 32768 + 12288 + 256);
    std::atomic<bool> stop{true};
    assert(!ExtractedBaseBytes(game, &stop).has_value());
    stop.store(false);
    assert(ExtractedBaseBytes(game, &stop) == bytes);
    const auto zero = tmp / "empty";
    fs::create_directory(zero);
    assert(!ExtractedBaseBytes(zero, nullptr).has_value());
    // Partial nested traversal must never report a believable but false size.
    fs::create_directories(game / "readerr");
    assert(!ExtractedBaseBytes(game, nullptr).has_value());
    fs::remove(game / "readerr");
    assert(ExtractedBaseBytes(game, nullptr) == bytes);
    std::puts("PS5_EXEFS_SIZE_NATIVE_OWNER_HOST_PASS full_3GiB=1 updates_skipped=1 "
              "symlinks_skipped=1 partial_fail_closed=1 cancel=1");
}
"""
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "Need C++20 compiler"
with tempfile.TemporaryDirectory(prefix="encore-exefs-size-") as td:
    directory = Path(td)
    cpp = directory / "owner.cpp"
    cpp.write_text(prefix + "\n" + real_owner + "\n" + suffix)
    exe = directory / "owner"
    subprocess.run([compiler, "-std=c++20", "-DPS5_NATIVE=1", "-O1", "-g",
                    "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    "-I", str(ROOT / "headless"), str(cpp), "-o", str(exe)],
                   check=True, timeout=90)
    subprocess.run([str(exe), str(directory / "fixture")],
                   check=True, timeout=45)
