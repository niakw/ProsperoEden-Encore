# Eden Encore — DualSense touchpad quick overlay (PS5)

**Status:** draft implementation on PR #28. Code is integrated with the active
Vulkan game-present path; host/CI and PS5 hardware qualification are tracked
separately. Do not interpret this document as a successful PS5 console test.

## Entry and controller behavior

A **short click and release of the DualSense touchpad** opens the Encore quick
menu while a **Vulkan game is running**. Clicking the touchpad again closes it.
This is the *touchpad click*, **not** the PS button. The real PlayStation
PS/Home key remains owned by the PS5 system and is not available via scePadRead.

- **D-pad Up/Down:** choose an item.
- **D-pad Left/Right:** edit a setting.
- **L1/R1:** move between menu tabs.
- **Cross:** select, edit, resume, or return to the game library.
- **Circle:** close the quick menu.
- **Touchpad click:** close the quick menu.

While the quick menu is visible, the emulator receives neutral gameplay
buttons/sticks/triggers/motion rather than accidentally consuming these menu
navigation actions. It does not force a guest operating-system pause.

### Existing controller semantics

- Long touchpad hold still provides the guest-mapped Switch Minus button
  when the quick menu is closed.
- Touchpad + L1 remains a direct return-to-library shortcut outside the menu.
- Touchpad + Options remains the emulated Switch HOME fallback.
- **Touchpad + R1 no longer toggles FPS**; the R1 shoulder is no longer consumed
  by that retired shortcut.
- OpenGL games and loading/legacy paths do **not** open the quick menu, and
  retain the old short-touchpad guest Minus tap mapping.
- The quick menu is controlled by player 1; while it is open, all local
  gameplay controllers are neutralized to avoid guest input leakage.

## UI and settings

The native Vulkan compositor draws a translucent black backdrop and a
right-side **purple Encore panel** over the current game frame. It reuses the
existing lightweight HUD shader/pipeline and has no second fullscreen swapchain.

| Tab | Contents | Application |
| --- | --- | --- |
| **GAME** | Resume, FPS readout, detailed logs, return to library | Immediate for resume/FPS/logs |
| **GRAPHICS** | Renderer, render scale, upscale, sharpness, AA, anisotropy, refresh, frame generation, neural rendering, NR strength, output, handheld/docked | Per-title JSON; **next launch** |
| **PAD** | Assign guest A/B/X/Y/L/R/ZL/ZR/Plus/Minus/L3/R3 to physical DualSense buttons; existing assignment is swapped | Per-title JSON; **next launch** |
| **DEBUG** | FPS HUD, bounded detailed log preference, FPS measurement meaning, title ID | Immediate for FPS/logs |

Graphics and pad assignments reuse `LoadGameSettings` and `SaveGameSettings`
with the actual resolved game Title ID. The menu retains `-1` as an inherited
setting and refuses invalid combinations through the existing JSON validator.
On a rejected save, the editor restores the previous value and displays an
error message. Once a graphics or mapping edit is saved, the quick menu retains
an **amber, French warning** (`RELANCER LE JEU REQUIS`) even after the menu is
closed and reopened. The warning is about restarting the **game**, not the PS5
or the emulator; current gameplay can continue safely. FPS visibility and
detailed logging update immediately and do not trigger the restart banner.
The displayed labels use ASCII French because the low-cost native bitmap font
has no accented glyphs yet. This implementation intentionally does not hot-swap a Vulkan renderer,
a framebuffer configuration or the HID mapping mid-guest-session.

The FPS switch changes the existing **host-present HUD**, not a fictional
emulated Switch application FPS counter. Detailed logs follow the existing
bounded runtime log policy; they are not always-on unbounded tracing.

## Design and performance boundaries

The closed quick menu adds one atomic visibility check to the compositor.
While open, a bounded 14-line glyph snapshot is published from input and read
by the renderer under a short mutex. The menu only reads or writes JSON on
opening or explicit user changes, never on every rendered frame. Postprocess
composition occurs **after** image generation on both the synthetic and real
Vulkan frames to avoid feeding the UI into the optical-flow input.

## Remaining validation

The branch is not approved for release until all of these are checked:

1. C++ native build, shader compile, and host input regression checks are green.
2. Touchpad short press, long hold, L1/Options chords, disconnected samples,
   close/reopen and all guest input neutralization cases work.
3. Per-title override save/reload, invalid combinations and mapping swaps
   do not mutate NS1/NS2 defaults.
4. Vulkan output with FPS off, FPS on, a persistent restart banner, and frame generation composes exactly
   one overlay without guest pixels being changed.
5. The panel remains legible on output modes, and the PS5 controller menus
   cannot accidentally select an in-game action.
6. OpenGL guest Minus and loading-screen controls remain unchanged.

Known limitation: the overlay is composed on a Vulkan presentation callback,
so it cannot independently render a fresh frame if the game's entire present
path is frozen. Also, localization and richer typography remain follow-ups
after the native input/render loop is verified.
