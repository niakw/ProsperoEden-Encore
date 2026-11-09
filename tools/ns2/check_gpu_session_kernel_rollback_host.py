#!/usr/bin/env python3
"""H06: execute REAL CreateWorkerKernelSession owner under host OOM injection.

Extracts the maintained C++ method unmodified (including its actual
SCOPE_EXIT guard) and compiles/runs it against minimal kernel endpoint
accounting, using the upstream scope_exit.h macro. This does not claim
complete GPU TIPC ABI or console execution.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
vendor = ROOT / "vendor"
owner_path = vendor / "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp"
owner = owner_path.read_text()
session = (vendor / "sources/eden/src/core/hle/kernel/k_session.cpp").read_text()
server = (vendor / "sources/eden/src/core/hle/service/server_manager.cpp").read_text()
parent = (vendor / "sources/eden/src/core/hle/kernel/k_client_port.cpp").read_text()
scope = (vendor / "sources/eden/src/common/scope_exit.h").read_text()
assert 'void KSession::Initialize(' in session and 'this->Open(kernel);' in session
assert 'm_server.Initialize(this);' in session and 'm_client.Initialize(this);' in session
assert 'auto* session = new Session(' in server
assert 'this->RegisterSession(server_session, std::move(manager));' in server
assert 'session->GetClientSession().Close(kernel);' in parent
assert 'session->GetServerSession().Close(kernel);' in parent
assert '#define SCOPE_EXIT' in scope
assert '#include "common/scope_exit.h"' in owner

begin = 'static Result CreateWorkerKernelSession('
end = '\nvoid IGpuSession::RequestWorker('
assert owner.count(begin) == owner.count(end) == 1
method = owner.split(begin, 1)[1].split(end, 1)[0]
method = begin + method
assert method.count('SCOPE_EXIT {') == 1
assert method.index('SCOPE_EXIT {') < method.index('server.RegisterSession(')
assert method.count('session->GetClientSession().Close(kernel);') == 1
assert method.count('session->GetServerSession().Close(kernel);') == 1
assert method.index('transferred_to_server = true') > method.index('server.RegisterSession(')
assert method.index('transferred_to_server = true') < method.index('*out_client =')
# Only the real SDK owner function is under test; no copied rewrite of it.
harness = r"""
#include <cassert>
#include <cstdint>
#include <memory>
#include <new>
#include <utility>
#include "common/scope_exit.h"

struct Result {
    int raw{};
    bool IsSuccess() const { return raw == 0; }
};
inline constexpr Result ResultSuccess{0};
#define R_UNLESS(c, r) do { if (!(c)) return (r); } while (0)
#define R_TRY(expr) do { const auto result_ = (expr); if (!result_.IsSuccess()) return result_; } while (0)
#define R_SUCCEED() return ResultSuccess

namespace Kernel {
    enum class LimitableResource { SessionCountMax };
    inline constexpr Result ResultLimitReached{1};
    inline constexpr Result ResultOutOfResource{2};
    struct KProcess {};
    struct KSession;
    struct KernelCore {
        int quota{}, closed_client{}, closed_server{}, registrations{};
        bool fail_manager{}, fail_create{}, fail_register_alloc{}, fail_register_result{};
        bool accepted_server{};
        KSession* latest{};
    };
    inline KProcess* GetCurrentProcessPointer(KernelCore&) {
        static KProcess p;
        return &p;
    }
    struct KScopedResourceReservation {
        KernelCore& kernel;
        bool committed{};
        KScopedResourceReservation(KernelCore& k, KProcess*, LimitableResource)
           : kernel{k} { ++kernel.quota; }
        bool Succeeded() const { return true; }
        void Commit() { committed = true; }
        ~KScopedResourceReservation() { if (!committed) --kernel.quota; }
    };
    struct KClientSession {
        KSession* parent{};
        void Close(KernelCore&);
    };
    struct KServerSession {
        KSession* parent{};
        void Close(KernelCore&);
    };
    struct KSession {
        KernelCore& kernel;
        KClientSession client{this};
        KServerSession server{this};
        bool client_open{}, server_open{}, initialized{};
        explicit KSession(KernelCore& k): kernel{k} {}
        static KSession* Create(KernelCore& kernel) {
            if (kernel.fail_create) return nullptr;
            return kernel.latest = new KSession(kernel);
        }
        void Initialize(KernelCore&, void*, int) {
            initialized = client_open = server_open = true;
        }
        static void Register(KernelCore& k, KSession* s) {
            assert(s->initialized);
            ++k.registrations;
        }
        KClientSession& GetClientSession() { return client; }
        KServerSession& GetServerSession() { return server; }
    };
    inline void KClientSession::Close(KernelCore& k) {
        assert(parent->client_open);
        parent->client_open = false;
        ++k.closed_client;
        if (!parent->server_open) --k.quota;
    }
    inline void KServerSession::Close(KernelCore& k) {
        assert(parent->server_open);
        parent->server_open = false;
        ++k.closed_server;
        if (!parent->client_open) --k.quota;
    }
}

