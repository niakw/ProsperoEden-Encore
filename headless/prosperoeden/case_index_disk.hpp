// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <array>
#include <istream>
#include <string>
#include <string_view>

namespace Eden::CaseIndexDisk {
inline constexpr char kGlobalMarker[] = "# global media sorted by standard name";
inline constexpr std::streamoff kMaxRow = 9000;

// Binary search complete rows without loading the global catalogue into RAM.
// Both bounds are row boundaries. A bounded backwards scan finds the row
// containing the midpoint. The generator emits ASCII keys in sorted order.
inline std::string FindSortedRow(std::istream& in, std::streamoff first,
                                 std::string_view wanted) {
    if (first < 0 || wanted.empty()) return {};
    in.clear();
    in.seekg(0, std::ios::end);
    const auto end = static_cast<std::streamoff>(in.tellg());
    if (end <= first) return {};
    auto lo = first, hi = end;
    std::array<char, static_cast<std::size_t>(kMaxRow + 1)> bytes{};
    while (lo < hi) {
        const auto mid = lo + (hi - lo) / 2;
        const auto base = std::max(lo, mid - kMaxRow - 1);
        const auto count = mid - base;
        in.clear();
        in.seekg(base);
        if (!in) return {};
        if (count) {
            in.read(bytes.data(), count);
            if (in.gcount() != count) return {};
        }
        const std::string_view window(bytes.data(), static_cast<std::size_t>(count));
        const auto newline = window.rfind('\n');
        if (newline == std::string_view::npos && base != lo) return {};
        const auto start = newline == std::string_view::npos
            ? base : base + static_cast<std::streamoff>(newline) + 1;
        in.clear();
        in.seekg(start);
        std::string row;
        if (!std::getline(in, row) || row.size() > static_cast<std::size_t>(kMaxRow))
            return {};
        const auto tab = row.find('\t');
        if (tab == std::string::npos) return {};
        const std::string_view key(row.data(), tab);
        if (key == wanted) return row;
        if (key > wanted) hi = start;
        else {
            const auto next = start + static_cast<std::streamoff>(row.size()) + 1;
            if (next <= lo) return {};
            lo = std::min(next, end);
        }
    }
    return {};
}
} // namespace Eden::CaseIndexDisk
