// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Strictly host-testable R08 Vulkan history lifetime model.
// The owning renderer supplies *completed* and *submitting* GPU timeline
// serials observed on the SAME graphics queue. CPU frame IDs are NOT fences.
// No work is submitted by this class; normal real-frame presentation never
// depends on a plan being accepted.
#include "framegen_present_gate.h"
#include "mihawk_native_surface_contract.h"
#include <array>
#include <cstdint>
#include <algorithm>
#include <limits>

namespace Eden::FeatureLab {
enum class MihawkPlanStatus : std::uint8_t {
    CaptureOnly, GenerateAndCapture, Disabled, UnsafeResources,
    InvalidSerial, SubmissionPending, GpuBusy, RejectedCadence, Quarantined
};
struct MihawkSubmitRequest {
    FrameGeneration mode = FrameGeneration::Off;
    GraphicsCapabilities graphics{};
    MihawkSurfaceCapabilities surface{};
    PresentGateInput source{};
    std::uint64_t completed_gpu_serial = 0;  // actual fence/timeline completed
    std::uint64_t reserved_gpu_serial = 0;   // future submission serial
};
struct MihawkSubmissionPlan {
    MihawkPlanStatus status = MihawkPlanStatus::Disabled;
    std::uint64_t reserved_gpu_serial = 0;
    std::uint8_t capture_slot = 0;
    std::uint8_t previous_slot = 0;
    bool reset_history = false;
    constexpr bool CanCapture() const noexcept {
        return status == MihawkPlanStatus::CaptureOnly ||
               status == MihawkPlanStatus::GenerateAndCapture;
    }
    constexpr bool CanGenerate() const noexcept {
        return status == MihawkPlanStatus::GenerateAndCapture;
    }
};

class MihawkSubmissionTimeline {
public:
    // Externally pause/discard source history without lying about the GPU
    // completion of resources still being read. Busy serials stay untouched.
    constexpr void InvalidateHistory() noexcept {
        gate_.Reset();
        previous_valid_ = false;
    }

    // Scheduler::IsFree(tick) can safely poll these already-submitted ticks
    // without blocking CPU presentation. Never invent a completed GPU tick.
    template<typename IsFree>
    std::uint64_t PollCompleted(IsFree&& is_free) noexcept {
        const std::array<std::uint64_t, 3> serials{
            busy_until_[0], busy_until_[1], output_busy_until_};
        for (const auto tick : serials) {
            if (tick > last_completed_ && tick != std::numeric_limits<std::uint64_t>::max() &&
                is_free(tick))
                last_completed_ = tick;
        }
        return last_completed_;
    }

    // A reservation is a minimum guarantee, not a guessed exact Vulkan tick.
    // The actual tick returned by Scheduler::Flush must be passed to Commit.
    constexpr std::uint64_t NextReservation(std::uint64_t completed) const noexcept {
        const auto lower_bound = std::max(completed, latest_submitted_);
        return lower_bound == std::numeric_limits<std::uint64_t>::max()
                   ? 0 : lower_bound + 1;
    }
    constexpr MihawkSubmissionPlan Prepare(const MihawkSubmitRequest& request) noexcept {
        if (pending_) return {MihawkPlanStatus::SubmissionPending};
        if (quarantined_) return {MihawkPlanStatus::Quarantined};
        if (request.mode != FrameGeneration::MihawkGen) {
            InvalidateHistory();
            return {MihawkPlanStatus::Disabled};
        }
        if (CheckNativeMihawkSurface(request.surface) != NativeMihawkReject::None) {
            InvalidateHistory();
            return {MihawkPlanStatus::UnsafeResources};
        }
        // The graphics queue may submit unrelated work between R08 frames;
        // completed can exceed the last *R08* serial. Only require globally
        // monotonic completion and reservation with completed < reserved.
        // Serials come from a real fence/timeline, not CPU frame counts.
        if (!request.reserved_gpu_serial ||
            request.reserved_gpu_serial <= latest_submitted_ ||
            request.completed_gpu_serial < last_completed_ ||
            request.reserved_gpu_serial <= request.completed_gpu_serial) {
            InvalidateHistory();
            return {MihawkPlanStatus::InvalidSerial};
        }
        last_completed_ = request.completed_gpu_serial;
        const PresentGateDecision decision = gate_.OnRealFrame(
            request.mode, request.graphics, request.source);
        if (decision.reset_history) previous_valid_ = false;
        if (decision.reason != PresentGateReason::Eligible &&
            decision.reason != PresentGateReason::NoStablePair &&
            decision.reason != PresentGateReason::NoDisplayHeadroom) {
            InvalidateHistory();
            return {MihawkPlanStatus::RejectedCadence};
        }
        if (request.source.width != request.surface.width ||
            request.source.height != request.surface.height) {
            InvalidateHistory();
            return {MihawkPlanStatus::UnsafeResources};
        }
        const std::uint8_t slot = next_capture_slot_;
        // Never overwrite a snapshot referenced by a queued GPU dispatch.
        if (busy_until_[slot] > last_completed_) {
            InvalidateHistory();
            return {MihawkPlanStatus::GpuBusy};
        }
        const bool eligible_pair =
            previous_valid_ && previous_slot_ != slot &&
            decision.eligible() &&
            busy_until_[previous_slot_] <= last_completed_ &&
            output_busy_until_ <= last_completed_;
        MihawkSubmissionPlan plan{};
        plan.status = eligible_pair ? MihawkPlanStatus::GenerateAndCapture
                                    : MihawkPlanStatus::CaptureOnly;
        plan.reserved_gpu_serial = request.reserved_gpu_serial;
        plan.capture_slot = slot;
        plan.previous_slot = previous_slot_;
        plan.reset_history = decision.reset_history;
        pending_ = true;
        pending_plan_ = plan;
        return plan;
    }

