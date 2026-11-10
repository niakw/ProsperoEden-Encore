// SPDX-License-Identifier: MIT
// Host-only fixture: EXACT body of the pinned native QMD3 SSBO CBUF reader,
// wrapped in stub launch/read owners. NOT the native Vulkan renderer.
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <utility>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
struct NativeCbuf { bool enabled{}; u32 size{}; u64 gpu_address{}; };
struct NativeLaunch { std::array<NativeCbuf, 8> constant_buffers{}; };
using NativeRead = bool(*)(void*, u64, void*, std::size_t);
struct ReadScenario {
    u64 address{};
    std::array<u32,4> words{0x11223344, 0x1234, 266, 0};
    unsigned calls{};
    bool succeed{true};
};
static bool DoRead(void* opaque, u64 addr, void* dst, std::size_t bytes) {
    auto& scenario = *static_cast<ReadScenario*>(opaque);
    ++scenario.calls;
    if (!scenario.succeed || addr != scenario.address || bytes != sizeof(scenario.words)) return false;
    std::memcpy(dst, scenario.words.data(), sizeof(scenario.words));
    return true;
}
struct NativeEnvironmentFixture {
    NativeLaunch launch{};
    NativeRead read{DoRead};
    void* context{};
    // Exact method body from vendor 22b69d6053db41b74edac2633c012f925b84f69e
    // encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h
    [[nodiscard]] std::array<u32, 4> ReadStorageDescriptor(
        u32 bank, u32 offset) {
        if (bank >= launch.constant_buffers.size() || (offset & 3U) ||
            offset > 0x10000U - 4U * sizeof(u32))
            throw std::out_of_range{"invalid native SSBO descriptor alignment/bank"};
        const auto& cbuf = launch.constant_buffers[bank];
        constexpr u64 limit = u64{1} << 49;
        constexpr u32 bytes = 4U * sizeof(u32);
        if (!cbuf.enabled || !cbuf.size || offset > cbuf.size ||
            bytes > cbuf.size - offset ||
            cbuf.gpu_address >= limit ||
            offset > limit - cbuf.gpu_address ||
            bytes > limit - cbuf.gpu_address - offset)
            throw std::out_of_range{"native SSBO descriptor outside mapped CBUF"};
        std::array<u32, 4> descriptor{};
        if (!read(context, cbuf.gpu_address + offset,
                  descriptor.data(), sizeof(descriptor)))
            throw std::out_of_range{"native SSBO descriptor GMMU read failed"};
        return descriptor;
    }
};
int main() {
    int n{};
    const auto check = [&](bool ok) {
        ++n;
        if (!ok) throw std::runtime_error("QMD owner test #" + std::to_string(n));
    };
    ReadScenario state{};
    NativeEnvironmentFixture env{};
    env.context = &state;
    env.launch.constant_buffers[0] = {true,65536,0x100000};
    auto good = [&](u32 bank,u32 offset) {
        state.address = env.launch.constant_buffers[bank].gpu_address + offset;
        unsigned prev = state.calls;
        const auto value = env.ReadStorageDescriptor(bank,offset);
        check(value==state.words);
        check(state.calls==prev+1); // one coherent 16-byte callback, not four.
    };
    auto bad = [&](u32 bank,u32 offset) {
        const auto prev = state.calls;
        try { static_cast<void>(env.ReadStorageDescriptor(bank,offset)); }
        catch (const std::out_of_range&) { check(true); return; }
        check(false);
        check(state.calls == prev); // never reached for a malformed host input.
    };
    good(0,0);
    good(0,16);
    good(0,65520);
    env.launch.constant_buffers[7] = {true,65536,0x400000};
    good(7,65520);
    bad(8,0);
    bad(std::numeric_limits<u32>::max(),0);
    bad(0,2);
    bad(0,65524);
    bad(0,65535);
    bad(0,std::numeric_limits<u32>::max());
    bad(2,0);
    env.launch.constant_buffers[0].size=15;
    bad(0,0);
    env.launch.constant_buffers[0].size=16;
    good(0,0);
    bad(0,4);
    env.launch.constant_buffers[0].size=65536;
    env.launch.constant_buffers[0].enabled=false;
    bad(0,0);
    env.launch.constant_buffers[0].enabled=true;
    env.launch.constant_buffers[0].size=0;
    bad(0,0);
    env.launch.constant_buffers[0].size=65536;
    env.launch.constant_buffers[0].gpu_address=(u64{1}<<49);
    bad(0,0);
    env.launch.constant_buffers[0].gpu_address=(u64{1}<<49)-8;
    bad(0,0);
    env.launch.constant_buffers[0].gpu_address=(u64{1}<<49)-16;
    good(0,0);
    env.launch.constant_buffers[0].gpu_address=(u64{1}<<49)-32;
    good(0,16);
    bad(0,20);
    env.launch.constant_buffers[0].gpu_address=0x100000;
    state.address=0x100000;
    state.succeed=false;
    bad(0,0);
    state.succeed=true;
    state.address=0x110000;
    bad(0,0);
    state.words={0xaabbccdd, 0x1ffff,0,5};
    good(0,0);
    state.words={0xaabbccdd, 0x1ffff,10000000,0};
    good(0,0); // reader captures bytes; separate plan must validate semantics.
    check(state.calls>0);
    std::cout << "PASS: " << n << " pinned QMD3 ReadStorageDescriptor owner checks\n";
}
