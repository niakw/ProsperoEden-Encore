// SPDX-License-Identifier: GPL-3.0-or-later
// Native updater archive tests on a disposable host folder.
// Does not access PS5 or /data/homebrew and cannot install any app.
#include "archive.hpp"

#include <atomic>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <string_view>

namespace fs = std::filesystem;

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    const std::string mode = argv[1], archive = argv[2], dest = argv[3];
    if (mode != "valid" && mode != "reject") return 2;
    self_update::ArchiveInfo info{};
    std::string error;
    const bool accepted = self_update::inspect_archive(
        archive, "PPSA99008", info, error);
    if (mode == "reject") {
        if (accepted || fs::exists(dest)) {
            std::cerr << "Unexpectedly accepted unsafe ZIP: " << archive << "\n";
            return 3;
        }
        return 0;
    }
    if (!accepted || info.files < 3 || info.unpacked < 4096) {
        std::cerr << "Valid ZIP inspection failed: " << error << "\n";
        return 4;
    }
    std::atomic<bool> cancel{false};
    std::atomic<std::uint64_t> written{0};
    if (!self_update::extract_archive(archive, "PPSA99008", dest,
                                      cancel, written, error)) {
        std::cerr << "Valid ZIP extraction failed: " << error << "\n";
        return 5;
    }
    if (written.load() != info.unpacked ||
        !fs::is_regular_file(fs::path(dest) / "eboot.bin") ||
        !fs::is_regular_file(fs::path(dest) / "sce_sys/param.json") ||
        !fs::is_regular_file(fs::path(dest) / "sce_module/libc.prx")) {
        std::cerr << "Extracted application content incomplete\n";
        return 6;
    }
    // Read-only check of output, no system/other homebrew paths used.
    std::ifstream file(fs::path(dest) / "eboot.bin", std::ios::binary);
    char first{};
    file.get(first);
    if (!file || first != 'E') return 7;
    return 0;
}
