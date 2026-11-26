// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only substitute for the existing disabled-addons map.
#pragma once
#include <cstdint>
#include <map>
#include <string>
#include <vector>
namespace Settings {
inline struct {
    std::map<std::uint64_t, std::vector<std::string>> disabled_addons;
} values;
}
