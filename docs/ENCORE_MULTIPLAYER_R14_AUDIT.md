# Eden Encore — R14 local wireless and multiplayer audit

**Branch:** `feat/encore-r21-r25-launcher` (PR #20, draft)

**Date:** 2026-11-05

## Scope and verified facts

The upstream [Swordpdf/ProsperoEden](https://github.com/Swordpdf/ProsperoEden) already has multiplayer-specific components for public room discovery, a room-client/session controller, a guest BSD proxy and LDN packet guards. Its broader network code also relies on a compatible `Network::RoomMember` implementation and an ENet/UDP transport. Those elements require a separate review against Encore's **pinned** emulator sources and native PS5 networking; importing a UI screen alone does **not** enable multiplayer games.

This batch adapts the room-directory parser into `headless/prosperoeden/room_directory.{hpp,cpp}` (bounded response, malformed rows isolated, public IPv4-only advertised endpoints, no private/loopback/multicast destinations). A native launcher service provides a detached, read-only request for the public directory. The new `pe/ui/multiplayer.cpp` screen shows room name, game, population and password requirement; it is reachable using the Switch HOME Multiplayer shortcut, or Options on Encore Home. All eight new strings are cataloged in 29 languages.

**Joining is explicitly disabled.** No guest socket or LDN IPC handler has been changed; no packet is sent to room servers and no password is collected or stored. The parser receives protocol `0` only as a placeholder and **does not** make compatibility claims until a pinned protocol constant and real transport are integrated. A directory outage does not prevent offline gaming.

## Pin-level integration audit (05 November 2026)

The precise Encore vendor gitlink at the time of this audit is
`c62ecbb58555fd71b13f98266e745fe22789111d` (repo
`niakw/Prospero.Eden-Encore-vendor`). GitHub file/directory inspection
finds `encore-active/eden-core/src/core/hle/service/sockets/bsd.cpp`
and `core/internal_network/network.cpp`, and the source contains socket
proxy includes, but the active `eden-core/src/core/hle/service/`
service list does **not** include `ldn`. The separate
`eden-backports/src/core/hle/service/` service list has NIFM and sockets
but no LDN service. `eden-core/src/network/`, expected by upstream's
`network/network.h` / `RoomMember` integration, is not present at this
gitlink path.

The original ProsperoEden multiplayer design depends specifically on:
`Network::RoomMember` for room lifecycle and ENet handshake;
`Network::ProxySocket` and BSD descriptor interception to carry guest
game traffic; `Service::LDN` packet and service types for Switch Local
Wireless. These are *not* equivalent to merely downloading the public
room list. Directly pasting `multiplayer_bsd.inc` into Encore's BSD code
would therefore be incorrect, especially for NS1/NS2 coexistence.

**Preserve the existing security boundary.** Encore has both
`eden-ps5-guest-offline.patch` and
`eden-ps5-guest-domain-filter.patch` in the source. The latter
intentionally changes `kGuestNetworkOffline` from `true` to `false`
while applying domain filtering. Never replace these guards with a
global unconditional "Internet enabled" switch for guest games. A real
room connection needs an independently owned and bounded LDN transport
with no fallback to arbitrary host sockets when a room is lost.

This audit read the exact pinned public source on GitHub; a full local
vendor checkout/PS5 SDK was unavailable, so neither the full emulator
network layer nor the native payload has been compiled or tested here.
The offline `tools/check-universal-emulation-policy.py` source-policy
check passed. `tools/check-guest-network-isolation.py` could not finish
because this local worktree does not contain a populated vendor folder,
not because the check reported a network-policy failure.

### Next source change to unblock R14

1. Establish the pinned core's real LDN service registration and guest
   socket APIs, and reconcile its backported NS1 HLE service code.
2. Port the upstream ENet `RoomMember` and BSD proxy only through an
   ABI-checked adapter with explicit per-process guest mode and memory
   and peer limits; preserve existing DNS/IP-domain policies.
3. Compile the core and linker with the correct pinned vendor before
   advertising Join. Then validate session lifecycle and two actual
   running guest titles. Do not mark read-only directory as multiplayer
   compatibility.

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
