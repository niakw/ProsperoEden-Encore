// SPDX-License-Identifier: MIT
// Integration test: NRMODEL1 stores ROW-MAJOR E4M3FN model matrices.
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_model_file.h"
#include "video_core/renderer_vulkan/nr_rdna2_weight_arena.h"
using namespace Eden::Graphics::NeuralRDNA2;
static void u32(std::vector<std::uint8_t>& b,std::uint32_t x){
    for(unsigned i=0;i<4u;++i)b.push_back(std::uint8_t(x>>(8u*i)));
}
static void u64(std::vector<std::uint8_t>& b,std::uint64_t x){
    for(unsigned i=0;i<8u;++i)b.push_back(std::uint8_t(x>>(8u*i)));
}
static void save(const std::filesystem::path& path,
                 const std::vector<std::uint8_t>& bytes){
    std::ofstream out(path,std::ios::binary|std::ios::trunc);
    assert(out);
    out.write(reinterpret_cast<const char*>(bytes.data()),
              static_cast<std::streamsize>(bytes.size()));
    assert(out);
}
int main(){
    constexpr std::uint32_t rows=16u,cols=32u;
    std::vector<std::uint8_t> linear(rows*cols),tiled(rows*cols);
    for(std::uint32_t r=0u;r<rows;++r)
        for(std::uint32_t c=0u;c<cols;++c)
            linear[r*cols+c]=std::uint8_t((r*13u+c*7u)&255u);
    assert(RowMajorToNeuralTiles(linear,tiled,rows,cols)==NeuralTileResult::Ok);
    std::vector<std::uint8_t> pack{'N','R','M','O','D','E','L','1'};
    u32(pack,1u);u32(pack,0u);
    const std::string name="weights/matrix.bin";
    u32(pack,static_cast<std::uint32_t>(name.size()));
    for(char ch:name)pack.push_back(std::uint8_t(ch));
    u64(pack,256u);u64(pack,rows*cols);
    pack.resize(256u,0u);
    pack.insert(pack.end(),linear.begin(),linear.end());
    const auto path=std::filesystem::temp_directory_path()/
        ("eden_rdna2_modelpack_"+std::to_string(
          reinterpret_cast<std::uintptr_t>(pack.data()))+".bin");
    save(path,pack);
    NeuralModelFile file;
    assert(file.Open(path.string()));
    assert(file.IsOpen());
    assert(file.Entries().size()==1u);
    assert(file.Find(name)&&file.Find(name)->size==rows*cols);
    assert(file.Find("../weights/matrix.bin")==nullptr);
    std::vector<std::uint8_t> data;
    assert(file.LoadRaw(name,data)&&data==linear);
    assert(file.LoadModelMatrix(name,rows,cols,data)&&data==linear);
    NeuralWeightArena arena;
    NeuralWeightRange matrix{};
    assert(arena.AppendModelMatrix(file,name,rows,cols,matrix));
    assert(matrix.offset_bytes==0u&&matrix.length_bytes==rows*cols);
    assert(arena.Bytes().size()==rows*cols);
    assert(std::equal(arena.Bytes().begin(),arena.Bytes().end(),linear.begin()));
    assert(arena.Find(name)!=nullptr);
    assert(!arena.AppendModelMatrix(file,name,rows,cols,matrix));
    assert(matrix.length_bytes==0u);
    NeuralWeightArena raw_arena;
    NeuralWeightRange raw{};
    assert(raw_arena.AppendRaw(file,name,raw));
    assert(raw.offset_bytes==0u&&raw.length_bytes==rows*cols);
    assert(std::equal(raw_arena.Bytes().begin(),raw_arena.Bytes().end(),linear.begin()));
    raw_arena.Clear();
    assert(raw_arena.Bytes().empty()&&raw_arena.Find(name)==nullptr);
    assert(!file.LoadModelMatrix(name,rows,16u,data)&&data.empty());
    assert(!file.LoadRaw("notfound",data)&&data.empty());
    // Mutating the backing file's length invalidates a previously opened index.
    pack.pop_back();
    save(path,pack);
    assert(!file.LoadRaw(name,data)&&data.empty());
    file.Reset();
    assert(!file.IsOpen());
    assert(!file.LoadRaw(name,data));
    std::filesystem::remove(path);
}
