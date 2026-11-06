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
}
