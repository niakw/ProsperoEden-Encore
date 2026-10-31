#!/usr/bin/env python3
"""Execute unmodified maintained KCapabilities core/SVC decoding on public NPDM.

Exercises real InitializeForUser, SetCapability, SetCapabilities, core priority
and syscall-mask member function bodies. Kernel memory mapping and unrelated
capability families are unreachable host stubs. Does not create KProcess.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor/sources/eden/src"
KCAP = VENDOR / "core/hle/kernel/k_capabilities.cpp"


def exact(source: str, first: str, last: str) -> str:
    if source.count(first) != 1:
        raise AssertionError(f"KCapabilities anchor changed: {first}")
    tail = source.split(first, 1)[1]
    if last not in tail:
        raise AssertionError(f"KCapabilities next owner missing: {last}")
    return first + tail.split(last, 1)[0]


PREFIX = r"""
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <span>
#include <stdexcept>
#include <vector>
#include "common/assert.h"
#include "core/hardware_properties.h"
#include "core/hle/kernel/k_capabilities.h"
#include "core/hle/kernel/svc_results.h"
#include "core/loader/ns2_main_thread_admission.h"
#include "core/loader/ns2_public_homebrew_svc.h"
#undef ASSERT
#define ASSERT(expr) do { if (!(expr)) std::abort(); } while (false)

namespace Kernel {
// Unreachable mapping/other capability families have no guest VFS or memory
// side effects; actual tested dispatch, core and SVC bodies are untouched.
Result KCapabilities::MapRange_(u32, u32, KProcessPageTable*) {
    return ResultInvalidArgument;
}
Result KCapabilities::MapIoPage_(u32, KProcessPageTable*) {
    return ResultInvalidArgument;
}
Result KCapabilities::MapRegion_(u32, KProcessPageTable*) {
    return ResultInvalidArgument;
}
Result KCapabilities::SetInterruptPairCapability(u32) {
    return ResultInvalidArgument;
}
Result KCapabilities::SetProgramTypeCapability(u32) {
    return ResultInvalidArgument;
}
Result KCapabilities::SetKernelVersionCapability(u32) {
    return ResultInvalidArgument;
}
Result KCapabilities::SetHandleTableCapability(u32) {
    return ResultInvalidArgument;
}
Result KCapabilities::SetDebugFlagsCapability(u32) {
    return ResultInvalidArgument;
}
"""
TEST = r"""
} // namespace Kernel

