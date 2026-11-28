// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only substitute for the existing disabled-addons map.
#pragma once
#include <cstdint>
#include <map>
#include <string>
#include <vector>
namespace Settings {
// Named external-linkage type: the inline variable must denote ONE settings
// object across the harness and the separately compiled native loader TU.
struct HostValues {
    std::map<std::uint64_t, std::vector<std::string>> disabled_addons;
};
inline HostValues values;
}
