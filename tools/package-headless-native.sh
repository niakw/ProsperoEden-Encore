#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
[[ $# == 0 || ( $# == 1 && ( "$1" == --integration || "$1" == --game ) ) ]]
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
source "$root/tools/host-env.sh"
eden_host_env "$root"
scratch=$(cat "$root/.local/headless-cache")
[[ "$(cd -- "$(cat "$scratch/owner")" && pwd -P)" == "$root" ]]
template="$root/../ps5-native-app-boilerplate"
builder="$root/build/host/ps5-native-tool"
out="$root/build/headless-native"
app="${EDEN_PACKAGE_DIR:-$root/dist/headless/PPSA99008}"
# A separate clean staging directory lets driver candidates omit private game
# assets without deleting or copying the existing development installation.
if [[ -n ${EDEN_PACKAGE_DIR:-} ]]; then
    canonical_root=$(realpath -m "$root")
    canonical_app=$(realpath -m "$app")
    [[ $canonical_app == "$canonical_root"/build/*/PPSA99008 ]] || exit 2
    [[ ${1:-} != --game ]] || exit 2
fi
test -x "$builder"
(cd "$template/runtime" && sha256sum --check --strict libc.prx.sha256)
mkdir -p "$out" "$app/sce_sys" "$app/sce_module"
cp "$scratch/native-local/bin/eden-headless" "$out/llvm-pie.elf"
cp "$scratch/native-local/bin/eden-headless.map" "$out/link.map"
cp "$scratch/native-local/CMakeCache.txt" "$out/CMakeCache.txt"
stub_flags=(--stub-dir "$scratch/sdk/target/lib")
if grep -qx 'EDEN_PS5_OPENGL:BOOL=ON' "$out/CMakeCache.txt"; then
    gl46="$root/.local/ps5-opengl-sdk-ad2807d"
    stub_flags=()
    for stub in "$scratch/sdk/target/lib/"*.so; do
        case "${stub##*/}" in libSceAgc.so|libSceAgcDriver.so) continue ;; esac
        stub_flags+=(--stub "$stub")
    done
    driver_stub="$gl46/lib/libSceAgcDriver.so"
    if grep -qx 'EDEN_PS5_VULKAN:BOOL=ON' "$out/CMakeCache.txt"; then
        driver_stub="$root/build/stubs/libSceAgcDriver.so"
    fi
    stub_flags+=(--stub "$gl46/lib/libSceAgc.so" --stub "$driver_stub")
fi
"$builder" link --in "$out/llvm-pie.elf" --out "$out/eboot.elf" \
    "${stub_flags[@]}" --module-sdk 0x02000009 \
    --companion-sdk 0x08050001 --file-name eboot.elf
"$builder" self --sign --in "$out/eboot.elf" --out "$app/eboot.bin" --magic 0x1D3D154F
cp "$template/runtime/libc.prx" "$app/sce_module/libc.prx"
cp "$root/assets/"{pic0.dds,pic1.dds,snd0.at9} "$app/sce_sys/"
# One Encore raster source feeds both the PS5 tile and the launcher brand.
cp "$root/assets/icon0.png" "$app/sce_sys/icon0.png"
cp "$root/assets/icon0.dds" "$app/sce_sys/icon0.dds"
rm -rf "$app/ui"
cp -a "$root/headless/prosperoeden/ui" "$app/ui"
# Zero built-in daily images and zero daily-art downloads by default.
# Only an explicit, reviewed packaging opt-in enables automatic catalog
# snapshot fetching. The console-side Daily option remains off by default.
# Never allow source-tree art to silently re-enable a disabled snapshot.
rm -rf "$app/ui/art/daily"
if [[ ${EDEN_BAKE_DAILY_SWITCH_ART:-0} == 1 ]]; then
    python3 "$root/tools/launcher/fetch_daily_switch.py" \
        --output "$app/ui/art/daily" ||
        echo "Daily Switch artwork unavailable; keep the original Encore background" >&2
fi
# Read-only embedded hosts policy. Release must never lose this file.
cp "$root/headless/network-hosts.txt" "$app/network-hosts.txt"
rm -f "$app/ui/art/backdrop.tga" "$app/ui/art/backdrop-blur.tga"
# Keep complete legal notices inside the title itself so a standalone .ffpfsc install never
# separates the binary from the GPL and third-party license texts that accompany it.
rm -rf "$app/legal"
mkdir -p "$app/legal"
cp "$root/LICENSE" "$root/THIRD_PARTY_NOTICES.md" "$app/legal/"
cp -a "$root/LICENSES" "$app/legal/LICENSES"
cp "$root/vendor/sources/libwebp/COPYING" "$app/legal/LIBWEBP_LICENSE.txt"
cp "$root/vendor/sources/libwebp/PATENTS" "$app/legal/LIBWEBP_PATENTS.txt"
cp "$root/vendor/sources/ps5-mihawkgen/LICENSE.md" "$app/legal/MIHAWKGEN_LICENSE.md"
cp "$root/vendor/sources/ps5-mihawkgen/THIRD_PARTY_NOTICES.txt" "$app/legal/MIHAWKGEN_THIRD_PARTY_NOTICES.txt"
cp "$root/vendor/sources/ps5-fsr3-optical-flow/COPYING" "$app/legal/FSR3_OPTICAL_LICENSE.txt"
cp "$root/vendor/sources/ps5-fsr3-optical-flow/shaders/LICENSE.txt" "$app/legal/FSR3_OPTICAL_SHADER_LICENSE.txt"
# PS5-native MihawkGen network, bundled with the installed app only, including
# the upstream GPL-3.0-or-later licence and all model distillation credits.
# A mismatching/missing model must not silently produce a broken package.
mihawk_root="$root/vendor/sources/ps5-mihawkgen"
python3 - "$mihawk_root/framegen/models/network.fgw" <<'PY_MIHAWK_NETWORK'
import hashlib, sys
from pathlib import Path
network = Path(sys.argv[1])
assert network.is_file(), "Vendored MihawkGen model missing"
assert network.stat().st_size == 1757240, "MihawkGen model size mismatch"
assert hashlib.sha256(network.read_bytes()).hexdigest() == "31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b", "MihawkGen model hash mismatch"
PY_MIHAWK_NETWORK
mkdir -p "$app/mihawkgen"
cp "$mihawk_root/framegen/models/network.fgw" "$app/mihawkgen/network.fgw"
cp "$mihawk_root/LICENSE.md" "$app/legal/MIHAWKGEN_LICENSE.md"
cp "$mihawk_root/THIRD_PARTY_NOTICES.txt" "$app/legal/MIHAWKGEN_THIRD_PARTY_NOTICES.txt"
# Some ShadowMount/package-image install paths preserve ui/lang but drop .po payloads.
# Keep the canonical catalogs and add byte-identical .txt companions; the runtime accepts either.
for catalog in "$app/ui/lang/"*.po; do
    cp "$catalog" "${catalog%.po}.txt"
done
if command -v magick >/dev/null 2>&1; then
    image_convert=(magick)
elif command -v convert >/dev/null 2>&1; then
    image_convert=(convert)
else
    echo "ImageMagick (magick or convert) is required to build Encore launcher art" >&2
    exit 2
fi
# PS5 tile remains native; ship only compressed WebP scenery and brand.
# ImageMagick directly decodes the JPEG/PNG source and WebP-encodes once.
"${image_convert[@]}" "$root/assets/encore-background.jpg" -resize '1920x1080^'     -gravity center -extent 1920x1080 -alpha off     -quality 80 -define webp:method=5 "$app/ui/art/backdrop.webp"
# The UI renderer samples image row zero at its top edge. Store source-oriented
# WebP directly; the historical -flip operation inverted logos on real PS5.
"${image_convert[@]}" "$app/sce_sys/icon0.png" -resize 256x256 -alpha on     -define webp:lossless=true -quality 80 "$app/ui/art/brand.webp"
for logo in noneon white dark; do
    "${image_convert[@]}" "$root/assets/branding/encore-${logo}.png"         -resize 256x256 -alpha on -define webp:lossless=true -quality 80         "$app/ui/art/brand-${logo}.webp"
done
rm -f "$app/ui/art/backdrop.tga" "$app/ui/art/brand.tga"       "$app/ui/art/brand-noneon.tga" "$app/ui/art/brand-white.tga"       "$app/ui/art/brand-dark.tga"
python3 - "$app/ui/art/backdrop.webp" "$app/ui/art/brand.webp" <<'PY_WEBP_STAGE'
import sys
from pathlib import Path
for name in sys.argv[1:]:
    data = Path(name).read_bytes()
    if len(data) < 30 or data[:4] != b'RIFF' or data[8:12] != b'WEBP' or (
        int.from_bytes(data[4:8], 'little') + 8 != len(data)
    ):
        raise SystemExit(f"Generated launcher WebP is invalid: {name}")
PY_WEBP_STAGE
# UI-only assets use lossless WebP to preserve original alpha, plastic
# jacket panels, printed spine logos and controller-mask edges.
"${image_convert[@]}" "$root/headless/prosperoeden/ui/art/controller.tga"     -define webp:lossless=true -quality 80 "$app/ui/art/controller.webp"
rm -f "$app/ui/art/controller.tga"
# Keep all three original NS1/NS2 case inserts (including NS2 head),
# encoded losslessly in WebP; preserve the gold-seal correction.
for stem in switch-logo switch-rear-footer ns2-head; do
    encoded="$app/ui/art/${stem}.png.b64"
    unpacked="$app/ui/art/${stem}.png"
    target="$app/ui/art/${stem}.webp"
    python3 - "$encoded" "$unpacked" <<'PY_FIXED_CASE'
import base64
from pathlib import Path
import sys
source, destination = map(Path, sys.argv[1:3])
destination.write_bytes(base64.b64decode(source.read_text().strip(), validate=True))
PY_FIXED_CASE
    fixed_ink=()
    if [[ $stem == switch-rear-footer ]]; then
        fixed_ink=(-colorspace sRGB -region '82x80+182+195'                    -fill '#af884c' -opaque black +region)
    fi
    "${image_convert[@]}" "$unpacked" "${fixed_ink[@]}" -type TrueColorAlpha         -define webp:lossless=true -quality 80 "$target"
    python3 - "$target" <<'PY_FIXED_WEBP'
from pathlib import Path
import sys
p = Path(sys.argv[1])
b = p.read_bytes()
if len(b) < 30 or b[:4] != b'RIFF' or b[8:12] != b'WEBP' or (
    int.from_bytes(b[4:8], 'little') + 8 != len(b)
):
    raise SystemExit(f"Invalid lossless WebP case art: {p.name}")
PY_FIXED_WEBP
    rm -f "$encoded" "$unpacked"
done

# Filesystem access helper (headless/elevation, built for PPSA99008): elfldr runs it at startup.
make -s -C "$root/headless/elevation/helper" OUTPUT="$root/build/elevation/sandbox-elevator.elf" \
    PS5_PAYLOAD_SDK="${PS5_ELEVATION_SDK:-/opt/ps5-payload-sdk}"
python3 "$root/headless/elevation/validate-helper.py" "$root/build/elevation/sandbox-elevator.elf"
cp "$root/build/elevation/sandbox-elevator.elf" "$app/sandbox-elevator.elf"

# R21: independent updater payload. The running app never replaces its own
# files. The helper enforces target PPSA99008, ZIP bounds, SHA256, rollback
# and waits until the app sandbox exits before applying.
make -s -C "$root/headless/self_update_helper" OUTPUT="$root/build/self-update/self-updater.elf"     PS5_PAYLOAD_SDK="${PS5_ELEVATION_SDK:-/opt/ps5-payload-sdk}"
test -s "$root/build/self-update/self-updater.elf"
cp "$root/build/self-update/self-updater.elf" "$app/self-updater.elf"

python3 - "$root" "$template" "$app" "${1:-}" <<'PY'
import json, pathlib, runpy, shutil, sys
root, template, app = map(pathlib.Path, sys.argv[1:4])
game = sys.argv[4] == '--game'
integration = sys.argv[4] in ('--integration', '--game')
if game:
    assert (app / 'game-assets.json').is_file()
    assert (app / 'assets/keys/prod.keys').is_file()
value = json.loads((template / 'sce_sys/param.json').read_text())
value.update(titleId='PPSA99008', conceptId='99008', contentId='UP9000-PPSA99008_00-PROSPEROEDEN0001')
# The app version has one home: the launcher shows the same value.
import re
native_cache = (root / 'build/headless-native/CMakeCache.txt').read_text()
compiled_revision = re.search(r'^EDEN_LAUNCHER_BUILD_LABEL:STRING=(R[1-9][0-9]{0,5})$', native_cache, re.M)
compiled_version = re.search(r'^EDEN_LAUNCHER_PACKAGE_VERSION:STRING=([0-9]{2}[.][0-9]{3}[.][0-9]{3})$', native_cache, re.M)
assert compiled_revision and compiled_version, 'Missing compiled native R version provenance'
import subprocess
expected_version = subprocess.check_output([
    sys.executable, str(root / 'tools/ci/native-content-version.py'),
    compiled_revision.group(1)], text=True).strip()
assert compiled_version.group(1) == expected_version, (
    'Compiled R revision and PS5 contentVersion do not match')
value['contentVersion'] = compiled_version.group(1)
value['localizedParameters']['en-US']['titleName'] = 'Prospero.Eden Encore'
# Bind release metadata to the exact compiled R-label and source commit.
revision = __import__('re').search(r'^EDEN_LAUNCHER_BUILD_LABEL:STRING=(R[1-9][0-9]{0,5})$',
                                     (root / 'build/headless-native/CMakeCache.txt').read_text(), __import__('re').M)
assert revision, 'Missing attested compiled launcher R revision in CMakeCache'
import subprocess
source_sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                     text=True).strip()
assert re.fullmatch(r'[0-9a-f]{40}', source_sha)
# Attest the SHA CMake actually received to compile the native executable,
# not merely whichever commit happens to be checked out at package time.
native_cache = (root / 'build/headless-native/CMakeCache.txt').read_text()
compiled_source = re.search(r'^EDEN_ENCORE_SOURCE_COMMIT:(?:STRING|UNINITIALIZED)=([0-9a-f]{40})$',
                            native_cache, re.M)
assert compiled_source and compiled_source.group(1) == source_sha, (
    'native executable source SHA differs from the packaging checkout')
(app / 'encore-release.json').write_text(json.dumps({
    'build_revision': revision.group(1),
    'source_sha': source_sha,
    'native_content_version': value['contentVersion'],
}, indent=2) + '\n')
value['pubtools']['loudnessSnd0'] = '-28.00'
# The console gives a 120 Hz output (Settings > Video, headless/display_refresh.h) only to a title
# that declares it. Declaring it changes nothing by itself: the output stays at 60 Hz until asked.
value['attribute3'] = int(value['attribute3']) | 0x80040
# Match the primary port's tested native package request. This is not the
# size of physical RAM, the guest heap, or the dynamically committed JIT cache.
value.setdefault('kernel', {})['flexibleMemorySize'] = 335544320
(app / 'sce_sys/param.json').write_text(json.dumps(value, indent=2) + '\n')
runpy.run_path(str(root / 'tools/load_alignment.py'))['check_load_alignment']((app / 'eboot.bin').read_bytes())
profile = (root / 'build/headless-native/CMakeCache.txt').read_text()
development = 'EDEN_DEV_PROFILE:BOOL=ON' in profile
# The consolidated native CMake graph no longer declares the old
# experiment options, so no corresponding BOOL=OFF cache lines exist.
# Preserve the fail-closed rule: an explicit ON (BOOL or UNINITIALIZED)
# still refuses packaging. CMake hardwires the production A64 units and
# defines both availability macros to zero for the shipped executable.
for experimental in ('EDEN_SHARED_JIT', 'EDEN_JIT_COMPILE_BATCH'):
    assert experimental + ':BOOL=ON' not in profile
    assert experimental + ':UNINITIALIZED=ON' not in profile
# The shipping native UI is selected by a real target compile definition,
# not by the retired EDEN_DEVICE_FRONTEND CMake cache option. Prove that the
# launcher object was compiled with the only allowed production value.
# The earlier cache-only assertion incorrectly rejected a successfully linked
# PS5 title when no legacy BOOL entry existed.
import shlex
native_scratch = pathlib.Path((root / '.local/headless-cache').read_text().strip())
compiled_db = json.loads((native_scratch / 'native-local/compile_commands.json').read_text())
launcher_units = [entry for entry in compiled_db
                  if pathlib.Path(entry['file']).as_posix().endswith('/headless/main.cpp')]
assert len(launcher_units) == 1, 'Cannot prove native launcher frontend selection'
launcher = launcher_units[0]
launcher_args = (launcher['arguments'] if 'arguments' in launcher
                 else shlex.split(launcher['command']))
frontend_flags = [flag for flag in launcher_args if flag.startswith('-DEDEN_DEVICE_FRONTEND=')]
assert frontend_flags == ['-DEDEN_DEVICE_FRONTEND=0'], (
    'Shipping PS5 native frontend must be compiled OFF', frontend_flags)
assert 'EDEN_DEVICE_FRONTEND:BOOL=ON' not in profile
assert 'EDEN_DEVICE_FRONTEND:UNINITIALIZED=ON' not in profile
devices = False
graphics = 'EDEN_PS5_OPENGL:BOOL=ON' in profile
assert not (integration and devices)
assert not game or graphics
fixture_name = 'core-integration.nro' if integration else 'core-devices.nro' if devices else 'core-homebrew.nro'
shutil.copy2(root / 'build/fixture' / fixture_name, app / 'core-homebrew.nro')
(root / 'build/headless-native/frontend.json').write_text(json.dumps({
    'devices': devices,
    'gpu_probe': 'EDEN_GPU_PROBE:BOOL=ON' in profile,
    'renderer': 'opengl-4.6-compatibility' if graphics else 'null', 'guest_fixture': 'retail-game' if game else 'cpu-state-memory-atomics-fp-simd-services' if integration else 'timer-sync-service-storage-hid-audio-renderer-voice-mix-src-high' if devices else 'timer-sync-service-storage',
    'vulkan': 'EDEN_PS5_VULKAN:BOOL=ON' in profile,
    'vulkan_driver': 'RADV' if 'EDEN_VULKAN_DRIVER:STRING=RADV' in profile else 'CUSTOM',
    'development_backend': 'Vulkan' if 'EDEN_DEV_VULKAN:BOOL=ON' in profile else 'user-preference',
    'development_rom_id': next((line.split('=', 1)[1] for line in profile.splitlines()
                                if line.startswith('EDEN_DEV_ROM_ID:STRING=')), ''),
    'hardware_qualified': False,
}, indent=2) + '\n')
PY
llvm-readobj-18 --dyn-symbols --needed-libs "$out/llvm-pie.elf" > "$out/imports.txt"
"$builder" self --inspect --file "$app/eboot.bin" > "$out/fself-inspection.txt"
sha256sum "$app/eboot.bin" "$app/core-homebrew.nro" "$app/sce_module/libc.prx" \
    "$app/sce_sys/param.json" "$app/sce_sys/icon0.png" "$app/sce_sys/icon0.dds" "$app/sce_sys/pic0.dds" "$app/sce_sys/pic1.dds" \
    "$app/sce_sys/snd0.at9"
