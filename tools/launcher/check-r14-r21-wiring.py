#!/usr/bin/env python3
"""Offline source invariants for launcher update checks and public room browser."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def source(path):
    return (ROOT / path).read_text()

services = source("headless/prosperoeden/eden_services.cpp")
release = source("headless/prosperoeden/launcher_update_release.hpp")
rooms = source("headless/prosperoeden/pe/ui/multiplayer.cpp")
helper = source("headless/update_check/README.md")
ui_services = source("headless/prosperoeden/pe/ui/services.hpp")
version = source("tools/ci/native-content-version.py")

assert '/repos/niakw/ProsperoEden-Encore/releases/latest' in services
assert 'github.com/niakw/ProsperoEden-Encore/releases/download/' in release
assert 'niakw/Prospero.Eden-Encore' not in services
assert 'niakw/Prospero.Eden-Encore' not in release
assert 'SafeSha256(digest)' in release
assert 'SafeAssetName(name, tag)' in release
assert 'asset["browser_download_url"].get<std::string>() != expected' in release
assert 'data["draft"].get<bool>()' in release
assert 'data["prerelease"].get<bool>()' in release
assert 'State::newer_uninstallable' in services
assert 'report.state = Report::State::available;' not in services
assert 'native downloading' in helper.lower()
assert 'NATIVE_MINOR = 400' in version

assert '#include "network/room.h"' in services
assert 'Network::network_version' in services
assert 'ParseRoomDirectory(*response, 0)' not in services
assert '"/lobby"' in services
assert 'Room joining is not available yet.' in rooms
assert 'Public rooms (read-only)' in rooms
assert 'Network::GetRoomMember()' not in rooms
assert 'detached_room_directory_task()' in ui_services
assert 'return Eden::Multiplayer::ParseRoomDirectory(' in services
assert 'std::thread([state, task = std::move(task)]' in rooms

print("R14/R21 source PASS: active release origin, no native installer claims, linked lobby protocol, read-only joins")
