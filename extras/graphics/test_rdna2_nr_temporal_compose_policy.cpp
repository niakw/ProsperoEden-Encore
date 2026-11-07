// SPDX-License-Identifier: MIT
#include "rdna2_nr_temporal_compose_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_temporal_blend_weight_loader.h"
#include <array>
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
static void Write32(std::vector<std::uint8_t>& v,std::size_t at,
                    std::uint32_t x){
    for(std::size_t i=0;i<4u;++i)v[at+i]=
        static_cast<std::uint8_t>(x>>(8u*i));
}
static void Write64(std::vector<std::uint8_t>& v,std::size_t at,
                    std::uint64_t x){
    for(std::size_t i=0;i<8u;++i)v[at+i]=
        static_cast<std::uint8_t>(x>>(8u*i));
}
static void FakePack(const std::filesystem::path& file,
                     std::uint16_t coefficient,
                     std::size_t payload_size=2u){
    const std::string name=
        "unpacked-postblock/block70.layer0.layer.blend_scale.bin";
    std::vector<std::uint8_t> bytes(256u+payload_size);
    const std::string magic="NRMODEL1";
    for(std::size_t i=0;i<8u;++i)bytes[i]=
        static_cast<std::uint8_t>(magic[i]);
    Write32(bytes,8u,1u);
    Write32(bytes,12u,0u);
    Write32(bytes,16u,static_cast<std::uint32_t>(name.size()));
    std::size_t at=20u;
    for(char c:name)bytes[at++]=static_cast<std::uint8_t>(c);
    Write64(bytes,at,256u);
    Write64(bytes,at+8u,payload_size);
    bytes[256u]=static_cast<std::uint8_t>(coefficient);
    bytes[257u]=static_cast<std::uint8_t>(coefficient>>8u);
    const std::ofstream output(file,std::ios::binary);
    // The stream's lifetime is intentionally bounded by the function.
    // Ensure the pack is closed before NeuralModelFile::Open.
    const_cast<std::ofstream&>(output).write(
        reinterpret_cast<const char*>(bytes.data()),
        static_cast<std::streamsize>(bytes.size()));
    assert(output.good());
}
int main(){
    constexpr NRTemporalComposeShape shape{80u,60u,0.65f,0.75f,1u,0u,0u,0u};
    constexpr std::uint64_t n=80ull*60ull;
    const std::array<std::uint64_t,6> capacities{
        n*16u,n*32u,n*16u,n*16u,n*16u,n*16u};
    assert(CanNRTemporalCompose(shape,capacities));
    auto invalid=shape;
    invalid.intensity=1.1f;
    assert(!CanNRTemporalCompose(invalid,capacities));
    invalid=shape;invalid.blend_scale=-1.0f;
    assert(!CanNRTemporalCompose(invalid,capacities));
    invalid=shape;invalid.history_valid=2u;
    assert(!CanNRTemporalCompose(invalid,capacities));
    invalid=shape;invalid.reserved2=1u;
    assert(!CanNRTemporalCompose(invalid,capacities));
    invalid=shape;invalid.width=0u;
    assert(!CanNRTemporalCompose(invalid,capacities));
    auto short_head=capacities;--short_head[1];
    assert(!CanNRTemporalCompose(shape,short_head));
    auto invalid_float=shape;
    invalid_float.intensity=std::nanf("");
    assert(!CanNRTemporalCompose(invalid_float,capacities));
    NRTemporalComposeShape cold=shape;
    cold.history_valid=0u;
    assert(CanNRTemporalCompose(cold,capacities));

    const auto file=std::filesystem::temp_directory_path()/
        ("eden-r09-blend-"+
         std::to_string(std::chrono::steady_clock::now()
            .time_since_epoch().count())+".nrmodel");
    auto checked=[&](std::uint16_t scalar,std::size_t size,
                     bool should_pass){
        FakePack(file,scalar,size);
        NeuralModelFile pack;
        assert(pack.Open(file.string()));
        float blend=99.0f;
        const bool ok=PrepareNRTemporalBlendScale(pack,70u,blend);
        assert(ok==should_pass);
        if(should_pass)assert(blend==0.75f);
        else assert(blend==0.0f);
        std::filesystem::remove(file);
    };
    checked(0x3a00u,2u,true); // exactly 0.75 FP16
    checked(0x4000u,2u,false); // greater than one
    checked(0x7e00u,2u,false); // NaN
    checked(0x3a00u,4u,false); // not precisely one FP16 scalar
    float missing=1.0f;
    assert(!PrepareNRTemporalBlendScale(NeuralModelFile{},70u,missing));
    assert(missing==0.0f);
}
