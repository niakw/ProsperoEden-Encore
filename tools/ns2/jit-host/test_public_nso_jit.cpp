// SPDX-License-Identifier: GPL-3.0-or-later
// N3r: execute independently published AArch64 HOS SVC code from a real NSO0
// in the same maintained Dynarmic JIT already used by Encore's NS2 tests.
//
// The host test stages NSO text/rodata/data and zero-filled BSS, using a
// deterministic six-SVC *test dispatcher*, not Encore's
// production HLE, NPDM process creation, application loader or PS5 hardware.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

#include "dynarmic/tests/A64/testenv.h"
#include "dynarmic/interface/A64/a64.h"
#include "dynarmic/interface/exclusive_monitor.h"
#include "core/loader/ns2_nso_preflight.h"

using Eden::NS2::ExeFS::NsoHeaderBytes;
using Eden::NS2::ExeFS::NsoWord;
using Eden::NS2::ExeFS::PreflightNso;

static void Require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
struct SvcHost final : A64TestEnv {
    Dynarmic::ExclusiveMonitor monitor{6};
    std::uint32_t pending_svc{};
    unsigned callbacks{};
    void CallSVC(std::uint32_t swi) override {
        pending_svc = swi;
        ++callbacks;
    }
    void ExceptionRaised(u64, Dynarmic::A64::Exception) override {
        throw std::runtime_error("guest AArch64 exception in HOS hello");
    }
};
static std::vector<std::uint8_t> ReadFile(const char* path) {
    std::ifstream input(path, std::ios::binary);
    Require(bool(input), "missing independently built NSO0");
    return {std::istreambuf_iterator<char>{input},
            std::istreambuf_iterator<char>{}};
}
// Full uncompressed NSO0 image layout, independent host-only staging.
// Production ExeFS still uses the maintained AppLoader_NSO::LoadModule.
struct StagedNso {
    std::vector<std::uint8_t> bytes;
    std::array<std::size_t, 3> positions{};
    std::array<std::size_t, 3> sizes{};
};
static StagedNso StageNso(std::span<const std::uint8_t> file) {
    Require(file.size() >= NsoHeaderBytes, "truncated NSO0 fixture");
    const auto header = file.first(NsoHeaderBytes);
    const auto result = PreflightNso(header, file.size());
    Require(result.Ready() && result.image_bytes <= 0x100000 && result.image_bytes != 0,
            "NSO0 fixture failed bounded header validation");
    Require((NsoWord(header, 0x0c) & 7U) == 0,
            "compressed NSO0 segments require actual decompression");
    StagedNso staged;
    staged.bytes.resize(static_cast<std::size_t>(result.image_bytes), 0);
    for (std::size_t i = 0; i < 3; ++i) {
        const auto offset = static_cast<std::size_t>(NsoWord(header, 0x10 + 16 * i));
        const auto location = static_cast<std::size_t>(NsoWord(header, 0x14 + 16 * i));
        const auto length = static_cast<std::size_t>(NsoWord(header, 0x18 + 16 * i));
        const auto stored = static_cast<std::size_t>(NsoWord(header, 0x60 + 4 * i));
        Require(stored == length && offset <= file.size() &&
                    length <= file.size() - offset &&
                    location <= staged.bytes.size() &&
                    length <= staged.bytes.size() - location,
                "NSO0 uncompressed segment did not fit its image");
        if (length)
            std::memcpy(staged.bytes.data() + location, file.data() + offset, length);
        staged.positions[i] = location;
        staged.sizes[i] = length;
    }
    const auto& p = staged.positions;
    const auto& s = staged.sizes;
    Require(p[0] == 0 && s[0] >= 64 && s[0] <= 0x10000,
            "invalid NSO0 text segment");
    constexpr char rodata[] = "open-source-loader-test";
    constexpr char data[] = "NS2-DATA-SEGMENT";
    Require(s[1] == sizeof(rodata) &&
                std::memcmp(staged.bytes.data() + p[1], rodata, sizeof(rodata)) == 0,
            "NSO0 rodata virtual mapping mismatch");
    Require(s[2] == sizeof(data) - 1 &&
                std::memcmp(staged.bytes.data() + p[2], data, sizeof(data) - 1) == 0,
            "NSO0 data virtual mapping mismatch");
    const auto zero = [&](std::size_t first, std::size_t last) {
        return std::all_of(staged.bytes.begin() + first, staged.bytes.begin() + last,
                           [](std::uint8_t b) { return b == 0; });
    };
    Require(zero(p[0] + s[0], p[1]) && zero(p[1] + s[1], p[2]) &&
                zero(p[2] + s[2], staged.bytes.size()),
            "NSO0 virtual gaps or BSS not initialized to zero");
    return staged;
}
int main(int argc, char** argv) {
    try {
        Require(argc == 2, "usage: ns2_public_nso_jit_test hello.nso");
        const auto image = ReadFile(argv[1]);
        const auto staged = StageNso(image);
        const std::size_t text_bytes = staged.sizes[0];
        constexpr std::uint64_t guest_base = 0x08000000;
        SvcHost env;
        env.code_mem_start_address = guest_base;
        env.code_mem.resize((staged.bytes.size() + 3) / 4, 0);
        std::memcpy(env.code_mem.data(), staged.bytes.data(), staged.bytes.size());
        Dynarmic::A64::UserConfig cfg{};
        cfg.callbacks = &env;
        cfg.global_monitor = &env.monitor;
        cfg.code_cache_size = 16 * 1024 * 1024;
        Dynarmic::A64::Jit cpu{cfg};
        cpu.SetPC(guest_base);
        cpu.SetSP(0x90000000);
        std::vector<std::uint32_t> calls;
        std::string output;
        unsigned notified_breaks = 0;
        unsigned timer_reads = 0;
        bool exited = false;
        for (unsigned instruction = 0; instruction < 128 && !exited; ++instruction) {
            Require(cpu.GetPC() >= guest_base &&
                        cpu.GetPC() - guest_base < text_bytes &&
                        (cpu.GetPC() - guest_base) % 4 == 0,
                    "guest attempted instruction execution outside NSO0 text");
            const unsigned prior = env.callbacks;
            env.ticks_left = 1;
            cpu.Step(); // Real maintained x86-64 Dynarmic A64 JIT, one guest instruction
            Require(env.callbacks == prior || env.callbacks == prior + 1,
                    "unexpected number of HOS SVC callbacks per step");
            if (env.callbacks == prior) continue;
            const auto svc = env.pending_svc;
            calls.push_back(svc);
            switch (svc) {
            case 0x27: { // svcOutputDebugString (HOS test stub)
                const auto address = cpu.GetRegister(0);
                const auto count = cpu.GetRegister(1);
                Require(count == 15 && address >= guest_base &&
                        address <= guest_base + text_bytes &&
                        count <= text_bytes - (address - guest_base),
                        "AArch64 guest debug string outside loaded NSO0 text");
                output.reserve(count);
                for (std::uint64_t i = 0; i < count; ++i)
                    output.push_back(static_cast<char>(env.MemoryRead8(address + i)));
                Require(output == "hello from HOS\n", "guest ADR or text read incorrect");
                break;
            }
            case 0x0B: // svcSleepThread: check request, do not really sleep
                Require(cpu.GetRegister(0) == 1'000'000,
                        "guest A64 64-bit sleep argument mismatch");
                break;
            case 0x1E: // svcGetSystemTick: deterministic monotonic stub
                cpu.SetRegister(0, 0x12340000 + ++timer_reads * 1'000);
                break;
            case 0x26: // svcBreak notification only (not panic)
                Require((cpu.GetRegister(0) & 0x80000000ULL) != 0 &&
                        (cpu.GetRegister(0) & 0xffffULL) == 2,
                        "guest attempted panic: system tick did not advance");
                ++notified_breaks;
                break;
            case 0x07: // svcExitProcess
                exited = true;
                break;
            default:
                throw std::runtime_error("unexpected HOS service call in real homebrew");
            }
        }
        const std::vector<std::uint32_t> expected{0x27, 0x0B, 0x1E, 0x26, 0x1E, 0x07};
        Require(exited && calls == expected && timer_reads == 2 && notified_breaks == 1,
                "real guest did not complete the expected HOS execution flow");
        std::cout << "NS2 A64 real NSO0 text -> maintained Dynarmic JIT -> HOS SVC"
                  << " callbacks: PASS (" << calls.size() << " calls, three NSO segments + BSS, no panic)\n"
                  << "No production AppLoader/NPDM/HLE or native PS5 execution tested.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "NS2 real NSO0 CPU JIT: FAILED: " << error.what() << '\n';
        return 1;
    }
}
