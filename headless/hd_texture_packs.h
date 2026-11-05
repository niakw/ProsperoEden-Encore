// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R10: independent title-scoped HD texture packs, stored beside mods/.
// Only confirmed native RomFS replacement files are accepted, never ExeFS
// patches/cheats or raw AI-generated images. The vendor's PS5 patch manager
// directly overlays this root: no copying/symlinking into mods/.
#include "mods.h"
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

namespace Eden::HdTextures {
namespace fs = std::filesystem;
struct Pack {
    std::string name;
    std::uint64_t files = 0;
    std::uint64_t bytes = 0;
};
inline constexpr const char* kDisabledPrefix = "@hd:";

// Same schema and metadata checks as the maintained vendor patch manager.
inline std::vector<Pack> List(const std::string& root, std::uint64_t title_id) {
    std::vector<Pack> packs;
    if (title_id == 0) return packs;
    const auto title_dir = Eden::Mods::TitleFolder(root, title_id);
    if (title_dir.empty()) return packs;
    for (const auto& entry : Eden::Mods::ListFolder(title_dir)) {
        if (!Eden::Mods::IsFolder(entry) || entry.is_symlink()) continue;
        const std::string name = entry.path().filename().string();
        if (name.empty() || name.front() == '.' ||
            name.find('/') != std::string::npos ||
            name.find('\\') != std::string::npos) continue;
        const auto manifest = entry.path() / "encore-hd-textures.json";
        std::error_code error;
        if (!fs::is_regular_file(manifest,error) || error ||
            fs::is_symlink(manifest,error) || error ||
            fs::file_size(manifest,error) > (1U<<20) || error)
            continue;
        std::ifstream source(manifest, std::ios::binary);
        if (!source) continue;
        const auto json = nlohmann::json::parse(source, nullptr, false);
        if (!json.is_object()) continue;
        const auto matches = [&json](const char* key, const std::string& value) {
            const auto it = json.find(key);
            return it != json.end() && it->is_string() &&
                   it->get<std::string>() == value;
        };
        if (!matches("schema","eden-encore-hd-romfs-v1") ||
            !matches("title_id",Eden::Mods::TitleName(title_id)) ||
            !matches("replacement_mode","game-compatible-romfs"))
            continue;
        const auto romfs = entry.path() / "romfs";
        if (!fs::is_directory(romfs,error) || error ||
            fs::is_symlink(romfs,error) || error ||
            Eden::Mods::ListFolder(romfs).empty())
            continue;
        const auto files = json.find("file_count");
        const auto size = json.find("total_bytes");
        if (files==json.end() || size==json.end() ||
            !files->is_number_unsigned() || !size->is_number_unsigned())
            continue;
        const auto count=files->get<std::uint64_t>();
        const auto bytes=size->get<std::uint64_t>();
        if (count==0 || count>10000 || bytes==0 || bytes>(8ULL<<30)) continue;
        packs.push_back({name,count,bytes});
    }
    std::sort(packs.begin(),packs.end(),
              [](const Pack& a,const Pack& b){return a.name < b.name;});
    return packs;
}
} // namespace Eden::HdTextures
