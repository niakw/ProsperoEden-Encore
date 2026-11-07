// SPDX-License-Identifier: MIT
// Host regression: the user DLL is checked at menu time (no PE execution).
#include "nr_dll_user_file.h"
#include <array>
#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>

namespace fs=std::filesystem;
using Eden::Graphics::DlssNrUserFileLooksValid;

static void WriteFake(const fs::path& file,bool valid,std::size_t length=1024u) {
    std::ofstream out(file,std::ios::binary|std::ios::trunc);
    assert(out);
    out.write(valid?"MZ":"NO",2);
    std::array<char,1022> zeros{};
    if(length>2u)
        out.write(zeros.data(),static_cast<std::streamsize>(length-2u));
    out.close();
    assert(out);
}
int main() {
    const auto root=fs::temp_directory_path()/"eden-encore-r09-user-dll-alert-host";
    std::error_code ec;
    fs::remove_all(root,ec);
    const auto user=root/"user", config=root/"config";
    fs::create_directories(user/"dlssnr",ec);
    assert(!ec);
    fs::create_directories(config/"neural",ec);
    assert(!ec);
    const auto first=user/"dlssnr/nvngx_dlssnr.dll";
    const auto old=config/"neural/nvngx_dlssnr.dll";
    assert(!DlssNrUserFileLooksValid(user,config));
    WriteFake(first,true,100u);
    assert(!DlssNrUserFileLooksValid(user,config));
    WriteFake(first,false);
    assert(!DlssNrUserFileLooksValid(user,config));
    WriteFake(first,true);
    assert(DlssNrUserFileLooksValid(user,config));
    fs::remove(first,ec);
    assert(!DlssNrUserFileLooksValid(user,config));
    WriteFake(old,true);
    assert(DlssNrUserFileLooksValid(user,config));
    fs::remove(old,ec);
    assert(!DlssNrUserFileLooksValid(user,config));
    WriteFake(old,true);
    fs::create_symlink(old,first,ec);
    assert(!ec);
    // Do not follow a user-controlled symlink into a private model source.
    assert(DlssNrUserFileLooksValid(user,config)); // valid old path remains
    fs::remove(old,ec);
    assert(!DlssNrUserFileLooksValid(user,config));
    fs::remove_all(root,ec);
    assert(!ec);
}
