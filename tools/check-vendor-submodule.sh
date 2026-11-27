#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
entry="$(git ls-tree HEAD -- vendor)"
case "$entry" in
  "160000 commit "*"vendor") ;;
  *) echo "Expected vendor/ gitlink (160000): $entry" >&2; exit 1 ;;
esac
expected="$(printf '%s\n' "$entry" | awk '{print $3}')"
test -n "$expected"
mods="$(git ls-tree -r HEAD | awk '$1=="160000" {print $4}')"
expected_mods="$(printf 'encore-overrides\nvendor')"
test "$mods" = "$expected_mods" || { echo "Unexpected root Gitlinks: $mods" >&2; exit 1; }
test "$(grep -c "^\[submodule " .gitmodules)" -eq 2
test "$(git config -f .gitmodules submodule.vendor.branch)" = main
test "$(git config -f .gitmodules submodule.encore-overrides.branch)" = main
# The override gitlink tracks upstream main independently of the immutable
# vendor/sources/encore-overrides snapshot compiled into the current binary.
override_link="$(git rev-parse HEAD:encore-overrides)"
[[ "$override_link" =~ ^[a-f0-9]{40}$ ]]
test "$(git config -f .gitmodules submodule.encore-overrides.update)" = none
test ! -e encore-overrides/.git
test ! -e vendor/.gitmodules
test -f vendor/README.md
test -f vendor/encore-active/eden/src/video_core/renderer_vulkan/vulkan_rasterizer.cpp
test -f vendor/encore-active/eden/src/video_core/vulkan_common/vulkan_device.cpp
test -f vendor/encore-active/eden/src/shader_recompiler/frontend/ampere/probe.cpp
test -f vendor/encore-active/eden/src/core/hle/kernel/k_address_arbiter.cpp
test -f vendor/encore-active/eden/externals/amd-fsr31/LICENSE.txt
for retired in ns2-runtime eden-vulkan amd-fsr31; do
  test ! -e "vendor/encore-active/$retired" || {
    echo "Retired vendor override root returned: $retired" >&2
    exit 1
  }
done
for alias in srcpere src_wait64 src_as src_gpu src_structure; do
  test ! -e "vendor/encore-active/eden/$alias" || {
    echo "Retired Eden alias returned: $alias" >&2
    exit 1
  }
done
if git grep -nE 'encore-active/(eden-vulkan|amd-fsr31|ns2-runtime)|encore-active/eden/(srcpere|src_wait64|src_as|src_gpu|src_structure)' --     headless tools .github extras ':(exclude)tools/check-vendor-submodule.sh' ':(exclude)tools/check-active-source-inventory.py' ':(exclude)tools/check-eden-optimization-coverage.py'; then
  echo "Retired active-source reference remains in engine build/gates" >&2
  exit 1
fi
test -d vendor/sources/eden-cpm
actual="$(git -C vendor rev-parse HEAD)"
test "$actual" = "$expected" || { echo "Submodule SHA mismatch: $expected != $actual" >&2; exit 1; }
git -C vendor diff --quiet
# Pin source-only third-party trees and keep encore-active reserved for overrides.
python3 -B tools/graphics/check-internalized-ps5-deps.py
echo "vendor gitlink and file paths verified at $actual"
