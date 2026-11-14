// SPDX-License-Identifier: GPL-3.0-or-later
// R14: public room discovery plus user-initiated ENet join / private LAN host.
// Transport is handled by the upstream network objects on a detached worker;
// guest LDN packet flow and console behaviour still require PS5 validation.
#include "pe/ui/launcher.hpp"

#include <algorithm>
#include <exception>
#include <memory>
#include <thread>

namespace pe::ui {

using audio::Cue;

void Launcher::refresh_multiplayer()
{
    if (room_load_ && !room_load_->completed.load(std::memory_order_acquire))
        return;
    auto task = services_.detached_room_directory_task();
    if (!task) {
        room_directory_ = {{}, "Public room service unavailable."};
        rooms_loaded_ = true;
        return;
    }
    auto state = std::make_shared<RoomLoadState>();
    room_load_ = state;
    rooms_loaded_ = false;
    // A destroyed launcher must not cause a use-after-free while waiting
    // on the network. No lambda captures Launcher or Services.
    std::thread([state, task = std::move(task)]() mutable {
        try {
            state->result = task();
        } catch (const std::exception&) {
            state->result = {{}, "Public room service unavailable."};
        } catch (...) {
            state->result = {{}, "Public room service unavailable."};
        }
        state->completed.store(true, std::memory_order_release);
    }).detach();
}

void Launcher::enter_multiplayer()
{
    open(Screen::multiplayer, true);
    if (!rooms_loaded_ && !room_load_)
        refresh_multiplayer();
}

void Launcher::press_multiplayer(Key key)
{
    const auto begin_action = [this](Eden::Multiplayer::RoomAction action,
                                     Eden::Multiplayer::PublicRoom room = {}) {
        if (room_action_) return;
        auto task = services_.detached_room_action_task(action, room);
        if (!task) {
            say(tr(TR("Room not available.")), true);
            cue(Cue::error);
            return;
        }
        auto state = std::make_shared<RoomActionState>();
        room_action_ = state;
        std::thread([state, task = std::move(task)]() mutable {
            try {
                state->result = task();
            } catch (...) {
                state->result = {false, "Room not available."};
            }
            state->completed.store(true, std::memory_order_release);
        }).detach();
        say(tr(TR("Connecting to room...")), false);
        cue(Cue::focus);
    };
    // No second operation while a join/host/leave worker is active.
    // Circle still allows navigation away without destroying task state.
    if (room_action_ && key != Key::circle)
        return;
    switch (key) {
    case Key::circle:
        open(Screen::home, false);
        return;
    case Key::triangle:
        refresh_multiplayer();
        cue(Cue::focus);
        return;
    case Key::up:
        room_selected_ = std::max(0, room_selected_ - 1);
        cue(Cue::focus);
        return;
    case Key::down:
        room_selected_ = std::min(
            std::max(0, static_cast<int>(room_directory_.rooms.size()) - 1),
            room_selected_ + 1);
        cue(Cue::focus);
        return;
    case Key::cross:
        if (rooms_loaded_ && !room_directory_.rooms.empty()) {
            const auto& room = room_directory_.rooms[static_cast<std::size_t>(
                std::clamp(room_selected_, 0, static_cast<int>(room_directory_.rooms.size()) - 1))];
            if (Eden::Multiplayer::CanJoinPublicRoom(room)) {
                begin_action(Eden::Multiplayer::RoomAction::Join, room);
                return;
            }
        }
        say(tr(TR("Room not available.")), true);
        cue(Cue::error);
        return;
    case Key::square:
        begin_action(services_.room_connected()
            ? Eden::Multiplayer::RoomAction::Leave
            : Eden::Multiplayer::RoomAction::HostPrivate);
        return;
    default:
        return;
    }
}

void Launcher::draw_multiplayer(Canvas &c)
{
    const bool paper = prefs_.ui_theme == 1;
    if (paper) draw_switch_header(c, tr("Multiplayer"));
    else draw_top_nav(c, -1);

    const Color primary = paper ? Color::rgb(0x252b33) : theme::kTitle;
    const Color secondary = paper ? Color::rgb(0x55616b) : theme::kBody;
    const Color panel = paper ? Color::rgb(0xffffff) : theme::kPanel;
    const Color selected = paper ? Color::rgb(0xe4f3f4) : theme::kGlass;
    const Color border = paper ? Color::rgb(0x0a8d9a) : theme::kLimePale;

    text_shrink(c, tr("Multiplayer"), 106.0f,
                baseline(141.0f, 54.0f, theme::kHeading), theme::kHeading,
                primary, 1590.0f);
    text_shrink(c, tr(TR("Public rooms")), 112.0f,
                baseline(213.0f, 35.0f, theme::kSmall), theme::kSmall,
                secondary, 1540.0f);
    text_shrink(c, room_action_ ? tr(TR("Connecting to room...")) :
                (services_.room_connected() ? tr(TR("Connected to room")) :
                 tr(TR("Choose a room to join or host a LAN room."))), 112.0f,
                baseline(256.0f, 34.0f, theme::kSmall), theme::kSmall,
                secondary, 1540.0f);

    constexpr float x = 108.0f;
    constexpr float top = 316.0f;
    constexpr float height = 82.0f;
    constexpr float gap = 8.0f;
    constexpr int visible = 6;
    const auto count = static_cast<int>(room_directory_.rooms.size());
    const int offset = count <= visible ? 0 :
        std::clamp(room_selected_ - visible / 2, 0, count - visible);

    if (!rooms_loaded_) {
        text_shrink(c, tr("Checking public rooms..."), 128.0f,
                    baseline(top + 58.0f, 42.0f, theme::kText24),
                    theme::kText24, secondary, 1450.0f);
    } else if (!room_directory_.error.empty()) {
        text_shrink(c, tr("Public room service unavailable."), 128.0f,
                    baseline(top + 58.0f, 42.0f, theme::kText24),
                    theme::kText24, secondary, 1450.0f);
    } else if (count == 0) {
        text_shrink(c, tr("No public rooms to display."), 128.0f,
                    baseline(top + 58.0f, 42.0f, theme::kText24),
                    theme::kText24, secondary, 1450.0f);
    } else {
        for (int i = offset; i < std::min(count, offset + visible); ++i) {
            const float y = top + (height + gap) * float(i - offset);
            const bool focus = i == room_selected_;
            const Rect r{x, y, 1704.0f, height};
            c.list.rounded_rect(r, 16.0f, panel_fill(focus ? selected : panel));
            if (focus)
                c.list.bordered_rect(r, 16.0f, Color::rgb(0x000000, 0.0f),
                                     2.3f, border);
            const auto& room = room_directory_.rooms[static_cast<std::size_t>(i)];
            text_shrink(c, room.name, x + 25.0f,
                        baseline(y + 6.0f, 35.0f, theme::kText24),
                        theme::kText24, primary, 860.0f);
            text_shrink(c, room.game, x + 25.0f,
                        baseline(y + 45.0f, 25.0f, theme::kSmall),
                        theme::kSmall, secondary, 900.0f);
            const auto population = std::to_string(room.players) + " / " +
                                    std::to_string(room.capacity);
            text_shrink(c, population, x + 1200.0f,
                        baseline(y + 15.0f, 36.0f, theme::kText24),
                        theme::kText24, primary, 215.0f, Align::right);
            if (room.password)
                text_shrink(c, tr("Password"), x + 1420.0f,
                            baseline(y + 19.0f, 31.0f, theme::kSmall),
                            theme::kSmall, secondary, 210.0f, Align::center);
        }
    }
    if (paper)
        draw_switch_footer(c, services_.room_connected()
            ? tr("Host / Leave") : tr("Join"));
    else {
        static constexpr Hint hints[] = {
            {Pad::updown, TR("Browse")}, {Pad::cross, TR("Join")},
            {Pad::square, TR("Host / Leave")},
            {Pad::triangle, TR("Refresh")}, {Pad::circle, TR("Back")}};
        draw_footer(c, hints, 5);
    }
}

} // namespace pe::ui
