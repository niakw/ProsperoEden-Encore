# Post-R457 complete outstanding work reconciliation (2026-11-14)

Basis: recorded Nov13/14 console feedback in #101/#100/#123/#124/#97 and the exact R457 retest register; original chats are only partially recoverable, not an assertion of exhaustive verbatim coverage. No native build until explicit user approval. Latest merged engine bc0b9b4c4ee8713922ca33cdc94b7545786d5e47, vendor bc78a7610425e95d6645685cbd023a67b729ec24. Console-tested engine cbfab557e1c8cd459d67c6afae7353ca20000ab3 only.

| Item | Source evidence/status | Next gate |
|---|---|---|
| PS5 crash with Circle / CE-108262-9 | #97, paired GPU teardown #134, crash owner follow-up #170/#172 | Native exit twice in NS1/NS2, no system restart |
| NS2 Bananza earlier PC4 and current no frame | #123, selected KProcess/RomFS candidates, GPU progress #170/#172 | First visible guest frame; correct actual metadata/update identity; PC4 not reproduced in latest archive |
| NS2 Mario Kart World no first frame | #123, shared MME DRAM #172 | First guest frame + gameplay, not loading presents |
| RADV mesh output/hang | #132, stage #133 | Native driver archive identity and real GPU regression |
| FC27 black intro with audio | #100, FFmpeg EAGAIN and selected VIC #173 | Separate decode/VIC/present evidence; not a semantic video proof |
| FC27 missing letters, numerals/accents/menu/HUD | #100, Lichii #1296/Eglantine #785 equivalent skip guard already present; forced MSAA hypothesis | A/B AA off vs 4x, identical cache/render config; draw rejection and atlas visibility evidence |
| FC27 geometry/clothes/arms/alpha/texture corruption | #100; partial upload/usage tracker candidates | Real before/after rendering, no cache/lifetime regression |
| FC27 stutter, first match, 30 FPS/frame pacing | #100; last 29.105 weighted FPS, worst 1314.871 ms, 49 pipeline waits | Cold and warm same match, cache/prewarm, PC/GPU/decoder differentiated |
| Language launcher fr-FR vs Nintendo fr | #161 / vendor #125, actual returned AM reply trace | Inspect actual reply, not a font fix |
| Single dynamic jacket/loading, zero black transition | #166 same shader and retained EGL surface; still frozen during core load | Real physical frame continuity + dynamic pre-core loading; NOT done |
| Overlay Montserrat/UTF-8, five pages, L1/R1, option parity | #153 tabs, #165 UTF8 data-only; renderer still 3x5 legacy bitmap | Actual atlas/font renderer and all pages/options; NOT done |
| Settings general/per-game/quick AA and all options | #152/#157/#158 source guidance, AA gate | Compare editable values and backend constraints, no missing/misleading options |
| Wrapped help EVERY category and color/inactive state | #176 candidate expands Audio/Accessibility and Switch Controls/Appearance/Audio/Accessibility/Application, Diagnostics; application normal release status retained | Storage/language/setup/modal and per-option audio copy still audit; real viewport/fr/en and all themes |
| Local Image wording, inactive state, empty folder, long names | #122/#126, #176 dims Switch disabled local row | All UI variants; no cropped text; no false empty |
| Merge personal wallpapers and full PS5 capture list | #122/#126 vendor #106 JXR selected-only | JPG/PNG/JXR actual gallery count vs system, HDR quality, no bulk conversion |
| Opacity at 0/50/100 including category tabs | #150 corrected endpoints, default 50 | Every surface + accessibility and both themes; not just one card |
| Daily original title + formatted release date + verified source, hide on game backdrop, below modals | #122/#127 caption source | Actual manifest/source unknown handling, z-order, Home selected game backdrop |
| Deadzone understandable | Existing control description reused for Switch in #176 | 0–20%, physical travel and drift explanation visual |
| Home recent list prefilled installed, order recent plays | #150/#154/#159/#160/#163, existing fallback logic | cold/return, distinct NS2 extracted IDs, recents correctness |
| Square NS2 icons / red NS2 boxes / Network available until focus | #150 canonical prioritized icon worker, #171 pending authentic case state | all front/home fit, not reliant on focus, preserve red NS2 cases |
| MKW original front vs synthetic / Fire Emblem crop / Bananza 3 screenshots | #159/#171 and role dimension #155 | verify actual game art receipt, all genuine available images, 3 accessible viewer slots |
| ExeFS total GB and description with offline fallback | #95/#127 and library #124 | complete nested base size, explicit unknown on failure, no fabricated metadata |
| Lazy media and startup/return speed, WebP by role | #155/#160/#163, #124 | measure cold and warm loads, confirmed source/output dimensions & avoid blocking deep walks |
| Genres Strategy/Other, light theme text contrast | catalog/theme candidates, not separately validated in latest retest | dropdown/detail translated genres + contrast screenshots |
| Native warnings and security | #174, #108; five C++ source candidates, Meson TLS/Node external; #118 7 high STB source fixes | real native warning count and alert state independent of green jobs |
| Log sharing | #176 queue/policy & UI plus private website #2 merged prototype; default off | durable post-consent epoch, native worker/cancel/HTTPS, authenticated private transport and private mirrors, GDPR notice/retention. NO upload today |
| Two repos cleanup | #175/#133; divergent home-rail and EmitInvalid branches preserved | check ref ancestry, no deletion of unique work |

Remaining priorities: P0 shutdown and NS2 first output; P1 FC27 text/video/texture/pacing, unified animated loader and overlay; P2 full UI/library; log feature must remain inactive until actual collector and native path verified. Mainline CodeQL and source/host success are not PS5 acceptance. No private user logs committed.
