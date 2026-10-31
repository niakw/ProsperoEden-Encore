#!/usr/bin/env python3
"""FC27-shaped offline stress oracle, NOT an emulated FC27 game/GPU."""
from __future__ import annotations
import argparse
from collections import OrderedDict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/fixtures/fc27-2efd8b3c-stutter-windows.json"
SHA = "2efd8b3c96608667a2b22f1751eed1a475091cce"
FIELDS = ("total", "frames", "seconds", "fps", "worst_ms", "late50",
          "late100", "late200", "late500", "cache_wait_ms", "cache_contended",
          "jit_ms", "guest_ipc_ms", "guest_dequeue_ms", "gpu_idle_ms",
          "gpu_dispatch_ms", "gpu_fence_ms", "gpu_full_ms",
          "cache_buffer_wait_ms", "cache_texture_wait_ms")


def capture(path: Path = FIXTURE) -> list[dict[str, float]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("source_sha") != SHA or doc.get("fields") != list(FIELDS):
        raise ValueError("Untrusted or incompatible FC27 telemetry")
    raw = doc.get("rows")
    if not isinstance(raw, list) or len(raw) != 415:
        raise ValueError("Expected 415 historical windows")
    rows = [dict(zip(FIELDS, row, strict=True)) for row in raw]
    if (int(rows[0]["total"]) != 130 or int(rows[-1]["total"]) != 60955
        or any(a["total"] >= b["total"] for a, b in zip(rows, rows[1:]))
        or any(r["seconds"] <= 0 or r["frames"] <= 0 or
               r["late50"] < r["late100"] or r["late100"] < r["late500"]
               for r in rows)):
        raise ValueError("Malformed FC27 timeline")
    return rows


@dataclass
class Texture:
    revision: int = 0
    epoch: int = 0


class CacheModel:
    """Independent texture version oracle with intentionally broken variants."""
    def __init__(self, capacity: int = 96):
        self.truth: dict[str, Texture] = {}
        self.views: OrderedDict[str, tuple[int, int]] = OrderedDict()
        self.capacity = capacity
        self.draws = self.writes = self.remaps = self.evictions = 0
        self.stale = self.black = self.peak = 0

    def write(self, key: str, remap: bool = False) -> None:
        t = self.truth.setdefault(key, Texture())
        t.revision += 1
        self.writes += 1
        if remap:
            t.epoch += 1
            self.remaps += 1

    def draw(self, key: str, tick: int, fault: str | None) -> None:
        t = self.truth.setdefault(key, Texture())
        truth = (t.revision, t.epoch)
        cached = self.views.get(key)
        if fault == "black" and tick > 100 and tick % 53 == 0:
            shown = None
        elif fault == "stale" and cached is not None and cached != truth:
            shown = cached
        else:
            shown = truth
            self.views[key] = shown
            self.views.move_to_end(key)
            if len(self.views) > self.capacity:
                self.views.popitem(last=False)
                self.evictions += 1
        self.draws += 1
        self.peak = max(self.peak, len(self.views))
        self.black += int(shown is None)
        self.stale += int(shown is not None and shown != truth)

    def run(self, rows: list[dict[str, float]], factor: int,
            fault: str | None = None) -> dict[str, int]:
        if factor not in (1, 4, 8):
            raise ValueError("Only x1/x4/x8 research stress allowed")
        tick = 0
        for row in rows:
            # Counts are measured; individual events are SYNTHETIC. Never
            # attribute these fake texture events to actual FC27 frames.
            for _ in range(round(row["frames"]) * factor):
                hud = f"hud:{tick % 24}"
                pitch = f"pitch:{tick % 64}"
                kit = f"kit:{tick % 96}"
                if tick % 5 == 0 or tick % 17 == 0:
                    self.write(hud, remap=tick % 17 == 0)
                if tick % 23 == 0:
                    self.write(pitch, remap=tick % 69 == 0)
                if tick % 31 == 0:
                    self.write(kit, remap=tick % 93 == 0)
                if tick % 47 == 0:
                    self.views.pop(hud, None)
                self.draw(hud, tick, fault)
                self.draw(pitch, tick, None)
                self.draw(kit, tick, None)
                tick += 1
        return {key: getattr(self, key) for key in (
            "draws", "writes", "remaps", "evictions", "stale", "black", "peak")}


def queue_model(rows: list[dict[str, float]], factor: int,
                capacity: int = 32) -> dict[str, int]:
    # Explicit counterfactual: ONE worker at 60 units/sec, NOT actual RADV
    # throughput, and no claim about the actual driver queue.
    backlog = peak = pressure = 0
    for row in rows:
        arrivals = round(row["frames"]) * 2 * factor
        service = round(row["seconds"] * 60)
        backlog = max(0, backlog + arrivals - service)
        if backlog > capacity:
            pressure += backlog - capacity
            backlog = capacity
        peak = max(peak, backlog)
    return {"capacity": capacity, "peak": peak, "backpressure": pressure}


def frozen_progress() -> dict[str, int]:
    """Synthetic producer stops 750ms while compositor stays at 30Hz."""
    previous = None
    repeats = run = longest = 0
    for frame in range(90):
        ms = frame * 1000 / 30
        guest_revision = 29 if 1000 <= ms < 1750 else frame
        if guest_revision == previous:
            repeats += 1
            run += 1
        else:
            longest = max(longest, run)
            run = 0
        previous = guest_revision
    return {"present_fps": 30, "present_late50": 0,
            "repeated_content": repeats, "longest_repeat": max(run, longest)}


def exercise(rows: list[dict[str, float]]) -> dict[str, Any]:
    late50 = round(sum(r["late50"] for r in rows))
    late500 = round(sum(r["late500"] for r in rows))
    worst = max(r["worst_ms"] for r in rows)
    if late50 != 858 or late500 != 10 or not 1288 < worst < 1289:
        raise AssertionError("Historical FC27 stutter baseline changed")
    report: dict[str, Any] = {
        "historical_measured": {
            "sha": SHA, "windows": 415, "present_callbacks": 60955,
            "late50": late50, "late500": late500,
            "worst_ms": round(worst, 3), "stutter_sla": "FAIL"},
        "synthetic_only": {},
    }
    for factor in (1, 4, 8):
        cache = CacheModel()
        stats = cache.run(rows, factor)
        if stats["stale"] or stats["black"] or stats["peak"] > cache.capacity:
            raise AssertionError(f"x{factor}: broken HUD texture freshness")
        report["synthetic_only"][f"x{factor}"] = {
            "cache": stats, "queue": queue_model(rows, factor)}
    stale = CacheModel().run(rows[:12], 8, "stale")
    black = CacheModel().run(rows[:12], 4, "black")
    freeze = frozen_progress()
    if (stale["stale"] == 0 or black["black"] == 0 or
        freeze["repeated_content"] < 20 or freeze["longest_repeat"] < 20 or
        report["synthetic_only"]["x4"]["queue"]["backpressure"] == 0 or
        report["synthetic_only"]["x8"]["queue"]["backpressure"] == 0):
        raise AssertionError("Deliberate FC27-style fault escaped detector")
    report["fault_injection"] = {
        "stale_descriptors_caught": stale["stale"],
        "missing_hud_caught": black["black"],
        "frozen_guest_at_30_fps": freeze}
    report["proof"] = ("Historic five-second counters + adversarial models "
                       "only. No native GPU pixels, PS5 console or NSW2 game boot.")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, default=FIXTURE)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = exercise(capture(args.fixture))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("FC27_STRESS_ORACLE_PASS; measured=415 windows; synthetic=x1/x4/x8;"
          " injected stale HUD, black HUD, and frozen guest all detected")
    print(json.dumps({
        "measured": report["historical_measured"],
        "x8": report["synthetic_only"]["x8"],
        "fault_detection": report["fault_injection"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
