#!/usr/bin/env python3
"""Source contract for the native opt-in diagnostics client. No network I/O."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
client=(root/"headless/diagnostics_native_client.cpp").read_text()
header=(root/"headless/diagnostics_native_client.h").read_text()
queue=(root/"headless/diagnostics_report_queue.h").read_text()
frontend=(root/"headless/prosperoeden/frontend.cpp").read_text()
service_h=(root/"headless/prosperoeden/eden_services.h").read_text()
service=(root/"headless/prosperoeden/eden_services.cpp").read_text()
main=(root/"headless/main.cpp").read_text()
cmake=(root/"headless/CMakeLists.txt").read_text()
settings=(root/"headless/settings_store.h").read_text()

# Destination and transport are fixed HTTPS; no GitHub/Forgejo token or raw-log upload.
assert 'kCollector = "https://encore.dynv6.net"' in client
assert 'kReportsPath = "/api/diagnostics/v1/reports"' in client
assert 'kErasePath = "/api/diagnostics/v1/erase"' in client
assert client.count("Common::Net::PostJson(") == 2
assert 'work.report->envelope, 1)' in client
assert 'body.dump(), 1)' in client
for forbidden in ("Authorization", "github.com", "git.encore", "prod.keys", "username", "ip_address"):
    assert forbidden not in client

# Only allowlisted projections enter report JSON. Raw files are capped before parsing.
assert "kMaxReadBytes = 2u * 1024u * 1024u" in client
assert "DiagnosticsSharing::kMaxReportBytes" in client
for field in ("gpu_submitted_sample","gpu_completed_floor64","watchdog_stalls",
              "invalid_guest_accesses","frames","loading_waits"):
    assert field in client
assert 'report["source_sha"] = state.source_sha;' in client
assert 'Json envelope{{"report_id"' in client and '{"erase_token"' in client
assert '::chmod(staged.c_str(), 0600)' in client

# Report identities and erase secrets use the PS5 kernel RNG, not a stable device/user ID.
assert "sceRandomGetRandomNumber" in client
assert 'std::array<std::uint8_t, 16> uuid' in client
assert 'std::array<std::uint8_t, 32> erase' in client
assert 'libSceRandom.so' in cmake

# Explicit versioned consent, queue bounds, idle-only lifecycle and nonblocking detached transfer.
assert "sharing_consent_version" in settings
assert "bool log_sharing_available() const override;" in service_h
assert "DiagnosticsClient::Available()" in service
assert "DiagnosticsClient::SetConsent(" in service
for call in ("EnterLauncher(launch_error)","Activity()","Poll()","GameStarting()"):
    assert "DiagnosticsClient::"+call in frontend
assert "DiagnosticsClient::Shutdown()" in main
assert "idle_since_ = now;" in queue.split("void Activity(",1)[1].split("}",2)[0]
assert "std::thread(" in client and ").detach();" in client
assert "std::future<" not in client

# Crash handler never invokes the transport: reports are consumed only after launcher recovery.
crash=(root/"headless/crash_report.cpp").read_text()
assert "DiagnosticsClient" not in crash
assert "launch_error.starts_with(Eden::Crash::kNotice)" in client
assert "ReadSmallFile(path, kMaxReadBytes)" in client
print("DIAGNOSTICS_NATIVE_CLIENT_SOURCE_PASS https_only=1 projection_only=1 consent=1 idle=1 erase=1 nonblocking=1")
