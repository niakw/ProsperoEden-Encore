#!/usr/bin/env python3
"""Compile and execute the actual extracted Process::Run member, Clang + GCC."""
from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2]
owner=(root/'vendor/encore-active/ns2-runtime/process/core/hle/service/os/process.cpp').read_text()
start=owner.index('bool Process::Run() {')
end=owner.index('\nvoid Process::Terminate()',start)
real=owner[start:end]
fin_begin=owner.index('void Process::Finalize() {')
fin_end=owner.index('\nbool Process::Run()',fin_begin)
real_finalize=owner[fin_begin:fin_end]
term_begin=owner.index('void Process::Terminate() {')
term_end=owner.index('\nvoid Process::ResetSignal()',term_begin)
real_terminate=owner[term_begin:term_end]
harness=r'''
#include <cassert>
#include <atomic>
#include <cstdint>
#include "core/loader/ns2_svc_trace.h"
using u64=std::uint64_t;
struct Result { unsigned raw; bool IsFailure()const{return raw!=0;} };
#define R_FAILED(v) ((v).IsFailure())
#define LOG_ERROR(...) ((void)0)
constexpr int Service_LDR=0;
struct FakeKProcess;
struct KernelCore {
    unsigned removals{};
    void RemoveProcess(FakeKProcess*);
};
struct FakeFilesystem {
    unsigned removed{};
    u64 last_pid{};
    void UnregisterProcessIfPresent(u64 pid) {
        ++removed;
        last_pid=pid;
    }
};
struct CoreSystem {
    KernelCore kernel;
    FakeFilesystem filesystem;
    KernelCore& Kernel(){return kernel;}
    FakeFilesystem& GetFileSystemController(){return filesystem;}
};
struct FakeKProcess {
    u64 pid{};
    Result result{0};
    int calls{};
    unsigned guest_pages{4},closes{},terminates{};
    u64 GetProcessId()const{return pid;}
    Result Run(KernelCore&,int,u64) {++calls;return result;}
    Result Terminate(KernelCore&) {++terminates;return {111};}
    void Close(KernelCore&) {++closes;guest_pages=0;}
};
inline void KernelCore::RemoveProcess(FakeKProcess* p) {
    assert(p && p->closes==1);
    ++removals;
}
class Process {
public:
    explicit Process(CoreSystem& sys):m_system(sys){}
    bool Run();
    void Finalize();
    void Terminate();
    bool m_process_started{};
    FakeKProcess* m_process{};
    CoreSystem& m_system;
    int m_main_thread_priority{44};
    u64 m_main_thread_stack_size{0x4000};
};
''' + real_finalize + '\n' + real + '\n' + real_terminate + r'''
int main() {
    using namespace Eden::NS2::SvcTrace;
    CoreSystem sys;
    FakeKProcess ns2{33,{0},0};
    Register(33);
    Process ok(sys);ok.m_process=&ns2;
    assert(ok.Run());assert(!ok.Run());assert(ns2.calls==1);
    FakeKProcess failed{44,{0x111},0};
    Register(44);
    Process bad(sys);bad.m_process=&failed;
    assert(!bad.Run());assert(!bad.Run());assert(failed.calls==1);
    // The maintained late-failure owner must retire the KProcess, its code
    // pages and RomFS immediately; a second Run() must stay rejected.
    assert(bad.m_process==nullptr && bad.m_process_started);
    assert(failed.closes==1 && failed.terminates==1 && failed.guest_pages==0);
    assert(sys.kernel.removals==1);
    assert(active_pid.load()==0);
    assert(sys.filesystem.removed==1 && sys.filesystem.last_pid==44);
    FakeKProcess sw1{55,{0x222},0};
    Register(0);
    Process legacy(sys);legacy.m_process=&sw1;
    assert(legacy.Run());assert(!legacy.Run());assert(sw1.calls==1);
    assert(sys.filesystem.removed==1 && sw1.closes==0 && sys.kernel.removals==1); // NS1 unchanged.
    Process nil(sys);
    assert(nil.Run());assert(!nil.Run());
    FakeKProcess other{99,{0x234},0};
    Register(100);
    Process wrong(sys);wrong.m_process=&other;
    assert(wrong.Run());assert(other.calls==1);
    Register(100);
    Unregister(99);
    assert(active_pid.load()==100); // stale error must not clear another PID
    Unregister(100);
    assert(active_pid.load()==0);
}
'''
with tempfile.TemporaryDirectory(prefix="n52-os-process-") as d:
    src=Path(d)/"test.cpp";src.write_text(harness)
    for cxx in ("clang++","g++"):
        exe=Path(d)/("test-"+cxx.replace("+","p"))
        subprocess.run([cxx,"-std=c++20","-O1","-Wall","-Wextra",
                        "-Wno-unused-variable","-Werror","-fsanitize=undefined",
                        "-fno-sanitize-recover=all",
                        "-DEDEN_NS2_PROCESS_RUN_GUARD=1",
                        "-I",str(root/"vendor/encore-active/ns2-runtime/metadata"),
                        "-I",str(root/"vendor/encore-active/ns2-helpers/include"),
                        str(src),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print("N52_REAL_PROCESS_RUN_HOST_LIFECYCLE_PASS late_kprocess_close=1"
      " native_romfs_cleanup=1 native_guest_page_model_rollback=1"
      " rejected_second_run=1 historical_ns1_unchanged=1"
      " real_kpage_table=not_exercised")
