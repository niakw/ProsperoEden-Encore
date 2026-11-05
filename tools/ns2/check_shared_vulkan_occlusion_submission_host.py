#!/usr/bin/env python3
"""P2/P4: execute source-extracted shared Vulkan ZPass query close policy.

Host proof only: real PS5 Vulkan driver/query results are not simulated.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCHEDULER = ROOT/"vendor/encore-active/eden-vulkan/vulkan_scheduler.cpp"
QUERY = ROOT/"vendor/encore-active/eden-vulkan/vulkan_query_cache.cpp"
scheduler = SCHEDULER.read_text()
query = QUERY.read_text()
anchor = "void Scheduler::EndPendingOperations() {"
assert scheduler.count(anchor) == 1
operations = scheduler.split(anchor, 1)[1].split("\n}", 1)[0]
assert "query_cache->CounterClose(VideoCommon::QueryType::ZPassPixelCount64);" in operations
assert "query_cache->CounterReset(VideoCommon::QueryType::ZPassPixelCount64);" not in operations
assert "EndRenderPass();" in operations
assert operations.index("CounterClose") < operations.index("EndRenderPass()")

bank_anchor = "static constexpr size_t BANK_SIZE = 256;"
assert query.count(bank_anchor) == 1
sample_start = query.index("class SamplesStreamer : public BaseStreamer")
sample = query[sample_start:]
close = "    void CloseCounter() override {"
end = "    bool HasPendingSync() const override {"
assert sample.count(close) >= 1
start = sample.index(close)  # SamplesStreamer; later counter subclasses have their own CloseCounter
stop = sample.index(end, start)
actual_method = sample[start:stop].rstrip()
assert actual_method.count("PauseCounter();") == 1
assert actual_method.count("ResetCounter();") == 1
assert "current_query->size_slots > SamplesQueryBank::BANK_SIZE" in actual_method
assert actual_method.index("PauseCounter();") < actual_method.index("ResetCounter();")

program = r"""
#include <cassert>
#include <cstddef>
#include <cstdio>
struct SamplesQueryBank { static constexpr std::size_t BANK_SIZE = 256; };
struct Query { std::size_t size_slots{}; };
struct Streamer {
    Query* current_query{};
    unsigned pause_count{};
    unsigned reset_count{};
    void PauseCounter() { ++pause_count; }
    void ResetCounter() { ++reset_count; current_query = nullptr; }
__CLOSE_METHOD__
};
int main() {
    Streamer s;
    s.CloseCounter();
    assert(s.pause_count == 1 && s.reset_count == 0);

    Query q{36};
    s.current_query = &q;
    s.CloseCounter();
    assert(s.pause_count == 2 && s.reset_count == 0 && s.current_query == &q);

    q.size_slots = 256;
    s.CloseCounter();
    assert(s.pause_count == 3 && s.reset_count == 0 && s.current_query == &q);

    q.size_slots = 257;
    s.CloseCounter();
    assert(s.pause_count == 4 && s.reset_count == 1 && s.current_query == nullptr);

    // The next submission does not reset a query already retired.
    s.CloseCounter();
    assert(s.pause_count == 5 && s.reset_count == 1);

    Query title_screen{16'384};
    s.current_query = &title_screen;
    s.CloseCounter();
    assert(s.pause_count == 6 && s.reset_count == 2 && s.current_query == nullptr);
    std::puts("SHARED_VULKAN_OCCLUSION_SUBMISSION_PASS");
}
""".replace("__CLOSE_METHOD__", actual_method.replace(" override", ""))
env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
compilers = list(dict.fromkeys(filter(None,
    (shutil.which("clang++"), shutil.which("g++")))))
assert compilers, "No host C++20 compiler"
with tempfile.TemporaryDirectory(prefix="eden-occlusion-submit-") as tmp:
    cpp = Path(tmp)/"occlusion.cpp"
    cpp.write_text(program)
    for compiler in compilers:
        for optimization in ("-O0", "-O2"):
            binary = Path(tmp)/(Path(compiler).name.replace("+","p")+optimization)
            built = subprocess.run(
                [compiler, "-std=c++20", optimization, "-Wall", "-Wextra",
                 "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                 str(cpp), "-o", str(binary)],
                env=env, capture_output=True, text=True, timeout=45)
            assert built.returncode == 0, (compiler, built.stderr[-2000:])
            ran = subprocess.run([str(binary)], env=env, capture_output=True,
                                 text=True, timeout=10)
            assert ran.returncode == 0, (compiler, ran.stderr[-2000:])
            assert "SHARED_VULKAN_OCCLUSION_SUBMISSION_PASS" in ran.stdout
            print("SHARED_VULKAN_OCCLUSION_SUBMISSION_PASS",
                  Path(compiler).name, optimization, flush=True)
