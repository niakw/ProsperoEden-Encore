# Diagnostic sharing: event-driven, opt-in, privacy-minimized

Implementation status, 16 November 2026: the controlled collector is deployed at
`https://encore.dynv6.net/api/diagnostics/v1/` and the VPS production proof
(run 43928528203) completed report acceptance, duplicate handling, authenticated
erasure and tombstone rejection. The native client is source/host-qualified in
the dependent engine PR; no PS5 transmission claim is made until the next native
build and console test.

The project website niakw/encore-website is a static nginx runtime (Dockerfile 9afc5068b5c80c6924431f365066f5507cc0a667). It has no collector today. The intended independent HTTPS service is separate from static asset serving, on Encore's controlled infrastructure. No GitHub/Forgejo credentials on PS5. Both destinations must be private; Git history is not an erasable log database. Store actual reports in expiring private storage, mirror reviewed nonpersonal aggregates/receipts in separate diagnostics/standard and diagnostics/advanced folders. If individual report mirroring is required, use encrypted report blobs with revocable keys and a tested deletion policy across backups; do not commit raw logs. No public report dump in engine or vendor.

### Event contract and initial tunables
- Default off, category-specific consent; collecting detailed logs and sharing are independent. Versioned consent, no legacy inheritance. Explicit Cross for share changes. Retain local crash reports independently.
- Game exit (after workers joined): snapshot only closed approved log records, enqueue at most one bounded report per category per session; send only after returning to idle launcher for five seconds. Never send during game startup, gameplay, emulation loading, audio/rendering or shutdown.
- App exit: do not delay exit; persist small pending summary if safe or defer preparation to next launch. Cancel any transfer on departure. No new network request on exit.
- Crash: never touch network, JSON, filesystem traversal or queue locks in signal handler; existing report remains local. Read on later healthy launcher start, only if report was generated after opt-in. Revoking a category clears unsent data, invalidates leases, cancels transfers/retries. Needs owner integration and durable per-category consent epochs.
- Prototype gate: 4 queued reports maximum, 32 KiB per report, one in-flight request, max 2 attempts per launcher visit, at least 30 seconds between attempts, 5-second transfer limit, at least 5 seconds idle. Bound queue bytes to 128 KiB; deduplicate; preserve standard crash priority, oldest advanced evicted first. Retry with backoff only on later idle visit, no polling during gameplay. On low-memory/network failure skip sharing rather than affect play. Do not claim timing/queue enforcement until actual worker wired and measured.
- Default deny input projection: crash signal and bounded counters, exact source SHA from trusted build metadata, frame/present timing and GPU progress; exclude arbitrary messages, absolute pointers, registers, IP/MAC, paths, game filenames, IP/network-accepted logs, keys, credentials, memory dumps, screenshots, input samples, saves. Title ID, symbolized relative offsets and shader/pipeline counters may be added after separate schema review. Report ID random per report, no permanent device identifier. Treat remaining data as potentially personal.
- HTTPS certificate validation, strict receive schema and size caps, server-side rate limit and duplicate delivery handling, one receipt per destination, no request body/access IP logging beyond strictly necessary security retention. No silent retry while playing. Proposed retention 30 days, notice and withdrawal/erasure/contact before activation; never assert legal certification. See CNIL https://www.cnil.fr/fr/comprendre-le-rgpd/les-six-grands-principes-du-rgpd. Upstream design reference Dolphin opt-in analytics https://dolphin-emu.org/docs/privacy/ (published category and retention policy); our approach intentionally avoids stable analytics IDs and raw reports. Existing Encore crash and frame owners reviewed.

### State
UI/persistence, C++ pure admission policy (not yet called) and offline Python reference projection/test. Collector, durable queue, native owner calls, consent epoch and actual transmission not implemented. Settings sharing availability remains false by design. Additional locale translations, synthetic host/relay and PS5 validation pending. No native build without user consent.


### Implemented native client contract (source/host; PS5 runtime pending)
- `DiagnosticsClient::Initialize` performs no network request and accepts only the exact 40-hex build SHA compiled into the native app.
- User consent remains category-specific and versioned. Revocation immediately drops unsent reports and schedules authenticated erasure of accepted reports.
- Report identity is per-report UUIDv4 and the 256-bit erase secret is generated from `sceRandomGetRandomNumber`; no account, console, IP or device identifier is included.
- Crash evidence is projected only after the next healthy launcher opens. Raw reports/logs are never used as the request body.
- Advanced metrics are projected only from the closed game-session log range after returning to the launcher.
- Transfers start only after five seconds of launcher inactivity, maximum two attempts per visit, one detached request at a time, one-second HTTP timeout. Game start, shutdown, activity or consent changes cancel queue ownership; no transfer is initiated from a render, guest or crash thread.
- Local pending/erasure state is bounded and atomically stored mode 0600. The collector caps requests at 32 KiB and retains private reports for 30 days.
- Production collector deployment is independent from the app build. Native build, PS5 toggle behavior, DNS/TLS and real report delivery/erasure remain explicit hardware acceptance gates.
