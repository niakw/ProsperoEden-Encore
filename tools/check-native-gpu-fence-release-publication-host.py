#!/usr/bin/env python3
"""Host witness for release/acquire fence publication in the canonical GPU worker."""
from pathlib import Path
import shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=(ROOT/"vendor/sources/eden/src/video_core/gpu_thread.cpp").read_text()
WORKER=(ROOT/"vendor/encore-active/eden/src/video_core/gpu_thread.cpp").read_text()
HEADER=(ROOT/"vendor/encore-active/eden/src/video_core/gpu_thread.h").read_text()
FAST=(ROOT/".github/workflows/encore-core-fast-gate.yml").read_text()
FULL=(ROOT/".github/workflows/encore-core-preflight.yml").read_text()
SCRIPT="python3 -B tools/check-native-gpu-fence-release-publication-host.py"
assert SCRIPT in FAST and SCRIPT in FULL
assert "std::atomic<u64> signaled_fence" in HEADER
PIN="state.signaled_fence.store(next.fence);"
OPT="state.signaled_fence.store(next.fence, std::memory_order_release);"
CONSUME="state.signaled_fence.load(std::memory_order_acquire)"
assert ORIGINAL.count(PIN)==1
assert WORKER.count(OPT)==1 and WORKER.count(PIN)==0
assert WORKER.count(CONSUME)==3
assert WORKER.count("state.cv.notify_all();")==1 and WORKER.index(OPT)<WORKER.index("state.cv.notify_all();")
cmake=(ROOT/"headless/CMakeLists.txt").read_text()
assert 'list(APPEND video_sources "${EDEN_GPU_WORKER}")' in cmake
assert "gpu_thread_quiet.cpp" not in cmake and "gpu_thread_dev.cpp" not in cmake
cpp=r"""
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <thread>
#include <vector>
using u64=std::uint64_t;
struct SynchState { std::atomic<u64> signaled_fence{}; }; struct Next { u64 fence{}; };
int main(){ constexpr u64 limit=32768; std::vector<u64> payload(limit+1); SynchState state;
 std::thread worker([&]{ Next next; for(u64 i=1;i<=limit;++i){payload[i]=i^0x5a5a5a5aULL;next.fence=i;WRITE_EXPRESSION} });
 u64 inspected=0; while(inspected<limit){ const u64 completed=READ_EXPRESSION; assert(completed<=limit);
   while(inspected<completed){++inspected;assert(payload[inspected]==(inspected^0x5a5a5a5aULL));}
   if(inspected<limit)std::this_thread::yield(); }
 worker.join(); assert(state.signaled_fence.load(std::memory_order_acquire)==limit);
 std::printf("GPU_FENCE_RELEASE_PUBLICATION_PASS commands=%llu\n",(unsigned long long)limit); }
"""
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++"); assert compiler
with tempfile.TemporaryDirectory(prefix="encore-fence-release-") as tmp:
 for name,publication in (("upstream",PIN),("maintained",OPT)):
  target=Path(tmp)/(name+".cpp"); output=Path(tmp)/name
  target.write_text(cpp.replace("WRITE_EXPRESSION",publication).replace("READ_EXPRESSION",CONSUME))
  subprocess.run([compiler,"-std=c++20","-O1","-g","-Wall","-Wextra","-Werror","-pthread",
   "-fsanitize=address,undefined","-fno-sanitize-recover=all",str(target),"-o",str(output)],check=True,timeout=90)
  subprocess.run([str(output)],check=True,timeout=45)
print("GPU_FENCE_RELEASE_HOST_PASS canonical_owner=1 publisher=release reader=acquire")
