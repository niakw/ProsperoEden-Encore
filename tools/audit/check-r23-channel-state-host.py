#!/usr/bin/env python3
"""R23 #146 source-compiled host default initialization, not PS5 proof."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vendor/sources/eden/src/video_core/control/channel_state_cache.h"
PATCHED = ROOT / "headless/r23_channel_state_cache_ps5.h"
COMMENT = ("// PS5 source owner for upstream Eden #4406: initialize channel_state on construction.\n"
           "// Exact baseline: vendor/sources/eden/src/video_core/control/channel_state_cache.h\n"
           "// Only this pointer default initializer differs from the pinned header.\n")

def main():
    original = SOURCE.read_text()
    corrected = PATCHED.read_text()
    old = "    P* channel_state;\n"
    new = "    P* channel_state = nullptr;\n"
    assert original.count(old) == 1
    assert corrected.count(new) == 1
    assert corrected.replace(COMMENT, "", 1) == original.replace(old, new, 1)
    cmake = (ROOT / "headless/CMakeLists.txt").read_text()
    assert "r23_channel_state_cache_ps5.h" in cmake
    assert 'include/video_core/control/channel_state_cache.h" COPYONLY' in cmake
    assert 'target_include_directories(video_core BEFORE PRIVATE "' in cmake
    assert 'target_include_directories(core BEFORE PRIVATE "' in cmake

    with tempfile.TemporaryDirectory(prefix="r23-channel-") as directory:
        root = Path(directory)
        (root / "common/container").mkdir(parents=True)
        (root / "video_core/control").mkdir(parents=True)
        (root / "common/common_types.h").write_text(
            "#pragma once\n#include <cstdint>\nusing s32=std::int32_t; using u64=std::uint64_t;\n")
        (root / "common/container/unordered_map.h").write_text(
            "#pragma once\n#include <unordered_map>\n"
            "namespace Common {template<class K,class V> using unordered_map=std::unordered_map<K,V>;}\n")
        (root / "video_core/control/channel_state_cache.h").write_text(corrected)
        source = root / "test.cpp"
        binary = root / "test"
        source.write_text(r"""
#include <cassert>
#include <memory>
#include "video_core/control/channel_state_cache.h"
namespace VideoCommon {
template<class P> ChannelSetupCaches<P>::~ChannelSetupCaches()=default;
template<class P> void ChannelSetupCaches<P>::CreateChannel(Tegra::Control::ChannelState&){}
template<class P> void ChannelSetupCaches<P>::BindToChannel(s32){}
}
struct Entry { int value; };
struct Probe : VideoCommon::ChannelSetupCaches<Entry> {
    bool Null() const { return channel_state == nullptr; }
};
int main(){
    for(int i=0;i<1024;++i){auto p=std::make_unique<Probe>(); assert(p->Null());}
    Probe stack; assert(stack.Null());
}
""")
        subprocess.run(["clang++", "-std=c++20", "-O1", "-g", "-Wall", "-Wextra",
                        "-Werror", "-fsanitize=address,undefined",
                        "-fno-omit-frame-pointer", "-I", str(root), str(source),
                        "-o", str(binary)], check=True, timeout=80)
        subprocess.run([str(binary)], check=True, timeout=15,
                       env={**os.environ,"ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1"})
    print("R23_MAXWELL_CHANNEL_POINTER_SOURCE_ASAN_UBSAN_PASS",
          "only_one_initializer_changed=1", "real_PS5_include_unproven=1")

if __name__ == "__main__":
    try:
        main()
    except (OSError, AssertionError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as error:
        print("R23_MAXWELL_CHANNEL_HOST_FAIL", error, file=sys.stderr)
        sys.exit(1)
