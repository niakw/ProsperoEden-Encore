# Eden Encore — Khắc phục sự cố · Tiếng Việt

[Tổng quan](README.vi-VN.md) · [Cài đặt và cập nhật](INSTALL.vi-VN.md) · [Thiết lập](SETTINGS.vi-VN.md) · [Khắc phục sự cố](TROUBLESHOOTING.vi-VN.md) · [Hỗ trợ](SUPPORT.vi-VN.md) · [Khả năng tiếp cận](ACCESSIBILITY.vi-VN.md) · [🌐](../../LANGUAGES.md)

Nếu ứng dụng không mở, kiểm tra eboot.bin, sce_sys và ui/lang. Nếu game không xuất hiện, kiểm tra roms ở thư mục lưu trữ gốc đã chọn. Nếu giao diện vẫn là tiếng Anh, kiểm tra tệp dịch. Safe Launch có thể khôi phục thiết lập riêng của game mà không xóa bản lưu.

## Cài đặt và cập nhật

Tải gói thực sự đã phát hành từ Releases và sao lưu ứng dụng cùng dữ liệu trước. Với ZIP/FTP, chép toàn bộ thư mục PPSA99008 vào /data/homebrew/PPSA99008/. Không trộn ZIP/FTP với FFPFSC/ShadowMountPlus; kiểm tra SHA-256 nếu có.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/keys/
/data/prosperoeden/firmware/
```

## Thiết lập

Hồ sơ đề xuất sử dụng Vulkan, đầu ra TV 1440p, độ phân giải game nội bộ 1.25x, FSR 1 không gian với độ nét 50%, FXAA và 60 Hz. Đầu ra TV không đồng nghĩa với độ phân giải render của trò chơi. Tạo khung hình không tăng tốc độ mô phỏng game.

## Hỗ trợ

Trong GitHub Issues, cung cấp phiên bản Encore, firmware PS5, các bước tái hiện, thiết lập liên quan và nhật ký đã loại bỏ thông tin cá nhân. Tuyệt đối không công khai khóa, dữ liệu lưu game hay thông tin riêng tư.

Không bao giờ xóa /data/prosperoeden/ vì có thể chứa bản lưu, thiết lập và khóa. Hãy sao lưu cả ổ lưu trữ ngoài.

---

Gói PS5 công khai cuối cùng thực sự được biên dịch ngày 15 tháng 10 năm 2026. Bản đăng ngày 30 tháng 10 chỉ là bản sao. Bản nháp phát hành mới không có tệp nhị phân hay trò chơi thế hệ thứ hai được xác nhận chạy trên console.

[English](../../TROUBLESHOOTING.md) · [Cài đặt và cập nhật](INSTALL.vi-VN.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
