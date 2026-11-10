#!/usr/bin/env bash
# Research-only: five local C++ host fixtures + optional full vendor source validation.
# NEVER runs the Encore PS5 build, modifies vendor, or enables GitHub Actions.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

for compiler in clang++ g++; do
  if ! command -v "$compiler" >/dev/null 2>&1; then
    echo "MISSING compiler: $compiler" >&2
    exit 2
  fi
  for test in test_ssbo_extent_contract test_gpu_backing_lifetime test_epoch_guarded_gmmu_memo test_native_vk_range_contract test_qmd3_descriptor_read_owner; do
    "$compiler" -std=c++20 -pthread -O1 -Wall -Wextra -Werror \
      -fsanitize=undefined -fno-sanitize-recover=all \
      "$root/research/ns2/${test}.cpp" -o "$tmp/${compiler//+/p}-$test"
    "$tmp/${compiler//+/p}-$test"
  done
done
if [[ -f "$root/vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h" ]]; then
  python3 -B "$root/research/ns2/check_native_qmd_owners.py" --vendor "$root/vendor"
else
  echo 'SKIP: exact-source NS2 QMD3 guard (pinned vendor checkout unavailable)'
fi
