// SPDX-License-Identifier: GPL-3.0-or-later
// Data-only identity reader. Game records and descriptions never belong in C++.
#pragma once
#include <array>
#include <charconv>
#include <cstdint>
#include <istream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>

namespace Eden::Ns2Catalog {
struct Entry {
    std::uint64_t id{};
    std::string name, publisher, release_date, genre;
};
using Catalog = std::unordered_map<std::uint64_t, Entry>;

inline Catalog Read(std::istream& input) {
    Catalog result;
    std::unordered_set<std::uint64_t> ambiguous;
    std::string row;
    for (std::size_t count = 0; count < 40000 && std::getline(input, row); ++count) {
        if (row.empty() || row[0] == '#' || row.size() > 1024) continue;
        if (row.back() == '\r') row.pop_back();
        std::array<std::string_view, 5> fields{};
        std::string_view remaining{row};
        bool valid = true;
        for (std::size_t i = 0; i < fields.size(); ++i) {
            const auto tab = remaining.find('\t');
            // Publisher/date/genre are optional trailing fields. Accept
            // a row ending at the last populated field without requiring
            // literal trailing tabs. Still reject a sixth field.
            if (i == fields.size() - 1 && tab != std::string_view::npos) {
                valid = false;
                break;
            }
            fields[i] = remaining.substr(0, tab);
            if (tab == std::string_view::npos) break;
            remaining.remove_prefix(tab + 1);
        }
        if (!valid || fields[0].size() != 16 || fields[1].empty()) continue;
        std::uint64_t id{};
        const auto parsed = std::from_chars(fields[0].data(), fields[0].data() + fields[0].size(), id, 16);
        if (parsed.ec != std::errc{} || parsed.ptr != fields[0].data() + fields[0].size() ||
            (id >> 56) != 4 || ambiguous.contains(id)) continue;
        if (result.contains(id)) {
            result.erase(id);
            ambiguous.insert(id);
            continue;
        }
        result.emplace(id, Entry{id, std::string(fields[1]), std::string(fields[2]),
                                 std::string(fields[3]), std::string(fields[4])});
    }
    return result;
}
inline const Entry* Find(const Catalog& catalog, std::uint64_t id) noexcept {
    const auto found = catalog.find(id);
    return found == catalog.end() ? nullptr : &found->second;
}

// Reject purchase conditions, not real game descriptions.
inline constexpr bool CommercialDescription(std::string_view text) noexcept {
    return text.starts_with("Si vous achetez") ||
           text.starts_with("If you purchase") ||
           text.starts_with("If you buy") ||
           text.starts_with("En achetant") ||
           text.starts_with("When you purchase");
}
inline constexpr std::string_view SelectDescription(std::string_view description) noexcept {
    if (!description.empty() && !CommercialDescription(description)) return description;
    return {};
}
} // namespace Eden::Ns2Catalog
