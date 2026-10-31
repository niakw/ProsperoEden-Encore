#!/usr/bin/env python3
"""Install maintained CPU I-cache and host service-wait sources unconditionally.

Production copies complete checked-in sources from vendor/encore-active.
The two historical patches are replayed only into a temporary comparison
tree to prove byte-for-byte parity. Any difference fails closed.
The quarantined dummy-thread workaround remains excluded (unsafe wait queue).
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "vendor/sources/eden"
ACTIVE = ROOT / "vendor/encore-active/eden-core"
PATCHES = (
    ROOT / "headless/backports/eden-dynarmic-icache-coherence.patch",
    ROOT / "headless/backports/eden-sm-host-wait.patch",
)
PIN = "5f142c7926d0c7fcbbd0ce30794d72f638a43b2a"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def affected() -> list[str]:
    names = set()
    for patch in PATCHES:
        data = patch.read_text(encoding="utf-8")
        for line in data.splitlines():
            if line.startswith("+++ b/"):
                rel = line[6:]
                if not rel.startswith("src/") or ".." in Path(rel).parts:
                    raise RuntimeError(f"Invalid target in {patch}: {rel}")
                names.add(rel)
    if len(names) != 5:
        raise RuntimeError(f"Expected exactly five core patch sources: {sorted(names)}")
    return sorted(names)


def derive() -> dict[str, tuple[bytes, bytes]]:
    files = affected()
    with tempfile.TemporaryDirectory(prefix="encore-active-core-") as temp:
        stage = Path(temp)
        for relative in files:
            source = ORIGINAL / relative
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for patch in PATCHES:
            result = subprocess.run(
                ["patch", "--batch", "--fuzz=0", "-p1", "-d", str(stage)],
                input=patch.read_bytes(), capture_output=True, timeout=20,
            )
            if result.returncode:
                raise RuntimeError(
                    f"{patch.name}: pinned source does not accept patch: "
                    f"{result.stderr.decode(errors='replace')[-1200:]} "
                    f"{result.stdout.decode(errors='replace')[-1200:]}"
                )
        result = {}
        for relative in files:
            old = (ORIGINAL / relative).read_bytes()
            new = (stage / relative).read_bytes()
            if old == new:
                raise RuntimeError(f"Unapplied active patch: {relative}")
            result[relative] = (old, new)
        return result


def stage_source(destination: Path, expected: dict[str, tuple[bytes, bytes]], *, check: bool) -> None:
    if (destination / "GIT-COMMIT").read_text().strip() != PIN:
        raise RuntimeError("Wrong pinned core revision")
    changed = 0
    for relative, (old, new) in expected.items():
        target = destination / relative
        # The old patches are replayed to a temporary tree as a parity oracle.
        # The source installed into the native build comes only from Encore.
        maintained = ACTIVE / relative
        if not maintained.is_file():
            raise RuntimeError(f"Missing maintained active-core source: {relative}")
        maintained_bytes = maintained.read_bytes()
        if maintained_bytes != new:
            # N76 is a guarded, exact additive extension of the canonical
            # A64 JIT source; reject all other source drift.
            if relative != "src/core/arm/dynarmic/arm_dynarmic_64.cpp":
                raise RuntimeError(f"Unreviewed active-core patch drift: {relative}")
            header = "#ifdef EDEN_NS2_GUEST_COUNTER\n#include \"encore/guest_counter_policy.h\"\n#endif\n".encode()
            guest_counter = "#ifdef EDEN_NS2_GUEST_COUNTER\n    // Set before JIT is instantiated; never hardcode a game-specific name.\n    config.cntfrq_el0 = static_cast<u32>(Eden::GuestCounter::Rate());\n#else\n    config.cntfrq_el0 = Hardware::CNTFREQ;\n#endif".encode()
            original_counter = b"    config.cntfrq_el0 = Hardware::CNTFREQ;"
            if (maintained_bytes.count(header) != 1 or
                    maintained_bytes.count(guest_counter) != 1 or
                    maintained_bytes.replace(header, b"").replace(
                        guest_counter, original_counter) != new):
                raise RuntimeError("N76 modified unrelated native A64 source")
        current = target.read_bytes()
        if current == maintained_bytes:
            continue
        if check or current not in (old, new):
            raise RuntimeError(
                f"Active source missing/unknown revision: {relative} "
                f"current={sha(current)} base={sha(old)} active={sha(maintained_bytes)}"
            )
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            tmp = Path(handle.name)
        try:
            shutil.copyfile(maintained, tmp)
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
        changed += 1
    print(f"EDEN_ACTIVE_CORE_BACKPORTS files={len(expected)} changed={changed} "
          "icache=on service_wait=on dummy_wait=quarantined")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = derive()
    if args.destination:
        stage_source(args.destination, expected, check=args.check)
    else:
        print(f"EDEN_ACTIVE_CORE_PATCH_REPLAY_OK files={len(expected)} "
              "icache=on service_wait=on")
if __name__ == "__main__":
    main()
