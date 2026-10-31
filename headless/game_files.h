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

// Accept packaged base titles inside a title folder, while excluding extracted
// updates/DLC and unsafe path components. Content type still needs metadata.
inline bool IsNestedGameFileSelection(std::string_view selection) {
    if (selection.empty() || selection.size() > 255) return false;
    if (!IsPackageFile(selection) && !IsCardImageFile(selection)) return false;
    const auto last_slash = selection.find_last_of('/');
    if (last_slash == std::string_view::npos || last_slash == 0 ||
        last_slash == selection.size() - 1) return false;
    std::size_t levels = 0;
    while (!selection.empty()) {
        const auto slash = selection.find('/');
        const auto segment = selection.substr(0, slash);
        if (segment.empty() || segment == "." || segment == "..") return false;
        for (const unsigned char c : segment)
            if (c < 32 || c == 127 || c == '\\') return false;
        if (slash == std::string_view::npos) break;
        if (segment == "updates" || segment == "dlc" || segment == "romfs")
            return false;
        if (++levels > 8) return false;
        selection.remove_prefix(slash + 1);
    }
    return levels >= 1;
}

// Look for a packaged base, allowing one or more ordinary wrapper folders.
// Prefer a uniquely named "base.*" or "game.*" package. If multiple possible
// base packages exist, do not guess or accidentally launch an update/DLC.
inline std::string FindNestedGamePackage(const std::filesystem::path& title) {
    namespace fs = std::filesystem;
    if (!IsSafeExtractedDirectory(title)) return {};
    const auto root_name = title.filename().string();
    if (root_name == "updates" || root_name == "dlc" || root_name == "romfs")
        return {};
    std::vector<std::string> candidates;
    std::size_t visited = 0;
    const auto scan = [&](const auto& self, const fs::path& directory,
                          const std::string& relative, unsigned depth) -> void {
        if (depth > 6 || ++visited > 128 || candidates.size() > 64) return;
        std::error_code error;
        std::vector<fs::path> subdirs;
        std::size_t examined = 0;
        for (fs::directory_iterator it{directory, fs::directory_options::skip_permission_denied, error},
                                    end;
             !error && it != end && examined++ < 128; it.increment(error)) {
            const auto path = it->path();
            const auto name = path.filename().string();
            if (name.empty() || name.front() == '.' || name == "updates" ||
                name == "dlc" || name == "romfs") continue;
            if (IsSafeExtractedDirectory(path)) {
                subdirs.push_back(path);
                continue;
            }
            error.clear();
            const auto status = fs::symlink_status(path, error);
            if (error) { error.clear(); continue; }
            if (!fs::is_regular_file(status) ||
                (!IsPackageFile(name) && !IsCardImageFile(name))) continue;
            std::string stem = path.stem().string();
            std::transform(stem.begin(), stem.end(), stem.begin(),
                           [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
            if (stem == "update" || stem == "patch" || stem == "dlc" ||
                stem == "aoc" || stem.starts_with("update_") ||
                stem.starts_with("update-") || stem.starts_with("dlc_") ||
                stem.starts_with("dlc-")) continue;
            const auto candidate = relative.empty() ? name : relative + "/" + name;
            if (IsNestedGameFileSelection(candidate)) candidates.push_back(candidate);
        }
        std::sort(subdirs.begin(), subdirs.end(), [](const fs::path& a, const fs::path& b) {
            const auto a_name = a.filename().string();
            const auto b_name = b.filename().string();
            if (a_name == "base" && b_name != "base") return true;
            if (b_name == "base" && a_name != "base") return false;
            return a_name < b_name;
        });
        for (const auto& path : subdirs) {
            if (visited >= 128 || candidates.size() > 64) break;
            const auto name = path.filename().string();
            self(self, path, relative.empty() ? name : relative + "/" + name, depth + 1);
        }
    };
    scan(scan, title, "", 0);
    if (candidates.empty() || candidates.size() > 64) return {};
    std::sort(candidates.begin(), candidates.end());
    std::vector<std::string> named_base;
    for (const auto& candidate : candidates) {
        std::string stem = fs::path(candidate).stem().string();
        std::transform(stem.begin(), stem.end(), stem.begin(),
                       [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        if (stem == "base" || stem == "game") named_base.push_back(candidate);
    }
    if (named_base.size() == 1) return named_base.front();
    if (named_base.empty() && candidates.size() == 1) return candidates.front();
    return {};
}

inline std::string FindGameFolderInput(const std::filesystem::path& title) {
    if (const auto extracted = FindDeconstructedGameMain(title); !extracted.empty())
        return extracted;
    return FindNestedGamePackage(title);
}

inline bool IsSafeNestedGameFilePath(const std::filesystem::path& roms_root,
                                    std::string_view selection) {
    namespace fs = std::filesystem;
    if (!IsNestedGameFileSelection(selection) || !IsSafeExtractedDirectory(roms_root))
        return false;
    fs::path path = roms_root;
    const fs::path relative{std::string(selection)};
    for (const auto& part : relative.parent_path()) {
        path /= part;
        if (!IsSafeExtractedDirectory(path)) return false;
    }
    std::error_code error;
    const auto status = fs::symlink_status(path / relative.filename(), error);
    return !error && fs::is_regular_file(status) && !fs::is_symlink(status);
}

// Discover add-on content roots without treating each update/DLC as a game.
// These roots may contain arbitrary deeper subdirectories: the existing
// ExternalContentProvider classifies packages by Nintendo title metadata.
// Keep traversal bounded and do not inspect extracted ExeFS/RomFS payloads.
inline bool IsAddOnContainerName(std::string_view name) {
    std::string lower{name};
    std::transform(lower.begin(), lower.end(), lower.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return lower == "updates" || lower == "update" || lower == "patches" ||
           lower == "dlc" || lower == "addons" || lower == "add-ons";
}

inline std::vector<std::filesystem::path> FindAddOnContentDirectories(
    const std::filesystem::path& title_root) {
    namespace fs = std::filesystem;
    std::vector<fs::path> found;
    if (!IsSafeExtractedDirectory(title_root)) return found;
    std::size_t visited = 0;
    const auto scan = [&](const auto& self, const fs::path& dir, unsigned depth) -> void {
        if (depth > 5 || ++visited > 128 || found.size() >= 32) return;
        std::error_code error;
        std::vector<fs::path> subdirs;
        std::size_t enumerated = 0;
        for (fs::directory_iterator it{dir, fs::directory_options::skip_permission_denied, error},
                                    end;
             !error && it != end && enumerated++ < 128; it.increment(error)) {
            const fs::path path = it->path();
            const auto name = path.filename().string();
            if (name.empty() || name.front() == '.' ||
                name == "romfs" || name == "exefs") continue;
            if (!IsSafeExtractedDirectory(path)) continue;
            if (IsAddOnContainerName(name)) {
                found.push_back(path);
            } else {
                subdirs.push_back(path);
            }
        }
        std::sort(subdirs.begin(), subdirs.end());
        for (const auto& child : subdirs) {
            if (visited >= 128 || found.size() >= 32) break;
            self(self, child, depth + 1);
        }
    };
    scan(scan, title_root, 0);
    // A loose NSP/XCI beside a base can itself be an update or DLC.
    // Include the title folder when such a package exists, allowing the
    // native provider to decide from actual CNMT metadata. The provider
    // explicitly skips expanded romfs/exefs trees. Selecting the whole
    // folder here avoids inventing a fragile name/version convention.
    const auto base_input = FindGameFolderInput(title_root);
    std::error_code loose_error;
    for (fs::directory_iterator it{
             title_root, fs::directory_options::skip_permission_denied, loose_error},
         end; !loose_error && it != end; it.increment(loose_error)) {
        const auto path = it->path();
        const auto name = path.filename().string();
        if ((!IsPackageFile(name) && !IsCardImageFile(name)) ||
            name == base_input) continue;
        const auto status = fs::symlink_status(path, loose_error);
        if (loose_error) break;
        if (!fs::is_regular_file(status) || fs::is_symlink(status)) continue;
        return {title_root}; // A single root covers its nested add-on paths.
    }
    std::sort(found.begin(), found.end());
    found.erase(std::unique(found.begin(), found.end()), found.end());
    return found;
}
} // namespace Eden
