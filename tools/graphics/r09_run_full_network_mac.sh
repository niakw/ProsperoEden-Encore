#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Mac M1/M2: real attempt of R09 Original entire Vulkan session.
# IMPORTANT: legacy linked 2026-11-08 Linux amd64 binary, not a new build.
# Proprietary DLL, tensor pack, capture and readback never leave the Mac.
set -euo pipefail
umask 077

usage() {
  cat <<'EOF'
Usage:
  bash tools/graphics/r09_run_full_network_mac.sh \
    "$HOME/Downloads/nvngx_dlssnr.dll.zip" \
    "$HOME/Downloads/real-game-screenshot.png"

Second argument optional: if omitted, capture the Mac screen locally.
The user file must be a Windows NVIDIA DLL or ZIP containing it.
This script executes the real full-network ENTRYPOINT (not the old R09
partial fixture runner). A finished readback is not proof of 152 correct
operations, nor an independently validated NVIDIA-quality image.
Requires: macOS, Docker (running), gh CLI (authenticated), python3.
EOF
}
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then usage; exit 0; fi
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "R09_MAC_HOST_REQUIRED: this wrapper is intended for macOS." >&2
  exit 64
fi
if [[ $# -gt 2 ]]; then usage >&2; exit 64; fi

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
dll_input="${1:-$HOME/Downloads/nvngx_dlssnr.dll.zip}"
capture_input="${2:-}"
github_repo="niakw/ProsperoEden-Encore"
linked_run=42465459699
binary_sha256="7f41403249b594ea6ad9d3a00127384845bab3f0940e6ae275c87a8877e6fbe5"
image="eden-r09-original-host:ubuntu2404-amd64"

for tool in docker gh python3 shasum; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "R09_MAC_MISSING_TOOL=$tool" >&2
    [[ "$tool" == "gh" ]] && echo "Install with brew install gh; then gh auth login" >&2
    exit 65
  fi
done
docker info >/dev/null 2>&1 || {
  echo "R09_MAC_DOCKER_NOT_RUNNING: start Docker Desktop or Colima." >&2
  exit 66
}
gh auth status --hostname github.com >/dev/null 2>&1 || {
  echo "R09_MAC_GH_NOT_AUTHENTICATED: run gh auth login first." >&2
  exit 67
}
if [[ ! -f "$repo/headless/nr_dll_model_import.h" ||
      ! -f "$repo/tools/graphics/r09_private_model_import.cpp" ||
      ! -f "$repo/vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/nr_rdna2_model_manifest.h" ]]; then
  echo "R09_MAC_REPO_NOT_UPDATED: update main and vendor before running." >&2
  exit 68
fi
if [[ ! -f "$dll_input" || -L "$dll_input" ]]; then
  echo "R09_MAC_DLL_MISSING_OR_SYMLINK=$dll_input" >&2
  exit 69
fi

base="$HOME/.cache/eden-encore-r09-private"
mkdir -p "$base"
chmod 700 "$base"
work="$(mktemp -d "$base/full-network-XXXXXXXX")"
chmod 700 "$work"
mkdir -p "$work/download" "$work/bin" "$work/docker-context"
cleanup() {
  # Only the public runner, logs, previews and capture are retained.
  rm -f "$work/nvngx_dlssnr.dll" "$work/original.nrmodel" \
        "$work/original.nrmodel.importing"
}
trap cleanup EXIT
echo "R09_PRIVATE_WORK=$work"
echo "R09_ENGINE_MAIN=$(git -C "$repo" rev-parse --short HEAD)"
echo "R09_VENDOR=$(git -C "$repo/vendor" rev-parse --short HEAD)"

python3 - "$dll_input" "$work/nvngx_dlssnr.dll" <<'PY'
import hashlib, pathlib, shutil, sys, zipfile
src, dst = map(pathlib.Path, sys.argv[1:])
if src.is_symlink() or not src.is_file():
    raise SystemExit("R09_PRIVATE_DLL_NOT_A_REGULAR_FILE")
if zipfile.is_zipfile(src):
    with zipfile.ZipFile(src) as archive:
        files = [i for i in archive.infolist()
                 if not i.is_dir()
                 and pathlib.PurePosixPath(i.filename).name.lower() == "nvngx_dlssnr.dll"]
        if len(files) != 1 or files[0].file_size > 200_000_000:
            raise SystemExit("R09_PRIVATE_ZIP_REQUIRES_ONE_BOUNDED_NVIDIA_DLL")
        with archive.open(files[0]) as incoming, dst.open("xb") as out:
            shutil.copyfileobj(incoming, out)
else:
    if src.suffix.lower() != ".dll" or src.stat().st_size > 200_000_000:
        raise SystemExit("R09_PRIVATE_INPUT_NOT_DLL_OR_ZIP")
    with src.open("rb") as incoming, dst.open("xb") as out:
        shutil.copyfileobj(incoming, out)
length = dst.stat().st_size
if length < 1_000_000:
    raise SystemExit("R09_PRIVATE_DLL_TOO_SMALL")
print("R09_PRIVATE_DLL_BYTES=" + str(length))
print("R09_PRIVATE_DLL_SHA256=" + hashlib.sha256(dst.read_bytes()).hexdigest())
PY

if [[ -n "$capture_input" ]]; then
  if [[ ! -f "$capture_input" || -L "$capture_input" ]]; then
    echo "R09_MAC_CAPTURE_MISSING_OR_SYMLINK=$capture_input" >&2
    exit 70
  fi
  if [[ "$capture_input" == *.rgba8 ]]; then
    cp "$capture_input" "$work/capture-source.rgba8"
    capture_is_raw=1
  else
    cp "$capture_input" "$work/capture-source.image"
    capture_is_raw=0
  fi
else
  echo "R09_MAC_CAPTURE=local_mac_screen (NOT a game-render reference)"
  screencapture -x -t png "$work/capture-source.image"
  [[ -s "$work/capture-source.image" ]] || {
    echo "R09_MAC_SCREEN_CAPTURE_FAILED: specify a real screenshot file." >&2
    exit 70
  }
  capture_is_raw=0
fi

echo "R09_FETCHING_PREVIOUSLY_LINKED_PUBLIC_BINARY_RUN=$linked_run"
gh run download "$linked_run" -R "$github_repo" \
  -n r09-public-host-vulkan-runner -D "$work/download"
binary="$(find "$work/download" -type f -name r09-full-gpu-host -print -quit)"
if [[ -z "$binary" ]]; then
  echo "R09_MAC_ARTIFACT_MISSING_OR_EXPIRED" >&2
  exit 71
fi
actual_sha256="$(shasum -a 256 "$binary" | awk '{print $1}')"
if [[ "$actual_sha256" != "$binary_sha256" ]]; then
  echo "R09_MAC_BINARY_SHA256_MISMATCH=$actual_sha256" >&2
  exit 72
fi
cp "$binary" "$work/bin/r09-full-gpu-host"
chmod 700 "$work/bin/r09-full-gpu-host"
echo "R09_PINNED_PUBLIC_BINARY_SHA256_PASS=$actual_sha256"
echo "R09_PINNED_PUBLIC_BINARY=engine_756e80c_vendor_dfd6f3f"
echo "R09_WARNING: this host binary predates the direct-DLL and exclusive-readback patches."
echo "R09_DOCKER_BUILD=public_dependencies_only (no proprietary input in image)"
docker build --platform linux/amd64 \
  -f "$repo/tools/graphics/Dockerfile.r09-full-host" \
  -t "$image" "$work/docker-context"

memory="$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)"
if [[ "$memory" =~ ^[0-9]+$ ]] && (( memory > 0 && memory < 5368709120 )); then
  echo "R09_WARNING_DOCKER_MEMORY_LOW_BYTES=$memory (full 1080p neural graph may OOM)"
fi

echo "R09_FULL_NETWORK_ATTEMPT_START"
set +e
docker run --rm --init --platform linux/amd64 \
  --mount "type=bind,source=$repo,target=/repo,readonly" \
  --mount "type=bind,source=$work,target=/private" \
  -e "R09_CAPTURE_IS_RAW=$capture_is_raw" \
  -e LP_NUM_THREADS=2 -e GALLIUM_NUM_THREADS=2 \
  "$image" bash -euo pipefail -c '
    test "$(uname -m)" = "x86_64"
    g++ -std=c++20 -O1 -Wall -Wextra -Werror \
      -I/repo/headless -I/repo/extras/graphics \
      -I/repo/vendor/encore-active/eden-vulkan/include \
      /repo/tools/graphics/r09_private_model_import.cpp \
      -o /private/bin/r09-private-model-import
    /private/bin/r09-private-model-import \
      /private/nvngx_dlssnr.dll /private/original.nrmodel
    if [ "$R09_CAPTURE_IS_RAW" = 1 ]; then
      cp /private/capture-source.rgba8 /private/capture-1920x1080.rgba8
    else
      ffmpeg -hide_banner -nostdin -loglevel error -y \
        -i /private/capture-source.image \
        -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,format=rgba" \
        -frames:v 1 -pix_fmt rgba -f rawvideo \
        /private/capture-1920x1080.rgba8
    fi
    test "$(stat -c %s /private/capture-1920x1080.rgba8)" = "8294400"
    icd="$(find /usr/share/vulkan/icd.d /etc/vulkan/icd.d \
      -type f -iname "*lvp*.json" -print -quit 2>/dev/null || true)"
    test -n "$icd" || { echo R09_MESA_LAVAPIPE_ICD_MISSING; exit 78; }
    export VK_ICD_FILENAMES="$icd"
    export VK_DRIVER_FILES="$icd"
    echo "R09_PRIVATE_LAVAPIPE_ICD=$icd"
    ldd /private/bin/r09-full-gpu-host
    if ldd /private/bin/r09-full-gpu-host | grep -q "not found"; then
      echo "R09_HOST_SHARED_LIBRARY_MISSING"
      exit 79
    fi
    echo "R09_AUTHENTIC_152_GRAPH_EXECUTION_ATTEMPT"
    /private/bin/r09-full-gpu-host \
      /private/original.nrmodel \
      /private/capture-1920x1080.rgba8 \
      /private/output-original.rgba32f
    test "$(stat -c %s /private/output-original.rgba32f)" = "33177600"
    python3 /repo/tools/graphics/r09_authentic_preview_png.py \
      --input-rgba8 /private/capture-1920x1080.rgba8 \
      --output-rgba32f /private/output-original.rgba32f \
      --before-png /private/r09_before_real.png \
      --after-png /private/r09_after_unverified_gpu.png
    echo "R09_GPU_READBACK_PRODUCED_NOT_YET_INDEPENDENTLY_VERIFIED"
  ' 2>&1 | tee "$work/r09_full_network.log"
status=${PIPESTATUS[0]}
set -e
echo "R09_FULL_NETWORK_EXIT_CODE=$status"
echo "R09_FULL_NETWORK_LOG=$work/r09_full_network.log"
echo "R09_PRIVATE_RESULTS=$work"
if [[ "$status" -ne 0 ]]; then
  echo "R09_FULL_NETWORK_NOT_COMPLETED: send only r09_full_network.log" >&2
  exit "$status"
fi
echo "R09_OUTPUT=$work/output-original.rgba32f"
echo "R09_PREVIEW=$work/r09_after_unverified_gpu.png"
echo "R09_NOTICE: a completed frame is NOT an independently verified 152-op trace."
