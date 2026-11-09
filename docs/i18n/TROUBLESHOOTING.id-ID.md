# Eden Encore — Pemecahan masalah · Bahasa Indonesia

[Ringkasan](README.id-ID.md) · [Pemasangan dan pembaruan](INSTALL.id-ID.md) · [Pengaturan](SETTINGS.id-ID.md) · [Pemecahan masalah](TROUBLESHOOTING.id-ID.md) · [Dukungan](SUPPORT.id-ID.md) · [Aksesibilitas](ACCESSIBILITY.id-ID.md) · [Languages](../../LANGUAGES.md)

Jika aplikasi gagal dibuka, periksa eboot.bin, sce_sys, dan ui/lang. Jika gim tidak muncul, periksa roms pada akar penyimpanan yang dipilih. Jika menu tetap berbahasa Inggris, periksa berkas terjemahan. Safe Launch dapat memulihkan pengaturan satu gim tanpa menghapus simpanan.

## Pemasangan dan pembaruan

Unduh paket yang benar-benar diterbitkan dari Releases dan cadangkan aplikasi serta data terlebih dahulu. Untuk ZIP/FTP, salin seluruh folder PPSA99008 ke /data/homebrew/PPSA99008/. Jangan campurkan pemasangan ZIP/FTP dengan FFPFSC/ShadowMountPlus; verifikasi SHA-256 bila tersedia.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## Pengaturan

Profil awal yang disarankan memakai Vulkan, keluaran TV 1440p, skala render gim 1.25x, FSR 1 spasial dengan ketajaman 50%, FXAA, dan 60 Hz. Resolusi keluaran TV berbeda dari resolusi internal gim. Pembuatan bingkai tidak mempercepat simulasi gim.

## Dukungan

Saat melaporkan masalah melalui GitHub Issues, sertakan versi Encore, firmware PS5, langkah reproduksi, pengaturan terkait, serta log yang sudah disamarkan. Jangan unggah kunci, berkas simpanan, atau data pribadi.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

Jangan pernah menghapus /data/prosperoeden/ karena dapat berisi simpanan, pengaturan, dan kunci. Cadangkan juga penyimpanan eksternal.

---

Paket PS5 publik terakhir yang benar-benar dikompilasi bertanggal 15 Oktober 2026. Rilis 30 Oktober hanyalah salinan. Draf prarilis baru tidak menyediakan binari atau kompatibilitas gim generasi kedua yang telah dibuktikan di konsol.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)