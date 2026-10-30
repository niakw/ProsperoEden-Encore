// SPDX-License-Identifier: GPL-3.0-or-later
// N3r: execute independently published AArch64 HOS SVC code from a real NSO0
// in the same maintained Dynarmic JIT already used by Encore's NS2 tests.
//
// This host test uses a six-SVC deterministic *test dispatcher*, not Encore's
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
int main(int argc, char** argv) {
    try {
        Require(argc == 2, "usage: ns2_public_nso_jit_test hello.nso");
        auto image = ReadFile(argv[1]);
        Require(image.size() >= NsoHeaderBytes, "truncated on-disk NSO0");
        std::span<const std::uint8_t> header{image.data(), NsoHeaderBytes};
        const auto inspected = PreflightNso(header, image.size());
        Require(inspected.Ready(), "actual NS2 NSO0 preflight rejected cross-built guest");
        const auto flags = NsoWord(header, 0x0c);
        Require((flags & 1U) == 0, "test must use real uncompressed text, never simulate LZ4");
        const std::size_t text_file_offset = NsoWord(header, 0x10);
        const std::size_t text_virtual_offset = NsoWord(header, 0x14);
        const std::size_t text_bytes = NsoWord(header, 0x18);
        const std::size_t stored_text_bytes = NsoWord(header, 0x60);
        Require(text_virtual_offset == 0 && text_bytes >= 64 && text_bytes <= 0x10000 &&
                stored_text_bytes == text_bytes &&
                text_file_offset <= image.size() &&
                text_bytes <= image.size() - text_file_offset,
                "invalid NSO0 code segment");
        constexpr std::uint64_t guest_base = 0x08000000;
        SvcHost env;
        env.code_mem_start_address = guest_base;
        env.code_mem.resize((text_bytes + 3) / 4, 0xD4200000U);
        std::memcpy(env.code_mem.data(), image.data() + text_file_offset, text_bytes);
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
                  << " callbacks: PASS (" << calls.size() << " calls, no panic)\n"
                  << "No production AppLoader/NPDM/HLE or native PS5 execution tested.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "NS2 real NSO0 CPU JIT: FAILED: " << error.what() << '\n';
        return 1;
    }
}
