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
    // The launcher cycles in best->least quality order, while serialized
    // IDs remain frozen (existing user preferences are never renumbered).
    {
        constexpr auto all=[](int) { return true; };
        int value=kUpscalingQualityOrder[0];
        for (int expected: {5,1,4,2,0,3,6}) {
            value=CycleQualityRanked(value,1,kUpscalingQualityOrder,false,all);
            assert(value==expected);
        }
        value=-1;
        for(int expected: {6,5,1,4,2,0,3,-1}) {
            value=CycleQualityRanked(value,1,kUpscalingQualityOrder,true,all);
            assert(value==expected);
        }
        value=kAntiAliasingQualityOrder[0];
        for(int expected: {3,1,0,7,6,5,4,2}) {
            value=CycleQualityRanked(value,1,kAntiAliasingQualityOrder,false,all);
            assert(value==expected);
        }
        // Vulkan-only modes are skipped on OpenGL; persisted IDs remain
        // untouched, including an imported MSAA setting.
        for(int mode: {3,4,5,6,7}) {
            assert(!AntiAliasingOptionSelectable(mode, 0));
            assert(AntiAliasingOptionSelectable(mode, 1));
        }
        for(int mode: {0,1,2}) assert(AntiAliasingOptionSelectable(mode, 0));
        auto allowed_opengl=[](int option) { return option!=5 && option!=6; };
        value=-1;
        assert(CycleQualityRanked(value,1,kUpscalingQualityOrder,true,allowed_opengl)==1);
        value=-1;
        assert(CycleQualityRanked(value,-1,kUpscalingQualityOrder,true,allowed_opengl)==3);
        auto aa_opengl=[](int option) {
            return AntiAliasingOptionSelectable(option, 0);
        };
        assert(CycleQualityRanked(2,1,kAntiAliasingQualityOrder,false,aa_opengl)==1);
    }
    // A future curated Title ID can safely load new spatial/AA keys
    // from encore-overrides runtime. Existing general profiles remain
    // conservative; OpenGL profiles must NOT claim absent Vulkan shaders.
    {
        nlohmann::json live={
            {"renderer","vulkan"},{"tv_output","1440p"},
            {"game_resolution",1.25},{"upscaling_filter","sgsr_edge"},
            {"anti_aliasing","fxaa_quality"},{"fsr_sharpness",50},
            {"refresh_rate_hz",60},{"console_mode","docked"}
        };
        auto p=Eden::EncoreOverridesRuntime::ParseProfile(live);
        assert(p && p->filter==6 && p->anti_aliasing==3 && p->renderer==1);
        live["upscaling_filter"]="sgsr";
        p=Eden::EncoreOverridesRuntime::ParseProfile(live);
        assert(p && p->filter==5);
        live["upscaling_filter"]="lanczos";
        p=Eden::EncoreOverridesRuntime::ParseProfile(live);
        assert(p && p->filter==4);
        live["renderer"]="opengl";
        p=Eden::EncoreOverridesRuntime::ParseProfile(live);
        assert(!p);
        live["anti_aliasing"]="fxaa";
        p=Eden::EncoreOverridesRuntime::ParseProfile(live);
        assert(p && p->renderer==0 && p->filter==4);
        live["upscaling_filter"]="sgsr_edge";
        p=Eden::EncoreOverridesRuntime::ParseProfile(live);
        assert(!p);
    }
    // R07 new spatial methods: exact renderer dependencies.
    assert(UpscalingFilterSelectable(4,0));  // Lanczos on OpenGL too.
    assert(UpscalingFilterSelectable(4,1));
    assert(UpscalingFilterSelectable(5,1));  // SGSR Vulkan only.
    assert(UpscalingFilterSelectable(6,1));
    assert(!UpscalingFilterSelectable(5,0));
    assert(!UpscalingFilterSelectable(6,0));
    assert(UpscalingSupportsSharpness(1));
    assert(UpscalingSupportsSharpness(5));
    assert(UpscalingSupportsSharpness(6));
    for (int index: {0,2,3,4}) assert(!UpscalingSupportsSharpness(index));
    {
        Eden::Preferences persisted{};
        Eden::GameSettings title{};
        char path[]="/tmp/eden-upscales-XXXXXX";
        int fd=mkstemp(path);
        assert(fd>=0);
        close(fd);
        for(int index=0; index<=6; ++index) {
            persisted.upscaling_filter=index;
            assert(Eden::SavePreferences(persisted,path));
            assert(Eden::LoadPreferences(path).upscaling_filter==index);
            title.upscaling_filter=index;
            assert(Eden::SaveGameSettings(fc27,title,path));
            assert(Eden::LoadGameSettings(fc27,path).upscaling_filter==index);
        }
        title.upscaling_filter=7;
        assert(!Eden::SaveGameSettings(fc27,title,path));
        std::remove(path);
    }
    // FXAA+ is an additional quality shader, not an alias to SMAA.
    // It must roundtrip as a manual Custom selection by game and global.
    {
        Preferences extended{};
        ApplyVideoPreset(extended,1);
        extended.anti_aliasing=3;
        assert(DetectVideoProfile(extended)==kCustomVideoProfile);
        Eden::Preferences stored{};
        stored.anti_aliasing=3;
        char fn[]="/tmp/eden-fxaa-quality-XXXXXX";
        int handle=mkstemp(fn);
        assert(handle>=0);
        close(handle);
        assert(Eden::SavePreferences(stored,fn));
        assert(Eden::LoadPreferences(fn).anti_aliasing==3);
        Eden::GameSettings title{};
        title.anti_aliasing=3;
        assert(Eden::SaveGameSettings(fc27,title,fn));
        assert(Eden::LoadGameSettings(fc27,fn).anti_aliasing==3);
        std::remove(fn);
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
