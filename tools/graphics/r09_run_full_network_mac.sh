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
Research-only 720p mode (requires exact new Linux artifact, no fallback):
  R09_RESEARCH_720=1 bash tools/graphics/r09_run_full_network_mac.sh \\
    "$HOME/Downloads/nvngx_dlssnr.dll.zip" \\
    "$HOME/Downloads/real-game-screenshot.png"
The user file must be the supported Windows model DLL or a ZIP containing it.
This script executes the real full-network ENTRYPOINT (not the old R09
partial fixture runner). A finished readback is not proof of 152 correct
operations, nor an independently validated reference-quality image.
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
# The previous artifact 42465459699 was GDB-confirmed to dereference
# a null query cache before the first Vulkan dispatch. Refuse it forever.
# The default points to the ONE corrected, vendor-pinned public host link.
# Its exact binary SHA is included in the same GitHub Actions artifact
# together with engine/vendor commits; no user weights ever enter GitHub.
research_720="${R09_RESEARCH_720:-0}"
if [[ "$research_720" != 0 && "$research_720" != 1 ]]; then
  echo "R09_MAC_RESEARCH_720_FLAG_MUST_BE_ZERO_OR_ONE" >&2
  exit 64
fi
if [[ "$research_720" == 1 ]]; then
  linked_run="${R09_HOST_LINKED_RUN_ID:-43029338449}"
  expected_engine="${R09_HOST_EXPECTED_ENGINE_SHA:-7f5ea90ad29a5562161e8cb9aae1406b1bc9a2de}"
  expected_vendor="b26075ab190460014cbffd6c744faf897088375c"
  artifact_name="r09-min-720-authentic-linux-host-vulkan-runner-public-only"
  capture_width=1280
  capture_height=720
  capture_bytes=3686400
  output_bytes=14745600
else
  linked_run="${R09_HOST_LINKED_RUN_ID:-42488585951}"
  expected_engine="${R09_HOST_EXPECTED_ENGINE_SHA:-27e782902a06659691d857a1df0e802abd1dbef4}"
  expected_vendor="0f47339c219087801bb75075a7bcc862b39f5bfd"
  artifact_name="r09-public-host-vulkan-runner"
  capture_width=1920
  capture_height=1080
  capture_bytes=8294400
  output_bytes=33177600
fi
required_binary_sha="${R09_HOST_LINKED_SHA256:-}"
image="eden-r09-original-host:ubuntu2404-amd64"

if [[ "$linked_run" == "42465459699" ]]; then
  echo "R09_HOST_OBSOLETE_CRASHING_BINARY_REJECTED" >&2
  exit 78
fi
if [[ ! "$linked_run" =~ ^[0-9]+$ ||
      ! "$expected_engine" =~ ^[0-9a-f]{40}$ ||
      ( -n "$required_binary_sha" && ! "$required_binary_sha" =~ ^[0-9a-f]{64}$ ) ]]; then
  echo "R09_HOST_RELINK_INPUT_INVALID: use pinned run and valid SHA inputs" >&2
  exit 78
fi

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
# A Linux ARM64 Colima VM with the legacy builder silently ignores the
# requested amd64 image target. An x86_64 *VM* is required to use the
# linked R09 Linux binary reliably; never damage/change the default VM.
docker_context="$(docker context show)"
docker_server_arch="$(docker info --format '{{.Architecture}}' 2>/dev/null || true)"
echo "R09_DOCKER_CONTEXT=$docker_context server_arch=$docker_server_arch"
case "$docker_context" in
  colima*)
    case "$docker_server_arch" in
      x86_64|amd64) ;;
      *)
        echo "R09_COLIMA_X86_64_VM_REQUIRED: active Colima VM is $docker_server_arch" >&2
        echo "Create a separate profile: colima start r09 --arch x86_64 --vm-type qemu --cpu 2 --memory 5 --disk 30 --activate=false" >&2
        echo "Then run with: DOCKER_CONTEXT=colima-r09 bash tools/graphics/r09_run_full_network_mac.sh <DLL.zip> <capture.jpg>" >&2
        echo "Existing Colima data is not changed. On 8 GB Macs, stop the other VM if safe." >&2
        exit 76
        ;;
    esac
    ;;
esac
gh auth status --hostname github.com >/dev/null 2>&1 || {
  echo "R09_MAC_GH_NOT_AUTHENTICATED: run gh auth login first." >&2
  exit 67
}
# Fail before copying the private large model DLL or rebuilding the
# emulated Linux image if the public host link is not complete/successful.
echo "R09_CHECKING_PINNED_PUBLIC_LINK_RUN=$linked_run"
run_status="$(gh run view "$linked_run" -R "$github_repo" --json status --jq '.status')"
run_conclusion="$(gh run view "$linked_run" -R "$github_repo" --json conclusion --jq '.conclusion')"
run_engine="$(gh run view "$linked_run" -R "$github_repo" --json headSha --jq '.headSha')"
if [[ "$run_status" != completed || "$run_conclusion" != success ]]; then
  echo "R09_HOST_CORRECTED_LINK_NOT_SUCCESSFUL: $run_status / $run_conclusion" >&2
  echo "R09_LINK_URL=https://github.com/$github_repo/actions/runs/$linked_run" >&2
  exit 79
