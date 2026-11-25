#!/usr/bin/env bash
# Build isolated, pinned RADV dependencies; never deploy or replace the old SDK.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
source "$root/tools/host-env.sh"
eden_host_env "$root"
refs=$(dirname "$root")
export PS5_MESA_FORK="$refs/mihawk-mesa-review"
export PS5_PAYLOAD_SDK_FORK="$refs/mihawk-sdk-review"
vulkan="$refs/mihawk-vulkan-review"

# Mihawk's pinned setup scripts retain upstream wget fallbacks for zlib and
# the base PayloadSDK release. Encore already restores those exact archives
# from vendor/objects while hydrating the main boilerplate. Seed the RADV cache
# from those verified local bytes so the standard PS5 build never reaches the
# upstream network branches.
bootstrap="$refs/ps5-native-app-boilerplate/.deps/native"
zlib_archive="$bootstrap/zlib/zlib-1.3.2.tar.gz"
sdk_archive="$bootstrap/ps5-payload-sdk.zip"
[[ -f "$zlib_archive" && -f "$sdk_archive" ]] || {
    echo "Vendored RADV bootstrap archives are missing; run offline make deps first" >&2
    exit 2
}
printf '%s  %s\n' bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16 "$zlib_archive" \
    | sha256sum --check --strict >/dev/null
printf '%s  %s\n' 8cfbc7cd5811e719eb4f0c47eea668d3dc7b40bc8ab11c4a5031d40c23ec02da "$sdk_archive" \
    | sha256sum --check --strict >/dev/null
mkdir -p "$vulkan/.deps/native/zlib"
install -m 0644 "$zlib_archive" "$vulkan/.deps/native/zlib/zlib-1.3.2.tar.gz"
install -m 0644 "$sdk_archive" "$vulkan/.deps/native/ps5-payload-sdk.zip"

pin() {
    python3 - "$root/tools/deps.json" "$1" <<'PY'
import json, sys
manifest, name = sys.argv[1], sys.argv[2]
data = json.load(open(manifest))
print(next(item["commit"] for item in data["items"] if item["name"] == name))
PY
}
for check in "ps5-vulkan-tools $vulkan" "ps5-mesa $PS5_MESA_FORK" "ps5-payload-sdk-fork $PS5_PAYLOAD_SDK_FORK"; do
    read -r name path <<< "$check"
    actual=$(git -C "$path" rev-parse HEAD)
    expected=$(pin "$name")
    [[ $actual == "$expected" ]] || {
        echo "$path is at $actual, expected $expected from tools/deps.json" >&2
        exit 1
    }
done
if [[ $(uname -s) == Darwin ]]; then
    jobs=${EDEN_BUILD_JOBS:-$(eden_host_jobs)}
else
    jobs=${EDEN_BUILD_JOBS:-24}
fi
[[ $jobs =~ ^[1-9][0-9]*$ ]] || { echo "Invalid EDEN_BUILD_JOBS: $jobs" >&2; exit 1; }
export BUILD_JOBS="$jobs" CMAKE_BUILD_PARALLEL_LEVEL="$jobs"
mkdir -p "$root/build/radv-tools"
# Upstream calls ninja directly; enforce the same bounded parallelism everywhere.
ninja_bin=$(command -v ninja)
printf '#!/bin/sh\nexec %s -j%s "$@"\n' "$ninja_bin" "$jobs" > "$root/build/radv-tools/ninja"
chmod +x "$root/build/radv-tools/ninja"
export NINJA="$root/build/radv-tools/ninja"

# Mihawk's build-radv.sh controls both native mesa_clc and target RADV Meson
# setup. Force the real Meson CLI no-download mode for every setup invocation;
# MESON_WRAP_MODE is not a Meson runtime contract and must not be relied on.
meson_bin=$(command -v meson)
meson_wrapper="$root/build/radv-tools/meson-nodownload"
cat > "$meson_wrapper" <<EOF
#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == setup ]]; then
    shift
    exec "$meson_bin" setup --wrap-mode=nodownload "\$@"
fi
exec "$meson_bin" "\$@"
EOF
chmod +x "$meson_wrapper"
export MESON="$meson_wrapper"

command -v ccache >/dev/null
# Cross compilers do not get Meson's automatic native ccache detection. Derive the two-line ccache
# adaptation temporarily, and always restore the pinned upstream file on exit so dependency repos
# remain clean and `git status` continues to mean something.
cross_ini="$vulkan/tooling/radv/ps5-cross.ini"
cross_base="$root/build/radv-tools/ps5-cross.ini.upstream"
git -C "$vulkan" show HEAD:tooling/radv/ps5-cross.ini > "$cross_base"
python3 - "$cross_ini" "$cross_base" <<'PY'
from pathlib import Path
import sys
current, base = map(Path, sys.argv[1:])
original = base.read_text()
derived = original
for lang, compiler in [('c', 'prospero-clang'), ('cpp', 'prospero-clang++')]:
    plain = f"{lang} = sdk / 'bin/{compiler}'"
    cached = f"{lang} = ['ccache', sdk / 'bin/{compiler}']"
    assert plain in derived, 'Unexpected pinned upstream cross compiler configuration'
    derived = derived.replace(plain, cached)
