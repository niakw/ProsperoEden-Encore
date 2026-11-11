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
IPS_OWNER=ROOT/"headless/r23_ips_layer_ps5.cpp"
AUDIO_ORIGINAL=V/"core/hle/service/audio/audio.cpp"
AUDIO_OWNER=ROOT/"headless/r23_audren_debug_ps5.cpp"
IPS_SHA="9d46549bf0fae3ec5fd0ab6c65bc432dcff68818"
AUDIO_SHA="c4332833042d7bca6309fdbe532637d80d90b4e6"
REPLACE_IPS=(
 ("#include <span>\n", "#include <span>\n#include <vector>\n"),
 ("magic.size() > 3 && std::memcmp(magic.data(), \"EOF\", 3) == 0",
  "magic.size() >= 3 && std::memcmp(magic.data(), \"EOF\", 3) == 0"),
 ("magic.size() > 4 && std::memcmp(magic.data(), \"EEOF\", 4) == 0",
  "magic.size() >= 4 && std::memcmp(magic.data(), \"EEOF\", 4) == 0"),
 ("    auto in_data = in->ReadAllBytes();\n    auto const type = IdentifyMagic(in_data);\n    if (type == IPSFileType::Error)\n        return nullptr;\n\n",
  "    const auto type = IdentifyMagic(ips->ReadBytes(0x5));\n    if (type == IPSFileType::Error)\n        return nullptr;\n\n    auto in_data = in->ReadAllBytes();\n    if (in_data.size() == 0)\n        return nullptr;\n\n"),
 ("""struct IPSwitchRecord {
    std::array<uint8_t, 256 - sizeof(size_t)> data;
    size_t count;
};""", """struct IPSwitchRecord {
    std::vector<uint8_t> data;
};"""),
 ("static IPSwitchRecord EscapeStringSequences(std::string_view sv) {\n    IPSwitchRecord r{};\n    for (auto it = sv.cbegin(); it < sv.cend(); ) {\n        if (*it == '\\\\' && it + 1 < sv.cend()) {\n            switch (it[1]) {\n            case 'a': r.data[r.count] = '\\a'; break;\n            case 'b': r.data[r.count] = '\\b'; break;\n            case 'e': r.data[r.count] = '\\e'; break;\n            case 'f': r.data[r.count] = '\\f'; break;\n            case 'n': r.data[r.count] = '\\n'; break;\n            case 'r': r.data[r.count] = '\\r'; break;\n            case 't': r.data[r.count] = '\\t'; break;\n            case 'v': r.data[r.count] = '\\v'; break;\n            case '?': r.data[r.count] = '\\?'; break;\n            default: r.data[r.count] = it[1]; break;\n            }\n            ++r.count;\n            it += 2;\n        } else {\n            ++r.count;\n            ++it;\n        }\n    }\n    return r;\n}", "static IPSwitchRecord EscapeStringSequences(std::string_view sv) {\n    IPSwitchRecord r{};\n    for (auto it = sv.cbegin(); it < sv.cend(); ) {\n        if (*it == '\\\\' && it + 1 < sv.cend()) {\n            switch (it[1]) {\n            case 'a': r.data.push_back('\\a'); break;\n            case 'b': r.data.push_back('\\b'); break;\n            case 'e': r.data.push_back('\\e'); break;\n            case 'f': r.data.push_back('\\f'); break;\n            case 'n': r.data.push_back('\\n'); break;\n            case 'r': r.data.push_back('\\r'); break;\n            case 't': r.data.push_back('\\t'); break;\n            case 'v': r.data.push_back('\\v'); break;\n            case '?': r.data.push_back('\\?'); break;\n            default: r.data.push_back(it[1]); break;\n            }\n            it += 2;\n        } else {\n            r.data.push_back(*it);\n            ++it;\n        }\n    }\n    return r;\n}"),
 ("""std::memcpy(r.data.data(), hs.data(), hs.size());
                    r.count = hs.size();""", """r.data.resize(hs.size());
                    std::memcpy(r.data.data(), hs.data(), hs.size());"""),
 ("auto replace_size = record.second.count;", "auto replace_size = record.second.data.size();"),
)
REPLACE_AUDIO=(
 ("RegisterNamedService(\"audren:d\", std::make_shared<IAudioInManager>(system))",
  "RegisterNamedService(\"audren:d\", std::make_shared<IAudioRendererManagerForDebugger>(system))"),
)

def gitblob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def verify():
    pairs=((IPS_ORIGINAL,IPS_OWNER,IPS_SHA,REPLACE_IPS),
           (AUDIO_ORIGINAL,AUDIO_OWNER,AUDIO_SHA,REPLACE_AUDIO))
    for original,selected,sha,fixes in pairs:
        assert gitblob(original)==sha,("unpinned source",original)
        before=original.read_text()
        expected=before
        for old,new in fixes:
            assert expected.count(old)==1 and expected.count(new)==0,(original,old)
            expected=expected.replace(old,new)
        actual=selected.read_text()
        start=actual.find("// SPDX-FileCopyrightText")
        assert start>=0 and actual[start:]==expected,("unreviewed source drift",selected)
    cm=(ROOT/"headless/CMakeLists.txt").read_text()
    for marker in (
        'foreach(eden_r23_core_owner IN ITEMS',
        '"file_sys/ips_layer.cpp"',
        '"hle/service/audio/audio.cpp"',
        'list(FIND eden_r23_core_sources',
        'list(REMOVE_ITEM eden_r23_core_sources',
        "r23_ips_layer_ps5.cpp","r23_audren_debug_ps5.cpp",
        "R23 selected core source moved:"):
        assert marker in cm,("no exact full-TU owner",marker)
    print("R23_IPS_AUDREN_TWO_EXACT_SOURCE_OWNERS_PASS")

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
                     "if (in_data.size() == 0)"):
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
