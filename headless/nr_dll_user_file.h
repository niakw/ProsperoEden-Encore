// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Nonblocking launcher/launch-time discovery, like lossless_user_file.h.
// This only verifies the presence of a plausible user-owned PE DLL.
// The native Original importer verifies WEIGHTS_HT SHA-256 and tensor layout.
#include <array>
#include <cstdio>
#include <filesystem>
#include <system_error>

namespace Eden::Graphics {
inline constexpr const char* kDlssNrRelative = "dlssnr/nvngx_dlssnr.dll";
inline constexpr const char* kDlssNrConsolePath =
    "/data/prosperoeden/user/dlssnr/nvngx_dlssnr.dll";

inline bool DlssNrUserFileLooksValid(
    const std::filesystem::path& user_dir,
    const std::filesystem::path& config_dir) {
    // Match the Vulkan presenter's accepted import paths. Keep the documented
    // user/dlssnr/ path first; other locations are migration fallbacks only.
    const std::array<std::filesystem::path, 4> candidates{
        user_dir / kDlssNrRelative,
        config_dir / "neural/nvngx_dlssnr.dll",
        config_dir / "nvngx_dlssnr.dll",
        user_dir / "nvngx_dlssnr.dll",
    };
    for (const auto& path : candidates) {
        std::error_code ec;
        const auto status = std::filesystem::symlink_status(path, ec);
        if (ec || std::filesystem::is_symlink(status) ||
            !std::filesystem::is_regular_file(status)) continue;
        const auto size = std::filesystem::file_size(path, ec);
        if (ec || size < 1024u || size > (512ull << 20)) continue;
        std::FILE* file = std::fopen(path.string().c_str(), "rb");
        if (!file) continue;
        unsigned char magic[2]{};
        const bool read = std::fread(magic, 1, sizeof(magic), file) ==
                          sizeof(magic);
        (void)std::fclose(file);
        if (read && magic[0] == 'M' && magic[1] == 'Z') return true;
    }
    return false;
}
} // namespace Eden::Graphics
