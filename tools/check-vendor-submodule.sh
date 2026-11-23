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
test -f vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp
test -d vendor/sources/eden-cpm
actual="$(git -C vendor rev-parse HEAD)"
test "$actual" = "$expected" || { echo "Submodule SHA mismatch: $expected != $actual" >&2; exit 1; }
git -C vendor diff --quiet
# Pin source-only third-party trees and keep encore-active reserved for overrides.
python3 -B tools/graphics/check-internalized-ps5-deps.py
echo "vendor gitlink and file paths verified at $actual"
