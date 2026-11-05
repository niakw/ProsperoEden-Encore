#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# R08 gate for host-only sources and Vulkan recording. No PS5 build or CI.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
cxx=${CXX:-clang++}
flags=(-std=c++20 -Wall -Wextra -Werror -fsanitize=undefined)
vk=(-Ithird_party/PS5_MihawkGen/external)
native=(-Iextras/graphics -Iheadless -Ithird_party/PS5_MihawkGen/framegen/include)
build_run() {
    local name=$1; shift
    "$cxx" "${flags[@]}" "$@" -o "$out/$name"
    "$out/$name"
    echo "PASS $name"
}
build_run test_framegen_present_gate extras/graphics/test_framegen_present_gate.cpp
build_run test_mihawk_native_surface_contract extras/graphics/test_mihawk_native_surface_contract.cpp
build_run test_mihawk_submission_timeline -fsanitize=address,undefined \
    extras/graphics/test_mihawk_submission_timeline.cpp
build_run test_mihawk_vulkan_history_barriers "${vk[@]}" extras/graphics/test_mihawk_vulkan_history_barriers.cpp
build_run test_mihawk_vulkan_record "${vk[@]}" "${native[@]}" \
    extras/graphics/test_mihawk_vulkan_record.cpp headless/mihawk_vulkan_stage.cpp
build_run test_mihawk_vulkan_resources -fsanitize=address,undefined \
    -Ithird_party/PS5_MihawkGen/external -Iheadless \
    extras/graphics/test_mihawk_vulkan_resources.cpp headless/mihawk_vulkan_resources.cpp
"$cxx" -std=c++20 -Wall -Wextra -Werror -fsyntax-only -DVK_NO_PROTOTYPES \
    -Ithird_party/PS5_MihawkGen/external -Iheadless -Iextras/graphics \
    -Ithird_party/PS5_MihawkGen/framegen/include \
    -include third_party/PS5_MihawkGen/ps5/third_party/volk/volk.h \
    headless/mihawk_vulkan_stage.cpp headless/mihawk_vulkan_resources.cpp
echo "PASS native Vulkan source syntax (volk/VK_NO_PROTOTYPES)"
python3 tools/graphics/verify-mihawkgen-source.py
echo 'R08 HOST PASS — native PS5 GPU and real game untested'
