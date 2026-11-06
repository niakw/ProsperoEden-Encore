// SPDX-License-Identifier: GPL-3.0-or-later
// Host regression: helper must affect only the Encore directory, never other apps,
// and must refuse replacing a legacy asset folder containing user-owned keys.
#include "updater.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>
#include <unistd.h>
namespace fs=std::filesystem;
int main() {
    using self_update::approved_folder_path;
    assert(approved_folder_path("/data/homebrew/PPSA99008", "PPSA99008"));
    for(const auto &path: {"/data/homebrew/PPSA99001","/data/homebrew/PPSA99008/../PPSA00001",
                            "/data/homebrew/PPSA99008/", "/mnt/usb0/PPSA99008",
                            "/data/system/PPSA99008","/data/homebrew/PPSA99008/eboot.bin"})
        assert(!approved_folder_path(path,"PPSA99008"));
    assert(!approved_folder_path("/data/homebrew/PPSA99008","PPSA99009"));
    fs::path base=fs::temp_directory_path()/("encore-target-check-"+std::to_string(getpid()));
    fs::remove_all(base);
    fs::create_directories(base/"target/assets/keys");
    fs::create_directories(base/"stage/assets");
    std::ofstream(base/"target/eboot.bin")<<"old";
    std::ofstream(base/"target/assets/keys/prod.keys")<<"secret";
    std::ofstream(base/"target/keep.ini")<<"preferences";
    std::ofstream(base/"stage/eboot.bin")<<"new";
    std::ofstream(base/"stage/assets/icon0.tga")<<"art";
    assert(!self_update::swap_entries((base/"target").string(),
                                     (base/"stage").string(),
                                     (base/"backup").string()));
    assert(!fs::exists(base/"backup"));
    assert(fs::exists(base/"target/assets/keys/prod.keys"));
    assert(fs::exists(base/"target/eboot.bin"));
    assert(fs::exists(base/"stage/eboot.bin"));
    fs::remove_all(base/"target/assets/keys");
    // A previously installed custom asset not present in the new release
    // must NOT be deleted by swapping entire top-level directories.
    std::ofstream(base/"target/assets/extra-theme.tga")<<"custom";
    assert(!self_update::swap_entries((base/"target").string(),
                                     (base/"stage").string(),
                                     (base/"backup").string()));
    assert(fs::exists(base/"target/assets/extra-theme.tga"));
    assert(fs::exists(base/"stage/assets/icon0.tga"));
    fs::remove(base/"target/assets/extra-theme.tga");
    assert(self_update::swap_entries((base/"target").string(),
                                     (base/"stage").string(),
                                     (base/"backup").string()));
    assert(fs::exists(base/"target/keep.ini"));
    assert(fs::exists(base/"target/assets/icon0.tga"));
    assert(fs::exists(base/"backup/eboot.bin"));
    std::ifstream old(base/"backup/eboot.bin"),updated(base/"target/eboot.bin");
    std::string a,b; old>>a;updated>>b;
    assert(a=="old" && b=="new");
    fs::remove_all(base);
}
