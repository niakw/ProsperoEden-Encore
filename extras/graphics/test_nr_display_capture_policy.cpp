// SPDX-License-Identifier: MIT
#include "nr_display_capture_policy.h"
#include <cassert>
using namespace Eden::Graphics;
int main(){
    constexpr NRDisplayCapture raw{
        false,true,1920u,1080u,1920u,1080u,0.f,0.f,1.f,1.f};
    static_assert(CanR09CaptureDisplay(raw));
    constexpr NRDisplayCapture gpu{
        true,true,1280u,720u,1920u,1080u,0.f,0.f,1.f,1.f};
    static_assert(CanR09CaptureDisplay(gpu));
    constexpr NRDisplayCapture direct{
        true,true,1920u,1080u,1920u,1080u,0.f,0.f,1.f,1.f};
    static_assert(CanR09CaptureDisplay(direct));
    auto bad=raw;bad.live_image=false;
    assert(!CanR09CaptureDisplay(bad));
    bad=raw;bad.native_width=1280u;
    assert(!CanR09CaptureDisplay(bad));
    bad=gpu;bad.sampled_height=720u;
    assert(!CanR09CaptureDisplay(bad));
    bad=gpu;bad.sampled_width=2560u;
    assert(!CanR09CaptureDisplay(bad));
    bad=gpu;bad.native_width=0u;
    assert(!CanR09CaptureDisplay(bad));
    bad=gpu;bad.crop_left=0.125f;
    assert(!CanR09CaptureDisplay(bad));
    bad=gpu;bad.crop_bottom=0.9f;
    assert(!CanR09CaptureDisplay(bad));
    bad=gpu;bad.crop_right=0.0f;
    assert(!CanR09CaptureDisplay(bad));
    bad=gpu;bad.single_sample=false;
    assert(!CanR09CaptureDisplay(bad));
}
