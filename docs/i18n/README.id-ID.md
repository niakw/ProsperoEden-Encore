# Eden Encore — Ringkasan · Bahasa Indonesia

[Ringkasan](README.id-ID.md) · [Pemasangan dan pembaruan](INSTALL.id-ID.md) · [Pengaturan](SETTINGS.id-ID.md) · [Pemecahan masalah](TROUBLESHOOTING.id-ID.md) · [Dukungan](SUPPORT.id-ID.md) · [Aksesibilitas](ACCESSIBILITY.id-ID.md) · [Languages](../../LANGUAGES.md)

Eden Encore adalah proyek komunitas tidak resmi untuk PS5 yang mengembangkan mesin bersama bagi gim generasi pertama dan kedua. Antarmukanya dirancang untuk TV dan pengontrol. Lulus pengujian kode atau host tidak membuktikan bahwa sebuah gim berjalan di konsol.

## Pemasangan dan pembaruan

Unduh paket yang benar-benar diterbitkan dari Releases dan cadangkan aplikasi serta data terlebih dahulu. Untuk ZIP/FTP, salin seluruh folder PPSA99008 ke /data/homebrew/PPSA99008/. Jangan campurkan pemasangan ZIP/FTP dengan FFPFSC/ShadowMountPlus; verifikasi SHA-256 bila tersedia.

[Actual R1 package — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953)

## Pengaturan

Profil awal yang disarankan memakai Vulkan, keluaran TV 1440p, skala render gim 1.25x, FSR 1 spasial dengan ketajaman 50%, FXAA, dan 60 Hz. Resolusi keluaran TV berbeda dari resolusi internal gim. Pembuatan bingkai tidak mempercepat simulasi gim.

## Pemecahan masalah

Jika aplikasi gagal dibuka, periksa eboot.bin, sce_sys, dan ui/lang. Jika gim tidak muncul, periksa roms pada akar penyimpanan yang dipilih. Jika menu tetap berbahasa Inggris, periksa berkas terjemahan. Safe Launch dapat memulihkan pengaturan satu gim tanpa menghapus simpanan.

## Dukungan

Saat melaporkan masalah melalui GitHub Issues, sertakan versi Encore, firmware PS5, langkah reproduksi, pengaturan terkait, serta log yang sudah disamarkan. Jangan unggah kunci, berkas simpanan, atau data pribadi.

## Aksesibilitas

Teks lebih besar, kontras tinggi, dan gerakan berkurang dapat diaktifkan secara terpisah di Aksesibilitas; semuanya nonaktif secara bawaan. Kemudahan navigasi peluncur tidak menjamin aksesibilitas di setiap gim.

Jangan pernah menghapus /data/prosperoeden/ karena dapat berisi simpanan, pengaturan, dan kunci. Cadangkan juga penyimpanan eksternal.

---

Paket PS5 publik terakhir yang benar-benar dikompilasi bertanggal 15 Oktober 2026. Rilis 30 Oktober hanyalah salinan. Draf prarilis baru tidak menyediakan binari atau kompatibilitas gim generasi kedua yang telah dibuktikan di konsol.

[Full English reference](../../README.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)