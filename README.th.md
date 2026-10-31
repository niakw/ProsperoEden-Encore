<table width="100%">
  <tr><td align="center">
    <strong>🌐 LANGUAGES</strong> &nbsp; · &nbsp; <a href="README.md">English</a> &nbsp; · &nbsp; <a href="README.md">English UK</a> &nbsp; · &nbsp; <a href="README.zh-Hans.md">简体中文</a> &nbsp; · &nbsp; <a href="README.zh-Hant.md">繁體中文</a> &nbsp; · &nbsp; <a href="README.es-419.md">Español LatAm</a> &nbsp; · &nbsp; <a href="README.es.md">Español ES</a> &nbsp; · &nbsp; <a href="README.fr.md">Français</a> &nbsp; · &nbsp; <a href="README.fr-CA.md">Français CA</a> &nbsp; · &nbsp; <a href="README.pt-BR.md">Português BR</a><br>
    <a href="README.pt-PT.md">Português PT</a> &nbsp; · &nbsp; <a href="README.ru.md">Русский</a> &nbsp; · &nbsp; <a href="README.de.md">Deutsch</a> &nbsp; · &nbsp; <a href="README.ja.md">日本語</a> &nbsp; · &nbsp; <a href="README.ko.md">한국어</a> &nbsp; · &nbsp; <a href="README.it.md">Italiano</a> &nbsp; · &nbsp; <strong>ไทย</strong> &nbsp; · &nbsp; <a href="README.pl.md">Polski</a> &nbsp; · &nbsp; <a href="README.nl.md">Nederlands</a> &nbsp; · &nbsp; <a href="LANGUAGES.md"><strong>All languages</strong></a>
  </td></tr>
</table>

<table width="100%">
  <tr>
    <td width="21%" align="center" valign="middle"><a href="README.md"><img src="assets/icon0.png" alt="Prospero.Eden Encore logo" width="148"></a></td>
    <td width="79%" align="left" valign="middle">
      <h1>Prospero.Eden Encore</h1>
      <p><strong>อีมูเลเตอร์ PS5 ที่ออกแบบสำหรับเล่นบนทีวี</strong></p>
      <p>Encore เป็นโครงการอิสระของชุมชน มีตัวเปิดเกมที่รองรับจอย คลังเกม การตั้งค่าภาพ และระบบวินิจฉัย ไม่ใช่ผลิตภัณฑ์อย่างเป็นทางการของ Sony หรือ Nintendo</p>
      <p><kbd>เฟิร์มแวร์ 13.60 · ทดสอบ PS5</kbd> &nbsp; <kbd>Vulkan + OpenGL</kbd> &nbsp; <kbd>อินเทอร์เฟซทีวี</kbd> &nbsp; <kbd>Dynarmic</kbd></p>
    </td>
  </tr>
</table>

<table width="100%">
  <tr>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/releases"><strong>ดาวน์โหลด</strong></a></td>
    <td align="center"><a href="docs/i18n/INSTALL.th.md"><strong>ติดตั้ง</strong></a></td>
    <td align="center"><a href="#getting-started"><strong>เริ่มต้น</strong></a></td>
    <td align="center"><a href="#compatibility"><strong>ความเข้ากันได้</strong></a></td>
    <td align="center"><a href="#faq"><strong>คำถาม</strong></a></td>
    <td align="center"><a href="TROUBLESHOOTING.md"><strong>ช่วยเหลือ</strong></a></td>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md"><strong>แผนงาน</strong></a></td>
  </tr>
</table>

<a id="getting-started"></a>
## เริ่มต้นใช้งาน

1. ดาวน์โหลดแพ็กเกจเต็มจาก Encore Releases แล้วตรวจสอบ checksum
2. สำรองโฟลเดอร์ PPSA99008 ข้อมูล /data/prosperoeden และไดรฟ์ภายนอกก่อน
3. คัดลอกโฟลเดอร์ PPSA99008 ทั้งหมดไปยัง /data/homebrew/PPSA99008/ ไม่ใช่แค่ eboot.bin
4. เปิด Encore แล้วตรวจสอบ Settings → Storage และ Language ใช้เฉพาะไฟล์ที่คุณมีสิทธิ์ตามกฎหมาย

[ย้ายจากโครงการต้นฉบับและอัปเดต](docs/i18n/INSTALL.th.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## ย้ายจากโครงการต้นฉบับและอัปเดต

Encore และ ProsperoEden ดั้งเดิมใช้รหัสแอป PPSA99008 เดียวกัน จึงไม่ใช่แอปที่แยกติดตั้งคู่กันได้ ให้เปลี่ยนไฟล์แอปทั้งหมดแต่เก็บเซฟ การตั้งค่า เกม และคีย์ใน /data/prosperoeden ไว้ หากโฟลเดอร์ assets/ เก่ามีข้อมูลผู้ใช้ ให้สำรองก่อนย้าย

**รหัสแอป :** `PPSA99008`. **แอป :** `/data/homebrew/PPSA99008/`. **ข้อมูลถาวร :** `/data/prosperoeden/`.

[ย้ายจากโครงการต้นฉบับและอัปเดต — ทีละขั้นตอน](docs/i18n/INSTALL.th.md) · [คู่มือติดตั้งเต็มภาษาอังกฤษ](INSTALL.md)

<a id="compatibility"></a>
## ความเข้ากันได้และข้อจำกัด

Encore ทดสอบบน PS5 จริงเฉพาะเฟิร์มแวร์ 13.60 รุ่นเก่าอาจใช้ได้แต่ยังไม่ยืนยันและยังไม่มีเวอร์ชันขั้นต่ำที่รับรอง บางเกมอาจกระตุก HUD ช้า ปุ่มผิด หรือค้างขณะหยุดเกม การคอมไพล์ผ่านไม่ใช่หลักฐานว่าเกมเล่นได้

โค้ดที่กำลังพัฒนารองรับ NSP/XCI และรองรับ NSZ/XCZ แบบทดลอง ตัวโหลด NRO/NSO/NCA/NAX/KIP ต้องมีข้อมูลที่ถูกต้อง การรองรับนามสกุลไฟล์ไม่ได้รับประกันว่าเกมจะเริ่มได้

<a id="faq"></a>
## คำถามที่พบบ่อย

Switch 2 กำลังวิจัยในสาขาแยกและไม่รวมในรุ่น PS5 ปัจจุบัน ฟีเจอร์สร้างเฟรมและอัปเดตอัตโนมัติยังเป็นแผนงาน

หากเมนูยังเป็นอังกฤษ ให้เลือก Settings → Language และตรวจสอบว่าติดตั้งไฟล์ใน ui/lang/ ครบ

## ชุมชนและเครดิต

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

โครงการไม่แจกเกม คีย์ หรือเฟิร์มแวร์ อย่าเผยแพร่ข้อมูลส่วนตัวในรายงานสาธารณะ

> คำแปลนี้สรุปข้อมูลสำคัญสำหรับผู้ใช้ รายละเอียดทางเทคนิคฉบับเต็มอยู่ใน README ภาษาอังกฤษ และการทดสอบบนโฮสต์ไม่ได้พิสูจน์ประสิทธิภาพบน PS5 จริง
