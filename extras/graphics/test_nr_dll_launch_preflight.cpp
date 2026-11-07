// SPDX-License-Identifier: MIT
// Source-only R09 regression: Original user DLL admission is fail closed.
// No proprietary NVIDIA bytes or console execution in this host test.
#include "nr_dll_launch_preflight.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <vector>
#include <string_view>
#include <cstdint>
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
    // An index with all 599 canonical names and correctly sized
    // learned projections is NOT an authentic model. The exact tensor
    // digest gate must reject it before any guest/Vulkan initialization.
    {
        namespace NR=Eden::Graphics::NeuralRDNA2;
        auto& names=NR::R09OriginalManifest;
        std::size_t index_size=16u;
        for(const auto name:names)index_size+=4u+name.size()+16u;
        auto align=[](std::uint64_t v){
            return (v+255u)&~std::uint64_t(255u);
        };
        const auto put32=[](std::vector<unsigned char>& out,std::uint32_t n){
            for(unsigned i=0;i<4;++i)out.push_back(
                static_cast<unsigned char>(n>>(8*i)));
        };
        const auto put64=[](std::vector<unsigned char>& out,std::uint64_t n){
            for(unsigned i=0;i<8;++i)out.push_back(
                static_cast<unsigned char>(n>>(8*i)));
        };
        std::vector<unsigned char> image;
        for(char c:std::string_view("NRMODEL1"))
            image.push_back(static_cast<unsigned char>(c));
        put32(image,static_cast<std::uint32_t>(names.size()));
        put32(image,0u);
        std::uint64_t cursor=align(index_size);
        for(const auto name:names){
            put32(image,static_cast<std::uint32_t>(name.size()));
            for(char c:name)image.push_back(static_cast<unsigned char>(c));
            const bool projection=name.ends_with("input_lift.bin")||
                                  name.ends_with("out_project.bin");
            const std::uint64_t size=projection?1024u:1u;
            put64(image,cursor);
            put64(image,size);
            cursor=align(cursor+size);
        }
        assert(image.size()==index_size);
        image.resize(static_cast<std::size_t>(cursor),0u);
        std::ofstream fakepack(config/"neural/original.nrmodel",
                               std::ios::binary|std::ios::trunc);
        fakepack.write(reinterpret_cast<const char*>(image.data()),
                       static_cast<std::streamsize>(image.size()));
        fakepack.close();
        assert(!Eden::Graphics::R09UsableCachedPack(
                   config/"neural/original.nrmodel",
                   NR::R09ModelVariant::Original));
    }
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
