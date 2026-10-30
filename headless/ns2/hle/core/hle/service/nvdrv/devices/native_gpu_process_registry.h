// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Opt-in marker for processes that completed the experimental NS2 graphics
// bootstrap and own an IGpuSession. This replaces the upstream-only
// KProcess::UsesPAuthReturns() discriminator, which Encore's pinned kernel
// does not implement. Neither firmware nor Switch 1 uses this registry.
#include <cstddef>
#include <map>
#include <mutex>

namespace Kernel { class KProcess; }
namespace Service::Nvidia::Devices {

class NativeGpuProcessRegistry {
public:
    static NativeGpuProcessRegistry& Instance() {
        static NativeGpuProcessRegistry registry;
        return registry;
    }
    bool Register(Kernel::KProcess* process) {
        if (!process) return false;
        const std::scoped_lock lock{mutex};
        if (owners.size() >= 256 && !owners.contains(process)) return false;
        ++owners[process];
        return true;
    }
    void Unregister(Kernel::KProcess* process) {
        if (!process) return;
        const std::scoped_lock lock{mutex};
        const auto it = owners.find(process);
        if (it == owners.end()) return;
        if (--it->second == 0) owners.erase(it);
    }
    [[nodiscard]] bool Contains(const Kernel::KProcess* process) const {
        if (!process) return false;
        const std::scoped_lock lock{mutex};
        return owners.contains(const_cast<Kernel::KProcess*>(process));
    }
    [[nodiscard]] std::size_t Count() const {
        const std::scoped_lock lock{mutex};
        return owners.size();
    }
private:
    mutable std::mutex mutex;
    std::map<Kernel::KProcess*, std::size_t> owners;
};
} // namespace Service::Nvidia::Devices
