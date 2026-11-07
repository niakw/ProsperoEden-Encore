// SPDX-License-Identifier: MIT
// Source-only R09 regression: Original user DLL admission is fail closed.
// No proprietary NVIDIA bytes or console execution in this host test.
#include "nr_dll_launch_preflight.h"
#include <cassert>
#include <filesystem>
#include <fstream>
namespace fs=std::filesystem;
int main(){
    using Eden::Graphics::PrepareR09UserModel;
    const auto root=fs::temp_directory_path()/
        "encore-r09-dll-launch-admission-regression";
    const auto user=root/"user",config=root/"config";
    std::error_code ec;
    fs::remove_all(root,ec);
    fs::create_directories(user/"dlssnr",ec);
    assert(!ec);
    fs::create_directories(config/"neural",ec);
    assert(!ec);
    constexpr int off=Eden::NeuralVideo::kOff;
    constexpr int a4k=Eden::NeuralVideo::kA4kDetail;
    constexpr int original=Eden::NeuralVideo::kDlssOriginal;
    constexpr int compact=Eden::NeuralVideo::kDlssCompact;
    assert(PrepareR09UserModel(off,user,config).ready);
    assert(PrepareR09UserModel(a4k,user,config).ready);
    assert(!PrepareR09UserModel(original,user,config).ready);
    assert(!PrepareR09UserModel(compact,user,config).ready);
    // A corrupted private .nrmodel is NOT a substitute for an authentic DLL.
    {
        std::ofstream bad(config/"neural/original.nrmodel",std::ios::binary);
        bad << "NRMODEL1";
    }
    assert(!PrepareR09UserModel(original,user,config).ready);
    // A plausible MZ header passes the menu-level metadata sniff but
    // cannot pass the native PE/resource cryptographic importer.
    const auto dll=user/"dlssnr/nvngx_dlssnr.dll";
    {
        std::ofstream fake(dll,std::ios::binary);
        fake << "MZ";
        const std::string zeros(2048,char(0));
        fake.write(zeros.data(),static_cast<std::streamsize>(zeros.size()));
    }
    const auto rejected=PrepareR09UserModel(original,user,config);
    assert(!rejected.ready&&!rejected.imported&&rejected.reason);
    // No false claim that Original bytes can satisfy Compact.
    const auto compact_result=PrepareR09UserModel(compact,user,config);
    assert(!compact_result.ready&&!compact_result.imported);
    fs::remove_all(root,ec);
    assert(!ec);
}
