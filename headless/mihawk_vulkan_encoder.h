// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Composition of real-frame gating, GPU timeline ownership, source snapshots,
// neural dispatch and conversion. THIS IS NOT YET CALLED BY THE PS5 RENDERER.
// Opt-in qualifier cannot be enabled without real fences and HUD verification.
#include "mihawk_vulkan_stage.h"
#include "mihawk_submission_timeline.h"
#include "mihawk_vulkan_resources.h"

namespace Eden::FeatureLab {
struct MihawkEncoderImages {
    VkImage history[2]{VK_NULL_HANDLE, VK_NULL_HANDLE};
    VkImageView history_view[2]{VK_NULL_HANDLE, VK_NULL_HANDLE};
    VkImage rgba_output = VK_NULL_HANDLE;
    VkImageView rgba_view = VK_NULL_HANDLE;
    std::uint64_t resource_generation = 0;
    static MihawkEncoderImages FromOwned(const MihawkVulkanResources& owned) noexcept {
        if (!owned.IsReady()) return {};
        return {
            {owned.History(0).image, owned.History(1).image},
            {owned.History(0).view, owned.History(1).view},
            owned.RgbaOutput().image, owned.RgbaOutput().view,
            owned.Generation()
        };
    }
};
struct MihawkEncoderInput {
    MihawkSubmitRequest request{};
    VkCommandBuffer commands = VK_NULL_HANDLE;
    VkImage real_composited_image = VK_NULL_HANDLE;
    VkImage synthetic_present_image = VK_NULL_HANDLE;
    fg_context* neural_context = nullptr;
    std::uint32_t descriptor_slots = 0;
    MihawkEncoderImages images{};
};
struct MihawkEncoderResult {
    MihawkSubmissionPlan plan{};
    MihawkRecordResult recording = MihawkRecordResult::NotReady;
    constexpr bool IsRecorded() const noexcept {
        return plan.CanCapture() && recording == MihawkRecordResult::Recorded;
    }
    constexpr bool WillPresentSynthetic() const noexcept {
        return IsRecorded() && plan.CanGenerate();
    }
};

class MihawkVulkanEncoder {
public:
    MihawkEncoderResult Record(const MihawkEncoderInput& input) noexcept;
    // Must receive the actual GPU completion tick from Scheduler::Flush.
    bool Commit(const MihawkEncoderResult& result,
                std::uint64_t actual_gpu_serial) noexcept;
    // Aborting means the renderer DROPS its command buffer: no partial
    // snapshots/generation may be submitted after calling Abort.
    void Abort() noexcept { timeline_.Abort(); ResetLocalHistory(); }
    void InvalidateHistory() noexcept {
        timeline_.InvalidateHistory();
        ResetLocalHistory();
    }
    constexpr const MihawkSubmissionTimeline& Timeline() const noexcept { return timeline_; }
    // Must only be called after VkDeviceWaitIdle, destruction/reallocation of
    // the owned resources and a game/renderer reset. Not a frame fallback.
    void ResetAfterDeviceIdle() noexcept {
        timeline_.ResetAfterDeviceIdle();
        ResetLocalHistory();
        images_ = {};
    }
private:
    void AdoptResources(const MihawkEncoderImages& incoming) noexcept {
        if (images_.resource_generation != incoming.resource_generation ||
            images_.history[0] != incoming.history[0] ||
            images_.history[1] != incoming.history[1] ||
            images_.history_view[0] != incoming.history_view[0] ||
            images_.history_view[1] != incoming.history_view[1] ||
            images_.rgba_output != incoming.rgba_output ||
            images_.rgba_view != incoming.rgba_view) {
            InvalidateHistory(); // GPU serial reservations are NOT erased
            images_ = incoming;
        }
    }
    void ResetLocalHistory() noexcept {
        // Do not forget the in-flight GPU serials: Timeline retains them.
        history_initialized_[0] = history_initialized_[1] = false;
        output_blitted_ = false;
    }
    MihawkSubmissionTimeline timeline_{};
    MihawkEncoderImages images_{};
    bool history_initialized_[2]{};
    bool output_blitted_ = false;
};
} // namespace Eden::FeatureLab
