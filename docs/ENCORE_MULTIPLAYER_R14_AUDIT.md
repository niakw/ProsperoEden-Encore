# Eden Encore — R14 local wireless and multiplayer audit

**Branch:** `feat/encore-r21-r25-launcher` (PR #20, draft)

**Date:** 2026-11-05

## Scope and verified facts

The upstream [Swordpdf/ProsperoEden](https://github.com/Swordpdf/ProsperoEden) already has multiplayer-specific components for public room discovery, a room-client/session controller, a guest BSD proxy and LDN packet guards. Its broader network code also relies on a compatible `Network::RoomMember` implementation and an ENet/UDP transport. Those elements require a separate review against Encore's **pinned** emulator sources and native PS5 networking; importing a UI screen alone does **not** enable multiplayer games.

This batch adapts the room-directory parser into `headless/prosperoeden/room_directory.{hpp,cpp}` (bounded response, malformed rows isolated, public IPv4-only advertised endpoints, no private/loopback/multicast destinations). A native launcher service provides a detached, read-only request for the public directory. The new `pe/ui/multiplayer.cpp` screen shows room name, game, population and password requirement; it is reachable using the Switch HOME Multiplayer shortcut, or Options on Encore Home. All eight new strings are cataloged in 29 languages.

**Joining is explicitly disabled.** No guest socket or LDN IPC handler has been changed; no packet is sent to room servers and no password is collected or stored. The parser receives protocol `0` only as a placeholder and **does not** make compatibility claims until a pinned protocol constant and real transport are integrated. A directory outage does not prevent offline gaming.

## Work needed before claiming network multiplayer

1. Confirm the exact ENet/RoomMember protocol, version, packet and authentication semantics in the pinned Encore core; pin sources and adapt independently of any one game.
2. Implement the LDN service and guest BSD/ProxySocket bridge with process-scoped session ownership. When a room disconnects, guest sockets must not silently fall back to unrestricted host networking.
3. Restrict guest traffic, cap packet/peer counts and timeouts, authenticate private sessions, do not persist passwords, and verify IPv4/DNS behavior on PS5.
4. Expose Create/Join/Leave in the launcher only after transport integration, including cancellation and error handling; do not fake a successfully joined room from a directory entry.
5. Validate two independent players on compatible content plus cancellation, teardown, version mismatch, malformed packets, network loss and PS5 13.60 real hardware.

## Evidence

- `tools/launcher/room_directory_check.cpp` — offline parser tests for valid and malformed input, untrusted addresses, population limits and version ordering.
- Syntax-only compilation of the standalone parser and the launcher UI translation units; full PS5 build and runtime test are **not completed**.
- 29 launcher catalogs synchronized, 475 active strings each, no missing keys. Human-language/font QA outstanding.

R14 is therefore **read-only room discovery in code / host tests pass / actual local wireless multiplayer not integrated**.
