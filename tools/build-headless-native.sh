#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
# Only one native PS5 configuration is compiled; --graphics is a retained
# spelling for existing CI/package callers, not a different binary profile.
if [[ $# -gt 1 || ( $# == 1 && $1 != --graphics ) ]]; then
    echo "Usage: tools/build-headless-native.sh [--graphics]" >&2
    exit 2
fi
devices=OFF
graphics=ON
probe=OFF
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
source "$root/tools/host-env.sh"
eden_host_env "$root"
jobs=${EDEN_BUILD_JOBS:-$(eden_host_jobs)}
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid EDEN_BUILD_JOBS: $jobs" >&2; exit 1; }
command -v ninja >/dev/null
cache=$(command -v ccache)
cd "$root"
# Source provenance travels with the app; the scratch tree is a detached
# upstream snapshot, so derive the SHA from our actual Encore checkout.
source_commit=$(git -C "$root" rev-parse --verify HEAD)
# Do not conflate GitHub run numbers with Encore's R-revisions.
build_label="${EDEN_LAUNCHER_BUILD_LABEL:-$(python3 -B "$root/tools/ci/derive-encore-build-label.py")}"
[[ "$build_label" =~ ^R[0-9]+$ ]] || { echo "Invalid Encore build label: $build_label" >&2; exit 1; }
# Native contentVersion advances with the compiled R revision.
native_version="$(python3 -B "$root/tools/ci/native-content-version.py" "$build_label")"
[[ "$source_commit" =~ ^[0-9a-f]{40}$ ]] || {
    echo "Cannot attest the native Encore source commit" >&2
    exit 1
}
bash tools/build-core-fixture.sh
scratch=$(cat .local/headless-cache)
[[ "$scratch" == "${XDG_CACHE_HOME:-$HOME/.cache}"/ps5-eden-headless.* && "$(cd -- "$(cat "$scratch/owner")" && pwd -P)" == "$root" ]]
# Static release preflight has no extracted Eden source yet. At this later
# native stage, enforce patch applicability to the actual pinned upstream.
if [[ ${EDEN_SKIP_SOURCE_CHECKS:-0} != 1 && ${EDEN_SKIP_PREBUILD_SOURCE_CHECKS:-0} != 1 ]]; then
    python3 -B "$root/tools/check-dummy-thread-waits.py" --require-pinned-source
    python3 -B "$root/tools/check-dynarmic-icache.py" --require-pinned-source
fi
# Cache the read-only native dependency trees beside the upstream sources.
# Repeated header checks across /mnt/c took minutes before compilation began.
if [[ ! -f "$scratch/sdk/.complete" ]]; then
    mkdir -p "$scratch/sdk"
    cp -a "$root/../ps5-native-app-boilerplate/.deps/native/ps5-payload-sdk/target" "$scratch/sdk/"
    touch "$scratch/sdk/.complete"
fi
if [[ ! -f "$scratch/cdeps/.complete" ]]; then
    mkdir -p "$scratch/cdeps"
    cp -a "${EDEN_CDEPS_SOURCE:-$root/.deps/pacbrew-0.40.2/opt/ps5-payload-sdk/target/user/homebrew}/." "$scratch/cdeps/"
    touch "$scratch/cdeps/.complete"
fi
export PS5_PAYLOAD_SDK="$scratch/sdk"
export EDEN_NATIVE_C_DEPS="$scratch/cdeps"
export PKG_CONFIG_LIBDIR="$scratch/empty-pkgconfig"
export PKG_CONFIG_PATH=
mkdir -p "$PKG_CONFIG_LIBDIR"
cdeps="$EDEN_NATIVE_C_DEPS"
test -f "$cdeps/lib/libcrypto.a"
python3 -B "$root/tools/materialize-openssl-cert.py"     "$scratch/source/.patch/openssl/0001-add-bundled-cert.patch"     "$cdeps/include/openssl/cert.h"
ffmpeg="$scratch/ffmpeg-native/install"
test -f "$ffmpeg/lib/libavcodec.a" || { echo 'Run tools/build-headless-ffmpeg.sh first.' >&2; exit 1; }
# A fresh Git checkout gives every fork-owned source a new mtime, which makes a restored Ninja
# tree rebuild it even when its bytes did not change. Preserve a content+mtime manifest inside the
# cached scratch tree: matching files recover their previous mtime, while changed files keep the
# fresh checkout mtime and are rebuilt normally. Missing objects are still rebuilt by Ninja.
python3 -B - "$root" "$scratch/fork-source-stamps.json" <<'PY_STAMPS'
import hashlib, json, os, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1])
manifest_path = pathlib.Path(sys.argv[2])
previous = {}
try:
    previous = json.loads(manifest_path.read_text())
