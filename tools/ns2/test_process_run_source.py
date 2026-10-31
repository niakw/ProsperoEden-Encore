#!/usr/bin/env python3
"""Compile and execute the actual extracted Process::Run member, Clang + GCC."""
from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2]
owner=(root/'headless/ns2/overrides/core/hle/service/os/process.cpp').read_text()
start=owner.index('bool Process::Run() {')
end=owner.index('\nvoid Process::Terminate()',start)
real=owner[start:end]
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
struct KernelCore {};
struct CoreSystem { KernelCore kernel; KernelCore& Kernel(){return kernel;} };
struct FakeKProcess {
    u64 pid{};
    Result result{0};
    int calls{};
    u64 GetProcessId()const{return pid;}
    Result Run(KernelCore&,int,u64) {++calls;return result;}
};
class Process {
public:
    explicit Process(CoreSystem& sys):m_system(sys){}
    bool Run();
    bool m_process_started{};
    FakeKProcess* m_process{};
    CoreSystem& m_system;
    int m_main_thread_priority{44};
    u64 m_main_thread_stack_size{0x4000};
};
''' + real + r'''
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
    assert(active_pid.load()==0);
    FakeKProcess sw1{55,{0x222},0};
    Register(0);
    Process legacy(sys);legacy.m_process=&sw1;
    assert(legacy.Run());assert(!legacy.Run());assert(sw1.calls==1);
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
                        "-I",str(root/"headless/ns2/overrides"),
                        "-I",str(root/"vendor/encore-active/ns2-helpers/include"),
                        str(src),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print("N52_REAL_PROCESS_RUN_HOST_LIFECYCLE_PASS")
