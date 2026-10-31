# NSW2 N76 — upstream guest-counter-rate reconciliation (2026-10-31)

Source studied: Djihads80/Eglantine commit 0218eac:
https://github.com/Djihads80/Eglantine/commit/0218eac

Their confirmed Switch 2 SDK counter is 31.25 MHz, versus 19.2 MHz
on Switch 1. A 60 Hz frame corresponds to roughly 520833 guest CNT
ticks, not 320000. Wrong tick conversion can extend emulated waits.

## What is actually integrated

One shared CPU clock contract is owned by:
vendor/encore-active/eden-core/include/encore/guest_counter_policy.h

No game names/serials, duplicated core or separate emulator. The
existing Encore-maintained native cpu_features.cpp reads the rate for
x86-64 wall-clock CNTPCT; the existing Encore-maintained A64 host JIT
owner reads it for CNTFRQ_EL0 configuration. Validated NPDM retains
the existing first-generation identification; the real ExeFS
AppLoader_DeconstructedRomDirectory::Load selects the proper rate
after verifying the final program metadata and before loading guest
NSO modules. ProgramMetadata::Load itself intentionally has NO
side effects because scanners also read NPDM metadata during play.

Switch 1 and failed/unavailable research selection continue to use
19.2 MHz. A subsequent Switch 1 ExeFS load resets the rate even when
the process previously ran a Switch 2 title. The native x86 host
factor is computed once, not on every guest timer read.

## Qualification and limitations

EDEN_NS2_GUEST_COUNTER_EXPERIMENTAL=OFF by default, and PS5 native,
NS2 metadata, NS2 A64 and non-release are mandatory. The option
selects the SAME native common CPU owner and the maintained A64
frontend; it never copies the NS1 CPU implementation into another
directory.

tools/ns2/check_guest_counter_policy.py executes the actual vendor
policy under Clang/GCC UBSan (19.2 MHz, 31.25 MHz, one-second and
frame tick conversions, TSC multiplication, reset, absent TSC
calibration), and checks maintained source-owner hook locations.

Still to integrate and qualify: the non-multicore CoreTiming static
CPUTickToCNTPCT path, guest SVC/time-service ticks where a static
19.2 MHz conversion survives, and early boot order if host CPU
initialization precedes ExeFS metadata. This session does NOT
establish a PS5 bootable NS2 game or real frame rendering.

Related NSW2 comparison: docs/NS2_EGLANTINE_REAL_CONSOLE_GAP_AND_SHARED_ENGINE_N75_2026-10-31.md.
