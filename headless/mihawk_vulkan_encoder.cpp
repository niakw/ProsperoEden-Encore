// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_vulkan_encoder.h"

namespace Eden::FeatureLab {
MihawkEncoderResult MihawkVulkanEncoder::Record(const MihawkEncoderInput& input) noexcept {
    MihawkEncoderResult result{};
    if (timeline_.Pending()) {
        result.plan.status = MihawkPlanStatus::SubmissionPending;
        return result;
    }
    AdoptResources(input.images);
    result.plan = timeline_.Prepare(input.request);
    if (!result.plan.CanCapture())
        return result;

    const std::uint8_t next = result.plan.capture_slot;
    const std::uint8_t prev = result.plan.previous_slot;
    const MihawkSourceRecord copy{
        .cmd = input.commands,
        .source_real = input.real_composited_image,
        .history_owned = images_.history[next],
        .history_initialized = history_initialized_[next],
        .width = input.request.source.width,
        .height = input.request.source.height
    };
    result.recording = ValidateOwnedSnapshot(copy);
    if (result.recording != MihawkRecordResult::Recorded) {
        Abort();
        return result;
    }

    MihawkGenerateRecord generate{};
    if (result.plan.CanGenerate()) {
        generate = {
            .context = input.neural_context,
            .cmd = input.commands,
            .previous_owned = images_.history[prev],
            .current_owned = images_.history[next],
            .previous_view = images_.history_view[prev],
            .current_view = images_.history_view[next],
            .private_rgba_output = images_.rgba_output,
            .private_rgba_view = images_.rgba_view,
            .synthetic_present = input.synthetic_present_image,
            .width = input.request.source.width,
            .height = input.request.source.height,
            .descriptor_slot = 0,
            .context_slot_count = input.descriptor_slots,
            .output_was_blitted = output_blitted_,
            .capabilities = input.request.surface
        };
        // Check the *whole* stage before recording the first image barrier:
        // this avoids partially scheduled history copies on a failed generator.
        result.recording = ValidateNativeMihawkPair(generate);
        if (result.recording != MihawkRecordResult::Recorded) {
            Abort();
            return result;
        }
    }

    result.recording = RecordOwnedSnapshot(copy);
    if (result.recording != MihawkRecordResult::Recorded) {
        Abort();
        return result;
    }
    if (result.plan.CanGenerate()) {
        result.recording = RecordNativeMihawkPair(generate);
        if (result.recording != MihawkRecordResult::Recorded) {
            // A failure after recording commands must cause the entire command
            // buffer to be discarded. Caller sees IsRecorded()==false.
            Abort();
            return result;
        }
    }
    return result;
}

bool MihawkVulkanEncoder::Commit(const MihawkEncoderResult& result,
                                 std::uint64_t actual_gpu_serial) noexcept {
    if (!result.IsRecorded() ||
        !timeline_.Commit(result.plan, actual_gpu_serial)) return false;
    history_initialized_[result.plan.capture_slot] = true;
    if (result.WillPresentSynthetic()) output_blitted_ = true;
    return true;
}
} // namespace Eden::FeatureLab
