// SPDX-License-Identifier: MIT
// Host-only, no PS5, DLL, NVIDIA weight bytes or external network dependency.
#include "nr_dll_model_import.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <span>
#include <string_view>
#include <vector>

int main(){
    using namespace Eden::NRDllImport;
    using namespace Eden::NRDllImport::detail;
    {
        std::array<std::uint8_t,1024u> not_a_dll{};
        bool rejected=false;
        try{
            (void)FindOriginalResource({not_a_dll.data(),not_a_dll.size()});
        }catch(const BadModel&){rejected=true;}
        assert(rejected);
    }
    {
        const auto c32=SwinLayout(32u,32u,32u);
        const auto down=SwinLayout(256u,256u,512u);
        const auto up=SwinLayout(256u,512u,256u);
        assert(c32.back().off+c32.back().size==20672u);
        assert(down.back().off+down.back().size==820288u);
        assert(up.back().off+up.back().size==820784u);
        assert(FixedLayout(false).back().off+
               FixedLayout(false).back().size==21696u);
        assert(FixedLayout(true).back().off+
               FixedLayout(true).back().size==21808u);
        assert(SplitLayout(917568u).size()==3u);
        assert(VitLayout(3145856u).size()==4u);
        assert(VitLayout(4194320u).size()==2u);
    }
    {
        std::vector<std::uint8_t> pre(21696u);
        for(std::size_t i=0;i<pre.size();++i)
            pre[i]=static_cast<std::uint8_t>(i%251u);
        Records records;
        records.emplace("block0.layer0.layer",Bytes{pre.data(),pre.size()});
        const auto lift=Tensor(
            "unpacked-preblock/block0.layer0.layer.input_lift.bin",records);
        assert(lift.size()==1024u);
        for(std::size_t i=0;i<lift.size();++i)
            assert(lift[i]==pre[8208u+i]);
        const auto qkv=Tensor(
            "unpacked-preblock/block0.layer0.layer.qkv.bin",records);
        assert(qkv.size()==3072u);
        const auto out=Tensor(
            "unpacked-preblock/block0.layer0.layer.mlp_expand.bin",records);
        assert(out.size()==4096u);
        assert(out[0]==pre[0u]);
        assert(out[32u]==pre[64u]);
        bool refused=false;
        try{
            (void)Tensor("unpacked-preblock/block0.layer0.layer.not-a-weight.bin",
                         records);
        }catch(const BadModel&){refused=true;}
        assert(refused);
        const auto folder=std::filesystem::temp_directory_path()/
                          "encore-r09-single-dll-native-test";
        constexpr std::array<std::string_view,2> names{
            "unpacked-preblock/block0.layer0.layer.input_lift.bin",
            "unpacked-preblock/block0.layer0.layer.mlp_expand.bin"};
        const auto pack=folder/"fixture.nrmodel";
        assert(WritePack(pack,names,records));
        std::ifstream file(pack,std::ios::binary);
        assert(file.good());
        char magic[8]{};
        file.read(magic,8);
        assert(std::string_view(magic,8)=="NRMODEL1");
        std::error_code ec;
        std::filesystem::remove(pack,ec);
        std::filesystem::remove(folder,ec);
    }
    // The pure converter must reject unsupported/absent input, not create
    // a model file from nothing or silently substitute Compact weights.
    constexpr std::array<std::string_view,1> names{
        "inventory/weights/block0.layer0.layer.bin"};
    const auto absent=ImportOriginal(
        "/this-user-dll-file-does-not-exist/nvngx_dlssnr.dll",
        "/this-dir-should-not-be-written/original.nrmodel",names);
    assert(!absent.imported);
}
