// SPDX-License-Identifier: GPL-3.0-or-later
// Offline second-generation guest title identity fallback for games whose extracted
// Control NCA/NACP and Nlib Switch 1 database are unavailable.
// Names: https://www.switchbrew.org/wiki/Switch_2:Title_list/Games
// Original box scans are resolved separately from the Switch 1 + 2 LaunchBox
// media index; no merchandise photos are mistaken for physical flat scans.
#pragma once
#include <array>
#include <cstdint>
#include <string_view>

namespace Eden::Ns2Catalog {
struct Entry {
    std::uint64_t id;
    std::string_view name;
    std::string_view publisher;
    std::string_view release_date;
    std::string_view genre;
};
inline constexpr std::array<Entry, 18> kTitles{{
    {0x040003901FBC2000ULL, "Survival Kids", "", "", ""},
    {0x0400303021AAC000ULL, "DELTARUNE", "", "", ""},
    {0x040052E01D3DA000ULL, "Nintendo GameCube - Nintendo Classics", "", "", ""},
    {0x040057C02159A000ULL, "Nintendo Switch 2 Welcome Tour", "", "", ""},
    {0x04006CC0223D2000ULL, "HITMAN World of Assassination - Signature Edition", "", "", ""},
    {0x040074A01BF12000ULL, "Donkey Kong Bananza", "Nintendo", "2025-07-17", "Action · Platformer"},
    {0x040077201BE50000ULL, "Kirby Air Riders", "", "", ""},
    {0x040078001CCF6000ULL, "Street Fighter 6", "", "", ""},
    {0x0400813022B32000ULL, "Fortnite", "", "", ""},
    {0x040082902313C000ULL, "Arcade Archives 2 RIDGE RACER", "", "", ""},
    {0x04009570209F8000ULL, "Hogwarts Legacy", "", "", ""},
    {0x0400A4802437E000ULL, "Drag x Drive: Global Jam", "", "", ""},
    {0x0400BBB020FF0000ULL, "Yakuza 0 Director's Cut", "", "", ""},
    {0x0400C3F00006E000ULL, "Mario Kart World", "Nintendo", "2025-06-05", "Racing · Party"},
    {0x0400CA40208C8000ULL, "Split Fiction", "", "", ""},
    {0x0400CBA0221EA000ULL, "BRAVELY DEFAULT FLYING FAIRY HD Remaster", "", "", ""},
    {0x0400DDB020648000ULL, "Cyberpunk 2077: Ultimate Edition", "", "", ""},
    {0x0400E140216D4000ULL, "SONIC X SHADOW GENERATIONS", "", "", ""},
}};
// Localized, conservative offline overviews for retail NS2 titles when the
// NS1-only Nlib endpoint has no metadata. The Title ID, not the display
// name or an unverified file, is the sole lookup key.
inline constexpr std::string_view Description(std::uint64_t id, bool french) noexcept {
    switch (id) {
    case 0x0400C3F00006E000ULL:
        return french
            ? "Parcourez un vaste monde de courses avec Mario et ses amis, sur circuits et routes ouvertes."
            : "Race with Mario and friends across connected courses and open roads.";
    case 0x040074A01BF12000ULL:
        return french
            ? "Explorez des environnements destructibles avec Donkey Kong dans une aventure de plateformes."
            : "Explore destructible environments with Donkey Kong in a platforming adventure.";
    default:
        return {};
    }
}
inline const Entry* Find(std::uint64_t id) noexcept {
    for (const auto& item : kTitles)
        if (item.id == id) return &item;
    return nullptr;
}
}  // namespace Eden::Ns2Catalog
