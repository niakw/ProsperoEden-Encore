// SPDX-License-Identifier: MIT
// Host-only execution of the exact ReadNs2GpuShader callback from pinned
// vendor 22b69d60, with a tiny stand-in for MemoryManager's void ReadBlock.
// It proves a return-status contract gap under an artificial remap interleave,
// not that a real PS5 remap can race this path.
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
using u64=std::uint64_t;
namespace Shader::Ampere {
[[nodiscard]] constexpr bool NativeGpuRange49(u64 address,u64 bytes) noexcept {
    constexpr u64 limit = u64{1} << 49;
    return bytes && address < limit && bytes <= limit - address;
}
}
namespace Tegra {
struct MemoryManager {
    bool mapped{true};
    bool unmap_after_check{};
    bool throw_read{};
    bool partial_read{};
    int checks{};
    int reads{};
    bool IsFullyMappedRange(u64, std::size_t) {
        ++checks;
        const bool old=mapped;
        if(unmap_after_check)mapped=false;
        return old;
    }
    void ReadBlock(u64, void* dst, std::size_t n) {
        ++reads;
        if(throw_read) throw std::runtime_error("synthetic read fault");
        auto* p=static_cast<std::uint8_t*>(dst);
        if(!mapped){std::memset(dst,0,n);return;}
        std::memset(dst,0x5A,n);
        if(partial_read)std::memset(p+n/2,0,n-n/2);
    }
};
}
namespace VideoCommon {
// Unmodified body from encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp
bool ReadNs2GpuShader(void* context, u64 address, void* dest, std::size_t size) {
    auto* const memory = static_cast<Tegra::MemoryManager*>(context);
    if (!memory || !dest ||
        !Shader::Ampere::NativeGpuRange49(address, size))
        return false;
    try {
        if (!memory->IsFullyMappedRange(address, size))
            return false;
        // Mappings may disappear between admission and the actual read.
        // A failed/partial copy never publishes a native shader image.
        memory->ReadBlock(address, dest, size);
        return true;
    } catch (const std::exception&) {
        return false;
    }
}
}
int main(){
    int n{};
    const auto check=[&](bool valid){++n;if(!valid)throw std::runtime_error("native read test #"+std::to_string(n));};
    Tegra::MemoryManager m{};
    std::array<std::uint8_t,16> bytes{};
    check(VideoCommon::ReadNs2GpuShader(&m,0x100000,bytes.data(),bytes.size()));
    check(bytes[0]==0x5a && bytes[15]==0x5a && m.checks==1 && m.reads==1);
    m.mapped=false;
    check(!VideoCommon::ReadNs2GpuShader(&m,0x100000,bytes.data(),bytes.size()));
    check(m.reads==1);
    m.mapped=true;
    check(!VideoCommon::ReadNs2GpuShader(nullptr,0x100000,bytes.data(),bytes.size()));
    check(!VideoCommon::ReadNs2GpuShader(&m,0x100000,nullptr,16));
    check(!VideoCommon::ReadNs2GpuShader(&m,0x100000,bytes.data(),0));
    check(!VideoCommon::ReadNs2GpuShader(&m,(u64{1}<<49)-8,bytes.data(),16));
    check(!VideoCommon::ReadNs2GpuShader(&m,u64{1}<<49,bytes.data(),16));
    m.unmap_after_check=true;
    const auto result_after_unmap=VideoCommon::ReadNs2GpuShader(&m,0x100000,bytes.data(),bytes.size());
    check(result_after_unmap); // SOURCE CONTRACT GAP: void ReadBlock zero-fills after unmap.
    check(bytes[0]==0 && bytes[15]==0 && m.reads==2);
    m.mapped=true;
    m.unmap_after_check=false;
    m.partial_read=true;
    check(VideoCommon::ReadNs2GpuShader(&m,0x100000,bytes.data(),bytes.size()));
    check(bytes[0]==0x5a && bytes[15]==0);
    m.partial_read=false;
    m.throw_read=true;
    check(!VideoCommon::ReadNs2GpuShader(&m,0x100000,bytes.data(),bytes.size()));
    m.throw_read=false;
    check(VideoCommon::ReadNs2GpuShader(&m,0x100000,bytes.data(),bytes.size()));
    check(bytes[0]==0x5a && bytes[15]==0x5a);
    std::cout<<"PASS: "<<n<<" exact native shader read callback checks; artificial remap can return TRUE with zeros\n";
}
