#!/usr/bin/env python3
"""Nlib assets: complete demand-driven title enrichment with bounded decode memory.

Selected title fetching stays asynchronous and includes all available screens.
Do not reintroduce an eager sweep of titles outside the current selection.
"""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
services = (root / "headless/prosperoeden/eden_services.cpp").read_text()
library = (root / "headless/prosperoeden/pe/ui/library.cpp").read_text()
source = services[services.index("bool WriteJpegWebP("):services.index("std::string NlibPlayersPath(")]
assert "stbi_info_from_memory" in source
assert source.index("stbi_info_from_memory") < source.index("stbi_load_from_memory")
assert "encoded.size() > (16u << 20)" in source
assert "width > 4096 || height > 4096" in source
assert "(!tall_case && height > 2160)" in source
assert "std::scoped_lock codec_lock(ArtworkCodecMutex());" in source
assert "WebPEncodeRGBA(pixels, w, h, w * 4, 80.0f, &compressed)" in source
assert "WebPGetInfo(compressed, length, &checked_w, &checked_h)" in source
assert "3840u * 2160u" in source
section = services[services.index("NlibEnrichment EnsureNlibEnrichment("):
                   services.index("std::uintmax_t TreeBytes(")]
assert "std::vector<std::future<bool>> downloads;" in section
assert "std::async(std::launch::async" in section
assert "const int wanted_screens = std::clamp(screen_count, 0, 3);" in section
assert "/banner/1080p" in section and "/icon/512" in section and "/screen/" in section
assert "for (auto& pending : downloads)" in section
assert "CachedNlibEnrichment(title_id, language_choice)" in section
assert "home_priority" not in section
worker = library.split("void Launcher::start_selected_media()", 1)[1].split(
    "void Launcher::finish_selected_media()", 1)[0]
finish = library.split("void Launcher::finish_selected_media()", 1)[1].split(
    "void Launcher::apply_games(", 1)[0]
assert "for (std::size_t offset = 0; offset < games_.size(); ++offset)" not in worker
for needle in ("screen_ != Screen::library", "media_scan_.valid()",
               "library_.selected < 0", "library_.selected >= static_cast<int>(games_.size())",
               "games_[static_cast<std::size_t>(library_.selected)]",
               "services_.enrich_game_media(std::move(copy), &media_cancel_)"):
    assert needle in worker, needle
assert "enriched.title_id != media_scan_title_id_" in finish
assert "game.title_id != enriched.title_id" in finish
assert "game.screenshots = enriched.screenshots" in finish
assert "start_selected_media();" in finish
print("Nlib selected full-media concurrency + bounded JPEG decode memory: PASS")
