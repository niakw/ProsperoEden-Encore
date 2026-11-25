#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# GitHub Actions cannot cache relative paths containing "..". Keep the heavy pinned sibling
# checkouts under this repository's cacheable .deps tree and expose their historical sibling names
# through symlinks. Existing real sibling checkouts are never replaced.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
store="${PROSPEROEDEN_GIT_DEPS_ROOT:-.deps/repos}"
[[ "$store" = /* ]] || store="$root/$store"
mkdir -p "$store"

# A completed native build can leave tracked OpenGL source changes inside the
# GitHub cache's .deps/repos checkout. Never reset or overwrite that checkout:
# preserve this CI-owned copy in the runner temp folder, then let deps.py
# rehydrate the exact pinned commit from the immutable vendor Git bundle.
# This is only for the ephemeral Actions cache, never for a local sibling repo.
if [[ "\${GITHUB_ACTIONS:-}" == "true" && "$store" == "$root/.deps/repos" ]]; then
    cached_opengl="$store/ps5-opengl-review"
    if [[ ! -L "$cached_opengl" && -d "$cached_opengl/.git" ]] &&
       [[ -n "$(git -C "$cached_opengl" status --porcelain --untracked-files=no)" ]]; then
        pinned_opengl=$(python3 - "$root/tools/deps.json" <<'PY'
import json
import sys
items = json.load(open(sys.argv[1], encoding="utf-8"))["items"]
print(next(item["commit"] for item in items if item["name"] == "opengl-source"))
PY
)
        current_opengl=$(git -C "$cached_opengl" rev-parse HEAD)
        if [[ "$current_opengl" != "$pinned_opengl" ]]; then
            echo "Refusing to quarantine OpenGL cache at unexpected Git revision" >&2
            exit 1
        fi
        if [[ ! -f "$root/vendor/objects/opengl-source/chunks.json" ]]; then
            echo "Cannot rehydrate OpenGL: pinned vendor Git bundle is absent" >&2
            exit 1
        fi
        if [[ "$(cd -- "$store" && pwd -P)" != "$root/.deps/repos" ]]; then
            echo "Refusing to relocate OpenGL outside the expected CI cache root" >&2
            exit 1
        fi
        quarantine=$(mktemp -d "\${RUNNER_TEMP:?}/encore-opengl-cache-XXXXXX")
        mv -- "$cached_opengl" "$quarantine/ps5-opengl-review"
        echo "Encore CI: preserved dirty pinned OpenGL cache in runner temp; deps.py will restore vendor Git bundle"
    fi
fi

for name in ps5-native-app-boilerplate ps5-opengl-review mihawk-vulkan-review mihawk-mesa-review mihawk-sdk-review; do
    link="$root/../$name"
    target="$store/$name"
    if [[ -e "$link" && ! -L "$link" ]]; then
        echo "Refusing to replace real sibling checkout: $link" >&2
        exit 1
    fi
    rm -f "$link"
    ln -s "$target" "$link"
done

echo "Encore CI sibling cache links: ready under $store"