except (FileNotFoundError, json.JSONDecodeError, OSError):
    pass

tracked = subprocess.check_output(
    ['git', '-C', str(root), 'ls-files', '-z', 'headless'], text=False
).split(b'\0')
extensions = {'.c', '.cc', '.cpp', '.h', '.hpp', '.inc', '.cmake'}
files = []
for raw in tracked:
    if not raw:
        continue
    rel = raw.decode()
    path = root / rel
    if not path.is_file():
        continue
    if path.suffix not in extensions and path.name != 'CMakeLists.txt':
        continue
    files.append((rel, path))

current = {}
restored = 0
for rel, path in files:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    old = previous.get(rel)
    if isinstance(old, dict) and old.get('sha256') == digest:
        try:
            mtime_ns = int(old['mtime_ns'])
            os.utime(path, ns=(mtime_ns, mtime_ns))
            restored += 1
        except (KeyError, ValueError, OSError):
            pass
    stat = path.stat()
    current[rel] = {'sha256': digest, 'mtime_ns': stat.st_mtime_ns}

manifest_path.parent.mkdir(parents=True, exist_ok=True)
tmp = manifest_path.with_suffix('.new')
tmp.write_text(json.dumps(current, sort_keys=True, separators=(',', ':')) + '\n')
tmp.replace(manifest_path)
print(f'Encore incremental source stamps: {restored}/{len(files)} restored')
PY_STAMPS


# The native PS5 binary uses one source graph and one renderer profile.
# No release/DEV/P5 selector may alter the compiled program.
cmake -S "$scratch/source" -B "$scratch/native-local" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$root/headless/ps5.cmake" -DPS5_NATIVE=ON \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_LTO=OFF -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DEDEN_ENCORE_SOURCE_COMMIT="$source_commit" \
    -DEDEN_LAUNCHER_BUILD_LABEL="$build_label" \
    -DEDEN_LAUNCHER_PACKAGE_VERSION="$native_version" \
    -DEDEN_PS5_VULKAN=ON \
    -DEDEN_VULKAN_DRIVER=RADV \
    -DCMAKE_C_COMPILER_LAUNCHER="$cache" -DCMAKE_CXX_COMPILER_LAUNCHER="$cache" \
    -DCMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH=ON \
    -DCMAKE_PROJECT_yuzu_INCLUDE="$root/headless/inject.cmake" \
    -DENABLE_QT=OFF -DYUZU_CMD=OFF -DYUZU_ROOM=OFF -DYUZU_ROOM_STANDALONE=OFF \
    -DYUZU_TESTS=OFF -DBUILD_TESTING=OFF -DENABLE_OPENGL="$graphics" -DEDEN_PS5_OPENGL="$graphics" -DENABLE_CUBEB=OFF \
    -DENABLE_WEB_SERVICE=OFF -DENABLE_LIBUSB=OFF -DYUZU_CRASH_DUMPS=OFF \
    -U 'FFmpeg_*' -DYUZU_USE_EXTERNAL_FFMPEG=OFF -DFFMPEG_DIR="$ffmpeg" \
    -DOPENSSL_INCLUDE_DIR="$cdeps/include" -DOPENSSL_SSL_LIBRARY="$cdeps/lib/libssl.a" \
    -DOPENSSL_CRYPTO_LIBRARY="$cdeps/lib/libcrypto.a" -DOpenSSL_FORCE_SYSTEM=ON \
    -DZLIB_INCLUDE_DIR="$cdeps/include" -DZLIB_LIBRARY="$cdeps/lib/libz.a" \
    -DENABLE_WERROR=OFF -Dzstd_FORCE_BUNDLED=ON -DBoost_FORCE_BUNDLED=ON -Dfmt_FORCE_BUNDLED=ON \
    -DDYNARMIC_ENABLE_NO_EXECUTE_SUPPORT=ON -DDYNARMIC_IGNORE_ASSERTS=OFF \
    -DSDL_UNIX_CONSOLE_BUILD=ON -DSDL_OPENGL=OFF -DSDL_OPENGLES=OFF -DSDL_RENDER=OFF -DSDL_GPU=OFF

