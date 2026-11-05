// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only real roundtrip and menu dependency test; no PS5 build.
#include "settings_store.h"
#include "pe/ui/video_presets.hpp"
#include "encore_texture_profiles.h"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <string>
#include <unistd.h>

int main() {
    using namespace pe::ui;
    constexpr auto fc27 = Eden::EncoreTextureProfiles::kFc27TitleId;
    for (int tier=0; tier<kAuthoredVideoProfiles; ++tier) {
        Preferences p{};
        ApplyVideoPreset(p,tier);
        assert(p.performance_profile==tier);
        assert(p.texture_anisotropy==Eden::EncoreTextureProfiles::ForTitle(0,tier));
        assert(DetectVideoProfile(p)==tier);
        assert(p.fsr_sharpness==50);
        GameSettings g{};
        ApplyVideoPreset(g,tier,fc27);
        assert(g.texture_anisotropy==Eden::EncoreTextureProfiles::ForTitle(fc27,tier));
        assert(g.filter==VideoPresetForTitle(fc27,tier).filter);
        assert(EffectiveGameUpscalingFilter(g,p,fc27)==g.filter);
        assert(EffectiveGameRenderer(g,p,fc27)==g.renderer);
        assert(FrameGenerationSelectable(1));
        assert(!FrameGenerationSelectable(0));
    }
    // No custom sampler may be silently classified as an authored preset.
    Preferences p{};
    ApplyVideoPreset(p,1);
    p.texture_anisotropy=5;
    assert(DetectVideoProfile(p)==kCustomVideoProfile);
    RefreshVideoProfile(p);
    assert(p.performance_profile==kCustomVideoProfile);
    ApplyVideoPreset(p,1);
    GameSettings inherited{};
    assert(EffectiveGameUpscalingFilter(inherited,p,fc27)==
           VideoPresetForTitle(fc27,1).filter);
    assert(EffectiveGameRenderer(inherited,p,fc27)==
           VideoPresetForTitle(fc27,1).renderer);
    inherited.filter=1;
    assert(EffectiveGameUpscalingFilter(inherited,p,fc27)==1);
    inherited.renderer=0;
    assert(!FrameGenerationSelectable(
        EffectiveGameRenderer(inherited,p,fc27)));
    inherited.filter=-1;
    inherited.renderer=-1;
    char filename[]="/tmp/eden-graphics-policy-XXXXXX";
    const int fd=mkstemp(filename);
    assert(fd>=0);
    close(fd);
    Eden::Preferences saved{};
    saved.texture_anisotropy = p.texture_anisotropy;
    assert(Eden::SavePreferences(saved,filename));
    assert(Eden::LoadPreferences(filename).texture_anisotropy==
           Eden::EncoreTextureProfiles::ForTitle(0,1));
    Eden::GameSettings saved_game{};
    saved_game.texture_anisotropy = inherited.texture_anisotropy;
    assert(Eden::SaveGameSettings(fc27,saved_game,filename));
    assert(Eden::LoadGameSettings(fc27,filename).texture_anisotropy==-1);
    saved_game.texture_anisotropy=4;
    assert(Eden::SaveGameSettings(fc27,saved_game,filename));
    assert(Eden::LoadGameSettings(fc27,filename).texture_anisotropy==4);
    saved_game.texture_anisotropy=6;
    assert(!Eden::SaveGameSettings(fc27,saved_game,filename));
    saved_game.texture_anisotropy=-1;
    assert(Eden::SaveGameSettings(fc27,saved_game,filename));
    std::remove(filename);
    return 0;
}
