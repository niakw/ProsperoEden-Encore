# Eden Encore — offline updater helper protocol subset

Only the offline helper dependencies from ProsperoEden / PS5 Native App Boilerplate
are used here: bounded metadata parsing, SHA-256, and helper protocol.

The helper builds with UPDATE_CHECK_NO_NETWORK. R21 now wires the app-side
bounded HTTPS download against official stable GitHub metadata, exact byte
length and SHA256, the bundled ELF transfer through loopback elfldr, and
the staged/apply handshake. The external helper independently rechecks
ZIP paths, installed title/contentVersion, file preservation and rollback.
No installation may occur without explicit confirmation from the user.
The normal app process closes only after the helper confirms "applying".

Only /data/homebrew/PPSA99008 can be replaced. The helper rejects a staged
tree that would erase any existing file within a replaced directory. The independent helper is built and copied as /app0/self-updater.elf in
a new native package. No user games, saves, keys or firmwares are touched.

Host tests: tools/launcher/check-self-update-folder.sh.
App-side integration is versioned and host syntax-tested; actual PS5
firmware 13.60 build, ELF-loader handoff, HTTPS/TLS, atomic replacement,
recovery and reboot must still be validated on a console. No successful
native PS5 update is claimed by these host tests.

Upstream source: https://github.com/Swordpdf/ProsperoEden
Original boilerplate: https://github.com/blackbearreloaded/ps5-native-app-boilerplate
SPDX-License-Identifier: GPL-3.0-or-later