fi
if [[ "$run_engine" != "$expected_engine" ]]; then
  echo "R09_HOST_SOURCE_PROVENANCE_MISMATCH=$run_engine" >&2
  exit 80
fi
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
# Colima normally mounts the home directory, NOT a source checkout in /tmp.
# Stage ONLY the public headers and two tools in our private HOME workspace,
# avoiding empty container mounts or accidental uploads of user data.
mkdir -p "$work/public/headless" "$work/public/extras/graphics" \
  "$work/public/tools/graphics" \
  "$work/public/vendor/encore-active/eden-vulkan/include"
cp "$repo/headless/"*.h "$work/public/headless/"
cp "$repo/extras/graphics/"*.h "$work/public/extras/graphics/"
cp -R "$repo/vendor/encore-active/eden-vulkan/include/." \
  "$work/public/vendor/encore-active/eden-vulkan/include/"
cp "$repo/tools/graphics/r09_private_model_import.cpp" \
  "$repo/tools/graphics/r09_authentic_preview_png.py" \
  "$work/public/tools/graphics/"
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
            raise SystemExit("R09_PRIVATE_ZIP_REQUIRES_ONE_BOUNDED_MODEL_DLL")
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
  -n "$artifact_name" -D "$work/download"
binary="$(find "$work/download" -type f -name r09-full-gpu-host -print -quit)"
if [[ -z "$binary" ]]; then
  echo "R09_MAC_ARTIFACT_MISSING_OR_EXPIRED" >&2
  exit 71
fi
manifest="$work/download/R09_HOST_BINARY_SHA256.txt"
provenance="$work/download/R09_HOST_PROVENANCE.txt"
if [[ ! -f "$manifest" || ! -f "$provenance" ]]; then
  echo "R09_HOST_SIGNED_SOURCE_PROVENANCE_MANIFEST_MISSING" >&2
  exit 72
fi
if [[ "$research_720" == 1 ]]; then
  if ! grep -Fxq "engine=$expected_engine" "$provenance" ||
     ! grep -Fxq "vendor_research=$expected_vendor" "$provenance" ||
     ! grep -Fxq "engine_gitlink=22b69d6053db41b74edac2633c012f925b84f69e" "$provenance" ||
     ! grep -Fxq "research_720p=ON" "$provenance"; then
    echo "R09_MIN_720_RESEARCH_BINARY_PROVENANCE_REJECTED" >&2
    exit 72
  fi
else
  if ! grep -Fxq "engine=$expected_engine" "$provenance" ||
     ! grep -Fxq "vendor=$expected_vendor" "$provenance"; then
    echo "R09_HOST_ENGINE_OR_VENDOR_PROVENANCE_MISMATCH" >&2
    exit 72
  fi
fi
binary_sha256="$(awk 'NR==1 {print $1}' "$manifest")"
if [[ ! "$binary_sha256" =~ ^[0-9a-f]{64}$ ]]; then
  echo "R09_HOST_INVALID_BINARY_SHA256_MANIFEST" >&2
  exit 72
fi
if [[ -n "$required_binary_sha" && "$binary_sha256" != "$required_binary_sha" ]]; then
  echo "R09_HOST_EXPLICIT_BINARY_SHA256_MISMATCH" >&2
  exit 72
fi
actual_sha256="$(shasum -a 256 "$binary" | awk '{print $1}')"
if [[ "$actual_sha256" != "$binary_sha256" ]]; then
  echo "R09_MAC_BINARY_SHA256_MISMATCH=$actual_sha256" >&2
  exit 72
fi
cp "$binary" "$work/bin/r09-full-gpu-host"
chmod 700 "$work/bin/r09-full-gpu-host"
echo "R09_PINNED_PUBLIC_BINARY_SHA256_PASS=$actual_sha256"
echo "R09_PINNED_PUBLIC_BINARY_RUN=$linked_run"
echo "R09_PINNED_PUBLIC_BINARY_SHA256=$actual_sha256"
echo "R09_HOST_BINARY_EXECUTION_REQUIRES_INDEPENDENT_FULL_NETWORK_VALIDATION"
echo "R09_DOCKER_CONTEXT=$(docker context show)"
if docker image inspect "$image" >/dev/null 2>&1; then
  echo "R09_DOCKER_RUNTIME_REUSED_EXISTING_IMAGE=$image"
