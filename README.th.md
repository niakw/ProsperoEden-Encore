# Prospero.Eden Encore — ไทย

> อีมูเลเตอร์ PS5 ที่ออกแบบสำหรับเล่นบนทีวี · [English (default)](README.md) · [All launcher languages](LANGUAGES.md)

อีมูเลเตอร์ PS5 ที่ออกแบบสำหรับเล่นบนทีวี. Encore is an independent community emulator fork with a controller-first launcher, library, video settings and diagnostics. It is not an official Sony or Nintendo product.

## เริ่มต้นใช้งาน

1. ดาวน์โหลดแพ็กเกจเต็มจาก Encore Releases แล้วตรวจสอบ checksum
2. สำรองโฟลเดอร์ PPSA99008 ข้อมูล /data/prosperoeden และไดรฟ์ภายนอกก่อน
3. คัดลอกโฟลเดอร์ PPSA99008 ทั้งหมดไปยัง /data/homebrew/PPSA99008/ ไม่ใช่แค่ eboot.bin
4. เปิด Encore แล้วตรวจสอบ Settings → Storage และ Language ใช้เฉพาะไฟล์ที่คุณมีสิทธิ์ตามกฎหมาย

[ย้ายจากโครงการต้นฉบับและอัปเดต](docs/i18n/INSTALL.th.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## ย้ายจากโครงการต้นฉบับและอัปเดต

Encore และ ProsperoEden ดั้งเดิมใช้รหัสแอป PPSA99008 เดียวกัน จึงไม่ใช่แอปที่แยกติดตั้งคู่กันได้ ให้เปลี่ยนไฟล์แอปทั้งหมดแต่เก็บเซฟ การตั้งค่า เกม และคีย์ใน /data/prosperoeden ไว้ หากโฟลเดอร์ assets/ เก่ามีข้อมูลผู้ใช้ ให้สำรองก่อนย้าย

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[ย้ายจากโครงการต้นฉบับและอัปเดต — step-by-step](docs/i18n/INSTALL.th.md) · [Full installation instructions in English](INSTALL.md)

## ความเข้ากันได้และข้อจำกัด

Encore ทดสอบบน PS5 จริงเฉพาะเฟิร์มแวร์ 13.60 รุ่นเก่าอาจใช้ได้แต่ยังไม่ยืนยันและยังไม่มีเวอร์ชันขั้นต่ำที่รับรอง บางเกมอาจกระตุก HUD ช้า ปุ่มผิด หรือค้างขณะหยุดเกม การคอมไพล์ผ่านไม่ใช่หลักฐานว่าเกมเล่นได้

Game container support in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee a title will run.

## คำถามที่พบบ่อย

Switch 2 กำลังวิจัยในสาขาแยกและไม่รวมในรุ่น PS5 ปัจจุบัน ฟีเจอร์สร้างเฟรมและอัปเดตอัตโนมัติยังเป็นแผนงาน

หากเมนูยังเป็นอังกฤษ ให้เลือก Settings → Language และตรวจสอบว่าติดตั้งไฟล์ใน ui/lang/ ครบ

## Links and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

โครงการไม่แจกเกม คีย์ หรือเฟิร์มแวร์ อย่าเผยแพร่ข้อมูลส่วนตัวในรายงานสาธารณะ

> This localized README covers essential user information. The English README remains the full technical reference; host tests do not certify PS5 performance.
