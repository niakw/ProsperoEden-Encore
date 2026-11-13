#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Execute the real OpenGL Ninja adapter against a fake child process."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
helper = ROOT / "tools/ci/ninja-no-jobserver.sh"
sdk = (ROOT / "tools/build-opengl-sdk.sh").read_text()
assert 'ninja-no-jobserver.sh' in sdk
assert 'opengl-ninja-wrapper' in sdk
assert 'PATH="$ninja_wrapper_dir:$opengl_host_path" make' in sdk

with tempfile.TemporaryDirectory() as tmp:
    fake = Path(tmp, "ninja")
    fake.write_text(
        '#!/bin/sh\n'
        'printf "MAKEFLAGS:%s\\n" "${MAKEFLAGS-<unset>}"\n'
        'printf "MFLAGS:%s\\n" "${MFLAGS-<unset>}"\n'
        'printf "GNUMAKEFLAGS:%s\\n" "${GNUMAKEFLAGS-<unset>}"\n'
        'printf "ARG:%s\\n" "$@"\n'
    )
    fake.chmod(0o755)

    env = os.environ.copy()
    env.update(MAKEFLAGS="-j8 --jobserver-auth=3,4", MFLAGS="-j8",
               GNUMAKEFLAGS="-j8", EDEN_OPENGL_NINJA_JOBS="4")
    completed = subprocess.run(
        ["sh", str(helper), str(fake), "-C", "mesa-cache", "src/util/libmesa_util.a"],
        env=env, text=True, capture_output=True, check=True,
    )
    lines = completed.stdout.splitlines()
    assert lines == [
        "MAKEFLAGS:<unset>", "MFLAGS:<unset>", "GNUMAKEFLAGS:<unset>",
        "ARG:-j4", "ARG:-C", "ARG:mesa-cache", "ARG:src/util/libmesa_util.a",
    ], lines

    for count in ("0", "17", "invalid", "-1", ""):
        env["EDEN_OPENGL_NINJA_JOBS"] = count
        run = subprocess.run(
            ["sh", str(helper), str(fake)], env=env,
            text=True, capture_output=True,
        )
        assert run.returncode != 0, (count, run.stdout, run.stderr)
    run = subprocess.run(
        ["sh", str(helper), "relative/ninja"], env=env,
        text=True, capture_output=True,
    )
    assert run.returncode != 0

print("OPENGL_NINJA_ISOLATED_JOBSERVER_HOST_PASS")
