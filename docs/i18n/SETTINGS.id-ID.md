# Eden Encore — Pengaturan · Bahasa Indonesia

[Ringkasan](README.id-ID.md) · [Pemasangan dan pembaruan](INSTALL.id-ID.md) · [Pengaturan](SETTINGS.id-ID.md) · [Pemecahan masalah](TROUBLESHOOTING.id-ID.md) · [Dukungan](SUPPORT.id-ID.md) · [Aksesibilitas](ACCESSIBILITY.id-ID.md) · [Languages](../../LANGUAGES.md)

Profil awal yang disarankan memakai Vulkan, keluaran TV 1440p, skala render gim 1.25x, FSR 1 spasial dengan ketajaman 50%, FXAA, dan 60 Hz. Resolusi keluaran TV berbeda dari resolusi internal gim. Pembuatan bingkai tidak mempercepat simulasi gim.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Profil awal yang disarankan memakai Vulkan, keluaran TV 1440p, skala render gim 1.25x, FSR 1 spasial dengan ketajaman 50%, FXAA, dan 60 Hz. Resolusi keluaran TV berbeda dari resolusi internal gim. Pembuatan bingkai tidak mempercepat simulasi gim.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Aksesibilitas

Teks lebih besar, kontras tinggi, dan gerakan berkurang dapat diaktifkan secara terpisah di Aksesibilitas; semuanya nonaktif secara bawaan. Kemudahan navigasi peluncur tidak menjamin aksesibilitas di setiap gim.

## Pemecahan masalah

Jika aplikasi gagal dibuka, periksa eboot.bin, sce_sys, dan ui/lang. Jika gim tidak muncul, periksa roms pada akar penyimpanan yang dipilih. Jika menu tetap berbahasa Inggris, periksa berkas terjemahan. Safe Launch dapat memulihkan pengaturan satu gim tanpa menghapus simpanan.

Jangan pernah menghapus /data/prosperoeden/ karena dapat berisi simpanan, pengaturan, dan kunci. Cadangkan juga penyimpanan eksternal.

---

Paket PS5 publik terakhir yang benar-benar dikompilasi bertanggal 15 Oktober 2026. Rilis 30 Oktober hanyalah salinan. Draf prarilis baru tidak menyediakan binari atau kompatibilitas gim generasi kedua yang telah dibuktikan di konsol.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)