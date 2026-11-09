# Eden Encore — Cài đặt và cập nhật · Tiếng Việt

[Tổng quan](README.vi-VN.md) · [Cài đặt và cập nhật](INSTALL.vi-VN.md) · [Thiết lập](SETTINGS.vi-VN.md) · [Khắc phục sự cố](TROUBLESHOOTING.vi-VN.md) · [Hỗ trợ](SUPPORT.vi-VN.md) · [Khả năng tiếp cận](ACCESSIBILITY.vi-VN.md) · [Languages](../../LANGUAGES.md)

Tải gói thực sự đã phát hành từ Releases và sao lưu ứng dụng cùng dữ liệu trước. Với ZIP/FTP, chép toàn bộ thư mục PPSA99008 vào /data/homebrew/PPSA99008/. Không trộn ZIP/FTP với FFPFSC/ShadowMountPlus; kiểm tra SHA-256 nếu có.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

Không bao giờ xóa /data/prosperoeden/ vì có thể chứa bản lưu, thiết lập và khóa. Hãy sao lưu cả ổ lưu trữ ngoài.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## Khắc phục sự cố

Nếu ứng dụng không mở, kiểm tra eboot.bin, sce_sys và ui/lang. Nếu game không xuất hiện, kiểm tra roms ở thư mục lưu trữ gốc đã chọn. Nếu giao diện vẫn là tiếng Anh, kiểm tra tệp dịch. Safe Launch có thể khôi phục thiết lập riêng của game mà không xóa bản lưu.

Gói PS5 công khai cuối cùng thực sự được biên dịch ngày 15 tháng 10 năm 2026. Bản đăng ngày 30 tháng 10 chỉ là bản sao. Bản nháp phát hành mới không có tệp nhị phân hay trò chơi thế hệ thứ hai được xác nhận chạy trên console.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)