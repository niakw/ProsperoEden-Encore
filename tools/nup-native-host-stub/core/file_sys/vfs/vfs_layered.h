// SPDX-License-Identifier: GPL-3.0-or-later
// Host VFS stand-in for the real pinned LayeredVfsDirectory API.
// Test ordering, recursively merged directories, and first-layer priority.
#pragma once

#include <memory>
#include <set>
#include <string>
#include <utility>
#include <vector>
#include "core/file_sys/vfs/vfs.h"

namespace FileSys {
class LayeredVfsDirectory final : public ReadOnlyVfsDirectory {
public:
    static VirtualDir MakeLayeredDirectory(std::vector<VirtualDir> dirs,
                                           std::string name = "") {
        std::erase(dirs, nullptr);
        if (dirs.empty()) return {};
        if (dirs.size() == 1) return dirs[0];
        return VirtualDir(new LayeredVfsDirectory(std::move(dirs), std::move(name)));
    }

    std::vector<VirtualFile> GetFiles() const override {
        std::set<std::string> seen;
        std::vector<VirtualFile> result;
        for (const auto& layer : layers_) {
            for (const auto& file : layer->GetFiles())
                if (seen.insert(file->GetName()).second) result.push_back(file);
        }
        return result;
    }

    VirtualDir GetSubdirectory(std::string_view name) const override {
        std::vector<VirtualDir> selected;
        for (const auto& layer : layers_) {
            if (const auto subdir = layer->GetSubdirectory(name); subdir)
                selected.push_back(subdir);
        }
        return MakeLayeredDirectory(std::move(selected), std::string(name));
    }

    std::vector<VirtualDir> GetSubdirectories() const override {
        std::set<std::string> seen;
        for (const auto& layer : layers_)
            for (const auto& subdir : layer->GetSubdirectories())
                seen.insert(subdir->GetName());
        std::vector<VirtualDir> result;
        for (const auto& name : seen)
            result.push_back(GetSubdirectory(name));
        return result;
    }

    std::string GetName() const override {
        return name_.empty() ? layers_.front()->GetName() : name_;
    }
    VirtualDir GetParentDirectory() const override {
        return layers_.front()->GetParentDirectory();
    }

private:
    LayeredVfsDirectory(std::vector<VirtualDir> layers, std::string name)
        : layers_(std::move(layers)), name_(std::move(name)) {}
    std::vector<VirtualDir> layers_;
    std::string name_;
};
} // namespace FileSys
