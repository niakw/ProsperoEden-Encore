# Eden Encore — การตั้งค่า · ไทย

[ภาพรวม](README.th.md) · [การติดตั้งและอัปเดต](INSTALL.th-TH.md) · [การตั้งค่า](SETTINGS.th-TH.md) · [แก้ไขปัญหา](TROUBLESHOOTING.th-TH.md) · [การสนับสนุน](SUPPORT.th-TH.md) · [การช่วยการเข้าถึง](ACCESSIBILITY.th-TH.md) · [Languages](../../LANGUAGES.md)

ค่าเริ่มต้นที่แนะนำคือ Vulkan, เอาต์พุตทีวี 1440p, ความละเอียดเกมภายใน 1.25x, FSR 1 แบบเชิงพื้นที่ ความคมชัด 50%, FXAA และ 60 Hz ความละเอียดทีวีกับความละเอียดที่เกมเรนเดอร์เป็นคนละค่า การสร้างเฟรมไม่ได้ทำให้การจำลองเกมเร็วขึ้น

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** ค่าเริ่มต้นที่แนะนำคือ Vulkan, เอาต์พุตทีวี 1440p, ความละเอียดเกมภายใน 1.25x, FSR 1 แบบเชิงพื้นที่ ความคมชัด 50%, FXAA และ 60 Hz ความละเอียดทีวีกับความละเอียดที่เกมเรนเดอร์เป็นคนละค่า การสร้างเฟรมไม่ได้ทำให้การจำลองเกมเร็วขึ้น

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## การช่วยการเข้าถึง

สามารถเปิดข้อความขนาดใหญ่ คอนทราสต์สูง และลดการเคลื่อนไหวแยกกันในเมนูการช่วยการเข้าถึง โดยค่าเริ่มต้นปิดทั้งหมด การใช้หน้าตาแอปได้ไม่ได้หมายความว่าเกมทุกเกมเข้าถึงได้

## แก้ไขปัญหา

หากแอปเปิดไม่ได้ให้ตรวจสอบ eboot.bin, sce_sys และ ui/lang หากไม่พบเกมให้ตรวจสอบ roms ในรากพื้นที่จัดเก็บที่เลือก หากเมนูยังเป็นอังกฤษให้ตรวจสอบไฟล์ภาษา Safe Launch คืนค่าตั้งค่ารายเกมโดยไม่ลบเซฟ

ห้ามลบ /data/prosperoeden/ เพราะอาจมีเซฟ การตั้งค่า และคีย์ ควรสำรองพื้นที่จัดเก็บภายนอกด้วย

---

แพ็กเกจ PS5 สาธารณะที่คอมไพล์จริงล่าสุดคือวันที่ 15 ตุลาคม 2026 การเผยแพร่วันที่ 30 ตุลาคมเป็นเพียงสำเนา ฉบับร่างพรีรีลีสใหม่ไม่มีไฟล์ไบนารีหรือเกมรุ่นที่สองที่ยืนยันว่าเล่นบนคอนโซลได้

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)