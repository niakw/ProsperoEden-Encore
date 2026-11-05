#!/usr/bin/env python3
"""P1.3: parse true NS2 Sysmix and audio HLE owners with pinned Eden headers.

No native PS5 toolchain, audio device, runtime linking or game is exercised.
The source-extracted PCM ring and IPC fixtures perform separate behavior checks.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "vendor/encore-active/ns2-runtime/audio"
SOURCE = ROOT / "vendor/sources/eden/src"
files = [
    AUDIO / "core/hle/service/audio/nx2_sysmix.cpp",
    AUDIO / "core/hle/service/audio/audio.cpp",
]
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
assert "core/hle/service/audio/nx2_sysmix.cpp" in cmake
assert "list(APPEND eden_ns2_audio_sources" in cmake
assert "if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)" in cmake
assert "EDEN_FINAL_RELEASE_PROFILE" not in cmake
assert all(path.is_file() for path in files)
assert 'RegisterNamedService("audsmx:u"' in files[1].read_text()
assert 'RegisterNamedService("auddmg:u"' in files[1].read_text()
assert 'AudioCore::Sink::StreamType::Out' in files[0].read_text()
assert 'p.host->SetRingSize(NativeQueueHighWatermark * 2);' in files[0].read_text()
assert 'p.host->AppendBuffer(block, p.output);' in files[0].read_text()
assert 'p.host->GetQueueSize() >= NativeQueueHighWatermark' in files[0].read_text()
registry=(AUDIO / "core/hle/service/audio/nx2_sysmix_user_service.h").read_text()
assert "Result SetEngagedBatch(std::span<const u32> ids, bool engaged," in registry
assert "Result CreateBounded(Factory&& factory, u32& out_id," in registry
assert "std::scoped_lock lock{mutex};" in registry
assert "R_UNLESS(streams.size() < 32 && next_id != 0, ResultOutOfSessions);" in registry
assert "result = streams->SetEngagedBatch(" in registry
assert "streams->CreateBounded(" in registry
assert "catch (const std::bad_alloc&)" in registry
assert "python3 -B tools/ns2/check_native_sysmix_registry_host.py" in (
    ROOT / ".github/workflows/encore-core-preflight.yml").read_text()
assert "TryAppendOutputBlock(" not in files[0].read_text()
assert "MarkFaulted(" not in files[0].read_text()

includes = [AUDIO, SOURCE, ROOT / "vendor/encore-active/ns2-helpers/include",
            ROOT / "vendor/sources/fmt/include",
            ROOT / "vendor/sources/eden-cpm/opus/a3f0ec02b3/include"]
boost = ROOT / "vendor/sources/eden-cpm/boost/boost-1.90.0/libs"
if boost.is_dir():
    includes += sorted(boost.glob("*/include"))
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "A C++20 host compiler is required"
env = os.environ.copy()
extra = []
if sys.platform == "darwin":
    sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    libc = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk/usr/include/c++/v1")
    if sdk.is_dir() and libc.is_dir():
        env["SDKROOT"] = str(sdk)
        extra.extend(["-nostdinc++", "-isystem", str(libc)])
command = [compiler, "-std=c++20", "-fsyntax-only", "-DFMT_HEADER_ONLY",
           "-Wno-unused-parameter", "-Wno-unused-private-field", *extra]
command += ["-I" + str(include) for include in includes if include.is_dir()]
for opt in ("-O0", "-O2"):
    for file in files:
        done = subprocess.run([*command, opt, str(file)], capture_output=True,
                              text=True, timeout=90, env=env)
        assert done.returncode == 0, (
            file.relative_to(ROOT), opt, done.stderr[-7000:])
        print("P1_3_SYS_MIX_REAL_CPP_SYNTAX_PASS", file.name, opt, flush=True)
print("P1_3_SYS_MIX_REAL_CPP_SYNTAX_HOST_PASS owner_tus=2 ns1_unmodified=1")