now = current.read_text()
assert now in (original, derived), 'Unexpected local changes in PS5_Vulkan ps5-cross.ini'
current.write_text(derived)
PY
restore_cross_ini() { cp "$cross_base" "$cross_ini"; }
trap restore_cross_ini EXIT
if [[ $(uname -s) == Darwin ]]; then
    # zlib configures Apple's `libtool -o` archive convention on Darwin, while
    # this pinned bootstrap intentionally substitutes llvm-ar. Give make the
    # matching llvm-ar operation without editing the pinned dependency tree.
    MAKEFLAGS=-e ARFLAGS=rcs bash "$vulkan/tools/setup-native-dependencies.sh"
    # Apple's current CLT linker cannot consume the SDK 27 TAPI arm64e.x1
    # descriptors on this host. Mesa's native generator tools use the tested
    # Homebrew LLVM 18 pair; the PS5 cross compiler remains defined by Meson.
    export CC=clang-18 CXX=clang++-18
    bash "$root/tools/prepare-macos-llvm-spirv.sh"
    spirv_prefix="$root/.local/spirv-llvm-translator-18"
    export PKG_CONFIG_PATH="$spirv_prefix/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
    export CMAKE_PREFIX_PATH="$spirv_prefix${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
else
    bash "$vulkan/tools/setup-native-dependencies.sh"
fi

# Mesa's RADV profile forces the zlib fallback subproject for its shader
# cache. Keep the exact 1.3.1 version requested by PS5_Mesa, but stage the
# source + matching WrapDB Meson metadata from our pinned vendor instead of
# allowing Meson to download zlib or its patch archive.
radv_zlib_vendor="$root/vendor/sources/zlib-1.3.1"
radv_zlib_stage="$vulkan/.deps/work/radv-src/subprojects/zlib-1.3.1"
for required in zlib.h zconf.h zutil.c meson.build meson_options.txt test/meson.build; do
    [[ -f "$radv_zlib_vendor/$required" ]] || {
        echo "Vendored RADV zlib 1.3.1 closure is incomplete: $required" >&2
        exit 2
    }
done
grep -Fq "ZLIB_VERSION \"1.3.1\"" "$radv_zlib_vendor/zlib.h" || {
    echo "Vendored RADV zlib source version mismatch" >&2
    exit 2
}
rm -rf "$radv_zlib_stage"
mkdir -p "$(dirname "$radv_zlib_stage")"
cp -a "$radv_zlib_vendor" "$radv_zlib_stage"
# No Meson wrap may contact an upstream server in the production PS5 build.
# build-radv.sh preserves subprojects/zlib-* when refreshing its Mesa tree;
# the MESON wrapper above enforces the actual CLI --wrap-mode=nodownload.

# Meson may leave a partial directory after a failed host configure. A later
# setup cannot reliably reuse it unless build.ninja was written.
for partial in "$vulkan/.deps/work/radv-clc-build" "$vulkan/.deps/work/radv-build-ps5-release"; do
    [[ ! -d $partial || -f $partial/build.ninja ]] || rm -rf "$partial"
done
# R343: all PS5-specific RADV sources are now complete, versioned files
# checked into this fork. The pinned Mihawk build first stages Mesa worktree;
# install those exact fork files before the final incremental Ninja pass.
# No source rewrite script runs in a production PS5 build.
bash "$vulkan/tools/build-radv.sh" release
python3 "$root/tools/install-vendored-radv.py" \
    "$vulkan/.deps/work/radv-src" \
    --provenance "$vulkan/.deps/native/radv-release/PROVENANCE.txt" \
    --repair-owned-stage
bash "$vulkan/tools/build-radv.sh" release
sha256sum "$vulkan/.deps/work/radv-src/src/vulkan/wsi/wsi_common_videoout.c" \
    > "$vulkan/.deps/native/radv-release/EDEN_WSI_SHA256"
# Stamp the complete maintained native compiler input set ONLY after the
# final incremental link succeeds. Each rebuilt binary must correspond to
# all twelve checked-in modified units, not just the WSI translation unit.
python3 -B "$root/tools/radv-active-inputs.py" --stamp \
    "$vulkan/.deps/work/radv-src" \
    "$vulkan/.deps/native/radv-release/lib/libvulkan_radeon.ps5.a" \
    "$vulkan/.deps/native/radv-release/EDEN_ACTIVE_INPUTS_SHA256"
