#!/usr/bin/env python3
"""PS5 fatal/teardown safety policy: never auto-relaunch broken native state."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
stop=(ROOT/"headless/stop_limit.cpp").read_text()
crash=(ROOT/"headless/crash_report.cpp").read_text()
main=(ROOT/"headless/main.cpp").read_text()
life=(ROOT/"src/lifecycle.c").read_text()

assert 'extern "C" int eden_exit_app(void);' in stop
assert 'eden_restart_app' not in stop
assert 'void exit_now() noexcept' in stop
assert '(void)eden_exit_app();' in stop
assert stop.index('write(fd, "1\\n", 2)') < stop.index('(void)eden_exit_app();')
assert 'exiting app without automatic restart' in stop

# Fatal signals already fail closed on PS5; keep that invariant aligned with
# the teardown watchdog instead of creating a second restart path.
ps5=crash.split("#ifdef PS5_NATIVE",1)[1].split("#else",1)[0]
assert "const bool restart = false;" in ps5
assert 'if (!leave.load(std::memory_order_acquire)) eden_restart_app();' in crash
assert 'eden_exit_app();' in crash
assert 'closed without automatic restart to protect console state' in main

# Lifecycle keeps an explicit restart primitive for intentional non-crash
# flows, but the stop watchdog must not call it.
assert "int eden_restart_app(void)" in life
assert "int eden_exit_app(void)" in life
print("P0_PS5_STOP_FAIL_CLOSED_PASS crash_restart=0 stop_restart=0 note_before_exit=1 hardware=unverified")
