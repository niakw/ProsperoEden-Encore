// SPDX-License-Identifier: GPL-3.0-or-later
#include "settings_store.h"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <string>
#include <unistd.h>
int main(){
    char path[]="/tmp/eden-neural-settings-XXXXXX";
    const int fd=mkstemp(path);assert(fd>=0);close(fd);
    auto prefs=Eden::LoadPreferences(path);
    assert(prefs.neural_model==0 && prefs.neural_strength==100);
    const int filter=prefs.upscaling_filter;
    prefs.neural_model=1;prefs.neural_strength=55;
    assert(Eden::SavePreferences(prefs,path));
    prefs=Eden::LoadPreferences(path);
    assert(prefs.neural_model==1&&prefs.neural_strength==55);
    assert(prefs.upscaling_filter==filter);
    prefs.neural_model=2;assert(!Eden::SavePreferences(prefs,path));
    prefs.neural_model=0;prefs.neural_strength=101;
    assert(!Eden::SavePreferences(prefs,path));
    prefs=Eden::LoadPreferences(path);
    assert(prefs.neural_model==1&&prefs.neural_strength==55);
    constexpr auto title=0x0100000000010000ull;
    auto game=Eden::LoadGameSettings(title,path);
    assert(game.neural_model==-1&&game.neural_strength==-1);
    game.neural_model=0;game.neural_strength=0;
    assert(Eden::SaveGameSettings(title,game,path));
    game=Eden::LoadGameSettings(title,path);
    assert(game.neural_model==0&&game.neural_strength==0);
    game.neural_model=1;game.neural_strength=100;
    assert(Eden::SaveGameSettings(title,game,path));
    game=Eden::LoadGameSettings(title,path);
    assert(game.neural_model==1&&game.neural_strength==100);
    game.neural_model=2;assert(!Eden::SaveGameSettings(title,game,path));
    game.neural_model=-1;game.neural_strength=-1;
    assert(Eden::SaveGameSettings(title,game,path));
    game=Eden::LoadGameSettings(title,path);
    assert(game.neural_model==-1&&game.neural_strength==-1);
    const std::string bad=std::string(path)+".bad";
    {std::ofstream o(bad);o<<R"({"video":{"neural_model":"bogus","neural_strength":105},"games":{"0100000000010000":{"neural_model":"bad","neural_strength":-12}}})";}
    const auto defaults=Eden::LoadPreferences(bad);
    const auto inherited=Eden::LoadGameSettings(title,bad);
    assert(defaults.neural_model==0&&defaults.neural_strength==100);
    assert(inherited.neural_model==-1&&inherited.neural_strength==-1);
    std::remove(bad.c_str());std::remove(path);
}
