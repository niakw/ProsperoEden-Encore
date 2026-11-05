// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R08: native-present eligibility and reset rules, deliberately independent of a
// Vulkan backend. Calling this does NOT submit a generated frame.
#include "framegen_capabilities.h"

#include <cstdint>

namespace Eden::FeatureLab {

enum class PresentGateReason : std::uint8_t {
    Disabled, Unsupported, Unverified120Hz, UnsafeOverlay, Paused,
    NoStablePair, StaleOrSkippedFrame, WrongCadence, NoDisplayHeadroom,
    Eligible
};

struct PresentGateInput {
    // Monotonic ID and timestamp for REAL source frames only. Never count
    // synthetic presents as new source frames.
    std::uint64_t real_frame_id = 0;
    std::uint64_t timestamp_ns = 0;
    std::uint32_t width = 0;
    std::uint32_t height = 0;
    std::uint32_t output_hz = 60; // Negotiated, not merely requested
    bool display_mode_verified = false;
    bool pause_or_menu = false;
    bool overlay_changed = false; // HUD, subtitles, menus or compositor overlays
    bool scene_reset = false;     // Resolution/TV mode/renderer/seek/game change
};

struct PresentGateDecision {
    PresentGateReason reason = PresentGateReason::Disabled;
    // A real frame still goes to normal Vulkan presentation. Only this
    // optional extra display frame is gated.
    std::uint8_t synthetic_frames = 0;
    bool reset_history = false;
    constexpr bool eligible() const noexcept {
        return reason == PresentGateReason::Eligible && synthetic_frames != 0;
    }
};

// Frame pairs must not cross menus, scene resets, duplicated frames, altered
// overlays, or unsafe clock gaps. The application owns the actual GPU
// barriers, image lifetimes, and queue fences (not this helper).
class FramegenPresentGate {
public:
    constexpr void Reset() noexcept {
        primed_ = false;
        last_id_ = 0;
        last_ns_ = 0;
        last_width_ = 0;
        last_height_ = 0;
        last_hz_ = 0;
    }

    constexpr PresentGateDecision OnRealFrame(FrameGeneration mode,
                                              const GraphicsCapabilities& caps,
                                              const PresentGateInput& input) noexcept {
        const auto reject = [this](PresentGateReason reason) constexpr {
            Reset();
            return PresentGateDecision{reason, 0, true};
        };
        if (mode == FrameGeneration::Off)
            return reject(PresentGateReason::Disabled);
        if (QualifyFrameGeneration(mode, caps) == Availability::Unsupported)
            return reject(PresentGateReason::Unsupported);
        if (!input.display_mode_verified || (input.output_hz != 60 && input.output_hz != 120))
            return reject(PresentGateReason::Unverified120Hz);
        if (input.pause_or_menu || input.scene_reset)
            return reject(PresentGateReason::Paused);
        // Whole-screen colour-frame interpolation could smear guest HUD and
        // overlays. The renderer must prove a clean pair before enabling.
        if (input.overlay_changed)
            return reject(PresentGateReason::UnsafeOverlay);
        if (input.width == 0 || input.height == 0 ||
            input.width > 7680 || input.height > 4320 ||
            input.real_frame_id == 0 || input.timestamp_ns == 0)
            return reject(PresentGateReason::StaleOrSkippedFrame);
        if (caps.game_fps >= input.output_hz)
            return reject(PresentGateReason::NoDisplayHeadroom);
        if (!primed_) {
            Remember(input);
            return {PresentGateReason::NoStablePair, 0, true};
        }
        if (input.width != last_width_ || input.height != last_height_ ||
            input.output_hz != last_hz_ ||
            input.real_frame_id != last_id_ + 1 ||
            input.timestamp_ns <= last_ns_)
            return reject(PresentGateReason::StaleOrSkippedFrame);
        const std::uint64_t delta_ns = input.timestamp_ns - last_ns_;
        Remember(input);
        // 30..120 actual source frames/s, with a tolerant margin. A large
        // stall or a frame repeated by the emulator must not be interpolated.
        if (delta_ns < 8'000'000 || delta_ns > 42'000'000)
            return reject(PresentGateReason::WrongCadence);
        // Initially cap to one interpolated frame (30->60 or 60->120), NOT
        // the 30->120 x4 mode. Multi-interpolation needs a measured PS5 budget.
        if (caps.game_fps * 2 > input.output_hz + 3)
            return {PresentGateReason::NoDisplayHeadroom, 0, false};
        return {PresentGateReason::Eligible, 1, false};
    }

private:
    constexpr void Remember(const PresentGateInput& x) noexcept {
        primed_ = true;
        last_id_ = x.real_frame_id;
        last_ns_ = x.timestamp_ns;
        last_width_ = x.width;
        last_height_ = x.height;
        last_hz_ = x.output_hz;
    }
    bool primed_ = false;
    std::uint64_t last_id_ = 0, last_ns_ = 0;
    std::uint32_t last_width_ = 0, last_height_ = 0, last_hz_ = 0;
};

} // namespace Eden::FeatureLab
