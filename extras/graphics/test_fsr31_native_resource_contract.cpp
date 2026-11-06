// SPDX-License-Identifier: GPL-3.0-or-later
#include <cassert>
#include "fsr31_native_resource_contract.h"
using namespace Eden::Graphics::Temporal;
int main() {
    Inputs meta{};
    meta.scene_color={11,21,1,1,Producer::GuestGpuVerified};
    meta.depth={12,22,1,1,Producer::GuestGpuVerified};
    meta.motion={13,23,1,1,Producer::GuestGpuVerified};
    NativeResources n{{11,21},{12,22},{13,23}};
    assert(ValidateNativeResources(meta,n)==Rejection::None);
    n.depth.view=0;
    assert(ValidateNativeResources(meta,n)==Rejection::MissingResource);
    n.depth.view=22; n.motion.image=100;
    assert(ValidateNativeResources(meta,n)==Rejection::MismatchedNativeResource);
    n.motion.image=13; n.motion.view=21;
    assert(ValidateNativeResources(meta,n)==Rejection::MismatchedNativeResource);
    // Duplicate guest handles are not distinct temporal semantics.
    n.motion.view=23;meta.motion.view=21;n.motion.view=21;
    assert(ValidateNativeResources(meta,n)==Rejection::MismatchedNativeResource);
    meta.motion.view=23;n.motion.view=23;
    meta.depth.image=99;
    assert(ValidateNativeResources(meta,n)==Rejection::MismatchedNativeResource);
    meta.depth.image=12;
    meta.output_width=1920;
    meta.output_height=1080;
    NativeDestination dst{.image=88,.width=1920,.height=1080,
                          .samples=1,.single_color_no_depth=true};
    assert(ValidateNativeDestination(meta,dst)==Rejection::None);
    dst.image=11;
    assert(ValidateNativeDestination(meta,dst)==Rejection::OutputAliasesInput);
    dst.image=12;
    assert(ValidateNativeDestination(meta,dst)==Rejection::OutputAliasesInput);
    dst.image=13;
    assert(ValidateNativeDestination(meta,dst)==Rejection::OutputAliasesInput);
    dst.image=88;
    dst.samples=4;
    assert(ValidateNativeDestination(meta,dst)==Rejection::InvalidResolution);
    dst.samples=1;
    dst.width=1280;
    assert(ValidateNativeDestination(meta,dst)==Rejection::InvalidResolution);
    dst.width=1920;
    dst.single_color_no_depth=false;
    assert(ValidateNativeDestination(meta,dst)==Rejection::InvalidResolution);
}
