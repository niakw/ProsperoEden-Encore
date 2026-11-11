#!/usr/bin/env python3
"""R23 IPS/audren: exact minimal diffs and C++ source-extracted negative tests.

No PS5 ELF or actual guest FS/Audio IPC proof is implied.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
V=ROOT/"vendor/sources/eden/src"
IPS_ORIGINAL=V/"core/file_sys/ips_layer.cpp"
IPS_OWNER=ROOT/"vendor/encore-active/eden-core/src/core/file_sys/ips_layer.cpp"
AUDIO_ORIGINAL=V/"core/hle/service/audio/audio.cpp"
AUDIO_OWNER=ROOT/"headless/r23_audren_debug_ps5.cpp"
IPS_SHA="9d46549bf0fae3ec5fd0ab6c65bc432dcff68818"
AUDIO_SHA="c4332833042d7bca6309fdbe532637d80d90b4e6"
IPS_ACTIVE_SHA="f6687abf25ef2874c06c2523c530b5ba197e6d45"
REPLACE_AUDIO=(
 ("RegisterNamedService(\"audren:d\", std::make_shared<IAudioInManager>(system))",
  "RegisterNamedService(\"audren:d\", std::make_shared<IAudioRendererManagerForDebugger>(system))"),
)

def gitblob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def verify():
    assert gitblob(IPS_ORIGINAL)==IPS_SHA, "original IPS source changed"
    assert gitblob(IPS_OWNER)==IPS_ACTIVE_SHA, "maintained selected IPS source changed"
    source=IPS_OWNER.read_text()
    for k in ("std::vector<uint8_t> data;", "r.data.push_back(static_cast<uint8_t>(*it));",
              "magic.size() >= 3", "magic.size() >= 4",
              "IdentifyMagic(ips->ReadBytes(0x5))", "IsPatchRecord("):
        assert k in source, ("maintained IPS contract missing", k)
    assert gitblob(AUDIO_ORIGINAL)==AUDIO_SHA
    expected=AUDIO_ORIGINAL.read_text()
    for old,new in REPLACE_AUDIO:
        assert expected.count(old)==1 and expected.count(new)==0
        expected=expected.replace(old,new)
    actual=AUDIO_OWNER.read_text()
    start=actual.find("// SPDX-FileCopyrightText")
    assert start>=0 and actual[start:]==expected, "audren source changed"
    cm=(ROOT/"headless/CMakeLists.txt").read_text()
    for k in ("EDEN_MAINTAINED_IPS_LAYER", "eden_r23_ips_maintained_idx",
              "R23 selected IPS source changed", "hle/service/audio/audio.cpp",
              "r23_audren_debug_ps5.cpp"):
        assert k in cm, ("CMake selected owner missing", k)
    assert "r23_ips_layer_ps5.cpp" not in cm, "superseded IPS source reselected"
    print("R23_MAINTAINED_IPS_AND_AUDREN_SOURCE_OWNER_PASS")

def host(folder,name,code):
    inp,exe=folder/(name+".cpp"),folder/name
    inp.write_text(code)
    subprocess.run(
        ["clang++","-std=c++20","-O1","-g","-Wall","-Wextra","-Werror",
         "-fsanitize=address,undefined","-fno-omit-frame-pointer",
         str(inp),"-o",str(exe)],check=True,timeout=100,cwd=ROOT)
    subprocess.run([str(exe)],check=True,timeout=15,cwd=ROOT,
                   env={**os.environ,"ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1"})

def ips(folder):
    source=IPS_OWNER.read_text()
    start=source.index("enum class IPSFileType {")
    end=source.index("\nVirtualFile PatchIPS(",start)
    fragment=source[start:end]
    for required in ("magic.size() >= 3","magic.size() >= 4",
                     "IdentifyMagic(ips->ReadBytes(0x5))",
                     "if (in_data.empty())"):
        assert required in source,required
    code=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <span>
using u8=std::uint8_t;
namespace FileSys {
"""+fragment+r"""
}
int main(){
  using namespace FileSys;
  const std::array<u8,5> ips{'P','A','T','C','H'};
  const std::array<u8,5> ips32{'I','P','S','3','2'};
  const std::array<u8,5> invalid{'A','A','A','A','A'};
  const std::array<u8,3> eof{'E','O','F'};
  const std::array<u8,4> eeof{'E','E','O','F'};
  const std::array<u8,2> short_eof{'E','O'};
  assert(IdentifyMagic(ips)==IPSFileType::IPS);
  assert(IdentifyMagic(ips32)==IPSFileType::IPS32);
  assert(IdentifyMagic(invalid)==IPSFileType::Error);
  assert(IsEOF(IPSFileType::IPS,eof));
  assert(IsEOF(IPSFileType::IPS32,eeof));
  assert(!IsEOF(IPSFileType::IPS,short_eof));
  assert(!IsEOF(IPSFileType::IPS32,eof));
  assert(!IsEOF(IPSFileType::IPS,eeof));
}
"""
    host(folder,"ips",code)
    print("R23_IPS_EXTRACTED_MAGIC_EOF_HOST_ASAN_PASS")

def audren(folder):
    source=AUDIO_OWNER.read_text()
    matching=[x.strip() for x in source.splitlines()
              if 'RegisterNamedService("audren:d"' in x]
    assert len(matching)==1,("audren registration count",matching)
    code=r"""
#include <cassert>
#include <memory>
#include <string_view>
#include <type_traits>
namespace Core {struct System{};}
struct IAudioInManager { explicit IAudioInManager(Core::System&){} };
struct IAudioRendererManagerForDebugger {
    explicit IAudioRendererManagerForDebugger(Core::System&){}
};
struct Server {
    bool registered_correct{};
    template<class T>
    void RegisterNamedService(std::string_view name,std::shared_ptr<T> value) {
        assert(name=="audren:d" && value);
        registered_correct=std::is_same_v<T,IAudioRendererManagerForDebugger>;
    }
};
int main(){
  Core::System system;
  Server s;
  auto* server_manager=&s;
"""+matching[0]+r"""
  assert(s.registered_correct);
}
"""
    host(folder,"audren",code)
    print("R23_AUDREN_EXTRACTED_SERVICE_HOST_ASAN_PASS")

def main():
    verify()
    with tempfile.TemporaryDirectory(prefix="ab-r23-ips-") as dirname:
        ips(Path(dirname))
        audren(Path(dirname))
    print("R23_IPS_AUDREN_SELECTED_OWNER_HOST_PASS PS5_NOT_COMPILED=1")

if __name__=="__main__":
    try:
        main()
    except (AssertionError,OSError,ValueError,subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as err:
        print("R23_IPS_AUDREN_SELECTED_OWNER_HOST_FAIL",str(err),file=sys.stderr)
        sys.exit(1)
