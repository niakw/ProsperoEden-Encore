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
test "$mods" = vendor || { echo "External Gitlinks remain: $mods" >&2; exit 1; }
test "$(grep -c "^\[submodule " .gitmodules)" -eq 1
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
