#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Package a compiled PS5 NSW2 research build without pretending it is release-qualified.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
cd "$root"
[[ ${EDEN_NS2_NATIVE_EXPERIMENTAL:-OFF} == ON ]] || {
  echo "NS2 packaging requires an explicitly opted-in native research engine" >&2; exit 2;
}
[[ ${EDEN_FINAL_RELEASE_PROFILE:-OFF} == OFF ]] || {
  echo "Release profile must be OFF for NS2 research packaging" >&2; exit 2;
}
scratch=$(cat .local/headless-cache)
cache="$scratch/native-local/CMakeCache.txt"
[[ -f "$cache" && -f "$scratch/native-local/bin/eden-headless" ]] || {
  echo "Missing compiled native ELF/CMakeCache" >&2; exit 2;
}
python3 - "$cache" "$root/headless/CMakeLists.txt" <<'PY'
import pathlib, re, sys
cache=pathlib.Path(sys.argv[1]).read_text()
cmake=pathlib.Path(sys.argv[2]).read_text()
flags=re.findall(r"option\((EDEN_NS2_[A-Z0-9_]+)\s",cmake)
assert len(flags)==len(set(flags))==22
for name in flags:
    assert f"{name}:BOOL=ON" in cache, f"Research ELF lacks {name}=ON"
for item in ("EDEN_PS5_VULKAN:BOOL=ON","EDEN_VULKAN_DRIVER:STRING=RADV",
             "EDEN_FINAL_RELEASE_PROFILE:BOOL=OFF","EDEN_PS5_OPENGL:BOOL=ON"):
    assert item in cache, f"Research build profile mismatch: {item}"
print("NS2_RESEARCH_COMPILED_PROFILE_PASS",len(flags))
PY
# Stage into a separate title directory; never touch build/release or main's artifacts.
export EDEN_PACKAGE_DIR="$root/build/ns2-research/PPSA99008"
export PS5_ELEVATION_SDK="$root/../ps5-native-app-boilerplate/.deps/native/ps5-payload-sdk"
rm -rf "$EDEN_PACKAGE_DIR"
bash tools/package-headless-native.sh --integration
python3 - "$EDEN_PACKAGE_DIR" <<'PY'
from pathlib import Path
import json, subprocess, hashlib, sys
app=Path(sys.argv[1])
required=("eboot.bin","core-homebrew.nro","sandbox-elevator.elf",
          "sce_sys/param.json","sce_module/libc.prx","ui/lang/fr-FR.po",
          "network-hosts.txt","legal/LICENSE")
for name in required:
    path=app/name
    assert path.is_file() and path.stat().st_size>0,name
param=json.loads((app/"sce_sys/param.json").read_text())
assert param["titleId"]=="PPSA99008"
assert param["localizedParameters"]["en-US"]["titleName"]=="Prospero.Eden Encore"
git=lambda *args: subprocess.check_output(["git",*args],text=True).strip()
receipt={
 "app":"Prospero.Eden Encore",
 "title_id":"PPSA99008",
 "source_commit":git("rev-parse","HEAD"),
 "vendor_commit":git("-C","vendor","rev-parse","HEAD"),
 "build_variant":"NS1/NS2 experimental PS5 research",
 "ns2_native_compiled":True,
 "ns1_regressions_qualified":False,
 "ns2_gameplay_qualified":False,
 "hardware_qualified":False,
 "release":False,
 "eboot_sha256":hashlib.sha256((app/"eboot.bin").read_bytes()).hexdigest(),
 "core_homebrew_sha256":hashlib.sha256((app/"core-homebrew.nro").read_bytes()).hexdigest(),
 "compiled_cmake_profile_sha256":hashlib.sha256(
     (app.parent.parent.parent/"headless-native/CMakeCache.txt").read_bytes()
 ).hexdigest(),
}
out=app.parent/"NS2_RESEARCH_BUILD_RECEIPT.json"
out.write_text(json.dumps(receipt,indent=2)+"\n")
print("NS2_RESEARCH_STAGING_PASS",app,receipt["source_commit"])
PY