else
  echo "R09_DOCKER_BUILD=public_dependencies_only (no proprietary input in image)"
  # Buildx needs --load to install the image into the selected daemon.
  if docker buildx version >/dev/null 2>&1; then
    docker buildx build --load --platform linux/amd64 \
      -f "$repo/tools/graphics/Dockerfile.r09-full-host" \
      -t "$image" "$work/docker-context"
  else
    DOCKER_BUILDKIT=0 docker build --platform linux/amd64 \
      -f "$repo/tools/graphics/Dockerfile.r09-full-host" \
      -t "$image" "$work/docker-context"
  fi
fi
if ! docker image inspect "$image" >/dev/null 2>&1; then
  echo "R09_DOCKER_IMAGE_NOT_LOADED_IN_LOCAL_DAEMON" >&2
  echo "R09_DOCKER_DIAGNOSTIC_CONTEXT=$(docker context show)" >&2
  exit 73
fi
# A local Docker image tag can point to a multi-platform manifest.
# An unqualified 'docker image inspect' may report the Mac's default arm64
# variant even when the explicit linux/amd64 variant exists. Check the
# architecture that docker run actually selects instead.
default_arch="$(docker image inspect --format '{{.Architecture}}' "$image")"
echo "R09_DOCKER_INSPECT_DEFAULT_ARCH=$default_arch (not an amd64 proof)"
image_id="$(docker image inspect --format '{{.Id}}' "$image")"
echo "R09_DOCKER_IMAGE_LOADED=$image_id"
# Never pull or substitute a registry image: use the loaded linux/amd64
# variant and prove it with Ubuntu's actual dpkg architecture in-container.
set +e
selected_arch="$(docker run --pull never --rm --platform linux/amd64 \
  --entrypoint /usr/bin/dpkg "$image" --print-architecture)"
arch_rc=$?
set -e
if [[ "$arch_rc" -ne 0 ]]; then
  echo "R09_DOCKER_AMD64_VARIANT_OR_EMULATION_UNAVAILABLE" >&2
  echo "Check Docker Desktop Rosetta/x86_64 emulation or Colima QEMU configuration." >&2
  exit 75
fi
if [[ "$selected_arch" != "amd64" ]]; then
  echo "R09_DOCKER_RUNTIME_ARCH_MISMATCH=$selected_arch (expected amd64)" >&2
  exit 74
fi
echo "R09_DOCKER_IMAGE_READY=$image_id arch=$selected_arch"

memory="$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)"
if [[ "$memory" =~ ^[0-9]+$ ]] && (( memory > 0 && memory < 5368709120 )); then
  echo "R09_WARNING_DOCKER_MEMORY_LOW_BYTES=$memory (full neural graph may OOM)"
fi

echo "R09_FULL_NETWORK_ATTEMPT_START"
set +e
docker run --pull never --rm --init --platform linux/amd64 \
  --mount "type=bind,source=$work/public,target=/repo,readonly" \
  --mount "type=bind,source=$work,target=/private" \
  -e "R09_CAPTURE_IS_RAW=$capture_is_raw" \
  -e "R09_CAPTURE_WIDTH=$capture_width" \
  -e "R09_CAPTURE_HEIGHT=$capture_height" \
  -e "R09_CAPTURE_BYTES=$capture_bytes" \
  -e "R09_OUTPUT_BYTES=$output_bytes" \
  -e "R09_RESEARCH_720=$research_720" \
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
      cp /private/capture-source.rgba8 /private/capture-input.rgba8
    else
      ffmpeg -hide_banner -nostdin -loglevel error -y \
        -i /private/capture-source.image \
        -vf "scale=${R09_CAPTURE_WIDTH}:${R09_CAPTURE_HEIGHT}:force_original_aspect_ratio=decrease,pad=${R09_CAPTURE_WIDTH}:${R09_CAPTURE_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,format=rgba" \
        -frames:v 1 -pix_fmt rgba -f rawvideo \
        /private/capture-input.rgba8
    fi
    test "$(stat -c %s /private/capture-input.rgba8)" = "$R09_CAPTURE_BYTES"
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
    if [ "$R09_RESEARCH_720" = 1 ]; then
      echo "R09_AUTHENTIC_720P_152_GRAPH_EXECUTION_ATTEMPT_NOT_PROOF"
      /private/bin/r09-full-gpu-host \
        /private/original.nrmodel \
        /private/capture-input.rgba8 \
        /private/output-original.rgba32f --research-720p
    else
      /private/bin/r09-full-gpu-host \
        /private/original.nrmodel \
        /private/capture-input.rgba8 \
        /private/output-original.rgba32f
    fi
    test "$(stat -c %s /private/output-original.rgba32f)" = "$R09_OUTPUT_BYTES"
    python3 /repo/tools/graphics/r09_authentic_preview_png.py \
      --input-rgba8 /private/capture-input.rgba8 \
      --output-rgba32f /private/output-original.rgba32f \
      --width "$R09_CAPTURE_WIDTH" --height "$R09_CAPTURE_HEIGHT" \
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
