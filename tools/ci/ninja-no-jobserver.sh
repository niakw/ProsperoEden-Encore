#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU Make 4.3 exposes only a pipe-style jobserver; Ninja cannot consume it.
# Drop the *inherited* Make protocol for this Ninja child only while keeping
# an explicit bounded worker count. The parent Make/PSBC build remains parallel.
set -eu
if [ "$#" -lt 1 ]; then
    echo 'usage: ninja-no-jobserver.sh /absolute/path/to/ninja [ninja arguments]' >&2
    exit 2
fi
ninja=$1
shift
case "$ninja" in
    /*) ;;
    *) echo 'expected an absolute path to the original ninja executable' >&2; exit 2 ;;
esac
jobs=${EDEN_OPENGL_NINJA_JOBS-4}
case "$jobs" in
    ''|*[!0-9]*) echo 'invalid Ninja worker count' >&2; exit 2 ;;
esac
if [ "$jobs" -lt 1 ] || [ "$jobs" -gt 16 ]; then
    echo 'Ninja worker count must be between 1 and 16' >&2
    exit 2
fi
unset MAKEFLAGS MFLAGS GNUMAKEFLAGS
exec "$ninja" -j"$jobs" "$@"
