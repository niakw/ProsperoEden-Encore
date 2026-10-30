// SPDX-License-Identifier: GPL-3.0-or-later
// Executes the actual Dynarmic JIT with research A64 overlay.
#include <atomic>
#include <thread>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <unordered_map>
#include "dynarmic/tests/A64/testenv.h"
#include "dynarmic/interface/A64/a64.h"
#include "dynarmic/interface/exclusive_monitor.h"

struct Pattern {std::string_view name,bits;};
static constexpr Pattern patterns[]={
#define INST(method,name,bits) {#method,bits},
#include "dynarmic/frontend/A64/decoder/a64.inc"
#undef INST
};
static std::uint32_t encode(std::string_view name,
    std::initializer_list<std::pair<char,unsigned>> fields) {
    const Pattern* p=nullptr;
    for (auto& row:patterns) if(row.name==name){p=&row;break;}
    if(!p||p->bits.size()!=32) throw std::runtime_error("missing opcode");
    std::unordered_map<char,unsigned> args(fields.begin(),fields.end());
    std::unordered_map<char,unsigned> n;
    std::uint32_t result=0;
    for(int i=31;i>=0;--i){
        char ch=p->bits[i];
        if(ch=='1') result |= 1u << (31-i);
        else if(ch!='0'){
            auto it=args.find(ch);
            if(it!=args.end()&&((it->second>>n[ch])&1u)) result |= 1u << (31-i);
            ++n[ch];
        }
    }
    return result;
}
struct Env: A64TestEnv {
    Dynarmic::ExclusiveMonitor monitor{6};
    unsigned fail=0,writes=0;
    bool MemoryWriteExclusive64(u64 addr,u64 value,u64 expected) override {
        ++writes;
        if(fail){--fail;return false;}
        if(MemoryRead64(addr)!=expected)return false;
        MemoryWrite64(addr,value);
        return true;
    }
};
static void check(bool ok,const char* msg) {
    if(!ok){std::cerr<<"FAIL "<<msg<<"\n";std::exit(1);}
}
static void atomic(std::string_view op,u64 before,u64 src,u64 after,bool cas,unsigned fails=0){
    std::cerr << "RUN " << op << " before=" << before << " src=" << src << " after=" << after << " fails=" << fails << std::endl;
    Env env;Dynarmic::A64::UserConfig conf{}; conf.callbacks=&env;
    conf.global_monitor=&env.monitor;
    conf.code_cache_size=16*1024*1024;
    Dynarmic::A64::Jit jit{conf};
    env.code_mem={encode(op,{{'z',3},{'s',2},{'n',1},{'t',3},
                              {'L',0},{'o',0},{'A',0},{'R',0}}),0x14000000};
    env.MemoryWrite64(0x200,before);
    env.fail=fails;
    jit.SetPC(0);jit.SetRegister(1,0x200);jit.SetRegister(2,src);
    jit.SetRegister(3,cas?after:0xdeadbeef);
    for(int i=0;i<8&&jit.GetPC()==0;++i){env.ticks_left=2;jit.Step();}
    check(jit.GetPC()==4,"atomic completes / retries");
    check(env.MemoryRead64(0x200)==after,"atomic memory");
    check(jit.GetRegister(cas?2:3)==before,"atomic observed register");
    check(env.writes>=fails+1,"exclusive retry observed");
}
int main(){
    atomic("CAS",17,17,99,true);
    atomic("CAS",17,17,99,true,2);
    atomic("CAS",17,77,17,true);
    atomic("SWP",18,25,25,false);
    atomic("LDADD",18,7,25,false);
    atomic("LDCLR",255,0x55,0xaa,false);
    atomic("LDSET",16,0x81,0x91,false);
    atomic("LDEOR",48,0x14,0x24,false);
    {
        std::cerr << "RUN RETAA" << std::endl;
        Env env; Dynarmic::A64::UserConfig cfg{};cfg.callbacks=&env;cfg.global_monitor=&env.monitor;
        Dynarmic::A64::Jit jit{cfg};
        env.code_mem={0xD65F0BFF,0x14000000};
        jit.SetRegister(30,4);jit.SetPC(0);jit.Step();
        check(jit.GetPC()==4,"RETAA return");
    }
    {
        std::cerr << "RUN LDAPR" << std::endl;
        Env env;Dynarmic::A64::UserConfig cfg{};cfg.callbacks=&env;cfg.global_monitor=&env.monitor;
        Dynarmic::A64::Jit jit{cfg};
        env.code_mem={encode("LDAPR",{{'s',3},{'n',1},{'t',3}}),0x14000000};
        env.MemoryWrite64(0x200,0x12345678);
        jit.SetRegister(1,0x200);jit.SetPC(0);jit.Step();
        check(jit.GetRegister(3)==0x12345678,"LDAPR acquire");
    }

    // Six independent guest processors, shared reservation granule, concurrent
    // retry. Validate exclusive monitor capacity and cross-core invalidation.
    {
        Dynarmic::ExclusiveMonitor shared{6};
        check(shared.GetProcessorCount()==6,"six exclusive monitor slots");
        std::atomic<std::uint64_t> counter{0};
        std::atomic<bool> timed_out{false};
        std::vector<std::thread> workers;
        for (unsigned core=0;core<6;++core) {
            workers.emplace_back([&,core] {
                for (unsigned n=0;n<64;++n) {
                    bool success=false;
                    for (unsigned retries=0;retries<100000 && !success;++retries) {
                        const auto observed=shared.ReadAndMark<std::uint64_t>(
                            core,0x1000,[&] {return counter.load(std::memory_order_relaxed);});
                        success=shared.DoExclusiveOperation<std::uint64_t>(
                            core,0x1000,[&](std::uint64_t expected) {
                                return counter.compare_exchange_strong(
                                    expected,observed+1,std::memory_order_relaxed);
                            });
                    }
                    if(!success){timed_out.store(true);return;}
                }
            });
        }
        for (auto& worker:workers)worker.join();
        check(!timed_out.load(),"six-core contention terminated");
        check(counter.load()==384,"six-core exclusive operation counted exactly");
    }
    std::cout<<"Actual Dynarmic NS2 LSE/RETA/LDAPR JIT PASS\n";
}
