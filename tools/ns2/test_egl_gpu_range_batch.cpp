// SPDX-License-Identifier: GPL-3.0-or-later
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <random>
#include <utility>
#include <vector>
#include "video_core/ns2_egl_gpu_range_batch.h"
using Run=std::pair<std::uint64_t,std::uint64_t>;
using Eden::NS2::Eglantine::ChangedPageRuns;
static void Check(const std::vector<bool>& dirty, std::uint64_t base, std::uint64_t page) {
    ChangedPageRuns batching(page);
    std::vector<Run> expected,actual;
    auto notify=[&](std::uint64_t a,std::uint64_t n){actual.emplace_back(a,n);};
    for(std::size_t i=0;i<dirty.size();++i) {
        auto addr=base+i*page;
        if(dirty[i]) {
            if(!expected.empty() && expected.back().first+expected.back().second==addr)
                expected.back().second+=page;
            else expected.emplace_back(addr,page);
        }
        batching.Record(addr,dirty[i],notify);
    }
    batching.Flush(notify);
    batching.Flush(notify);
    assert(expected==actual);
}
int main() {
    for(const auto page:{4096ULL,65536ULL}) {
        Check({},0x100000,page);
        Check({false,true,true,false,true,false},0x100000,page);
        Check({true,false,true,true,false,true},0x100000,page);
        std::mt19937_64 rng(0xE61A51);
        for(int n=0;n<2000;++n){
            std::vector<bool> flags(1+(rng()%900));
            for(std::size_t j=0;j<flags.size();++j)
                flags[j]=(rng()&7)<static_cast<std::uint64_t>(n%9);
            Check(flags,0x100000,page);
        }
    }
    // 1.45 GiB synthetic run: one notification, not 380,108.
    constexpr std::uint64_t pages=380108,base=0x100000,granule=4096;
    ChangedPageRuns b(granule);std::vector<Run> runs;
    auto log=[&](std::uint64_t a,std::uint64_t n){runs.emplace_back(a,n);};
    for(std::uint64_t i=0;i<pages;++i)b.Record(base+i*granule,true,log);
    b.Flush(log);
    assert(runs==(std::vector<Run>{{base,pages*granule}}));
    runs.clear();
    constexpr auto max=(std::numeric_limits<std::uint64_t>::max)();
    ChangedPageRuns edge(4096);
    edge.Record(max-8192,true,log);
    edge.Record(max-4096,false,log);
    edge.Record(max-4095,true,log); // invalid page end; must not notify
    edge.Flush(log);
    assert(runs==(std::vector<Run>{{max-8192,4096}}));
    std::puts("N51_GPU_CHANGED_RUN_ORACLE_PASS");
}
