// SPDX-FileCopyrightText: Copyright 2026 Oliv3rmoon
// SPDX-License-Identifier: GPL-3.0-or-later
// File selection for the nine extensions recognized by Encore's game picker:
// NSP/XCI, their NCZ-compressed NSZ/XCZ variants, and direct NRO/NSO/NCA/NAX/KIP.
// Direct inputs can require external program contents and are not guaranteed
// to boot. Internal .ncz, NSO LZ4 and ZBIC/zstd are not standalone games.
#pragma once
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

namespace Eden {
inline bool EndsWithNoCase(std::string_view name, std::string_view suffix) {
    if (name.size() < suffix.size()) return false;
    name.remove_prefix(name.size() - suffix.size());
    for (std::size_t i = 0; i < suffix.size(); ++i)
        if (std::tolower(static_cast<unsigned char>(name[i])) != suffix[i]) return false;
    return true;
}
// Read as an NSP: a package of NCAs.
inline bool IsPackageFile(std::string_view name) {
    return EndsWithNoCase(name, ".nsp") || EndsWithNoCase(name, ".nsz");
}
// Read as an XCI: a game card's image.
inline bool IsCardImageFile(std::string_view name) {
    return EndsWithNoCase(name, ".xci") || EndsWithNoCase(name, ".xcz");
}
// Eden also has dedicated NRO, NSO, NCA, NAX and KIP loaders. These may be
// standalone homebrew, program partitions or system components, not necessarily
// complete game containers. Keep them selectable; let the native core loader
// determine whether enough content exists to boot the selection.
inline bool IsDirectLoaderFile(std::string_view name) {
    return EndsWithNoCase(name, ".nro") || EndsWithNoCase(name, ".nso") ||
           EndsWithNoCase(name, ".nca") || EndsWithNoCase(name, ".nax") ||
           EndsWithNoCase(name, ".kip");
}
inline bool IsGameFile(std::string_view name) {
    return IsPackageFile(name) || IsCardImageFile(name) || IsDirectLoaderFile(name);
}

// A saved extracted title is either <title>/main (legacy), or
// <title>/[subdirectories]/exefs/main. The first component is always the
// title folder in roms/. Nested updates/DLC must never become base titles.
// No arbitrary file paths, parent traversal or symlinked entries are allowed.
inline bool IsDeconstructedGameSelection(std::string_view name) {
    constexpr std::string_view suffix{"/main"};
    if (!name.ends_with(suffix)) return false;
    name.remove_suffix(suffix.size());
    if (name.empty() || name.size() > 250) return false;
    std::size_t segments = 0;
    std::string_view last;
    while (!name.empty()) {
        const auto slash = name.find('/');
        const auto segment = name.substr(0, slash);
        if (segment.empty() || segment == "." || segment == ".." ||
            segment == "updates" || segment == "dlc" || segment == "romfs")
            return false;
        for (unsigned char c : segment)
            if (c < 32 || c == 127 || c == '\\') return false;
        last = segment;
        ++segments;
        if (segments > 8) return false;
        if (slash == std::string_view::npos) break;
        name.remove_prefix(slash + 1);
    }
    return segments == 1 || (segments >= 2 && last == "exefs");
}

// Symlink-free detection avoids treating arbitrary ROM directories or
// symlink targets outside the selected storage root as launchable titles.
inline bool IsDeconstructedGameDirectory(const std::filesystem::path& folder) {
    namespace fs = std::filesystem;
    std::error_code error;
    const auto directory_status = fs::symlink_status(folder, error);
    if (error || !fs::is_directory(directory_status) || fs::is_symlink(directory_status))
        return false;
    for (const char* name : {"main", "main.npdm"}) {
        error.clear();
        const auto status = fs::symlink_status(folder / name, error);
        if (error || !fs::is_regular_file(status) || fs::is_symlink(status))
            return false;
    }
    return true;
}
// Avoid following symlinks at every directory level, not just at main.npdm.
inline bool IsSafeExtractedDirectory(const std::filesystem::path& folder) {
    std::error_code error;
    const auto status = std::filesystem::symlink_status(folder, error);
    return !error && std::filesystem::is_directory(status) &&
           !std::filesystem::is_symlink(status);
}

// Returns a title-relative file path such as "main" or
// "base/exefs/main". The search is bounded, deterministic and scans only
// under the selected top-level title; it never descends into RomFS/assets,
// patches or add-on folders.
inline std::string FindDeconstructedGameMain(const std::filesystem::path& title) {
    namespace fs = std::filesystem;
    if (!IsSafeExtractedDirectory(title)) return {};
    // Root-level content stores are not games, even when an update happens
    // to carry its own valid ExeFS. Only <title>/base is a launchable title.
    const auto root_name = title.filename().string();
    if (root_name == "updates" || root_name == "dlc" || root_name == "romfs")
        return {};
    if (IsDeconstructedGameDirectory(title)) return "main";
    std::size_t visited = 0;
    const auto search = [&](const auto& self, const fs::path& dir,
                            const std::string& relative, unsigned depth) -> std::string {
        if (depth > 6 || ++visited > 128) return {};
        if (dir.filename() == "exefs" && IsDeconstructedGameDirectory(dir))
            return relative + "/main";
        std::error_code error;
        std::vector<fs::path> subdirs;
        for (fs::directory_iterator it{dir, fs::directory_options::skip_permission_denied, error},
                                    end;
             !error && it != end && subdirs.size() < 128; it.increment(error)) {
            const auto path = it->path();
            const auto name = path.filename().string();
            if (name.empty() || name.front() == '.' || name == "romfs" ||
                name == "updates" || name == "dlc")
                continue;
            if (IsSafeExtractedDirectory(path)) subdirs.push_back(path);
        }
        // Prefer base, then exefs, then other nested extraction folders.
        std::sort(subdirs.begin(), subdirs.end(), [](const fs::path& a, const fs::path& b) {
            const auto rank = [](const fs::path& p) {
                const auto name = p.filename().string();
                return name == "base" ? 0 : name == "exefs" ? 1 : 2;
            };
            if (rank(a) != rank(b)) return rank(a) < rank(b);
            return a.filename().string() < b.filename().string();
        });
        for (const auto& path : subdirs) {
            const auto segment = path.filename().string();
            const auto next = relative.empty() ? segment : relative + "/" + segment;
            if (const auto found = self(self, path, next, depth + 1); !found.empty())
                return found;
        }
        return {};
    };
    return search(search, title, "", 0);
}

inline bool IsSafeDeconstructedGamePath(const std::filesystem::path& roms_root,
                                        std::string_view selection) {
    namespace fs = std::filesystem;
    if (!IsDeconstructedGameSelection(selection) || !IsSafeExtractedDirectory(roms_root))
        return false;
    fs::path path = roms_root;
    const fs::path relative{std::string(selection)};
    for (const auto& part : relative.parent_path()) {
        path /= part;
        if (!IsSafeExtractedDirectory(path)) return false;
    }
    return IsDeconstructedGameDirectory(path);
}
} // namespace Eden
