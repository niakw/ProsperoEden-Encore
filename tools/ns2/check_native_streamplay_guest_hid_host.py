#!/usr/bin/env python3
"""Compile the real NS2 stpl:u IPC owner against a mock kernel/IPC contract.

This is a host source/lifetime proof, NOT an NS2 OS, PS5 link, or GameShare test.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor/encore-active/ns2-runtime/audio"
HEADER = VENDOR / "core/hle/service/nx2_streamplay.h"
content = HEADER.read_text()
assert "GetGuestHidSharedMemory" in content
assert "KSharedMemory::Create(owner_kernel)" in content
assert "KSharedMemory::Register(owner_kernel, memory)" in content
assert "service_context.CreateEvent(" not in content
assert "rb.PushCopyObjects(ctx, guest_hid_memory)" in content
assert "GuestHidMemorySize = 0x9b000" in content

FAKES = {
    "core/core.h": r'''
#pragma once
#include <cstdint>
using u64 = std::uint64_t;
using u32 = std::uint32_t;
using Result = int;
constexpr Result ResultSuccess = 0;
constexpr bool R_FAILED(Result value) { return value != ResultSuccess; }
namespace Kernel { struct KernelCore {}; }
namespace Core {
struct DeviceMemory {};
struct System {
    Kernel::KernelCore kernel_instance{};
    Core::DeviceMemory device_instance{};
    Kernel::KernelCore& Kernel() { return kernel_instance; }
    Core::DeviceMemory& DeviceMemory() { return device_instance; }
};
}
''',
    "core/hle/kernel/svc_results.h": r'''
#pragma once
#include "core/core.h"
namespace Kernel {
inline constexpr Result ResultOutOfResource = -12;
namespace Svc { enum class MemoryPermission { ReadWrite, Read }; }
}
''',
    "core/hle/kernel/k_shared_memory.h": r'''
#pragma once
#include <cassert>
#include <cstddef>
#include "core/hle/kernel/svc_results.h"
namespace Kernel {
struct KSharedMemory {
    static inline int create_count{}, close_count{}, register_count{};
    static inline bool fail_create{}, fail_init{};
    static inline KSharedMemory* registered_object{};
    static KSharedMemory* Create(KernelCore&) {
        if (fail_create) return nullptr;
        ++create_count;
        return new KSharedMemory;
    }
    Result Initialize(KernelCore&, Core::DeviceMemory&, void* owner,
                      Svc::MemoryPermission owner_perm,
                      Svc::MemoryPermission guest_perm, std::size_t size) {
        assert(owner == nullptr);
        assert(owner_perm == Svc::MemoryPermission::ReadWrite);
        assert(guest_perm == Svc::MemoryPermission::Read);
        assert(size == 0x9b000);
        return fail_init ? -41 : ResultSuccess;
    }
    static void Register(KernelCore&, KSharedMemory* instance) {
        assert(instance);
        ++register_count;
        registered_object = instance;
    }
    void Close(KernelCore&) {
        ++close_count;
        delete this;
    }
};
}
''',
    "core/hle/service/ipc_helpers.h": r'''
#pragma once
#include <cassert>
#include "core/core.h"
namespace Service {
struct HLERequestContext {
    Result result{-99};
    int payload_words{}, copy_handles{}, interface_count{}, raw_count{};
    int cmd[10]{};
    u64 raw_size{}, raw_offset{};
    const void* shared{};
    int* CommandBuffer() { return cmd; }
    int GetCommand() { return 300; }
};
}
namespace IPC {
class ResponseBuilder {
public:
    Service::HLERequestContext& context;
    ResponseBuilder(Service::HLERequestContext& c, int words, int = 0, int = 0)
        : context{c} { c.payload_words = words; }
    void Push(Result result) { context.result = result; }
    template<class T> void PushRaw(const T& value) {
        static_assert(sizeof(T) == 16);
        context.raw_size = value.size;
        context.raw_offset = value.offset;
        ++context.raw_count;
    }
    template<class T>
    void PushCopyObjects(Service::HLERequestContext& c, T* instance) {
        assert(&c == &context);
        assert(instance != nullptr);
        ++context.copy_handles;
        context.shared = instance;
    }
    template<class T>
    void PushIpcInterface(Service::HLERequestContext& c, Core::System&) {
        assert(&c == &context);
        ++context.interface_count;
    }
};
}
''',
    "core/hle/service/service.h": r'''
#pragma once
#include <cstddef>
#include "core/hle/service/ipc_helpers.h"
#define LOG_WARNING(...) ((void)0)
namespace Service {
template<class T> class ServiceFramework {
protected:
    Core::System& system;
    Kernel::KernelCore& kernel;
public:
    struct FunctionInfo { int id; void(T::*fn)(HLERequestContext&); const char* label; };
    ServiceFramework(Core::System& s, const char*) : system{s}, kernel{s.Kernel()} {}
    virtual ~ServiceFramework() = default;
    template<std::size_t N> void RegisterHandlers(const FunctionInfo (&arr)[N]) {
        registered = arr; count = N;
    }
    void Dispatch(int command, HLERequestContext& ctx) {
        for (std::size_t i = 0; i < count; ++i)
            if (registered[i].id == command) {
                (static_cast<T*>(this)->*(registered[i].fn))(ctx);
                return;
            }
        assert(false && "missing IPC method");
    }
private:
    const FunctionInfo* registered{};
    std::size_t count{};
};
}
''',
}
TEST = r'''
#include <cassert>
#include <cstdio>
#include "core/hle/service/nx2_streamplay.h"
int main() {
    using Kernel::KSharedMemory;
    Core::System system{};
    {
        Service::INx2StreamPlayService parent{system};
        Service::HLERequestContext command0;
        parent.Dispatch(0, command0);
        assert(command0.result == ResultSuccess && command0.interface_count == 1);
    }
    {
        Service::INx2StreamPlayUserService user{system};
        Service::HLERequestContext first, second;
        user.Dispatch(300, first);
        assert(first.result == ResultSuccess && first.payload_words == 6);
        assert(first.raw_count == 1 && first.raw_size == 0x9b000 &&
               first.raw_offset == 0 && first.copy_handles == 1);
        assert(KSharedMemory::create_count == 1 &&
               KSharedMemory::register_count == 1 && KSharedMemory::close_count == 0);
        user.Dispatch(300, second);
        assert(second.result == ResultSuccess && second.shared == first.shared &&
               second.copy_handles == 1 && KSharedMemory::create_count == 1);
    }
    assert(KSharedMemory::close_count == 1);
    KSharedMemory::fail_create = true;
    {
        Service::INx2StreamPlayUserService user{system};
        Service::HLERequestContext first;
        user.Dispatch(300, first);
        assert(first.result == Kernel::ResultOutOfResource &&
               first.copy_handles == 0 && first.raw_count == 0 &&
               KSharedMemory::register_count == 1);
    }
    assert(KSharedMemory::close_count == 1);
    KSharedMemory::fail_create = false;
    KSharedMemory::fail_init = true;
    {
        Service::INx2StreamPlayUserService user{system};
        Service::HLERequestContext first;
        user.Dispatch(300, first);
        assert(first.result == -41 && first.copy_handles == 0 &&
               first.raw_count == 0 && KSharedMemory::register_count == 1);
    }
    assert(KSharedMemory::create_count == 2 && KSharedMemory::close_count == 2);
    KSharedMemory::fail_init = false;
    {
        Service::INx2StreamPlayUserService user{system};
        Service::HLERequestContext first;
        user.Dispatch(300, first);
        assert(first.result == ResultSuccess && first.copy_handles == 1 &&
               KSharedMemory::register_count == 2);
    }
    assert(KSharedMemory::close_count == 3);
    std::puts("NS2_STREAMPLAY_GUEST_HID_HOST_PASS reused=1 success=1 oom=1 init_fail=1 lifetime=1");
}
'''
compilers = list(dict.fromkeys(filter(None, (
    shutil.which("clang++-18"), shutil.which("g++"), shutil.which("clang++"),
))))
assert compilers, "a C++20 compiler is required"
env = os.environ.copy()
if not env.get("SDKROOT") and Path(
        "/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk").is_dir():
    env["SDKROOT"] = "/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk"
with tempfile.TemporaryDirectory(prefix="encore-guest-hid-") as temp:
    top = Path(temp)
    for relative, data in FAKES.items():
        p = top / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)
    cpp = top / "test.cpp"
    cpp.write_text(TEST)
    for compiler in compilers:
        for opt in ("-O0", "-O2"):
            binary = top / (Path(compiler).name + opt)
            subprocess.run([compiler, "-std=c++20", opt, "-Wall", "-Wextra",
                            "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                            "-I", str(top), "-I", str(VENDOR), str(cpp), "-o", str(binary)],
                           check=True, timeout=45, env=env)
            result = subprocess.run([str(binary)], text=True, capture_output=True,
                                    check=True, timeout=10, env=env)
            assert "NS2_STREAMPLAY_GUEST_HID_HOST_PASS" in result.stdout
            print(f"NS2_STREAMPLAY_GUEST_HID_SOURCE_PASS {Path(compiler).name} {opt}")
