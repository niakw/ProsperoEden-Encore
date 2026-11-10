#!/usr/bin/env bash
# Explicitly invoked host-only source gate; no PS5 build and no vendor mutation.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
output="${1:?usage: bash research/ns2/fetch_pinned_vendor_snapshot.sh /tmp/encore-vendor-snapshot}"
ref='22b69d6053db41b74edac2633c012f925b84f69e'
base="https://raw.githubusercontent.com/niakw/Prospero.Eden-Encore-vendor/$ref"
files=(
  encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h
  encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp
  encore-active/eden-vulkan/vulkan_rasterizer.cpp
  encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h
  encore-active/eden-core/src/video_core/memory_manager.cpp
  encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp
)
for file in "${files[@]}"; do
  mkdir -p "$output/$(dirname "$file")"
  curl --fail --location --silent --show-error --retry 2 "$base/$file" -o "$output/$file"
done
python3 -B "$root/research/ns2/check_native_qmd_owners.py" --vendor "$output" --source-snapshot
