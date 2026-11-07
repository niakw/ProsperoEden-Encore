// SPDX-License-Identifier: GPL-3.0-or-later
#include "neural_video_policy.h"
#include <cassert>
using namespace Eden::NeuralVideo;
int main() {
    static_assert(kModeCount==6);
    static_assert(kOff==0&&kA4kDetail==1&&kA4kSoft==2&&
                  kA4kDenoise==3&&kDlssOriginal==4&&kDlssCompact==5);
    assert(Check(kOff,1,0,1,0)==Reason::Disabled);
    for(int mode=kA4kDetail;mode<=kA4kDenoise;++mode) {
        assert(IsA4k(mode));
        assert(InternalA4kFilter(mode)==mode+6);
        assert(ModeFromLegacyA4kFilter(mode+6)==mode);
        assert(CanSelect(mode,1,0,1,0));
        assert(!CanSelect(mode,1,1,1,0));
        assert(!CanSelect(mode,0,0,1,0));
        assert(!CanSelect(mode,1,0,4,0));
        assert(!CanSelect(mode,1,0,1,2));
        assert(RuntimeParametersEnabled(mode));
        assert(!HasStrength(mode));
    }
    for(int mode=kDlssOriginal;mode<=kDlssCompact;++mode) {
        assert(IsDlss(mode)&&HasStrength(mode));
        assert(Check(mode,1,0,1,0)==Reason::EngineIncomplete);
        assert(CanSelect(mode,1,0,1,0)); // UI selection != GPU proof
        assert(!RuntimeParametersEnabled(mode));
        for(int aa=0;aa<=3;++aa) {
            assert(CanSelect(mode,1,0,aa,0));
            assert(EffectiveAntiAliasing(aa,1,mode,true)==0);
        }
        // A rejected model must never unexpectedly change the AA policy.
        assert(EffectiveAntiAliasing(1,1,mode,false)==1);
    }
    assert(EffectiveAntiAliasing(1,1,kOff,false)==1);
    assert(EffectiveAntiAliasing(3,1,kA4kDetail,true)==3);
    assert(EffectiveAntiAliasing(5,0,kOff,false)==0);
    assert(DlssModelIndex(kDlssOriginal)==0&&DlssModelIndex(kDlssCompact)==1);
    assert(!CanEnable(1,0,1,0));
    assert(FramegenMethodSelectable(0,1,kDlssOriginal,false));
    assert(!FramegenMethodSelectable(2,1,kDlssOriginal,true));
    assert(FramegenMethodSelectable(2,1,kOff,true));
    assert(!UpscaleSelectable(7,1,kOff));
    assert(!UpscaleSelectable(1,1,kA4kDetail));
    assert(UpscaleSelectable(0,1,kA4kSoft));
    assert(!AntiAliasingSelectable(4,1,kDlssCompact));
    assert(AntiAliasingSelectable(2,1,kDlssCompact));
    assert(PresetsMayBeStored(0,0)&&!PresetsMayBeStored(2,100));
}
