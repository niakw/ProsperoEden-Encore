# R458 — continuous GL/Vulkan loading handoff, 2026-11-14

## User-visible defect

R457 removed the explicit GL close/reopen black gap and retired the jacket screenshot plus
bottom-band Vulkan workaround, but its handoff still destroyed the launcher GL context before
`System::Load`. The retained EGL surface therefore scanned out one static frame for the whole
core-load interval. On the R457 PS5 evidence this interval was roughly 15 s for Bananza and
41 s for Mario Kart World. This document does **not** reinterpret those times as a guest stall
or claim either title reaches a first guest frame.

## Upstream-first basis

- The existing R457 audit already compared the PS5 Vulkan-tools R53 output-retention work:
  retaining VideoOut across renderer ownership changes avoids the close/reopen black-gap class.
  That supports the ownership model but is not Encore console proof.
- Eglantine PS5/Encore's prior shared loader work uses the same source-generated loading shader
  on the GL and Vulkan paths. R458 keeps that single visual identity rather than adding another
  loader.
- No desktop/Linux thread or WSI patch is imported: the relevant behavior here is the selected
  PS5 EGL backend, where destroying the window surface calls the native presentation shutdown.

## Selected-source correction

`pe::ps5::Display::defer_scanout_close(bool reduce_motion)` no longer destroys the GL context.

1. The launcher presents the canonical `loading_scene.glsl` once.
2. It releases the context from the launch thread and transfers the same EGL display, surface
   and context to one `std::jthread`.
3. That presenter makes the retained context current, uses the exact same generated shader and
   swaps at vsync while `System::Load` runs. Reduced-motion keeps the scenery fixed through the
   existing 1000-second shader convention while the loading ring can continue.
4. At Vulkan or OpenGL takeover, `close_deferred_scanout()` requests stop and joins the presenter
   **before** destroying the context, then destroys the surface (the native VideoOut release
   boundary), then terminates EGL.
5. If presenter shader setup or presentation fails, it exits and leaves the last valid buffer
   scanning out; it does not manufacture a second VideoOut owner or a black fallback screen.

The post-takeover Vulkan loading compositor is unchanged and continues the same visual recipe.

## Host/source acceptance

The two existing loading contracts are strengthened to reject the R457 frozen-context design.
They require:

- one generated loading scene on launcher GL, retained GL presenter and Vulkan;
- advancing presenter time and bounded-vsync swaps;
- no context/surface/terminate in `defer_scanout_close`;
- strict takeover order: stop -> join -> destroy context -> destroy surface -> terminate;
- no jacket upload, screenshot mailbox, lower-band loader or fabricated guest-frame handoff;
- existing 10 s / 30 s Vulkan no-guest-frame diagnostics preserved.

## Validation status

**Source candidate only.** No native PS5 build was requested or run. Physical continuity,
absence of black/white flashes, thread/toolchain behavior on PS5, Bananza/MKW first guest frame
and gameplay remain hardware gates. Console acceptance must identify the exact engine/vendor
SHAs and test launcher -> FC27, launcher -> Bananza, launcher -> MKW, return-to-launcher and
relaunch paths.
