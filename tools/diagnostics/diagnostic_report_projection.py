#!/usr/bin/env python3
"""Offline schema prototype: numeric allowlist, never raw logs or network I/O."""
import re
MAX_INPUT = 2*1024*1024
MAX_WINDOWS = 120
MAX_LINE = 512
UINT = r"[0-9]{1,12}"
DEC = r"[0-9]{1,8}(?:\.[0-9]{1,6})?"
SIGNALS = {"SIGSEGV","SIGBUS","SIGILL","SIGFPE","SIGABRT","SIGSYS","SIGTRAP"}
COUNTERS = {
    "gpu submitted lists (sample 1/2/3 then 64-step)": "gpu_submitted_sample",
    "gpu completed commands (64-step sample)": "gpu_completed_floor64",
    "watchdog suspected stalls": "watchdog_stalls",
    "invalid guest-memory accesses": "invalid_guest_accesses",
}
FRAME = re.compile(r"EDEN_GAME_FRAME frames=(" + UINT + r") seconds=(" + DEC +
                   r") fps=(" + DEC + r") worst_ms=(" + DEC + r") total=(" + UINT + r")")
WAIT = re.compile(r"EDEN_VULKAN_LOADING_WAIT stage=(10|30)s idle=([01]) loading_presents=(" +
                  UINT + r") guest_frame_handoff=0 gpu_submit_sample=(" + UINT +
                  r") gpu_worker_completed_floor64=(" + UINT +
                  r") gpu_worker_delta_floor64=(" + UINT + r") gpu_worker_counter_reset=([01])")

def project(raw: bytes, *, category: str, consent: bool, source_sha: str):
    if consent is not True:
        return None
    if category not in ("standard", "advanced"):
        raise ValueError("unknown category")
    if not isinstance(raw, bytes) or len(raw) > MAX_INPUT:
        raise ValueError("report input exceeds budget")
    if not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("invalid build provenance")
    report = {"schema": 1, "category": category, "source_sha": source_sha}
    frames, waits = [], []
    for line in raw.splitlines():
        if len(line) > MAX_LINE:
            continue
        try:
            line = line.decode("ascii")
        except UnicodeDecodeError:
            continue
        if category == "standard":
            m = re.fullmatch(r"what: (SIG[A-Z]+) \([a-z ]+\)(?:, code [0-9]{1,20}, address 0x[0-9a-fA-F]{1,16})?", line)
            if m and m[1] in SIGNALS:
                report.setdefault("signal", m[1])
            for label, key in COUNTERS.items():
                m = re.fullmatch(re.escape(label) + ": (" + UINT + ")", line)
                if m:
                    report.setdefault(key, int(m[1]))
        else:
            m = FRAME.fullmatch(line)
            if m and len(frames) < MAX_WINDOWS:
                frames.append([int(m[1]), float(m[2]), float(m[3]), float(m[4]), int(m[5])])
            m = WAIT.fullmatch(line)
            if m and len(waits) < 8:
                waits.append([int(x) for x in m.groups()])
    if category == "standard":
        return report if "signal" in report else None
    if not frames and not waits:
        return None
    report.update(frames=frames, loading_waits=waits)
    return report
