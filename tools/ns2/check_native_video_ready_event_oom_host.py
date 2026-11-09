#!/usr/bin/env python3
"""H05: execute real native video input-ready event/IPC owner under host OOM.

Clang/GCC UBSan inject timer, notification, event-callback and COPY
descriptor failures. Verify unscheduled timers, closed event lifetimes,
no success response with missing COPY handles and successful retry.
Does not claim authentic FFmpeg decode or GPU video frame output.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp").read_text()
start="void IGraphicsVideoDecoderSession::GetEvent("
end="\nbool IGraphicsVideoDecoderSession::EnsureSyncpoint("
assert source.count(start)==source.count(end)==1
owner=start+source.split(start,1)[1].split(end,1)[0]
assert "m_context.CloseEvent(m_event);" in owner
assert "m_ready->Detach();" in owner
assert "UnscheduleEvent(m_ready_timer);" in owner
assert "ctx.AddCopyObject(&m_event->GetReadableEvent());" in owner
assert owner.index("ctx.AddCopyObject(") < owner.index("IPC::ResponseBuilder rb{ctx, 2, 1, 0};")
assert owner.count("catch (const std::bad_alloc&)")==2

fixture=r"""
#include <cassert>
#include <chrono>
#include <cstdint>
#include <functional>
#include <memory>
#include <new>
#include <optional>
#include <string>
#include <vector>
using u32=std::uint32_t;
using s64=std::int64_t;
struct Result {u32 raw{};};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidState{1},ResultOutOfResource{2};
struct KReadableEvent {int id{17};};
}
struct HLERequestContext {
    bool fail_copy{};
    unsigned staged_copies{},response_copies{},response_words{};
    u32 reply{~u32{0}};
    void AddCopyObject(Kernel::KReadableEvent* obj) {
        assert(obj && obj->id==17);
        if(fail_copy)throw std::bad_alloc{};
        ++staged_copies;
    }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,int words,int copies=0,int moves=0)
        :ctx(c) {
        assert(words==2 && moves==0);
        ctx.response_words=static_cast<unsigned>(words);
        ctx.response_copies=static_cast<unsigned>(copies);
    }
    void Push(u32 value){ctx.reply=value;}
    void Push(Result value){ctx.reply=value.raw;}
};
}
struct FakeEvent {
    Kernel::KReadableEvent readable{};
    unsigned signals{};
    Kernel::KReadableEvent& GetReadableEvent(){return readable;}
    void Signal(int&){++signals;}
};
struct EventContext {
    FakeEvent event{};
    bool fail_create{};
    unsigned creates{},closes{};
    FakeEvent* CreateEvent(const char* name) {
        assert(std::string(name)=="NS2VideoInputReady");
        ++creates;
        if(fail_create) throw std::bad_alloc{};
        return &event;
    }
    void CloseEvent(FakeEvent* ptr) {
        assert(ptr==&event);
        ++closes;
    }
};
struct Ready {
    bool fail_attach{},active{},room{};
    unsigned attached{},detached{},notified{};
    std::function<void()> callback{};
    void Attach(std::function<void()> next) {
        if(fail_attach)throw std::bad_alloc{};
        callback=std::move(next);
        ++attached;
    }
    void Detach(){callback={};++detached;}
    void Set(bool started,bool has_room) {active=started;room=has_room;}
    void Notify() {
        ++notified;
        if(active&&room&&callback)callback();
    }
};
namespace Core::Timing {
inline bool fail_create{};
template<class Callback>
std::shared_ptr<int> CreateEvent(const char* name,Callback&& callback){
    assert(std::string(name)=="NS2VideoInputReadyPulse");
    (void)callback;
    if(fail_create)throw std::bad_alloc{};
    return std::make_shared<int>(1);
}
}
struct MockTiming {
    bool fail_schedule{};
    unsigned schedules{},unschedules{};
    template<class T>
    void ScheduleLoopingEvent(T,T,const std::shared_ptr<int>& handle) {
        assert(handle);
        ++schedules;
        if(fail_schedule)throw std::bad_alloc{};
    }
    void UnscheduleEvent(const std::shared_ptr<int>& handle){
        assert(handle);
        ++unschedules;
    }
};
struct MockSystem {
    int kernel{};
    MockTiming timing{};
    int& Kernel(){return kernel;}
    MockTiming& CoreTiming(){return timing;}
};
struct IGraphicsVideoDecoderSession {
    bool m_creator{},m_finalized{},m_started{true};
    static constexpr std::size_t MaxFrames=16;
    std::vector<int> m_pending{};
    MockSystem system{};
    EventContext m_context{};
    FakeEvent* m_event{};
    std::shared_ptr<int> m_ready_timer{};
    std::shared_ptr<Ready> m_ready{std::make_shared<Ready>()};
    void GetEvent(HLERequestContext&);
};
__REAL_OWNER__
static void rejected(HLERequestContext& ctx){
    assert(ctx.reply==Kernel::ResultOutOfResource.raw);
    assert(ctx.response_words==2 && ctx.response_copies==0);
    assert(ctx.staged_copies==0);
}
int main(){
    {
        IGraphicsVideoDecoderSession o;
        o.m_creator=true;
        HLERequestContext ctx;
        o.GetEvent(ctx);
        assert(ctx.reply==Kernel::ResultInvalidState.raw &&
               ctx.response_copies==0 && o.m_context.creates==0);
    }
    {
        IGraphicsVideoDecoderSession o;
        o.m_context.fail_create=true;
        HLERequestContext ctx;
        o.GetEvent(ctx);rejected(ctx);
        assert(!o.m_event && !o.m_ready_timer);
        assert(o.system.timing.schedules==0);
        o.m_context.fail_create=false;
        HLERequestContext retry;
        o.GetEvent(retry);
        assert(retry.reply==0 && retry.response_copies==1 &&
               retry.staged_copies==1);
    }
    {
        IGraphicsVideoDecoderSession o;
        o.m_ready->fail_attach=true;
        HLERequestContext ctx;
        o.GetEvent(ctx);rejected(ctx);
        assert(!o.m_event && !o.m_ready_timer && o.m_context.closes==1);
        assert(o.m_ready->detached==1);
    }
    {
        IGraphicsVideoDecoderSession o;
        Core::Timing::fail_create=true;
        HLERequestContext ctx;
        o.GetEvent(ctx);rejected(ctx);
        assert(!o.m_event && !o.m_ready_timer && o.m_context.closes==1);
        assert(o.m_ready->detached==1);
        Core::Timing::fail_create=false;
    }
    {
        IGraphicsVideoDecoderSession o;
        o.system.timing.fail_schedule=true;
        HLERequestContext ctx;
        o.GetEvent(ctx);rejected(ctx);
        assert(!o.m_event && !o.m_ready_timer);
        assert(o.system.timing.schedules==1 && o.system.timing.unschedules==1);
        assert(o.m_context.closes==1 && o.m_ready->detached==1);
    }
    {
        IGraphicsVideoDecoderSession o;
        HLERequestContext ctx;
        ctx.fail_copy=true;
        o.GetEvent(ctx);rejected(ctx);
        assert(o.m_event && o.m_ready_timer);
        assert(o.m_context.creates==1 && o.system.timing.schedules==1);
        HLERequestContext retry;
        o.GetEvent(retry);
        assert(retry.reply==0 && retry.response_copies==1 &&
               retry.staged_copies==1);
        assert(o.m_context.creates==1 && o.system.timing.schedules==1);
        assert(o.m_context.event.signals>=1);
    }
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Clang/GCC required"
with tempfile.TemporaryDirectory(prefix="eden-h05-video-event-") as temp:
    file=Path(temp)/"real_owner.cpp";file.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 str(file),"-o",str(exe)]
            built=subprocess.run(cmd,capture_output=True,text=True,timeout=60,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5500:]
            ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert ran.returncode==0,ran.stderr[-5500:]
            print("H05_VIDEO_READY_EVENT_OWNER_OOM_PASS",Path(cc).name,opt,
                  "create=rollback attach=rollback timer=rollback"
                  " schedule=rollback copy=not_transferred retry=success",flush=True)
