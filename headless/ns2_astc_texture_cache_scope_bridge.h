// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// P5: the pinned NS1/NS2 ASTC TextureCache implementation uses SCOPE_EXIT
// for native channel-lock ownership, but did not include its defining header.
// Keep the vendor implementation unchanged, adding only its missing dependency.
// This include wrapper must precede ns2-astc/include in the native video_core
// compile path; #include_next selects the original maintained implementation.
#include "common/scope_exit.h"
#include_next "video_core/texture_cache/texture_cache.h"
