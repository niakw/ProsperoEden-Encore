// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Lightweight, menu-time discovery. The actual LSFG shader loader still
// validates all PE structures and the required shader resource IDs.
#include <cstdio>
#include <filesystem>
#include <system_error>

namespace Eden::Graphics {
inline constexpr const char* kLosslessRelative = "lossless/Lossless.dll";
inline constexpr const char* kLosslessConsolePath =
    "/data/prosperoeden/user/lossless/Lossless.dll";

inline bool LosslessUserFileLooksValid(const std::filesystem::path& user_dir) {
    const std::filesystem::path path = user_dir / kLosslessRelative;
    std::error_code ec;
    const auto status = std::filesystem::symlink_status(path, ec);
    if (ec || !std::filesystem::is_regular_file(status) ||
        std::filesystem::is_symlink(status)) return false;
    const auto size = std::filesystem::file_size(path, ec);
    if (ec || size < 128 || size > 256ull * 1024 * 1024) return false;
    std::FILE* file = std::fopen(path.string().c_str(), "rb");
    if (!file) return false;
    unsigned char magic[2]{};
    const bool ok = std::fread(magic, 1, sizeof(magic), file) == sizeof(magic);
    (void)std::fclose(file);
    return ok && magic[0] == 'M' && magic[1] == 'Z';
}
} // namespace Eden::Graphics
