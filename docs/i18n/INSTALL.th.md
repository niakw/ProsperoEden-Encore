# Prospero.Eden Encore — ย้ายจากโครงการต้นฉบับและอัปเดต (ไทย)

[← ไทย](../../README.th.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

## เริ่มต้นใช้งาน

1. ดาวน์โหลดแพ็กเกจเต็มจาก Encore Releases แล้วตรวจสอบ checksum
2. สำรองโฟลเดอร์ PPSA99008 ข้อมูล /data/prosperoeden และไดรฟ์ภายนอกก่อน
3. คัดลอกโฟลเดอร์ PPSA99008 ทั้งหมดไปยัง /data/homebrew/PPSA99008/ ไม่ใช่แค่ eboot.bin
4. เปิด Encore แล้วตรวจสอบ Settings → Storage และ Language ใช้เฉพาะไฟล์ที่คุณมีสิทธิ์ตามกฎหมาย

## PPSA99008 / storage

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent data
/data/prosperoeden/keys/          # legal keys
/data/prosperoeden/firmware/      # compatible firmware
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # logs
```

## ย้ายจากโครงการต้นฉบับและอัปเดต

Encore และ ProsperoEden ดั้งเดิมใช้รหัสแอป PPSA99008 เดียวกัน จึงไม่ใช่แอปที่แยกติดตั้งคู่กันได้ ให้เปลี่ยนไฟล์แอปทั้งหมดแต่เก็บเซฟ การตั้งค่า เกม และคีย์ใน /data/prosperoeden ไว้ หากโฟลเดอร์ assets/ เก่ามีข้อมูลผู้ใช้ ให้สำรองก่อนย้าย

**Important:** Never delete `/data/prosperoeden/` or format external storage during an update. Back up first and preserve all saves, keys and existing media.

## ความเข้ากันได้และข้อจำกัด

Encore ทดสอบบน PS5 จริงเฉพาะเฟิร์มแวร์ 13.60 รุ่นเก่าอาจใช้ได้แต่ยังไม่ยืนยันและยังไม่มีเวอร์ชันขั้นต่ำที่รับรอง บางเกมอาจกระตุก HUD ช้า ปุ่มผิด หรือค้างขณะหยุดเกม การคอมไพล์ผ่านไม่ใช่หลักฐานว่าเกมเล่นได้

## คำถามที่พบบ่อย

หากเมนูยังเป็นอังกฤษ ให้เลือก Settings → Language และตรวจสอบว่าติดตั้งไฟล์ใน ui/lang/ ครบ

If one title stops booting after settings changes, try **Safe Launch** without deleting its saves. Consult [ZIP/FFPFSC/ShadowMountPlus instructions](../../INSTALL.md), [Troubleshooting](../../TROUBLESHOOTING.md) or [Support](../../SUPPORT.md).

โครงการไม่แจกเกม คีย์ หรือเฟิร์มแวร์ อย่าเผยแพร่ข้อมูลส่วนตัวในรายงานสาธารณะ
