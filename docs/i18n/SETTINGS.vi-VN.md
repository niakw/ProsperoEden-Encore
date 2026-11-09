# Eden Encore — Thiết lập · Tiếng Việt

[Tổng quan](README.vi-VN.md) · [Cài đặt và cập nhật](INSTALL.vi-VN.md) · [Thiết lập](SETTINGS.vi-VN.md) · [Khắc phục sự cố](TROUBLESHOOTING.vi-VN.md) · [Hỗ trợ](SUPPORT.vi-VN.md) · [Khả năng tiếp cận](ACCESSIBILITY.vi-VN.md) · [🌐](../../LANGUAGES.md)

Hồ sơ đề xuất sử dụng Vulkan, đầu ra TV 1440p, độ phân giải game nội bộ 1.25x, FSR 1 không gian với độ nét 50%, FXAA và 60 Hz. Đầu ra TV không đồng nghĩa với độ phân giải render của trò chơi. Tạo khung hình không tăng tốc độ mô phỏng game.

## Vulkan / FSR 1 — Thiết lập

| `Minimum` | `Recommended` | `High` |
| --- | --- | --- |
| `Vulkan` · `1080p` · `1×` · `Bilinear` · `60 Hz` | `Vulkan` · `1440p` · `1.25×` · `FSR 1` · `FXAA` · `60 Hz` | `Vulkan` · `2160p` · `1.5×` · `Bicubic` · `FXAA` · `60 Hz` |

## Thiết lập · Touchpad

Nhấn nhanh Touchpad để mở cài đặt nhanh Encore khi đang chơi; nút hệ thống ở giữa dành riêng cho máy chơi game. Menu gồm đồ họa, gán nút, FPS và chẩn đoán. Một số thay đổi cần khởi động lại trò chơi. Chọn ngôn ngữ tại Settings → Language. Menu có đúng 31 tùy chọn ngôn ngữ hệ thống PS5 chính thức.

## Khả năng tiếp cận

Chữ lớn, độ tương phản cao và giảm chuyển động là các tùy chọn độc lập trong Khả năng tiếp cận và đều tắt theo mặc định. Giao diện dễ sử dụng không bảo đảm mọi trò chơi đều hỗ trợ tiếp cận.

## Khắc phục sự cố

Nếu ứng dụng không mở, kiểm tra eboot.bin, sce_sys và ui/lang. Nếu game không xuất hiện, kiểm tra roms ở thư mục lưu trữ gốc đã chọn. Nếu giao diện vẫn là tiếng Anh, kiểm tra tệp dịch. Safe Launch có thể khôi phục thiết lập riêng của game mà không xóa bản lưu.

## Hỗ trợ

Trong GitHub Issues, cung cấp phiên bản Encore, firmware PS5, các bước tái hiện, thiết lập liên quan và nhật ký đã loại bỏ thông tin cá nhân. Tuyệt đối không công khai khóa, dữ liệu lưu game hay thông tin riêng tư.

Không bao giờ xóa /data/prosperoeden/ vì có thể chứa bản lưu, thiết lập và khóa. Hãy sao lưu cả ổ lưu trữ ngoài.

---

Gói PS5 công khai cuối cùng thực sự được biên dịch ngày 15 tháng 10 năm 2026. Bản đăng ngày 30 tháng 10 chỉ là bản sao. Bản nháp phát hành mới không có tệp nhị phân hay trò chơi thế hệ thứ hai được xác nhận chạy trên console.

[English](../../SETTINGS.md) · [Cài đặt và cập nhật](INSTALL.vi-VN.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
