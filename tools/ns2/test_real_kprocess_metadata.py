#!/usr/bin/env python3
"""N47: execute unchanged maintained KProcess::LoadFromMetadata against public
NPDM/NSO-derived attributes with controlled host kernel/resource fakes.
NOT actual process allocation, page-table creation, scheduler or PS5 boot.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/sources/eden/src/core/hle/kernel/k_process.cpp"
START = "Result KProcess::LoadFromMetadata("
STOP = "\nvoid KProcess::LoadModule("

PREFIX = r"""
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

using u8 = std::uint8_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s32 = std::int32_t;
namespace Svc {
enum class CreateProcessFlag : u32 {
    IsApplication = 1U << 0,
    Is64Bit = 1U << 1,
    AddressSpace64Bit = 1U << 2,
    AddressSpace64BitDeprecated = 1U << 3,
    AddressSpace32Bit = 1U << 4,
    AddressSpace32BitWithoutAlias = 1U << 5
};
constexpr CreateProcessFlag operator|(CreateProcessFlag a, CreateProcessFlag b) {
    return static_cast<CreateProcessFlag>(static_cast<u32>(a) | static_cast<u32>(b));
}
inline CreateProcessFlag& operator|=(CreateProcessFlag& a, CreateProcessFlag b) {
    return a = a | b;
}
inline constexpr u32 InvalidHandle = 0xFFFFFFFFU;
struct CreateProcessParameter {
    std::array<u8, 12> name{};
    std::array<u8, 4> version{};
    u64 program_id = 0;
    u64 code_address = 0;
    s32 code_num_pages = 0;
    CreateProcessFlag flags{};
    u32 reslimit = InvalidHandle;
    s32 system_resource_num_pages = 0;
};
}
namespace FileSys {
enum class ProgramAddressSpaceType : u8 {
    Is39Bit, Is36Bit, Is32Bit, Is32BitNoMap
};
struct ProgramMetadata {
    std::array<u8, 16> name{};
    std::vector<u32> kac;
    u64 title = 0;
    u64 system_resource_size = 0;
    unsigned core = 0;
    int pool = 0;
    bool arm64 = true;
    ProgramAddressSpaceType address_type = ProgramAddressSpaceType::Is39Bit;
    int GetPoolPartition() const { return pool; }
    bool Is64BitProgram() const { return arm64; }
    ProgramAddressSpaceType GetAddressSpaceType() const { return address_type; }
    u64 GetTitleID() const { return title; }
    std::size_t GetSystemResourceSize() const { return system_resource_size; }
    const std::array<u8,16>& GetName() const { return name; }
    const std::vector<u32>& GetKernelCapabilities() const { return kac; }
    unsigned GetMainThreadCore() const { return core; }
};
}
struct Result {
    int code = 0;
    bool IsError() const { return code != 0; }
    bool IsSuccess() const { return code == 0; }
};
template<class F> struct HostScopeExit {
    F fn;
    ~HostScopeExit() { fn(); }
};
struct HostScopeMaker {};
template<class F> HostScopeExit<F> operator+(HostScopeMaker, F fn) {
    return {std::move(fn)};
}
#define SCOPE_EXIT auto ns2_scope_exit_guard_ = HostScopeMaker{} + [&]()
#define R_TRY(expression) do { auto ns2_result_ = (expression); \
    if (ns2_result_.IsError()) return ns2_result_; } while (false)
#define R_SUCCEED() return Result{}

