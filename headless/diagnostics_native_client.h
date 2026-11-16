// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string_view>

namespace Eden::DiagnosticsClient {

// The HTTPS collector is an optional, privacy-minimized launcher service.
// Initialization never opens a connection.
void Initialize(std::string_view source_sha);
bool Available() noexcept;

// Called only by the launcher/main lifecycle, never by a render/guest/crash thread.
void EnterLauncher(std::string_view launch_error);
void Activity() noexcept;
void Poll();
void GameStarting() noexcept;
void Shutdown() noexcept;

// Versioned Settings consent. Revocation purges unsent reports and schedules
// erasure of already accepted reports.
void SetConsent(bool standard, bool advanced);

} // namespace Eden::DiagnosticsClient
