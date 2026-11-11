// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
// Source-extracted host semantic witness, not a patched production source.
// Original: vendor@22b69d6 sources/eden/src/common/fs/path_util.cpp blob b4c7eae343df49eaae5327c5efa04a8d13dc4e19
// Upstream: eden-emulator/mirror@c3f1e6562 path_util.cpp blob 82ea8f6cb2b3d365b0e3a96457694a81bb0bec7f
#include <algorithm>
#include <cassert>
#include <cctype>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>
namespace Common::FS {
enum class DirectorySeparator { ForwardSlash, BackwardSlash, PlatformDefault };
std::string_view RemoveTrailingSlash(std::string_view path) {
    if (path.empty()) {
        return path;
    }

    if (path.back() == '\\' || path.back() == '/') {
        path.remove_suffix(1);
        return path;
    }

    return path;
}

template <typename F>
static void ForEachPathComponent(std::string_view filename, F&& cb) {
    const char* component_begin = filename.data();
    const char* const end = component_begin + filename.size();
    for (const char* it = component_begin; it != end; ++it) {
        const char c = *it;
        if (c == '\\' || c == '/') {
            if (component_begin != it) {
                cb(std::string_view{component_begin, it});
            }
            component_begin = it + 1;
        }
    }
    if (component_begin != end) {
        cb(std::string_view{component_begin, end});
    }
}

std::vector<std::string_view> SplitPathComponents(std::string_view filename) {
    std::vector<std::string_view> components;
    ForEachPathComponent(filename, [&](auto component) { components.emplace_back(component); });

    return components;
}

namespace Pinned {
std::string SanitizePath(std::string_view path_, DirectorySeparator directory_separator) {
    std::string path(path_);
#ifdef __ANDROID__
    if (Android::IsContentUri(path)) {
        return path;
    }
#endif // __ANDROID__

    char type1 = directory_separator == DirectorySeparator::BackwardSlash ? '/' : '\\';
    char type2 = directory_separator == DirectorySeparator::BackwardSlash ? '\\' : '/';

    if (directory_separator == DirectorySeparator::PlatformDefault) {
#ifdef _WIN32
        type1 = '/';
        type2 = '\\';
#endif
    }

    std::replace(path.begin(), path.end(), type1, type2);

    auto start = path.begin();
#ifdef _WIN32
    // allow network paths which start with a double backslash (e.g. \\server\share)
    if (start != path.end())
        ++start;
#endif
    path.erase(std::unique(start, path.end(),
                           [type2](char c1, char c2) { return c1 == type2 && c2 == type2; }),
               path.end());

    const bool absolute = !path.empty() && path[0] == type2;
    std::vector<std::string_view> parts;

    for (const auto part : SplitPathComponents(path))
    {
        if (part.empty() || part == ".")
            continue;
        if (part == ".." && !parts.empty() && parts.back() != "..")
            parts.pop_back();
        else if (part != "..") parts.push_back(part);
    }

    std::string resolved = absolute ? std::string(1, type2) : std::string{};
    for (std::size_t i = 0; i < parts.size(); ++i)
    {
        if (i != 0)
            resolved += type2;
        resolved.append(parts[i].data(), parts[i].size());
    }

    path = std::move(resolved);

    return std::string(RemoveTrailingSlash(path));
}

}
namespace Upstream {
std::string SanitizePath(std::string_view path_, DirectorySeparator directory_separator) {
    std::string path(path_);
#ifdef __ANDROID__
    if (Android::IsContentUri(path)) {
        return path;
    }
#endif // __ANDROID__

    char type1 = directory_separator == DirectorySeparator::BackwardSlash ? '/' : '\\';
    char type2 = directory_separator == DirectorySeparator::BackwardSlash ? '\\' : '/';

    if (directory_separator == DirectorySeparator::PlatformDefault) {
#ifdef _WIN32
        type1 = '/';
        type2 = '\\';
#endif
    }

    std::replace(path.begin(), path.end(), type1, type2);

    auto start = path.begin();
#ifdef _WIN32
    // allow network paths which start with a double backslash (e.g. \\server\share)
    if (start != path.end())
        ++start;
#endif
    path.erase(std::unique(start, path.end(),
                           [type2](char c1, char c2) { return c1 == type2 && c2 == type2; }),
               path.end());

    std::string root;
    std::string_view components{path};
    bool drive_relative = false;

#ifdef _WIN32
    const bool network = path.size() > 1 && path[0] == type2 && path[1] == type2;
    const bool drive =
        path.size() > 1 && std::isalpha(static_cast<unsigned char>(path[0])) && path[1] == ':';

    if (network) {
        root.assign(2, type2);
        components.remove_prefix(2);
    } else if (drive) {
        root.assign(path.data(), 2);
        components.remove_prefix(2);
        if (!components.empty() && components.front() == type2) {
            root += type2;
            components.remove_prefix(1);
        } else {
            drive_relative = true;
        }
    }
#endif

    if (root.empty() && !components.empty() && components.front() == type2) {
        root += type2;
        components.remove_prefix(1);
    }

    const auto path_parts = SplitPathComponents(components);
    std::size_t root_component_count = 0;
#ifdef _WIN32
    if (network) {
        root_component_count = 2;

        const auto is_unc = [](std::string_view part) {
            return part.size() == 3 && (part[0] == 'U' || part[0] == 'u') &&
                   (part[1] == 'N' || part[1] == 'n') && (part[2] == 'C' || part[2] == 'c');
        };
        if (path_parts.size() >= 2 && path_parts[0] == "?" && is_unc(path_parts[1])) {
            root_component_count = 4;
        }
    }
#endif

    std::vector<std::string_view> parts;
    for (std::size_t i = 0; i < path_parts.size(); ++i) {
        const auto part = path_parts[i];
        if (i < root_component_count) {
            parts.push_back(part);
        } else if (part.empty() || part == ".") {
            continue;
        } else if (part == "..") {
            if (parts.size() > root_component_count) {
                parts.pop_back();
            }
        } else {
            parts.push_back(part);
        }
    }

    const std::size_t root_length = root.size();
    std::string resolved = std::move(root);
    for (std::size_t i = 0; i < parts.size(); ++i) {
        if (i != 0 || (!resolved.empty() && resolved.back() != type2 && !drive_relative))
            resolved += type2;
        resolved.append(parts[i].data(), parts[i].size());
    }

    path = std::move(resolved);

    if (!path.empty() && path.size() == root_length) {
        return path;
    }
    return std::string(RemoveTrailingSlash(path));
}

}
} // namespace Common::FS
int main() {
    using Common::FS::DirectorySeparator;
    using Common::FS::Pinned::SanitizePath;
    struct Case { const char* input; const char* pinned; const char* upstream; };
    constexpr Case corpus[] = {
        {"/", "", "/"},
        {"/../etc", "/etc", "/etc"},
        {"/a/../../etc", "/etc", "/etc"},
        {"../a", "a", "a"},
        {"a/../../etc", "etc", "etc"},
        {"/a/..", "", "/"},
        {"a/../b", "b", "b"},
        {"a//b", "a/b", "a/b"},
        {"", "", ""},
    };
    for (const auto& row : corpus) {
        const auto actual_pinned = SanitizePath(row.input, DirectorySeparator::ForwardSlash);
        const auto actual_new = Common::FS::Upstream::SanitizePath(row.input, DirectorySeparator::ForwardSlash);
        if (actual_pinned != row.pinned || actual_new != row.upstream) {
            std::cerr << "MISMATCH input=" << row.input << " pinned=" << actual_pinned
                      << " upstream=" << actual_new << "\n";
            return 1;
        }
    }
    std::cout << "R23_PS5_COMMON_FS_SANITIZE_EXACT_SOURCE_DIVERGENCE_PASS cases=9 "
              << "native_console_execution=false\n";
}
