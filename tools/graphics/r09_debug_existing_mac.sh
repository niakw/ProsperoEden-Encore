#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Reuse a previously prepared private R09 run. DO NOT rebuild Eden,
# regenerate the screenshot, or upload user-owned NVIDIA bytes.
set -euo pipefail
umask 077
if [[ "$(uname -s)" != Darwin || $# -ne 2 ]]; then
  echo 'Usage: DOCKER_CONTEXT=colima-r09 bash tools/graphics/r09_debug_existing_mac.sh "$HOME/.cache/eden-encore-r09-private/full-network-XXXX" "$HOME/Downloads/nvngx_dlssnr.dll.zip"' >&2
  exit 64
fi
base="$HOME/.cache/eden-encore-r09-private"
work="$1"
dll="$2"
case "$work" in
  "$base"/full-network-*) ;;
  *) echo "R09_DEBUG_INVALID_PRIVATE_WORKDIR" >&2; exit 65 ;;
esac
if [[ -L "$work" || ! -d "$work" || ! -d "$work/bin" ||
      ! -f "$work/bin/r09-full-gpu-host" ||
      ! -x "$work/bin/r09-private-model-import" ||
      ! -f "$work/capture-1920x1080.rgba8" ||
      ! -f "$dll" || -L "$dll" ]]; then
  echo "R09_DEBUG_EXPECTS_PREVIOUS_SUCCESSFUL_PRIVATE_PREPARATION" >&2
  exit 66
fi
if [[ "$(stat -f %z "$work/capture-1920x1080.rgba8")" != 8294400 ]]; then
  echo "R09_DEBUG_CAPTURE_SIZE_MISMATCH" >&2; exit 67
fi
for name in nvngx_dlssnr.dll original.nrmodel original.nrmodel.importing; do
  if [[ -e "$work/$name" || -L "$work/$name" ]]; then
    echo "R09_DEBUG_REFUSES_EXISTING_PRIVATE_MODEL=$name" >&2; exit 68
  fi
done
cleanup() {
  rm -f "$work/nvngx_dlssnr.dll" "$work/original.nrmodel"     "$work/original.nrmodel.importing"
}
trap cleanup EXIT

# Recreate ONLY the private DLL copy used by the exact existing binary.
# Never add model, DLL, or capture to an image build context.
python3 - "$dll" "$work/nvngx_dlssnr.dll" <<'PY'
import pathlib, shutil, sys, zipfile, hashlib
src, dst = map(pathlib.Path, sys.argv[1:])
if src.is_symlink() or not src.is_file():
    raise SystemExit("R09_DEBUG_DLL_NOT_REGULAR")
if zipfile.is_zipfile(src):
    with zipfile.ZipFile(src) as archive:
        found = [z for z in archive.infolist() if not z.is_dir() and
                 pathlib.PurePosixPath(z.filename).name.lower() == "nvngx_dlssnr.dll"]
        if len(found) != 1 or not 1024 < found[0].file_size < 200_000_000:
            raise SystemExit("R09_DEBUG_PRIVATE_ZIP_INVALID")
        with archive.open(found[0]) as inp, dst.open("xb") as out:
            shutil.copyfileobj(inp, out, length=1 << 20)
else:
    if src.suffix.lower() != ".dll" or not 1024 < src.stat().st_size < 200_000_000:
        raise SystemExit("R09_DEBUG_DLL_INVALID")
    with src.open("rb") as inp, dst.open("xb") as out:
        shutil.copyfileobj(inp, out, length=1 << 20)
digest = hashlib.sha256()
with dst.open("rb") as fp:
    for chunk in iter(lambda: fp.read(1 << 20), b""):
        digest.update(chunk)
print("R09_DEBUG_DLL_SHA256=" + digest.hexdigest())
PY

docker info >/dev/null 2>&1 || {
  echo "R09_DEBUG_DOCKER_UNAVAILABLE: set DOCKER_CONTEXT=colima-r09" >&2; exit 69;
}
architecture="$(docker info --format '{{.Architecture}}')"
if [[ "$architecture" != amd64 && "$architecture" != x86_64 ]]; then
  echo "R09_DEBUG_REQUIRES_X86_64_COLIMA_VM=$architecture" >&2; exit 70
fi
base_image="eden-r09-original-host:ubuntu2404-amd64"
debug_image="eden-r09-original-host-gdb:ubuntu2404-amd64"
docker image inspect "$base_image" >/dev/null 2>&1 || {
  echo "R09_DEBUG_BASE_DOCKER_IMAGE_MISSING" >&2; exit 71;
}
if ! docker image inspect "$debug_image" >/dev/null 2>&1; then
  echo "R09_DEBUG_GDB_IMAGE_INSTALL_ONCE (no neural rebuild)"
  printf '%s\n' "FROM $base_image" \
    'RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends gdb && rm -rf /var/lib/apt/lists/*' \
    | DOCKER_BUILDKIT=0 docker build --platform linux/amd64 \
         -t "$debug_image" -f - "$work/docker-context"
fi
echo "R09_DEBUG_REUSING_CAPTURE_AND_LINKED_EXECUTABLE=$work"
echo "R09_DEBUG_NO_MODEL_OR_DLL_UPLOADED"
set +e
docker run --pull never --rm --init --platform linux/amd64 \
  --mount "type=bind,source=$work,target=/private" \
  -e LP_NUM_THREADS=2 -e GALLIUM_NUM_THREADS=2 \
  "$debug_image" bash -euo pipefail -c '
    /private/bin/r09-private-model-import \
      /private/nvngx_dlssnr.dll /private/original.nrmodel
    icd="/usr/share/vulkan/icd.d/lvp_icd.json"
    test -f "$icd"
    export VK_ICD_FILENAMES="$icd" VK_DRIVER_FILES="$icd"
    ulimit -c 0
    echo R09_GDB_START_AUTHENTIC_ORIGINAL_EXACT_EXISTING_BINARY
    gdb -q -nx -batch \
      -ex "set pagination off" \
      -ex "set confirm off" \
      -ex "set debuginfod enabled off" \
      -ex "set disable-randomization off" \
      -ex "run" \
      -ex "bt 40" \
      -ex "thread apply all bt 5" \
      -ex "info registers" \
      -ex "info sharedlibrary" \
      --args /private/bin/r09-full-gpu-host \
        /private/original.nrmodel \
        /private/capture-1920x1080.rgba8 \
        /private/output-original-gdb.rgba32f
    echo R09_GDB_FINISHED_A_CRASH_IS_NOT_A_SUCCESSFUL_INFERENCE
  ' 2>&1 | tee "$work/r09_gdb_backtrace.log"
status=${PIPESTATUS[0]}
set -e
echo "R09_GDB_DOCKER_EXIT_CODE=$status"
echo "R09_GDB_BACKTRACE=$work/r09_gdb_backtrace.log"
echo "R09_DEBUG_SEND_ONLY_BACKTRACE_NOT_DLL_NOT_MODEL_NOT_CAPTURE"
exit "$status"
