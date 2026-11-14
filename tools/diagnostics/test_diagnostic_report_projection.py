#!/usr/bin/env python3
"""Synthetic-only offline tests. No native build, filesystem scan or transfer."""
import json
from diagnostic_report_projection import project, MAX_INPUT, MAX_WINDOWS
sha = "a"*40
private = b"username: Alice\nIP 192.0.2.1\nhttps://user:secret@example.test/foo\nregisters: 1234\n/home/private/prod.keys\n"
crash = b"what: SIGSEGV (invalid memory access), code 2, address 0x12345\nwatchdog suspected stalls: 2\n"
frame = b"EDEN_GAME_FRAME frames=150 seconds=5.000000 fps=30.000 worst_ms=105.000 total=300\n"
def result(data, category, consent=True):
    return project(data, category=category, consent=consent, source_sha=sha)
assert result(crash, "standard", False) is None
assert result(frame, "advanced", False) is None
assert result(private + crash + frame, "standard") == {
    "schema":1,"category":"standard","source_sha":sha,"signal":"SIGSEGV","watchdog_stalls":2}
assert result(private, "standard") is None
assert result(crash, "advanced") is None
assert result(frame, "standard") is None
assert result(frame.strip()+b" token=secret", "advanced") is None
assert result(private+frame, "advanced")["frames"] == [[150,5.0,30.0,105.0,300]]
assert len(result(frame*(MAX_WINDOWS+5),"advanced")["frames"]) == MAX_WINDOWS
assert len(json.dumps(result(frame*MAX_WINDOWS,"advanced")).encode()) < 32*1024
for invalid in (b"x"*(MAX_INPUT+1),):
    try:
        result(invalid,"standard")
    except ValueError:
        pass
    else:
        raise AssertionError("oversize accepted")
assert result(b"\xff\n"+crash, "standard")["signal"] == "SIGSEGV"
print("DIAGNOSTICS_PROJECTION_HOST_PASS default_off=1 categories_independent=1 raw_excluded=1 bounded=1")