# CMake can finish generation even when its resulting Ninja graph declares
# the same output twice (for example maintained Vulkan source/header inputs).
# Parse the REAL PS5 graph before running the expensive host validators; -t
# targets executes no compiler or shader generator.
echo "Checking native Ninja graph for duplicate output declarations"
ninja -C "$scratch/native-local" -t targets all >/dev/null
echo "ENCORE_NATIVE_NINJA_GRAPH_PASS"

python3 -B "$root/headless/check_slab_lifetime.py" \
    "$scratch/native-local/headless/include/core/hle/kernel/slab_helpers.h" \
    "$scratch/source/src/core/hle/kernel/slab_helpers.h"

# All authored Python generators must parse before expensive native translation.
# This does not run tests or execute any generator side effects.
python3 -B "$root/tools/check-python-source-syntax.py"

# The same native source syntax gate applies to every PS5 build.
if [[ ${EDEN_SKIP_PREBUILD_SOURCE_CHECKS:-0} != 1 ]]; then
    python3 -B "$root/tools/check-native-source-syntax.py" "$scratch/native-local"
fi

# Run every source/harness check that only needs the configured/generated source tree BEFORE the
# expensive native compile. A stale source extraction should fail in minutes, not after a 40-minute
# build. Development builds intentionally skip these release-shape checks.
if [[ ${EDEN_SKIP_SOURCE_CHECKS:-0} != 1 && ${EDEN_SKIP_PREBUILD_SOURCE_CHECKS:-0} != 1 ]]; then
    python3 -B "$root/headless/check_audio_shutdown.py" "$scratch/native-local/headless/core.cpp" "$scratch/source/src/core/core.cpp"
    python3 -B "$root/tools/check-load-failure.py"
    python3 -B "$root/tools/check-legacy-migration.py"
    python3 -B "$root/tools/check-storage-contract.py"
    python3 -B "$root/tools/check-nso-memory.py"
    python3 -B "$root/tools/check-performance.py"
    python3 -B "$root/tools/check-native-fiber-stack-host.py"
    python3 -B "$root/tools/check-startup-performance.py"
    python3 -B "$root/tools/check-worker-affinity.py"
    python3 -B "$root/tools/check-tsc-fallback.py"
    python3 -B "$root/tools/check-jit-protection.py"
    python3 -B "$root/tools/check-jit-allocator.py"
    python3 -B "$root/tools/check-jit-patch-lookup.py"
    python3 -B "$root/tools/check-jit-assert.py"
    python3 -B "$root/tools/check-crash-report.py"
    if [[ "$graphics" == ON ]]; then
        python3 -B "$root/tools/check-native-gpu-thread.py"
        python3 -B "$root/tools/check-gpu-producer-stop.py"
        python3 -B "$root/tools/check-gpu-sync-stop.py"
        python3 -B "$root/tools/check-nvdrv-process-lifetime.py"
        python3 -B "$root/tools/check-integer-buffer-clear.py"
        python3 -B "$root/tools/check-game-capture-shutdown.py"
    fi
    python3 -B "$root/tools/check-hud.py"
    python3 -B "$root/tools/check-game-frame-summary.py"
fi

echo "Building Eden with $jobs parallel jobs"
# The native build is expensive to prepare. If independent C++ files fail,
# finish every buildable Ninja edge (-k 0) so one CI run reports ALL compiler
# errors instead of hiding the next failure behind the first one. Ninja still
# exits nonzero and packaging never runs after a failed compilation.
cmake --build "$scratch/native-local" --target eden-headless core -j "$jobs" -- -k 0

# These two checks intentionally require the compiled dependency graph/native machine code.
python3 -B "$root/tools/check-sparse-header.py" "$scratch/native-local"
if [[ ${EDEN_SKIP_SOURCE_CHECKS:-0} != 1 && "$probe" == OFF ]]; then
    python3 -B "$root/tools/check-exclusive-monitor.py"
fi
