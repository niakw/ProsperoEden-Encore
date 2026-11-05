// SPDX-License-Identifier: GPL-3.0-or-later
#include "../../headless/lossless_user_file.h"
#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <unistd.h>
namespace fs = std::filesystem;
int main() {
    const auto dir=fs::temp_directory_path()/("eden-lossless-"+std::to_string(getpid()));
    fs::remove_all(dir);
    fs::create_directories(dir/"lossless");
    assert(!Eden::Graphics::LosslessUserFileLooksValid(dir));
    const auto file=dir/"lossless"/"Lossless.dll";
    { std::ofstream f(file,std::ios::binary); f << std::string(200,'Q'); }
    assert(!Eden::Graphics::LosslessUserFileLooksValid(dir));
    { std::ofstream f(file,std::ios::binary); f << "MZ" << std::string(198,'Q'); }
    assert(Eden::Graphics::LosslessUserFileLooksValid(dir));
    fs::rename(file,dir/"original");
    fs::create_symlink(dir/"original",file);
    assert(!Eden::Graphics::LosslessUserFileLooksValid(dir));
    fs::remove(file);
    fs::remove_all(dir);
    return 0;
}
