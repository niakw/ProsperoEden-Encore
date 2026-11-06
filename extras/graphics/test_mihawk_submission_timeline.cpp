// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_submission_timeline.h"
#include <cassert>
using namespace Eden::FeatureLab;

static MihawkSubmitRequest StandardRequest() {
    MihawkSubmitRequest r{};
    r.mode = FrameGeneration::MihawkGen;
    r.graphics.native_vulkan = true;
    r.graphics.mihawk_compute = true;
    r.graphics.model_weights_verified_and_loaded = true;
    r.graphics.game_fps = 30;
    r.surface = {
        .enabled = true, .native_vulkan = true,
        .compute_and_storage = true, .model_verified_and_loaded = true,
        .blit_rgba_to_present = true, .owned_history_pair = true,
        .history_matches_source_format = true,
        .private_output_rgba8_storage = true,
        .present_image_transfer_dst = true,
        .history_descriptor_slots_fenced = true,
        .present_queue_ordered = true, .native_hud_absent = true,
        .available_present_frames = 3,
        .width = 1920, .height = 1080,
        .compositor_format = ColorFormat::Bgra8Unorm
    };
    r.source = {
        .real_frame_id = 1,
        .timestamp_ns = 1'000'000'000,
        .width = 1920, .height = 1080,
        .output_hz = 60,
        .display_mode_verified = true
    };
    r.reserved_gpu_serial = 1;
    return r;
}

int main() {
    MihawkSubmissionTimeline timeline{};
    auto r = StandardRequest();
    assert(timeline.Prepare(r).status == MihawkPlanStatus::CaptureOnly);
    assert(timeline.Pending());
    assert(timeline.Prepare(r).status == MihawkPlanStatus::SubmissionPending);
    timeline.Abort();
    assert(!timeline.Pending() && timeline.LastSubmittedSerial() == 0);
    auto p = timeline.Prepare(r);
    assert(p.CanCapture() && !p.CanGenerate() && p.capture_slot == 0);
    assert(timeline.Commit(p, p.reserved_gpu_serial));
    assert(!timeline.Commit(p, p.reserved_gpu_serial));
    assert(timeline.SlotBusyUntil(0) == 1);

    // GPU hasn't signaled serial 1 yet: second snapshot may be copied, but
    // generation is prohibited because history 0 is still in flight.
    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    r.reserved_gpu_serial = 2;
    p = timeline.Prepare(r);
    assert(p.status == MihawkPlanStatus::CaptureOnly && p.capture_slot == 1);
    assert(timeline.Commit(p, p.reserved_gpu_serial));
    assert(timeline.SlotBusyUntil(1) == 2);

    // Slot 0 still busy -> skip rather than overwrite the previous source.
    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    r.reserved_gpu_serial = 3;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::GpuBusy);
    assert(!timeline.Pending());

    // Once completion arrives, re-prime safely with two new real pictures.
    r.completed_gpu_serial = 2;
    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    p = timeline.Prepare(r);
    assert(p.status == MihawkPlanStatus::CaptureOnly && p.capture_slot == 0);
    assert(timeline.Commit(p, p.reserved_gpu_serial));

    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    r.reserved_gpu_serial = 4;
    r.completed_gpu_serial = 3;
    p = timeline.Prepare(r);
    assert(p.CanGenerate() && p.capture_slot == 1 && p.previous_slot == 0);
    assert(timeline.Commit(p, p.reserved_gpu_serial));
    assert(timeline.OutputBusyUntil() == 4);
    assert(timeline.SlotBusyUntil(0) == 4);
    assert(timeline.SlotBusyUntil(1) == 4);

    // Synthetic output is still in flight: cannot overwrite even when one
    // source is somehow already free. Every slot remains busy until serial 4.
    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    r.reserved_gpu_serial = 5;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::GpuBusy);

    r.completed_gpu_serial = 4;
    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    p = timeline.Prepare(r);
    assert(p.CanCapture() && !p.CanGenerate());
    assert(timeline.Commit(p, p.reserved_gpu_serial));

    // Scene change resets the source pair and never allocates a synthetic
    // image from a stale game / HUD / TV mode.
    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    r.reserved_gpu_serial = 6;
    r.completed_gpu_serial = 5;
    r.source.scene_reset = true;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::RejectedCadence);
    r.source.scene_reset = false;

    ++r.source.real_frame_id;
    r.source.timestamp_ns += 33'333'333;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::CaptureOnly);
    // Cancel the plan: the renderer must discard the unsent GPU command
    // buffer; no bytes or image lifetimes are claimed by this timeline.
    timeline.Abort();
    assert(!timeline.Pending());

    r.source.overlay_changed = true;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::RejectedCadence);
    r.source.overlay_changed = false;
    r.surface.native_hud_absent = false;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::UnsafeResources);
    r.surface.native_hud_absent = true;
    r.mode = FrameGeneration::Fsr3Vulkan;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::Disabled);
    r.mode = FrameGeneration::Off;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::Disabled);

    // Reject invented or regressed GPU serials, not just bad frame IDs.
    r.mode = FrameGeneration::MihawkGen;
    r.reserved_gpu_serial = 5;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::InvalidSerial);
    r.reserved_gpu_serial = 6;
    r.completed_gpu_serial = 999;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::InvalidSerial);
    // Global timeline can advance beyond the last R08 submission due to
    // ordinary renderer work. That is valid if reservation stays ahead.
    r.reserved_gpu_serial = 1000;
    r.source.real_frame_id++;
    r.source.timestamp_ns += 33'333'333;
    assert(timeline.Prepare(r).status == MihawkPlanStatus::CaptureOnly);
    timeline.Abort();
}