static void Require(bool ok, const char* message) {
    if (!ok) throw std::runtime_error(message);
}
static std::vector<std::uint8_t> Read(const char* name) {
    std::ifstream input(name, std::ios::binary);
    Require(bool(input), "NPDM source unavailable");
    return {std::istreambuf_iterator<char>{input},
            std::istreambuf_iterator<char>{}};
}
static std::uint32_t Le32(const std::vector<std::uint8_t>& blob, size_t pos) {
    Require(pos <= blob.size() && blob.size() - pos >= 4,
            "NPDM capability exceeds source bounds");
    return std::uint32_t(blob[pos]) |
           (std::uint32_t(blob[pos + 1]) << 8) |
           (std::uint32_t(blob[pos + 2]) << 16) |
           (std::uint32_t(blob[pos + 3]) << 24);
}
int main(int argc, char** argv) {
    try {
        Require(argc == 2, "usage: kcap_fixture main.npdm");
        const auto npdm = Read(argv[1]);
        Require(npdm.size() == 0x600 &&
                npdm[0] == 'M' && npdm[1] == 'E' &&
                npdm[2] == 'T' && npdm[3] == 'A',
                "unexpected public research NPDM");
        const auto aci_start = Le32(npdm, 0x70);
        const auto aci_size = Le32(npdm, 0x74);
        Require(aci_start <= npdm.size() && aci_size <= npdm.size() - aci_start &&
                aci_size >= 0x80, "ACI bounds invalid");
        const auto kac_off = Le32(npdm, aci_start + 0x30);
        const auto kac_len = Le32(npdm, aci_start + 0x34);
        Require(kac_len == 12 && kac_off == 0x80 &&
                kac_off <= aci_size && kac_len <= aci_size - kac_off,
                "public fixture KAC location invalid");
        const std::array<u32, 3> user_caps{
            Le32(npdm, aci_start + kac_off),
            Le32(npdm, aci_start + kac_off + 4),
            Le32(npdm, aci_start + kac_off + 8),
        };
        Require(user_caps == std::array<u32, 3>{0x000043F7U, 0x0001100FU, 0x2018080FU},
                "unexpected raw KAC words");
        Kernel::KCapabilities real{};
        Require(real.InitializeForUser(user_caps, nullptr).IsSuccess(),
                "REAL KCapabilities InitializeForUser rejected public fixture");
        Require(real.GetCoreMask() == 1 && real.GetPhysicalCoreMask() == 1,
                "real KCapabilities core mapping incorrect");
        constexpr u64 expected_prio = (~u64{0}) & ~((u64{1} << 16) - 1);
        Require(real.GetPriorityMask() == expected_prio,
                "real KCapabilities priority authorization incorrect");
        Require(Eden::NS2::ExeFS::MainThreadPermitted(
                    real.GetCoreMask(), real.GetPriorityMask(), 0, 44),
                "KCapabilities disallowed expected NPDM thread core/priority");
        const auto required = Eden::NS2::ExeFS::MissingPublicHelloSvcs(
            [&](std::uint32_t svc) { return real.IsPermittedSvc(svc); });
        Require(required == 0, "real KCapabilities lacks public HOS SVC");
        unsigned permission_count = 0;
        for (unsigned id = 0; id < 128; ++id) {
            bool expected = false;
            for (const auto svc : Eden::NS2::ExeFS::PublicHelloSvcIds)
                expected |= (svc == id);
            Require(real.IsPermittedSvc(id) == expected,
                    "kernel unexpectedly granted a non-homebrew SVC");
            permission_count += real.IsPermittedSvc(id);
        }
        Require(permission_count == 5 && !real.IsPermittedSvc(128),
                "unexpected additional SVC permissions");

        // Invalid KAC inputs must be rejected by ACTUAL kernel methods.
        auto duplicate = std::array<u32, 4>{user_caps[0], user_caps[0],
                                             user_caps[1], user_caps[2]};
        Kernel::KCapabilities twice{};
        Require(twice.InitializeForUser(duplicate, nullptr).IsError(),
                "duplicate core-capability incorrectly accepted");
        auto duplicate_svc = std::array<u32, 4>{user_caps[0], user_caps[1],
                                                 user_caps[1], user_caps[2]};
        Kernel::KCapabilities repeated{};
        Require(repeated.InitializeForUser(duplicate_svc, nullptr).IsError(),
                "duplicate SVC group incorrectly accepted");
        auto kernel_priority = user_caps;
        kernel_priority[0] &= ~(0x3FU << 10); // grant priorities 0..63
        Kernel::KCapabilities kernel_prio{};
        Require(kernel_prio.InitializeForUser(kernel_priority, nullptr).IsError(),
                "unprivileged guest gained kernel thread priorities");
        auto inverted_cores = user_caps;
        inverted_cores[0] |= 2U << 16; // min core 2, max core 0
        Kernel::KCapabilities invalid_core{};
        Require(invalid_core.InitializeForUser(inverted_cores, nullptr).IsError(),
                "inverted permitted CPU cores incorrectly accepted");
        auto missing_debug = user_caps;
        missing_debug[2] &= ~(1U << (5 + (0x27 - 24)));
        Kernel::KCapabilities removed{};
        Require(removed.InitializeForUser(missing_debug, nullptr).IsSuccess() &&
                !removed.IsPermittedSvc(0x27) &&
                Eden::NS2::ExeFS::MissingPublicHelloSvcs(
                    [&](std::uint32_t id) { return removed.IsPermittedSvc(id); }) == 0x10,
                "SVC OutputDebugString removal was not detected");
        const std::array<u32, 0> no_caps{};
        Kernel::KCapabilities none{};
        Require(none.InitializeForUser(no_caps, nullptr).IsSuccess() &&
                !Eden::NS2::ExeFS::MainThreadPermitted(
                    none.GetCoreMask(), none.GetPriorityMask(), 0, 44),
                "zero-capability NPDM incorrectly admitted a main thread");
        std::cout << "NS2_REAL_KERNEL_KCAPABILITIES_PASS"
                  << " core_mask=0x1 priority_range=16..63"
                  << " exactly_five_svc=1"
                  << " duplicate_core_rejected=1 duplicate_svc_rejected=1"
                  << " kernel_priority_rejected=1 invalid_core_rejected=1"
                  << " missing_svc_detected=1 empty_thread_mask_denied=1"
                  << " full_KProcess_not_executed=1\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "NS2_REAL_KERNEL_KCAPABILITIES_FAIL: " << e.what() << '\n';
        return 1;
    }
}
"""


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--npdm", required=True, type=Path)
    args = cli.parse_args()
    text = KCAP.read_text()
    pieces = [
        exact(text, "Result KCapabilities::InitializeForUser(",
              "\nResult KCapabilities::SetCorePriorityCapability("),
        exact(text, "Result KCapabilities::SetCorePriorityCapability(",
              "\nResult KCapabilities::SetSyscallMaskCapability("),
        exact(text, "Result KCapabilities::SetSyscallMaskCapability(",
              "\nResult KCapabilities::MapRange_("),
        exact(text, "Result KCapabilities::SetCapability(",
              "\nResult KCapabilities::SetCapabilities("),
        exact(text, "Result KCapabilities::SetCapabilities(",
              "\nResult KCapabilities::CheckCapabilities("),
    ]
    harness = PREFIX + "\n".join(pieces) + TEST
    with tempfile.TemporaryDirectory(prefix="ns2-kcap-real-") as work:
        src = Path(work) / "kernel_caps.cpp"
        src.write_text(harness, encoding="utf-8")
        for compiler, optimize in (("clang++", "-O1"), ("g++", "-O2")):
            if not shutil.which(compiler):
                raise RuntimeError("Missing host compiler " + compiler)
            exe = Path(work) / (compiler.replace("+", "p") + "-caps")
            cmd = [compiler, "-std=c++20", optimize, "-g",
                   "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                   "-fno-omit-frame-pointer", "-Wall", "-Wextra", "-Werror",
                   "-I", str(VENDOR), "-I", str(ROOT / "headless/ns2/overrides"),
                   str(src), "-o", str(exe)]
            built = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if built.returncode:
                raise RuntimeError(f"{compiler} real kernel compile:\n"
                                   f"{built.stderr[-7000:]}")
            tested = subprocess.run([str(exe), str(args.npdm)],
                                    capture_output=True, text=True, timeout=30)
            if tested.returncode:
                raise RuntimeError(f"{compiler} real kernel checks:\n"
                                   f"{tested.stdout}\n{tested.stderr[-7000:]}")
            print(tested.stdout.strip(), compiler, optimize, flush=True)


if __name__ == "__main__":
    main()
