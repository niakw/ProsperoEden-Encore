// SPDX-License-Identifier: GPL-3.0-or-later
// R21: deterministic, network-free assessment of official GitHub Releases JSON.
// No package is installable without a separately verified native PS5 installer.
#pragma once

#include "launcher_update_version.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <string>
#include <string_view>

#include <nlohmann/json.hpp>

namespace Eden::EncoreUpdate {

struct ReleaseAssessment {
    enum class Status {
        malformed,
        current,
        newer_without_package,
        newer_package_candidate
    };
    Status status = Status::malformed;
    std::string latest_version;
    std::string notes;
    std::string package_name;
    std::string sha256;
    std::uint64_t package_bytes = 0;
};

inline std::string BoundedNotes(const nlohmann::json& data) {
    if (!data.contains("body") || !data["body"].is_string())
        return {};
    const auto& value = data["body"].get_ref<const std::string&>();
    std::string notes;
    notes.reserve(std::min<std::size_t>(value.size(), 240));
    bool space = false;
    for (std::size_t pos = 0; pos < value.size();) {
        const unsigned char c = static_cast<unsigned char>(value[pos]);
        if (c == '\n' || c == '\r' || c == '\t' || c == ' ') {
            space = !notes.empty();
            ++pos;
            continue;
        }
        if (c < 32 || c == 127) { ++pos; continue; }
        // Do not split a UTF-8 character at the UI's 240-byte limit.
        // nlohmann::json already validated the source UTF-8 on parse.
        const std::size_t width = c < 0x80 ? 1 : c < 0xE0 ? 2 :
                                  c < 0xF0 ? 3 : 4;
        if (pos + width > value.size()) break;
        // Unicode C1 control range U+0080..U+009F.
        if (c == 0xC2 && width == 2 &&
            static_cast<unsigned char>(value[pos + 1]) >= 0x80 &&
            static_cast<unsigned char>(value[pos + 1]) <= 0x9F) {
            pos += 2;
            continue;
        }
        if (notes.size() + width + (space ? 1u : 0u) > 240) break;
        if (space) notes.push_back(' ');
        space = false;
        notes.append(value, pos, width);
        pos += width;
    }
    return notes;
}

inline bool SafeAssetName(std::string_view name, std::string_view tag) {
    // Never offer FFPFSC or retail PKG for the directory installation. The
    // only install target is /data/homebrew/PPSA99008, so FTP ZIP is required.
    if (!tag.starts_with("encore-R") || ParseRevision(tag, true) <= 0)
        return false;
    // Legacy R1 was already published before the compiled-label ZIP schema.
    if (tag == "encore-R1-56293953")
        return name == "Eden-Encore-56293953-FTP-PPSA99008.zip";
    const auto revision = ParseRevision(tag, true);
    if (revision <= 0) return false;
    return name == "Eden-Encore-R" + std::to_string(revision) +
        "-" + std::string(tag.substr(tag.size() - 8)) +
        "-FTP-PPSA99008.zip";
}

inline bool SafeSha256(std::string_view digest) {
    if (!digest.starts_with("sha256:") || digest.size() != 71) return false;
    for (char c : digest.substr(7))
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')))
            return false;
    return true;
}

inline ReleaseAssessment AssessStableRelease(std::string_view response,
                                             std::string_view installed) {
    ReleaseAssessment result;
    if (response.empty() || response.size() > 512u * 1024u) return result;
    const auto data = nlohmann::json::parse(response.begin(), response.end(), nullptr, false);
    if (data.is_discarded() || !data.is_object() ||
        !data.contains("draft") || !data["draft"].is_boolean() ||
        !data.contains("prerelease") || !data["prerelease"].is_boolean() ||
        data["draft"].get<bool>() || data["prerelease"].get<bool>() ||
        !data.contains("tag_name") || !data["tag_name"].is_string())
        return result;

    const std::string tag = data["tag_name"].get<std::string>();
    const int own = ParseRevision(installed, false);
    const int latest = ParseRevision(tag, true);
    if (own < 0 || latest < 0) return result;
    result.latest_version = "R" + std::to_string(latest);
    result.notes = BoundedNotes(data);
    if (latest <= own) {
        result.status = ReleaseAssessment::Status::current;
        return result;
    }

    result.status = ReleaseAssessment::Status::newer_without_package;
    if (!data.contains("assets") || !data["assets"].is_array() ||
        data["assets"].size() > 80)
        return result;

    for (const auto& asset : data["assets"]) {
        if (!asset.is_object() || !asset.contains("name") ||
            !asset["name"].is_string() || !asset.contains("digest") ||
            !asset["digest"].is_string() ||
            !asset.contains("size") || !asset["size"].is_number_unsigned() ||
            !asset.contains("browser_download_url") ||
            !asset["browser_download_url"].is_string())
            continue;
        const std::string name = asset["name"].get<std::string>();
        const std::string digest = asset["digest"].get<std::string>();
        if (!SafeAssetName(name, tag) || !SafeSha256(digest)) continue;
        const auto bytes = asset["size"].get<std::uint64_t>();
        if (bytes < (1u << 20) || bytes > (1ull << 30)) continue;
        const std::string expected =
            "https://github.com/niakw/Prospero.Eden-Encore/releases/download/" +
            tag + "/" + name;
        if (asset["browser_download_url"].get<std::string>() != expected)
            continue;
        result.status = ReleaseAssessment::Status::newer_package_candidate;
        result.package_name = name;
        result.sha256 = digest.substr(7);
        result.package_bytes = bytes;
        break;
    }
    return result;
}

} // namespace Eden::EncoreUpdate
