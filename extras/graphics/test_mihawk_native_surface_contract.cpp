// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_native_surface_contract.h"
#include <cassert>
using namespace Eden::FeatureLab;
int main() {
    MihawkSurfaceCapabilities caps{};
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::Disabled);
    caps.enabled = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::NonNativeVulkan);
    caps.native_vulkan = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::MissingCompute);
    caps.compute_and_storage = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::MissingModel);
    caps.model_verified_and_loaded = true;
    caps.width = 1920; caps.height = 1080;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::UnsupportedFormat);
    caps.compositor_format = ColorFormat::Bgra8Unorm;
    caps.available_present_frames = 2;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::InsufficientSlots);
    caps.available_present_frames = 3;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::UnownedHistory);
    caps.owned_history_pair = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::IncorrectHistoryFormat);
    caps.history_matches_source_format = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::InvalidOutputFormat);
    caps.private_output_rgba8_storage = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::MissingPresentTransferUsage);
    caps.present_image_transfer_dst = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::InFlightResources);
    caps.history_descriptor_slots_fenced = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::NoPresenterSync);
    caps.present_queue_ordered = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::NativeHudPresent);
    caps.native_hud_absent = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::MissingBlitSupport);
    caps.blit_rgba_to_present = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::None);
    caps.compositor_format = ColorFormat::Rgba8Unorm;
    caps.blit_rgba_to_present = false;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::MissingBlitSupport);
    caps.blit_rgba_to_present = true;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::None);
    caps.width = 0;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::InvalidExtent);
    caps.width = 3840; caps.height = 2160;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::None);
    caps.available_present_frames = 2;
    assert(CheckNativeMihawkSurface(caps) == NativeMihawkReject::InsufficientSlots);
}
