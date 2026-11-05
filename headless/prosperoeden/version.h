// SPDX-License-Identifier: GPL-3.0-or-later
// Encore has its own user-facing release line. The PS5 contentVersion remains numeric because
// sce_sys/param.json requires that format.
#pragma once

namespace Eden {
// Keep the separately versioned public package metadata stable.
// The launcher footer uses the EXACT R-label supplied by CMake at build time.
// No fabricated R revision in host previews or custom unversioned builds.
// Native packaging passes the exact release label via the build system.
inline constexpr const char* kAppVersion = "Unversioned";
#if defined(PS5_NATIVE) && !defined(EDEN_LAUNCHER_BUILD_LABEL)
#error "Native Eden Encore requires EDEN_LAUNCHER_BUILD_LABEL from the source build"
#endif
#ifdef EDEN_LAUNCHER_BUILD_LABEL
inline constexpr const char* kBuildVersion = EDEN_LAUNCHER_BUILD_LABEL;
#else
inline constexpr const char* kBuildVersion = kAppVersion;
#endif
// Only the historical public R1 release used this immutable number.
inline constexpr const char* kLegacyPackageVersion = "01.000.041";
#ifdef EDEN_LAUNCHER_PACKAGE_VERSION
inline constexpr const char* kPackageVersion = EDEN_LAUNCHER_PACKAGE_VERSION;
#else
inline constexpr const char* kPackageVersion = "Unversioned";
#endif
}