namespace Service {
    class ServerManager {
        Kernel::KernelCore& kernel;
    public:
        explicit ServerManager(Kernel::KernelCore& k): kernel{k} {}
        Result RegisterSession(Kernel::KServerSession* server, std::shared_ptr<class SessionRequestManager>) {
            assert(server->parent->server_open);
            if (kernel.fail_register_alloc) throw std::bad_alloc{};
            if (kernel.fail_register_result) return Result{3};
            kernel.accepted_server = true;
            return ResultSuccess;
        }
    };
    class SessionRequestManager {
    public:
        SessionRequestManager(Kernel::KernelCore& k, ServerManager&) {
            if (k.fail_manager) throw std::bad_alloc{};
        }
        void SetSessionHandler(std::shared_ptr<class AM_IGpuWorker>) {}
    };
    class SessionContext {
        ServerManager& server;
    public:
        explicit SessionContext(ServerManager& s): server{s} {}
        ServerManager& GetServerManager() { return server; }
    };
    class HLERequestContext {
        SessionContext context;
    public:
        explicit HLERequestContext(ServerManager& s): context{s} {}
        SessionContext* GetManager() { return &context; }
    };
}
namespace Core {
    class System {
        Kernel::KernelCore& kernel;
    public:
        explicit System(Kernel::KernelCore& k): kernel{k} {}
        Kernel::KernelCore& Kernel() { return kernel; }
    };
}
namespace Service::AM {
    using IGpuWorker = Service::AM_IGpuWorker;
__OWNER__
}
static Result call(Kernel::KernelCore& k, Kernel::KClientSession** client) {
    Core::System system{k};
    Service::ServerManager server{k};
    Service::HLERequestContext ctx{server};
    auto handler = std::make_shared<Service::AM_IGpuWorker>();
    return Service::AM::CreateWorkerKernelSession(system, ctx, handler, client);
}
static void reset(Kernel::KernelCore& k) {
    delete k.latest;
    k.latest = nullptr;
}
int main() {
    // Fallible handler manager allocation occurs before any session exists.
    {
        Kernel::KernelCore k; k.fail_manager = true;
        Kernel::KClientSession* result{};
        assert(call(k, &result).raw == Kernel::ResultOutOfResource.raw);
        assert(!result && !k.latest && k.quota == 0 && k.registrations == 0);
    }
    // The kernel session allocator may reject without committing quota.
    {
        Kernel::KernelCore k; k.fail_create = true;
        Kernel::KClientSession* result{};
        assert(call(k, &result).raw == Kernel::ResultOutOfResource.raw);
        assert(!result && !k.latest && k.quota == 0);
    }
    // Allocation of ServerManager::Session throws after Initialize/Commit.
    // The REAL extracted SCOPE_EXIT must close BOTH endpoints and quota.
    {
        Kernel::KernelCore k; k.fail_register_alloc = true;
        Kernel::KClientSession* result{};
        bool failed{};
        try { (void)call(k, &result); }
        catch (const std::bad_alloc&) { failed = true; }
        assert(failed && !result && k.latest && !k.accepted_server);
        assert(k.closed_client == 1 && k.closed_server == 1 && k.quota == 0);
        assert(!k.latest->client_open && !k.latest->server_open);
        reset(k);
    }
    // An error Result must also roll back without guest-visible handles.
    {
        Kernel::KernelCore k; k.fail_register_result = true;
        Kernel::KClientSession* result{};
        assert(call(k, &result).raw == 3 && !result && k.latest);
        assert(k.closed_client == 1 && k.closed_server == 1 && k.quota == 0);
        reset(k);
    }
    // Success transfers exactly one opened server endpoint, with client
    // independently held for the guest. It is not prematurely closed.
    {
        Kernel::KernelCore k;
        Kernel::KClientSession* result{};
        assert(call(k, &result).IsSuccess() && result && k.accepted_server);
        assert(k.quota == 1 && k.closed_client == 0 && k.closed_server == 0);
        assert(k.latest && k.latest->client_open && k.latest->server_open);
        result->Close(k);
        k.latest->server.Close(k);
        assert(k.closed_client == 1 && k.closed_server == 1 && k.quota == 0);
        reset(k);
    }
}
"""
# The SDK method is compiled in full; only the surrounding Service/Kernel
# dependencies are substituted to inject failures deterministically.
harness = harness.replace("class AM_IGpuWorker", "struct AM_IGpuWorker")
harness = harness.replace("namespace Service {", "namespace Service {\n    struct AM_IGpuWorker {};")
harness = harness.replace("__OWNER__", method)
compilers = [x for x in (shutil.which("clang++"), shutil.which("g++")) if x]
assert compilers, "At least one C++20 compiler is required"
with tempfile.TemporaryDirectory(prefix="eden-gpu-kernel-rollback-") as temporary:
    source = Path(temporary) / "owner.cpp"
    source.write_text(harness)
    for compiler in dict.fromkeys(compilers):
        for opt in ("-O0", "-O2"):
            exe = Path(temporary) / (Path(compiler).name + opt)
            command = [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                       "-fsanitize=undefined", "-fno-sanitize-recover=all",
                       "-I" + str(vendor / "sources/eden/src"),
                       str(source), "-o", str(exe)]
            build = subprocess.run(command, capture_output=True, text=True, timeout=55,
                                   env=os.environ.copy())
            assert build.returncode == 0, build.stderr[-3500:]
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=20)
            assert run.returncode == 0, run.stderr[-2500:]
            print("H06_KERNEL_SESSION_ROLLBACK_PASS", Path(compiler).name, opt,
                  "real_owner=1 oom_before_session=1 host_register_oom=1"
                  " kernel_quota_rollback=1 success_transfer=1", flush=True)