namespace Kernel {
using KProcessAddress = u64;
inline constexpr std::size_t PageSize = 0x1000;
inline u64 GetInteger(KProcessAddress p) { return p; }
struct KMemoryManager {
    enum class Pool : int { Application=0, System=1 };
};
struct DummySystem {};
struct FakeMemoryManager {
    unsigned calls = 0;
    std::size_t GetSize(KMemoryManager::Pool pool) {
        ++calls;
        return pool == KMemoryManager::Pool::Application
             ? std::size_t{0x10000000} : std::size_t{0x8000000};
    }
};
struct KernelCore {
    DummySystem sys;
    FakeMemoryManager memory_manager;
    DummySystem& System() { return sys; }
    FakeMemoryManager& MemoryManager() { return memory_manager; }
};
struct KResourceLimit {
    inline static unsigned created = 0;
    inline static unsigned closed = 0;
    void Close(KernelCore&) { ++closed; }
};
inline KResourceLimit* CreateResourceLimitForProcess(DummySystem&,
                                                      std::size_t bytes) {
    if (bytes != 0x10000000 && bytes != 0x8000000)
        throw std::runtime_error("wrong physical memory pool size");
    ++KResourceLimit::created;
    static KResourceLimit limit;
    return &limit;
}
struct KProcess {
    bool m_is_application = false;
    unsigned m_ideal_core_id = 999;
    bool fail_initialize = false;
    bool initialized = false;
    bool interfaces_initialized = false;
    Svc::CreateProcessParameter captured{};
    std::vector<u32> captured_caps;
    KMemoryManager::Pool captured_pool = KMemoryManager::Pool::System;
    KProcessAddress captured_aslr_start = 0;
    Result Initialize(KernelCore&, const Svc::CreateProcessParameter& params,
                      std::span<const u32> caps, KResourceLimit* resource,
                      KMemoryManager::Pool pool, KProcessAddress start) {
        if (!resource) throw std::runtime_error("null kernel resource limit");
        initialized = true;
        captured = params;
        captured_caps.assign(caps.begin(), caps.end());
        captured_pool = pool;
        captured_aslr_start = start;
        return Result{fail_initialize ? 123 : 0};
    }
    void InitializeInterfaces(KernelCore&) { interfaces_initialized = true; }
    Result LoadFromMetadata(KernelCore& kernel, const FileSys::ProgramMetadata& metadata,
                            std::size_t code_size, KProcessAddress aslr_space_start,
                            std::size_t aslr_space_offset);
};
"""

TEST = r"""
} // namespace Kernel
static void Require(bool v, const char* why) {
    if (!v) throw std::runtime_error(why);
}
static std::vector<u8> Bytes(const char* name) {
    std::ifstream f(name, std::ios::binary);
    Require(f.is_open(), "missing source fixture");
    return {std::istreambuf_iterator<char>{f}, std::istreambuf_iterator<char>{}};
}
static u32 Read32(const std::vector<u8>& b, std::size_t p) {
    Require(p <= b.size() && b.size()-p >= 4, "unreadable source integer");
    return static_cast<u32>(b[p]) | static_cast<u32>(b[p+1])<<8 |
           static_cast<u32>(b[p+2])<<16 | static_cast<u32>(b[p+3])<<24;
}
static u64 Read64(const std::vector<u8>& b, std::size_t p) {
    return static_cast<u64>(Read32(b,p)) |
           (static_cast<u64>(Read32(b,p+4))<<32);
}
static FileSys::ProgramMetadata ParseKnownPublicFixture(const std::vector<u8>& npdm) {
    Require(npdm.size()==0x600 && std::memcmp(npdm.data(),"META",4)==0,
            "not known public NPDM");
    Require(npdm[0x0C]==0x07 && npdm[0x0E]==44 && npdm[0x0F]==0,
            "unexpected public AArch64/priority/core");
    Require(Read32(npdm,0x70)==0x80 && Read32(npdm,0x74)==0xC0 &&
            Read32(npdm,0x78)==0x140 && Read32(npdm,0x7C)==0x400 &&
            std::memcmp(npdm.data()+0x80,"ACI0",4)==0,
            "unexpected public ACI/ACID position");
    Require(Read32(npdm,0xB0)==0x80 && Read32(npdm,0xB4)==12,
            "unexpected public kernel capabilities layout");
    FileSys::ProgramMetadata result;
    std::copy_n(npdm.begin()+0x20, result.name.size(), result.name.begin());
    result.title = Read64(npdm,0x90);
    Require(result.title==0x0100000000000420ULL,
            "unexpected public HOS homebrew title");
    const std::array<u8,11> expected{'N','S','2','-','H','O','S','T','-','H','B'};
    Require(std::equal(expected.begin(),expected.end(),result.name.begin()) &&
            std::all_of(result.name.begin()+expected.size(),
                        result.name.end(),[](u8 b){return b==0;}),
            "unexpected public HOS process name");
    result.kac={Read32(npdm,0x100),Read32(npdm,0x104),Read32(npdm,0x108)};
    Require(result.kac == std::vector<u32>{0x000043F7,0x0001100F,0x2018080F},
            "unexpected public HOS KAC");
    result.pool=0;
    result.core=npdm[0x0F];
    result.system_resource_size=0;
    result.arm64=true;
    return result;
}
static std::size_t CodeBytesFromKnownNso(const std::vector<u8>& nso) {
    Require(nso.size()>=0x100 && std::memcmp(nso.data(),"NSO0",4)==0 &&
            Read32(nso,0x0C)==0, "bad public NSO");
    const std::size_t last=Read32(nso,0x34);
    const std::size_t len=Read32(nso,0x38);
    const std::size_t bss=Read32(nso,0x3C);
    Require(last==0x2000 && bss==0x1000 && len>0 && len<0x1000,
            "unexpected public NSO memory layout");
    const auto total=last+len+bss;
    return (total+0xFFF)&~std::size_t{0xFFF};
}
static void VerifyCase(const FileSys::ProgramMetadata& metadata,
                       std::size_t code_bytes,
                       FileSys::ProgramAddressSpaceType address_type,
                       u64 expected_address,
                       Svc::CreateProcessFlag expected_address_flag,
                       bool app) {
    auto m=metadata;
    m.address_type=address_type;
    m.pool=app?0:1;
    Kernel::KResourceLimit::created=0;
    Kernel::KResourceLimit::closed=0;
    Kernel::KProcess process;
    Kernel::KernelCore kernel;
    constexpr u64 start=0x200000;
    constexpr std::size_t offset=0x4000;
    const auto result=process.LoadFromMetadata(kernel,m,code_bytes,start,offset);
    Require(result.IsSuccess() && process.initialized && process.interfaces_initialized,
            "real KProcess metadata path did not initialize");
    Require(process.captured.code_address==expected_address &&
            process.captured.code_num_pages ==
                static_cast<s32>(code_bytes/Kernel::PageSize) &&
            process.captured.system_resource_num_pages==0,
            "real KProcess code address/page fields incorrect");
    const auto expected_flags = expected_address_flag |
             Svc::CreateProcessFlag::Is64Bit |
             (app ? Svc::CreateProcessFlag::IsApplication :
                    static_cast<Svc::CreateProcessFlag>(0));
    Require(process.captured.flags==expected_flags &&
            process.m_is_application==app && process.m_ideal_core_id==0,
            "real KProcess CPU/ASLR/application flags incorrect");
    Require(process.captured.program_id==0x0100000000000420ULL &&
            std::equal(process.captured.name.begin(),process.captured.name.end(),
                       m.name.begin()) &&
            process.captured.reslimit==Svc::InvalidHandle,
            "real KProcess header identity/handle incorrect");
    Require(process.captured_caps==m.kac &&
            process.captured_aslr_start==start &&
            process.captured_pool==(app?Kernel::KMemoryManager::Pool::Application:
                                        Kernel::KMemoryManager::Pool::System),
            "real KProcess did not pass original kernel capabilities/pool");
    Require(kernel.memory_manager.calls==1 &&
            Kernel::KResourceLimit::created==1 &&
            Kernel::KResourceLimit::closed==1,
            "real KProcess resource-limit scope/closure incorrect");
}
int main(int argc, char** argv) {
    try {
        Require(argc==3, "usage: test_real_kprocess_metadata main.npdm main");
        const auto npdm=Bytes(argv[1]);
        const auto nso=Bytes(argv[2]);
        const auto metadata=ParseKnownPublicFixture(npdm);
        const auto code_bytes=CodeBytesFromKnownNso(nso);
        Require(code_bytes==0x4000, "unexpected source NSO image page count");
        constexpr u64 start=0x200000, offset=0x4000;
        using A=FileSys::ProgramAddressSpaceType;
        using F=Svc::CreateProcessFlag;
        VerifyCase(metadata,code_bytes,A::Is39Bit,0x80000000ULL+start+offset,
                   F::AddressSpace64Bit,true);
        VerifyCase(metadata,code_bytes,A::Is36Bit,0x8000000ULL+start+offset,
                   F::AddressSpace64BitDeprecated,true);
        VerifyCase(metadata,code_bytes,A::Is32Bit,0x200000ULL+start+offset,
                   F::AddressSpace32Bit,true);
        VerifyCase(metadata,code_bytes,A::Is32BitNoMap,0x200000ULL+start+offset,
                   F::AddressSpace32BitWithoutAlias,true);
        VerifyCase(metadata,code_bytes,A::Is39Bit,0x80000000ULL+start+offset,
                   F::AddressSpace64Bit,false);

        Kernel::KResourceLimit::created=0;
        Kernel::KResourceLimit::closed=0;
        Kernel::KernelCore kernel;
        Kernel::KProcess denied;
        denied.fail_initialize=true;
        const auto error=denied.LoadFromMetadata(kernel,metadata,code_bytes,
                                                  start,offset);
        Require(error.IsError() && error.code==123 && denied.initialized &&
                !denied.interfaces_initialized && 
                Kernel::KResourceLimit::created==1 &&
                Kernel::KResourceLimit::closed==1,
                "real KProcess metadata failure did not close resource and stop");
        std::cout << "NS2_REAL_KPROCESS_LOADFROMMETADATA_HOST_PASS"
                  << " actual_owner_method=1 public_npdm_and_nso=1"
                  << " all_address_space_flags=1 code_pages=4"
                  << " core_and_kac_forwarding=1 resource_scope_exit=1"
                  << " failing_Initialize_short_circuit=1"
                  << " real_kernel_Initialize_not_executed=1"
                  << " PS5_runtime_not_executed=1\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "NS2_REAL_KPROCESS_LOADFROMMETADATA_HOST_FAIL: "
                  << e.what() << '\n';
        return 1;
    }
}
"""

def unchanged_member(source: str) -> str:
    if source.count(START) != 1 or STOP not in source.split(START,1)[1]:
        raise AssertionError("Maintained KProcess metadata function anchors changed")
    method = START + source.split(START,1)[1].split(STOP,1)[0]
    for anchor in ("CreateResourceLimitForProcess", "SCOPE_EXIT",
                   "CreateProcessParameter", "GetKernelCapabilities",
                   "this->Initialize(", "InitializeInterfaces("):
        if anchor not in method:
            raise AssertionError(f"Maintained KProcess owner changed: {anchor}")
    return method

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--npdm", type=Path, required=True)
    parser.add_argument("--nso", type=Path, required=True)
    args = parser.parse_args()
    if not args.npdm.is_file() or not args.nso.is_file():
        raise FileNotFoundError("Missing paired public ExeFS homebrew")
    src = OWNER.read_text(encoding="utf-8")
    method = unchanged_member(src)
    with tempfile.TemporaryDirectory(prefix="ns2-kprocess-metadata-host-") as d:
        cpp = Path(d) / "kprocess_metadata.cpp"
        cpp.write_text(PREFIX + "\n" + method + "\n" + TEST, encoding="utf-8")
        for cxx in ("clang++","g++"):
            if not shutil.which(cxx):
                raise RuntimeError("Host compiler unavailable: "+cxx)
            exe = Path(d) / cxx.replace("+","p")
            subprocess.run([cxx,"-std=c++20","-O1","-g","-Wall","-Wextra",
                            "-Werror","-Wno-unused-parameter",
                            "-fsanitize=address,undefined",
                            "-fno-sanitize-recover=all",
                            "-fno-omit-frame-pointer",str(cpp),"-o",str(exe)],
                           timeout=120,check=True)
            subprocess.run([str(exe),str(args.npdm.resolve()),str(args.nso.resolve())],
                           timeout=30,check=True)

if __name__ == "__main__":
    main()
