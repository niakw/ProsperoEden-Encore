#!/usr/bin/env bash
# Compile and test the directory updater on host. Never touches the console.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
temp="$(mktemp -d "${TMPDIR:-/tmp}/encore-self-update.XXXXXXXX")"
trap 'rm -rf "$temp"' EXIT
cc="${CC:-clang}"
cxx="${CXX:-clang++}"
common=( -DUPDATE_CHECK_NO_NETWORK -I"$root/headless/update_check" -I"$root/third_party" -I"$root/headless/self_update_helper" )
if [[ "$(uname)" == Darwin ]]; then
    sdk="/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk"
    [[ -d "$sdk" ]] && common+=( -isysroot "$sdk" )
fi
"$cc" -std=c11 -O0 "${common[@]}" -c \
  "$root/headless/update_check/update_check.c" -o "$temp/check.o"
"$cc" -std=c11 -O0 "${common[@]}" -c \
  "$root/headless/update_check/self_update_sha256.c" -o "$temp/sha.o"
for name in miniz miniz_zip miniz_tdef miniz_tinfl; do
    "$cc" -std=c11 -O0 "${common[@]}" -c \
      "$root/third_party/miniz/${name}.c" -o "$temp/${name}.o"
done
"$cxx" -std=c++20 -O0 "${common[@]}" -pthread \
  "$root/headless/self_update_helper/encore_target_check.cpp" \
  "$root/headless/self_update_helper/updater.cpp" \
  "$root/headless/self_update_helper/archive.cpp" \
  "$root/headless/self_update_helper/files.cpp" "$temp/"*.o \
  -o "$temp/helper-check"
"$cxx" -std=c++20 -O0 "${common[@]}" -pthread   "$root/tools/launcher/helper_archive_check.cpp"   "$root/headless/self_update_helper/archive.cpp"   "$root/headless/self_update_helper/files.cpp" "$temp/"*.o   -o "$temp/archive-check"
python3 "$root/tools/launcher/test_native_helper_archive.py" "$temp/archive-check"
"$temp/helper-check"
"$cxx" -std=c++20 -O0 "${common[@]}" -pthread \
  "$root/headless/self_update_files_check.cpp" \
  "$root/headless/self_update_helper/files.cpp" -o "$temp/files-check"
"$temp/files-check"
echo "R21 helper host: exact target, preservation, backups and file moves PASS"
