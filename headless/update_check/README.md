# Eden Encore — offline updater helper protocol subset

Only the offline helper dependencies from ProsperoEden / PS5 Native App Boilerplate
are used here: bounded metadata parsing, SHA-256, and helper protocol.

The helper builds with UPDATE_CHECK_NO_NETWORK. Native downloading, app-to-helper
handoff, signed catalog and restart are NOT linked to the launcher. The
GitHub Releases read-only discovery remains separate in the existing R21 UI.

Only /data/homebrew/PPSA99008 can be replaced. The helper rejects a staged
tree that would erase any existing file within a replaced directory. This
module is not included in the app image or installation by default.

Host tests: tools/launcher/check-self-update-folder.sh.
Full PS5 13.60 integration, download verification and restore remain open.

Upstream source: https://github.com/Swordpdf/ProsperoEden
Original boilerplate: https://github.com/blackbearreloaded/ps5-native-app-boilerplate
SPDX-License-Identifier: GPL-3.0-or-later
