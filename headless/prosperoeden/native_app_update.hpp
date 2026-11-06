// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <string>

namespace Eden::EncoreUpdate {
struct NativeInstallPlan {
    std::string installed_revision;
    std::string latest_revision;
    std::string package_name;
    std::string package_path;
    std::string sha256;
    std::uint64_t bytes{};
};
struct NativeInstallResult {
    bool applying{}; // only true after helper accepts the "apply" phase
    std::string message;
};
bool IsSafeNativeInstallPlan(const NativeInstallPlan& plan);
// Streaming download, verified size/SHA256, independent payload helper,
// then two-phase "ready -> staged -> apply -> applying" handoff.
// The launcher must EXIT on applying and never write its own install folder.
NativeInstallResult InstallNativeApp(const NativeInstallPlan& plan);
}
