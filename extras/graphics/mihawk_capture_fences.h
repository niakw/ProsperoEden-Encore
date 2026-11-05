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
    // Previous real source must actually have been captured immediately
    // before this one. Pure guest frame IDs and clock estimates never stand
    // in for a GPU-completed captured history image.
    template<class IsFree>
    bool CanGenerate(const MihawkCapturePermit& permit, std::uint64_t real_id,
                     IsFree&& is_free) const noexcept {
        if (!permit.valid || !pending_ || quarantined_ ||
            permit.slot != next_slot_ || real_id == 0 ||
            previous_source_id_ == 0 || previous_source_id_ + 1 != real_id)
            return false;
        const auto previous_tick = busy_until_[permit.slot ^ 1];
        return previous_tick != 0 && is_free(previous_tick) &&
            (output_busy_until_ == 0 || is_free(output_busy_until_));
    }

    // Must be called immediately after Scheduler::Flush returns the actual
    // submission tick. A zero or regressing tick quarantines this ring.
    bool Commit(const MihawkCapturePermit& permit, std::uint64_t actual_tick,
                std::uint64_t source_id = 0, bool generated = false) noexcept {
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
        if (generated) {
            // The compute dispatch sampled the previous snapshot and wrote
            // the sole RGBA output until this same GPU tick is complete.
            busy_until_[next_slot_ ^ 1] = actual_tick;
            output_busy_until_ = actual_tick;
        }
        previous_source_id_ = source_id;
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
    std::uint64_t OutputBusyUntil() const noexcept { return output_busy_until_; }
    std::uint64_t PreviousSourceId() const noexcept { return previous_source_id_; }
    std::uint64_t BusyUntil(std::uint32_t slot) const noexcept {
        return busy_until_[slot & 1];
    }

private:
    std::array<std::uint64_t, 2> busy_until_{};
    std::uint64_t latest_gpu_tick_ = 0;
    std::uint64_t previous_source_id_ = 0;
    std::uint64_t output_busy_until_ = 0;
    std::uint8_t next_slot_ = 0;
    bool quarantined_ = false;
    bool pending_ = false;
};
} // namespace Eden::FeatureLab
