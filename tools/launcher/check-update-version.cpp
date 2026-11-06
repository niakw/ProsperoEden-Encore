// SPDX-License-Identifier: GPL-3.0-or-later
// Offline compile-time checks for R21, including numeric and hostile tags.
#include "launcher_update_version.hpp"
using Eden::EncoreUpdate::ParseRevision;
static_assert(ParseRevision("R1", false) == 1);
static_assert(ParseRevision("R9", false) < ParseRevision("R10", false));
static_assert(ParseRevision("R1234", false) == 1234);
static_assert(ParseRevision("encore-R10-56293953", true) == 10);
static_assert(ParseRevision("R100", true) == 100);
static_assert(ParseRevision("encore-R11-12345", true) == -1);
static_assert(ParseRevision("encore-R11-1234567x", true) == -1);
static_assert(ParseRevision("encore-R11-12345678/evil", true) == -1);
static_assert(ParseRevision("R2-preview", false) == -1);
static_assert(ParseRevision("R100000000000000000", false) == -1);
static_assert(ParseRevision("v3.0.0", true) == -1);
int main() { return 0; }
