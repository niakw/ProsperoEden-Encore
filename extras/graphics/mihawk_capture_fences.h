// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Native Vulkan source-history capture ring. Owns only GPU submission serials:
// private VkImages and their final layout remain owned by MihawkVulkanResources.
// No screenshot-frame, CPU frame ID, or guessed timestamp is a GPU fence.
#include <array>
#include <cstdint>

namespace Eden::FeatureLab {

struct MihawkCapturePermit {
    std::uint64_t previous_gpu_tick = 0;
    std::uint8_t slot = 0;
    bool valid = false;
};

class MihawkCaptureFences {
public:
    template<class IsFree>
    MihawkCapturePermit Acquire(IsFree&& is_free) noexcept {
        if (quarantined_ || pending_) return {};
        const auto serial = busy_until_[next_slot_];
        if (serial && !is_free(serial)) return {};
        pending_ = true;
        return {serial, next_slot_, true};
    }
    // Must be called immediately after Scheduler::Flush returns the actual
    // submission tick. A zero or regressing tick quarantines this ring.
    bool Commit(const MihawkCapturePermit& permit, std::uint64_t actual_tick) noexcept {
        if (!pending_ || !permit.valid || permit.slot != next_slot_ ||
            permit.previous_gpu_tick != busy_until_[next_slot_])
            return false;
        pending_ = false;
        if (!actual_tick || actual_tick <= latest_gpu_tick_ ||
            actual_tick <= permit.previous_gpu_tick) {
            quarantined_ = true;
            return false;
        }
        busy_until_[next_slot_] = actual_tick;
        latest_gpu_tick_ = actual_tick;
        next_slot_ ^= 1;
        return true;
    }
    // Aborting is legal only if the associated command buffer is not
    // submitted. It does not discard GPU serials from earlier frames.
    void AbortUnsubmitted() noexcept { pending_ = false; }
    // Only after the owning VkDevice is fully idle and image resources are
    // recreated. Never call this for a per-frame fallback.
    void ResetAfterDeviceIdle() noexcept { *this = MihawkCaptureFences{}; }
    bool Quarantined() const noexcept { return quarantined_; }
    bool Pending() const noexcept { return pending_; }
    std::uint64_t LatestGpuTick() const noexcept { return latest_gpu_tick_; }
    std::uint64_t BusyUntil(std::uint32_t slot) const noexcept {
        return busy_until_[slot & 1];
    }

private:
    std::array<std::uint64_t, 2> busy_until_{};
    std::uint64_t latest_gpu_tick_ = 0;
    std::uint8_t next_slot_ = 0;
    bool quarantined_ = false;
    bool pending_ = false;
};
} // namespace Eden::FeatureLab
