// SPDX-License-Identifier: GPL-3.0-or-later
// Compile only this ordinary desktop unit; no PS5 SDK or app build.
#include "diagnostics_report_queue.h"
#include <cassert>
#include <iostream>
using namespace Eden::DiagnosticsSharing;
static std::string id(unsigned n) { return "00000000-0000-4000-8000-00000000000" + std::to_string(n); }
int main() {
    Queue q;
    const auto add=[&](Category c,unsigned n,std::uint64_t epoch=0) {
        return q.Enqueue({c, epoch ? epoch : q.Epoch(c), id(n), "{}"});
    };
    q.Conditions(true,true);
    assert(!add(Category::Standard,1));
    q.SetConsent({true,true});
    auto old_epoch=q.Epoch(Category::Advanced);
    assert(add(Category::Advanced,1));
    assert(add(Category::Advanced,2));
    assert(add(Category::Advanced,3));
    assert(add(Category::Advanced,4));
    assert(q.Count()==4 && q.Bytes()==8);
    assert(add(Category::Standard,5));
    assert(q.Count()==4 && !add(Category::Standard,5));
    assert(!q.Enqueue({Category::Standard,q.Epoch(Category::Standard),id(9),std::string(kMaxReportBytes+1,'x')}));
    // No transfer before idle, or during game/loading/shutdown/crash.
    for(auto phase:{Phase::GameStarting,Phase::Playing,Phase::Stopping,Phase::Crash}) {
        q.SetPhase(phase,10);
        assert(!q.TryStart(100));
    }
    q.SetPhase(Phase::LauncherIdle,100);
    assert(!q.TryStart(104));
    q.Activity(104);
    assert(!q.TryStart(108));
    auto first=q.TryStart(109);
    assert(first && first.report->category==Category::Standard && first.report->id==id(5));
    assert(!q.TryStart(106));
    q.SetPhase(Phase::GameStarting,106);
    assert(first.cancelled->load());
    q.SetPhase(Phase::LauncherIdle,200);
    assert(!q.TryStart(205)); // wait for actual worker acknowledgement
    assert(q.Finish(first.ticket,Queue::Result::Delivered));
    assert(q.Count()==4); // cancelled response not trusted; retry is idempotent
    assert(!q.TryStart(240)); // defer failure to later visit
    q.SetPhase(Phase::Playing,241);
    q.SetPhase(Phase::LauncherIdle,300);
    auto retry=q.TryStart(305);
    assert(retry && retry.report->id==id(5));
    assert(!q.Finish(first.ticket,Queue::Result::Delivered));
    assert(q.Finish(retry.ticket,Queue::Result::Delivered));
    assert(q.Count()==3);
    assert(!q.TryStart(334));
    auto second=q.TryStart(335);
    assert(second && second.report->category==Category::Advanced);
    q.SetConsent({true,false});
    assert(second.cancelled->load() && q.Count()==0);
    q.SetConsent({true,true});
    assert(q.Epoch(Category::Advanced)!=old_epoch);
    assert(!add(Category::Advanced,6,old_epoch));
    assert(add(Category::Advanced,6));
    assert(q.Finish(second.ticket,Queue::Result::Delivered));
    assert(q.Count()==1);
    q.SetPhase(Phase::Playing,340);
    q.SetPhase(Phase::LauncherIdle,400);
    auto expired=q.TryStart(405);
    assert(expired);
    q.Poll(410);
    assert(expired.cancelled->load());
    assert(q.Finish(expired.ticket,Queue::Result::Retry));
    q.SetPhase(Phase::Playing,411);
    q.SetPhase(Phase::LauncherIdle,500);
    q.Conditions(false,true);
    assert(!q.TryStart(505));
    q.SetConsent({false,false});
    assert(!q.Count());
    std::cout<<"DIAGNOSTICS_QUEUE_HOST_PASS capacity=4 consent_epoch=1 crash_priority=1 idle=1 cancellation=1 retry=1\n";
}
