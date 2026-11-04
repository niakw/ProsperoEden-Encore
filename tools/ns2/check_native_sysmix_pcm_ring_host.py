#!/usr/bin/env python3
"""P1.3: source-extracted NS2 Sysmix PCM16/float guest ring pump on host.

Compile the maintained SysmixOutput::Pump and its actual guest index reader
against strict stand-ins for guest RAM and the existing Eden SinkStream.
Does not claim real PS5 audio, scheduler integration or kernel IPC.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_sysmix.cpp"
OWNER = SOURCE.read_text()
CM = (ROOT / "headless/CMakeLists.txt").read_text()
AUDIO = (SOURCE.parent / "audio.cpp").read_text()
assert "core/hle/service/audio/nx2_sysmix.cpp" in CM
assert 'RegisterNamedService("audsmx:u"' in AUDIO
assert 'RegisterNamedService("auddmg:u"' in AUDIO
assert "p.host->GetQueueSize() >= NativeQueueHighWatermark" in OWNER
assert "p.host->AppendBuffer(block, p.output)" in OWNER
assert "memory.WriteExclusive32(p.buffer + ReadOffset, next, read)" in OWNER
assert "std::atomic_thread_fence(std::memory_order_acquire)" in OWNER
assert "StreamType::Out" in OWNER
assert "TryAppendOutputBlock(" not in OWNER

def native(source: str, start: str) -> str:
    assert source.count(start) == 1, start
    at = source.index(start)
    opening = source.index("{", at)
    depth = 0
    for cursor in range(opening, len(source)):
        if source[cursor] == "{":
            depth += 1
        elif source[cursor] == "}":
            depth -= 1
            if depth == 0:
                return source[at:cursor+1]
    raise AssertionError("unbalanced " + start)

read_acquire = native(OWNER, "bool ReadWordAcquire(")
pump = native(OWNER, "void SysmixOutput::Pump() {")
validate = native(OWNER, "Result SysmixOutput::ValidateRegion(")
formats = native(OWNER, "bool SysmixOutput::IsFormatSupported(")
# The actual counter and input layout, not a translated algorithm.
assert "p.output.fill(0);" in pump
assert "std::isfinite(value)" in pump
assert "read + taken" in pump
assert "std::try_to_lock" in pump
assert "p.counters.backpressure" in pump
assert "p.counters.nonzero_frames" in pump
assert "if (!p.engaged)" in pump
assert "p.Fault()" in pump

CPP = r'''
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <mutex>
#include <span>
#include <string>
#include <vector>
using u8 = std::uint8_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s16 = std::int16_t;
using s32 = std::int32_t;
using f32 = float;
using Result = int;
constexpr Result ResultSuccess = 0;
constexpr Result ResultNotSupported = -1;
constexpr Result ResultInvalidAddressInfo = -2;
constexpr Result ResultOperationFailed = -3;
#define R_UNLESS(check,err) do { if (!(check)) return err; } while(false)
#define R_SUCCEED() return ResultSuccess
#define LOG_INFO(...) ((void)0)
namespace AudioCore {
enum class SampleFormat : u8 { Invalid, PcmInt8, PcmInt16, PcmInt24, PcmInt32, PcmFloat, Adpcm };
namespace Sink {
struct SinkBuffer {
    u64 frames{},frames_played{},tag{};
    bool consumed{};
};
}
}
namespace Core {
namespace Memory {
struct Memory {
    static constexpr u64 Base=0x100000;
    static constexpr u32 Slots=300;
    static constexpr u32 FrameBytes=4;
    std::array<u8,Slots*FrameBytes> ring{};
    u32 read{},write{};
    bool guest_valid{true};
    bool failed_io{};
    bool fail_cas{};
    unsigned word_reads{}, block_reads{}, cas_attempts{};
    bool IsValidVirtualAddressRange(u64 at,u64 length) const {
        return guest_valid && at>=Base && length<=0x3000 &&
               at-Base<=0x3000-length;
    }
    u32 Read32(u64 at) {
        ++word_reads;
        if (at==Base+0x44) return read;
        if (at==Base+0x1004) return write;
        assert(false && "unknown guest ring index");
        return 0;
    }
    bool ReadBlock(u64 at,void* to,std::size_t bytes) {
        ++block_reads;
        if (failed_io || !IsValidVirtualAddressRange(at,bytes) ||
            at<Base+0x1040 || at-Base-0x1040+bytes>ring.size())
            return false;
        std::memcpy(to,ring.data()+(at-Base-0x1040),bytes);
        return true;
    }
    bool WriteExclusive32(u64 at,u32 next,u32 expected) {
        ++cas_attempts;
        if (fail_cas || at!=Base+0x44 || read!=expected) return false;
        read=next;
        return true;
    }
    void StorePCM16(u32 slot,s16 left,s16 right) {
        assert(slot<Slots);
        std::memcpy(ring.data()+slot*4,&left,sizeof(left));
        std::memcpy(ring.data()+slot*4+2,&right,sizeof(right));
    }
    void StoreFloat(u32 slot,f32 left,f32 right) {
        assert(slot<Slots && slot*8+8<=ring.size());
        std::memcpy(ring.data()+slot*8,&left,sizeof(left));
        std::memcpy(ring.data()+slot*8+4,&right,sizeof(right));
    }
};
}
struct System {
    bool shutdown{};
    bool IsShuttingDown() const { return shutdown; }
    struct KernelCore {};
    KernelCore& Kernel() { static KernelCore k; return k; }
};
}
namespace Kernel {
struct KProcess {
    Core::Memory::Memory memory;
    Core::Memory::Memory& GetMemory() { return memory; }
};
}
constexpr u64 ReadOffset = 0x44;
constexpr u64 WriteOffset = 0x1004;
constexpr u64 PayloadOffset = 0x1040;
constexpr u32 BlockFrames = 240;
constexpr u32 NativeQueueHighWatermark = 4;
__READ_ACQUIRE__
struct Host {
    unsigned pending{}, starts{}, stops{};
    std::vector<std::array<s16,BlockFrames*2>> submitted;
    void Start() {++starts;}
    void Stop() {++stops;}
    unsigned GetQueueSize() const {return pending;}
    void AppendBuffer(AudioCore::Sink::SinkBuffer& packet,std::span<s16> pcm) {
        assert(pending<NativeQueueHighWatermark);
        assert(packet.frames==BlockFrames && pcm.size()==BlockFrames*2);
        assert(packet.tag==submitted.size());
        std::array<s16,BlockFrames*2> sample{};
        std::copy(pcm.begin(),pcm.end(),sample.begin());
        submitted.push_back(sample);
        ++pending;
    }
};
struct Event {
    unsigned signals{};
    void Signal(Core::System::KernelCore&){++signals;}
};
struct MockProcess {
    Core::Memory::Memory memory{};
    Core::Memory::Memory& GetMemory(){return memory;}
};
struct Counters {
    u64 ticks{},copied_frames{},accepted_frames{},nonzero_frames{},
        admitted_blocks{},backpressure{},faults{};
};
struct MockImpl {
    Core::System system;
    MockProcess* process{};
    Host* host{};
    Event state_event_value, data_event_value;
    Event* state_event{&state_event_value};
    Event* data_event{&data_event_value};
    std::mutex mutex;
    u32 id{1},data_mode{0},slots{Core::Memory::Memory::Slots},
        frame_bytes{4},consumer{0};
    u64 buffer{Core::Memory::Memory::Base};
    bool open{true},engaged{true},faulted{};
    s32 threshold{};
    f32 gain{1};
    AudioCore::SampleFormat format{AudioCore::SampleFormat::PcmInt16};
    std::array<u8,BlockFrames*2*sizeof(f32)> input{};
    std::array<s16,BlockFrames*2> output{};
    Counters counters{};
    bool ReadOccupancy(u32& r,u32& w,u32& filled) {
        auto& memory=process->GetMemory();
        if (!ReadWordAcquire(memory,buffer+ReadOffset,r) || r!=consumer ||
            !ReadWordAcquire(memory,buffer+WriteOffset,w) ||
            r>=slots || w>=slots) return false;
        filled=(w+slots-r)%slots;
        return true;
    }
    Result Fault(Result result=ResultInvalidAddressInfo){
        faulted=true;engaged=false;++counters.faults;
        if(host) host->Stop();
        state_event->Signal(system.Kernel());
        return result;
    }
    void Notify(u32 filled) {
        if (data_mode==2 && slots-1-filled>=static_cast<u32>(threshold))
            data_event->Signal(system.Kernel());
    }
};
class SysmixOutput {
public:
    MockImpl* impl;
    static Result ValidateRegion(Kernel::KProcess&,u64,u64,u32);
    static bool IsFormatSupported(u32,u32,u32);
    void Pump();
};
__VALIDATE__
__FORMATS__
__PUMP__
int main() {
    using Core::Memory::Memory;
    Kernel::KProcess validated{};
    assert(SysmixOutput::ValidateRegion(validated,Memory::Base,0x3000,0x24)==ResultSuccess);
    assert(SysmixOutput::ValidateRegion(validated,Memory::Base+1,0x3000,0x24)==ResultInvalidAddressInfo);
    assert(SysmixOutput::ValidateRegion(validated,Memory::Base,0x1000,0x24)==ResultInvalidAddressInfo);
    assert(SysmixOutput::ValidateRegion(validated,Memory::Base,0x3000,0x25)==ResultNotSupported);
    validated.memory.guest_valid=false;
    assert(SysmixOutput::ValidateRegion(validated,Memory::Base,0x3000,0x24)==ResultInvalidAddressInfo);
    validated.memory.guest_valid=true;
    assert(SysmixOutput::IsFormatSupported(2,2,48000));
    assert(SysmixOutput::IsFormatSupported(5,2,48000));
    assert(!SysmixOutput::IsFormatSupported(2,1,48000));
    assert(!SysmixOutput::IsFormatSupported(3,2,48000));
    assert(!SysmixOutput::IsFormatSupported(2,2,44100));

    MockProcess process{};
    Host host{};
    MockImpl impl{};
    impl.process=&process;
    impl.host=&host;
    SysmixOutput stream{&impl};
    for(u32 slot=0;slot<240;++slot)
        process.memory.StorePCM16(slot,static_cast<s16>(slot+1),
                                 static_cast<s16>(-static_cast<s32>(slot+1)));
    process.memory.write=240;
    stream.Pump();
    assert(process.memory.read==240 && impl.consumer==240);
    assert(host.submitted.size()==1 && host.pending==1);
    assert(host.submitted[0][0]==1 && host.submitted[0][1]==-1);
    assert(host.submitted[0][478]==240 && host.submitted[0][479]==-240);
    assert(impl.counters.accepted_frames==240 && impl.counters.admitted_blocks==1);
    for(u32 slot=240;slot<260;++slot)process.memory.StorePCM16(slot, 1000,-2000);
    process.memory.write=260;
    host.pending=NativeQueueHighWatermark;
    stream.Pump();
    assert(process.memory.read==240 && impl.consumer==240);
    assert(impl.counters.backpressure==1 && host.submitted.size()==1);
    host.pending=0;
    stream.Pump();
    assert(process.memory.read==260 && impl.consumer==260);
    assert(host.submitted.size()==2 && host.submitted[1][0]==1000);
    assert(host.submitted[1][1]==-2000 && host.submitted[1][42]==0);
    assert(impl.counters.copied_frames==280 && impl.counters.accepted_frames==260);

    MockProcess wrap_process{};
    Host wrap_host{};
    MockImpl wrap{};
    wrap.process=&wrap_process; wrap.host=&wrap_host;
    wrap.consumer=Memory::Slots-2;
    wrap_process.memory.read=wrap.consumer;
    wrap_process.memory.write=5;
    for(u32 i=0;i<7;++i)
        wrap_process.memory.StorePCM16((wrap.consumer+i)%wrap.slots,
                                       300+i,-300-static_cast<s16>(i));
    SysmixOutput wrapped{&wrap};
    wrapped.Pump();
    assert(wrap_process.memory.read==5 && wrap.counters.accepted_frames==7);
    assert(wrap_process.memory.block_reads==2);
    for(int i=0;i<7;++i) {
        assert(wrap_host.submitted[0][2*i]==300+i);
        assert(wrap_host.submitted[0][2*i+1]==-300-i);
    }
    assert(wrap_host.submitted[0][16]==0);
    // PCM float variant: NaN is silence, +-saturation is clipped.
    MockProcess float_process{};
    Host float_host{};
    MockImpl floated{};
    floated.process=&float_process;floated.host=&float_host;
    floated.format=AudioCore::SampleFormat::PcmFloat;
    floated.frame_bytes=8;
    float_process.memory.StoreFloat(0,-1.0f,0.5f);
    float_process.memory.StoreFloat(1,std::numeric_limits<f32>::quiet_NaN(),2.0f);
    float_process.memory.write=2;
    SysmixOutput float_stream{&floated};
    float_stream.Pump();
    assert(float_process.memory.read==2 && float_host.submitted.size()==1);
    assert(float_host.submitted[0][0]==-32768 && float_host.submitted[0][1]==16384);
    assert(float_host.submitted[0][2]==0 && float_host.submitted[0][3]==32767);
    assert(floated.counters.nonzero_frames==2);

    MockProcess bad_process{};
    Host bad_host{};
    MockImpl bad{};
    bad.process=&bad_process;bad.host=&bad_host;
    bad_process.memory.write=1;
    bad_process.memory.failed_io=true;
    SysmixOutput bad_stream{&bad};
    bad_stream.Pump();
    assert(bad.faulted && bad.counters.faults==1 && bad_host.stops==1);
    assert(bad_process.memory.read==0 && bad_host.submitted.empty());

    MockProcess raced_process{};
    Host raced_host{};
    MockImpl raced{};
    raced.process=&raced_process;raced.host=&raced_host;
    raced_process.memory.write=1;
    raced_process.memory.fail_cas=true;
    SysmixOutput race_stream{&raced};
    race_stream.Pump();
    assert(raced.faulted && raced.counters.faults==1);
    assert(raced_process.memory.read==0 && raced.counters.accepted_frames==0);
    assert(raced_host.stops==1);
    // Never advertise a successful ring cursor update after failed CAS.
    std::puts("P1_3_SYS_MIX_PCM_RING_SOURCE_HOST_PASS "
              "validated=1 format=1 pcm16=240 pcm_float=2 wrap=1 "
              "queue_backpressure=1 invalid_memory=1 failed_cas=1");
}
'''
CPP = (CPP.replace("__READ_ACQUIRE__", read_acquire)
          .replace("__VALIDATE__", validate)
          .replace("__FORMATS__", formats)
          .replace("__PUMP__", pump))
for tag in ("__READ_ACQUIRE__", "__PUMP__", "__VALIDATE__", "__FORMATS__"):
    assert tag not in CPP
compilers = list(dict.fromkeys(filter(None, (
    shutil.which("clang++"), shutil.which("g++")
))))
assert compilers
env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
with tempfile.TemporaryDirectory(prefix="encore-sysmix-pcm-") as temp:
    top=Path(temp)
    file=top/"test.cpp"
    file.write_text(CPP)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            binary=top/(Path(compiler).name+opt)
            args=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-Wno-unused-parameter","-fsanitize=undefined",
                  "-fno-sanitize-recover=all",str(file),"-o",str(binary)]
            build=subprocess.run(args,env=env,capture_output=True,text=True,timeout=65)
            assert build.returncode==0,(opt,build.stderr[-4500:])
            test=subprocess.run([str(binary)],env=env,capture_output=True,text=True,timeout=25)
            assert test.returncode==0,(opt,test.stdout,test.stderr[-3500:])
            print(Path(compiler).name,opt,test.stdout.strip())
