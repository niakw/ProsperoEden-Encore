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
assert 'report.state = helper_ready ? Report::State::available' in services
assert 'std::filesystem::symlink_status("/app0/self-updater.elf", ec)' in services
assert 'native downloading' in helper.lower() or 'download' in helper.lower()
assert 'NATIVE_MINOR = 400' in version

assert '#include "network/room.h"' in services
assert 'Network::network_version' in services
assert 'ParseRoomDirectory(*response, 0)' not in services
assert '"/lobby"' in services
# User actions are now wired to real upstream Network::Room / RoomMember
# on a detached worker, not just read-only browser stubs.
assert 'Room joining is not available yet.' not in rooms
assert 'RoomAction::Join' in rooms and 'RoomAction::HostPrivate' in rooms
assert 'RoomAction::Leave' in rooms
assert 'detached_room_action_task(' in rooms
assert 'CanJoinPublicRoom(room)' in rooms
assert 'state->completed.store(true, std::memory_order_release)' in rooms
assert 'std::thread([state, task = std::move(task)]' in rooms
assert '#include "network/room_member.h"' in services
assert 'Network::Init()' in services
assert 'Network::GetRoomMember().lock()' in services
assert 'enet_host_create(nullptr, 1, Network::NumChannels, 0, 0)' in services
assert 'member->Join(nickname, address.c_str(), port)' in services
assert 'if (!Network::GetRoomMember().expired())' in services
assert 'CanJoinPublicRoom(' in source("headless/prosperoeden/room_directory.cpp")
assert 'RoomActionState' in source("headless/prosperoeden/pe/ui/launcher.hpp")
assert 'room_action_->completed.load(std::memory_order_acquire)' in source("headless/prosperoeden/pe/ui/launcher.cpp")
assert 'detached_room_directory_task()' in ui_services
assert 'return Eden::Multiplayer::ParseRoomDirectory(' in services
assert 'std::thread([state, task = std::move(task)]' in rooms

print("R14/R21 source PASS: official release origin, network actions on detached worker, PS5 still unvalidated")

native = source("headless/prosperoeden/native_app_update.cpp")
package = source("tools/package-headless-native.sh")
launcher = source("headless/prosperoeden/pe/ui/launcher.cpp")
cmake = source("headless/CMakeLists.txt")
assert '"/data/homebrew/PPSA99008/sce_sys/param.json"' in native
assert '"/niakw/ProsperoEden-Encore/releases/download/"' in native
assert 'VerifiedArchive validator(plan.bytes,plan.sha256)' in native
assert 'validator.Finish() && fsync(temp.fd) == 0' in native
assert '"/app0/self-updater.elf"' in native
assert 'SELF_UPDATE_LOADER_PORT' in native
assert 'if (!Until(socket,"ready",message))' in native
assert 'if (!Until(socket,"staged",message))' in native
assert 'socket.Text("apply")' in native
assert 'Until(socket,"applying",message)' in native
assert '"Native PS5 installer is unavailable on this host."' in native
assert '"/data/homebrew/PPSA99008"' not in native
assert 'self_update_helper' in package and 'self-updater.elf' in package
assert 'native_app_update.cpp' in cmake and 'self_update_sha256.c' in cmake
assert 'start_app_update_install()' in launcher
assert 'done_ = true;' in launcher
assert 'Confirmation::app_install' in launcher
assert 'detached_app_update_install_task(candidate)' not in launcher
assert 'detached_app_update_install_task(update_info_)' in launcher
assert 'check_updates_on_start = true' in source('headless/settings_store.h')
print("R21 native source PASS: consent, official URL, hash/size, helper handoff, rollback owner, exit after applying")
