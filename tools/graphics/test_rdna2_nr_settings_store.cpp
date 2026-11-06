// SPDX-License-Identifier: GPL-3.0-or-later
// Six direct NR choices; separate spatial scaling; legacy A4K/DLSS migration.
#include "settings_store.h"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <string>
#include <unistd.h>
using namespace Eden;
int main(){
    char path[]="/tmp/eden-nr-six-modes-XXXXXX";
    int fd=mkstemp(path);assert(fd>=0);close(fd);
    auto global=LoadPreferences(path);
    assert(global.neural_mode==NeuralVideo::kOff);
    assert(global.frame_generation==0);
    assert(global.neural_strength==100);
    for(int mode=NeuralVideo::kOff;mode<NeuralVideo::kModeCount;++mode){
        global.neural_mode=mode;
        global.upscaling_filter=0;
        global.frame_generation=0;
        global.neural_strength=65;
        assert(SavePreferences(global,path));
        auto loaded=LoadPreferences(path);
        assert(loaded.neural_mode==mode&&loaded.neural_strength==65);
        assert(loaded.upscaling_filter==0);
    }
    global.neural_mode=NeuralVideo::kA4kDetail;
    global.upscaling_filter=7; // legacy A4K must not be saved as an upscale
    assert(!SavePreferences(global,path));
    global.upscaling_filter=1; // no stacked spatial upscaler
    assert(!SavePreferences(global,path));
    global.upscaling_filter=0;
    global.frame_generation=2;
    assert(!SavePreferences(global,path));
    global.frame_generation=0;
    global.neural_mode=NeuralVideo::kDlssCompact;
    global.anti_aliasing=4; // no forced MSAA with current NR
    assert(!SavePreferences(global,path));
    global.anti_aliasing=1;
    assert(SavePreferences(global,path));

    constexpr auto title=0x0100000000010000ull;
    auto game=LoadGameSettings(title,path);
    assert(game.neural_mode==-1&&game.neural_strength==-1);
    for(int mode=NeuralVideo::kOff;mode<NeuralVideo::kModeCount;++mode){
        game.neural_mode=mode;
        game.neural_strength=40+mode*5;
        assert(SaveGameSettings(title,game,path));
        auto loaded=LoadGameSettings(title,path);
        assert(loaded.neural_mode==mode);
        assert(loaded.neural_strength==40+mode*5);
    }
    game.neural_mode=NeuralVideo::kOff;
    game.neural_strength=80; // prepare per-title intensity while NR is Off
    assert(SaveGameSettings(title,game,path));
    assert(LoadGameSettings(title,path).neural_strength==80);
    game.neural_mode=NeuralVideo::kDlssOriginal;
    game.frame_generation=2;
    assert(!SaveGameSettings(title,game,path));
    game.frame_generation=-1;
    game.neural_mode=-1;game.neural_strength=-1;
    assert(SaveGameSettings(title,game,path));
    assert(LoadGameSettings(title,path).neural_mode==-1);

    const std::string legacy=std::string(path)+".legacy";
    {std::ofstream f(legacy);
     f<<R"({"video":{"renderer":"vulkan","upscaling_filter":"anime4k_soft","frame_generation":"off"}})";}
    auto migrated=LoadPreferences(legacy);
    assert(migrated.neural_mode==NeuralVideo::kA4kSoft);
    assert(migrated.upscaling_filter==0);
    {std::ofstream f(legacy);
     f<<R"({"video":{"renderer":"vulkan","upscaling_filter":"bilinear","neural_rendering":"rdna2","neural_model":"small","frame_generation":"off"}})";}
    migrated=LoadPreferences(legacy);
    assert(migrated.neural_mode==NeuralVideo::kDlssCompact);
    assert(migrated.upscaling_filter==0);
    {std::ofstream f(legacy);
     f<<R"({"video":{"neural_rendering":"nonsense","neural_strength":300}})";}
    migrated=LoadPreferences(legacy);
    assert(migrated.neural_mode==NeuralVideo::kOff);
    assert(migrated.neural_strength==100);
    std::remove(legacy.c_str());std::remove(path);
}