    // Commit only AFTER commands have successfully been placed on a real GPU
    // queue with the declared completion serial. If no queue submission was
    // made, call Abort(). An aborted recording must not be submitted later.
    constexpr bool Commit(const MihawkSubmissionPlan& plan,
                          std::uint64_t actual_gpu_serial) noexcept {
        if (!pending_ || !plan.CanCapture() ||
            plan.reserved_gpu_serial != pending_plan_.reserved_gpu_serial ||
            plan.capture_slot != pending_plan_.capture_slot ||
            plan.previous_slot != pending_plan_.previous_slot ||
            plan.status != pending_plan_.status)
            return false;
        pending_ = false;
        if (actual_gpu_serial < plan.reserved_gpu_serial ||
            actual_gpu_serial <= last_completed_ ||
            actual_gpu_serial <= latest_submitted_) {
            // Commands may already have been submitted; never reuse the
            // resource until owner waits VkDeviceIdle and recreates them.
            quarantined_ = true;
            busy_until_.fill(std::numeric_limits<std::uint64_t>::max());
            output_busy_until_ = std::numeric_limits<std::uint64_t>::max();
            InvalidateHistory();
            return false;
        }
        latest_submitted_ = actual_gpu_serial;
        busy_until_[plan.capture_slot] = latest_submitted_;
        if (plan.CanGenerate()) {
            // Both snapshots are bound to the dispatch until this GPU serial
            // has actually completed, even if the next frame is queued early.
            busy_until_[plan.previous_slot] = latest_submitted_;
            output_busy_until_ = latest_submitted_;
        }
        previous_slot_ = plan.capture_slot;
        previous_valid_ = true;
        next_capture_slot_ = static_cast<std::uint8_t>(plan.capture_slot ^ 1U);
        return true;
    }

    constexpr bool Quarantined() const noexcept { return quarantined_; }
    // Only after the owning VkDevice is idle AND the private resources have
    // been destroyed/recreated. Never call in a render-loop fallback.
    constexpr void ResetAfterDeviceIdle() noexcept {
        *this = MihawkSubmissionTimeline{};
    }

    constexpr void Abort() noexcept {
        pending_ = false;
        InvalidateHistory();
    }
    constexpr std::uint64_t LastSubmittedSerial() const noexcept { return latest_submitted_; }
    constexpr std::uint64_t SlotBusyUntil(std::uint8_t index) const noexcept {
        return busy_until_[index & 1U];
    }
    constexpr std::uint64_t OutputBusyUntil() const noexcept { return output_busy_until_; }
    constexpr bool Pending() const noexcept { return pending_; }

private:
    FramegenPresentGate gate_{};
    std::array<std::uint64_t, 2> busy_until_{};
    std::uint64_t output_busy_until_ = 0;
    std::uint64_t latest_submitted_ = 0;
    std::uint64_t last_completed_ = 0;
    std::uint8_t previous_slot_ = 0;
    std::uint8_t next_capture_slot_ = 0;
    bool previous_valid_ = false;
    bool pending_ = false;
    bool quarantined_ = false;
    MihawkSubmissionPlan pending_plan_{};
};
} // namespace Eden::FeatureLab
