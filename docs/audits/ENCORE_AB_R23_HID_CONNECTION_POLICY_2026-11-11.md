# R23 #95 — HID button-triggered connection policy

Source comparison: Eden commit 87d2f03c39bc441055d593a7913f63a017795359; pinned vendor Gitlink 22b69d6053db41b74edac2633c012f925b84f69e.

Selected PS5 source: vendor/encore-active/eden-core/src/hid_core/frontend/emulated_controller.cpp (Git blob dba492c9d60e967cd051ff15e32ce2db0479830d). CMake selects it for hid_core. Pinned original blob: 1092970ee8fba966df0962d70142c4878b3d82ec.

Old source calls Connect() on a button change only when not already connected and the Handheld/Player1/secondary slot conditions are met. Upstream removes the separate per-slot controller_connected tracking and uses player.connected as the Connect decision, even when the controller is already connected.

The read-only source model tools/audit/check-r23-hid-button-connection-host.py inspects the maintained selected C++ branch and covers 48 input-state combinations. Divergent decisions are source-level evidence, not real NPad, callback, PS5 service or hardware behavior. Upstream is not automatically safer.

Classification: E1 verified relevant source gap awaiting native proof. Required: connected/disconnected Handheld, Player1, Player2, reconnect after sleep, repeated Connect idempotency, real NPad shared memory/event order and native PS5 build. Do not cherry-pick this cleanup as if it were mechanical.

Counts: runtime semantic review pending 66; 8 relevant source gaps awaiting PS5 proof; 155 total Eden commit decisions.
