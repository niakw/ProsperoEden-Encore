// SPDX-License-Identifier: MIT
// CPU-only, real source-level R09 session gate. The 2-byte payloads in
// synthetic NRMODEL1 files are NOT learned weights and MUST NEVER be
// consumed by a GPU inference test; this checks the index, manifest,
// complete 152/76 model plan, routes and exact geometry without Vulkan.
#include "video_core/renderer_vulkan/nr_rdna2_session_preflight.h"
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Put32(std::vector<std::uint8_t>& bytes,std::uint32_t v){
    for(std::uint32_t i=0;i<4u;++i)
        bytes.push_back(std::uint8_t(v>>(i*8u)));
}
static void Put64(std::vector<std::uint8_t>& bytes,std::uint64_t v){
    for(std::uint32_t i=0;i<8u;++i)
        bytes.push_back(std::uint8_t(v>>(i*8u)));
}
template<std::size_t N>
static void MakeIndexOnlyPack(const std::filesystem::path& path,
    const std::array<std::string_view,N>& manifest,
    std::string_view optional={},bool omit_last=false){
    const std::size_t n=N-(omit_last?1u:0u)+(!optional.empty()?1u:0u);
    std::vector<std::string_view> names(manifest.begin(),
                                        manifest.begin()+N-(omit_last?1u:0u));
    if(!optional.empty())names.emplace_back(optional);
    std::uint64_t cursor=16u;
    for(auto name:names)cursor+=4u+name.size()+16u;
    cursor=(cursor+255u)&~std::uint64_t(255u);
    std::vector<std::uint8_t> index{
        'N','R','M','O','D','E','L','1'};
    Put32(index,static_cast<std::uint32_t>(n));
    Put32(index,0u);
    for(const auto name:names){
        Put32(index,static_cast<std::uint32_t>(name.size()));
        for(const auto c:name)
            index.push_back(static_cast<std::uint8_t>(c));
        Put64(index,cursor);
        Put64(index,2u);
        cursor+=256u;
    }
    std::vector<std::uint8_t> full(static_cast<std::size_t>(cursor));
    assert(index.size()<=full.size());
    std::copy(index.begin(),index.end(),full.begin());
    std::ofstream stream(path,std::ios::binary|std::ios::trunc);
    assert(stream);
    stream.write(reinterpret_cast<const char*>(full.data()),
                 static_cast<std::streamsize>(full.size()));
    assert(stream.good());
    stream.close();
}
static std::string Read(const char* path){
    std::ifstream in(path,std::ios::binary);
    assert(in);
    return {std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>()};
}
template<std::size_t N>
static void Check(const std::array<std::string_view,N>& names,
    std::string_view extension,const std::string& good,
    const std::string& bad,const std::filesystem::path& file){
    R09SessionCPUPlan out{};
    MakeIndexOnlyPack(file,names);
    assert(PreflightR09Session(file.string(),good,1920u,1080u,
                               1920u,1080u,out));
    assert(out.model.IsOpen());
    assert(out.raster_width==1080u&&out.raster_height==1920u);
    assert(out.graph.count==4u);
    assert(out.routes.run_count==2u);
    assert(out.vit_route.count==8u);
    assert(out.down_segments[0]!=out.up_segments[0]);
    assert(!PreflightR09Session(file.string(),bad,1920u,1080u,
                                1920u,1080u,out));
    assert(!out.model.IsOpen());
    assert(!PreflightR09Session(file.string(),good,1280u,720u,
                                1920u,1080u,out));
    assert(!out.model.IsOpen());
    assert(!PreflightR09Session(file.string(),good,1920u,1080u,
                                1280u,720u,out));
    assert(!out.model.IsOpen());
    MakeIndexOnlyPack(file,names,{},true);
    assert(!PreflightR09Session(file.string(),good,1920u,1080u,
                                1920u,1080u,out));
    assert(!out.model.IsOpen());
    MakeIndexOnlyPack(file,names,extension);
    assert(PreflightR09Session(file.string(),good,1920u,1080u,
                               1920u,1080u,out));
    assert(out.model.Find(extension)!=nullptr);
    assert(!PreflightR09Session(file.string(),good.substr(0,110u),
                                1920u,1080u,1920u,1080u,out));
    std::filesystem::remove(file);
}
int main(int argc,char** argv){
    assert(argc==3);
    const auto original=Read(argv[1]);
    const auto compact=Read(argv[2]);
    const auto base=std::filesystem::temp_directory_path()/
        ("eden-r09-cpu-preflight-"+
         std::to_string(std::chrono::steady_clock::now()
                        .time_since_epoch().count())+".nrmodel");
    Check(R09OriginalManifest,R09OriginalTemporalScale,
          original,compact,base);
    Check(R09CompactManifest,R09CompactTemporalScale,
          compact,original,base);
}
