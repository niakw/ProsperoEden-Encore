// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string_view>
namespace Eden::EncoreUpdate {
constexpr int ParseRevision(std::string_view value, bool published_tag) {
    if (published_tag && value.substr(0, 7) == "encore-")
        value.remove_prefix(7);
    if (value.empty() || value.front() != 'R') return -1;
    value.remove_prefix(1);
    if (value.empty() || value.front() < '0' || value.front() > '9') return -1;
    int number = 0;
    std::size_t pos = 0;
    for (; pos < value.size() && value[pos] >= '0' && value[pos] <= '9'; ++pos) {
        const int digit = value[pos] - '0';
        if (number > (100000000 - digit) / 10) return -1;
        number = number * 10 + digit;
    }
    if (!published_tag) return pos == value.size() ? number : -1;
    if (pos == value.size()) return number;
    if (value[pos] != '-' || value.size() - (pos + 1) < 7 ||
        value.size() - (pos + 1) > 40) return -1;
    for (++pos; pos < value.size(); ++pos) {
        const char c = value[pos];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return -1;
    }
    return number;
}
} // namespace Eden::EncoreUpdate
