# Eden Encore — R25 Appearance / R21 Application Updates

Scope: isolated work on a feature PR based on feat/graphics-network-achievements.
No changes to main, vendor, GPU or NS2.

## R25 — Personalization architecture

The launcher layout and theme colors are independent. Existing Encore Neon
remains the default. The selectable themes are Neon, Switch, Non-Neon, Dark,
and Light. Switch retains its dedicated original controls and style.

The three official new logos were copied unchanged from the supplied files:
assets/branding/encore-noneon.png, encore-white.png and encore-dark.png.
They are packaged as TGA by the existing build pipeline, along with the
original Neon branding. The original Switch logo and source artwork are kept.
Automatic logo choices are Neon for Neon, Non-Neon for Non-Neon, White for
Dark and Dark for Light. The user can override the choice using the same
four official logos; no arbitrary image is accepted as an app logo.

Settings > Appearance includes a controller-first 14-row editor:
theme, logo, accent, background, local image, two colors, neon focus on/off,
focus intensity, overlay darkness, motion, image fit, show selected-game
background on/off, reset to defaults. The selections persist in the existing
atomically written prosperoeden.json, with backwards-compatible defaults and
range/type checks. They do not write any game configuration.

Local personal wallpaper folder: <Eden::UserDir()>/wallpapers.
Only regular PNG, JPEG and TGA files (up to 12 MiB and a basename no longer
than 120 characters) are accepted. WebP imports must be converted to PNG or
JPEG until a native PS5 WebP decoder is linked and tested. Decoding occurs
on the existing launcher texture worker, never synchronously in draw().

The daily wallpaper mode uses a reviewed, offline metadata snapshot at
<Eden::UserDir()>/wallpapers/daily/index.json. Eligible records have a
Switch 1 or Switch 2 platform, an already elapsed ISO date, approved=true,
and a local image filename. The most recent 16 valid candidates rotate by
local calendar day; no network calls are made in the rendering loop.
Example manifest with a placeholder image supplied by the user:

~~~json
{
  "entries": [
    {
      "title": "Example audited released title",
      "platform": "ns2",
      "release_date": "2026-10-30",
      "filename": "example.jpg",
      "approved": true
    }
  ]
}
~~~

Copy the matching image file to the daily/ folder. An operator-maintained,
up-to-date releases catalog and legally sourced images remain prerequisites
for claiming automatically fetched, recent Switch 1/2 releases. The
implementation must not invent or silently download unverified media.
Without a valid catalog, the authored launcher backdrop is retained.

When the user disables the game-specific backdrop, Home preserves title
metadata and actions while hiding the selected game's full-screen hero
image, leaving the user's own background visible.

## R21 — Application updates

An Application settings category exposes manual forced checking and an
opt-in check at launcher startup (off by default). Stable metadata comes
solely from:
https://api.github.com/repos/niakw/Prospero.Eden-Encore/releases/latest

A background worker performs the query. The parser rejects drafts,
prereleases, unexpected JSON, hostile tags, unsupported assets, and
network failures without interrupting normal navigation. R revisions are
compared numerically rather than lexically.

**Important safety limitation:** no installation/download button is exposed
until a verified native PS5 installer exists. Current official releases
publish an FTP ZIP, not a proven atomic PS5 self-install package.
This PR never overwrites an active executable or touches saves/settings.
Completing R21 requires an audited installer, SHA-256 verification, explicit
confirmation popup, cancellation, restart strategy and real-console proof.

## Tests and remaining qualification

- Host syntax checks for the changed launcher C++ screens and textures.
- Compile-time version parsing assertions.
- Preference roundtrip source assertions, including corrupt configuration,
  logo, background, game-backdrop toggle and update opt-in.
- Still needed: full native PS5 build, visual previews across all five
  themes, usable maintained daily-release media catalog, and secure native
  update installation before these roadmap IDs can be closed.
