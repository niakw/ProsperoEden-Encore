# Eden Encore — Thiết lập · Tiếng Việt

[Tổng quan](README.vi-VN.md) · [Cài đặt và cập nhật](INSTALL.vi-VN.md) · [Thiết lập](SETTINGS.vi-VN.md) · [Khắc phục sự cố](TROUBLESHOOTING.vi-VN.md) · [Hỗ trợ](SUPPORT.vi-VN.md) · [Khả năng tiếp cận](ACCESSIBILITY.vi-VN.md) · [Languages](../../LANGUAGES.md)

Hồ sơ đề xuất sử dụng Vulkan, đầu ra TV 1440p, độ phân giải game nội bộ 1.25x, FSR 1 không gian với độ nét 50%, FXAA và 60 Hz. Đầu ra TV không đồng nghĩa với độ phân giải render của trò chơi. Tạo khung hình không tăng tốc độ mô phỏng game.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Hồ sơ đề xuất sử dụng Vulkan, đầu ra TV 1440p, độ phân giải game nội bộ 1.25x, FSR 1 không gian với độ nét 50%, FXAA và 60 Hz. Đầu ra TV không đồng nghĩa với độ phân giải render của trò chơi. Tạo khung hình không tăng tốc độ mô phỏng game.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Khả năng tiếp cận

Chữ lớn, độ tương phản cao và giảm chuyển động là các tùy chọn độc lập trong Khả năng tiếp cận và đều tắt theo mặc định. Giao diện dễ sử dụng không bảo đảm mọi trò chơi đều hỗ trợ tiếp cận.

## Khắc phục sự cố

Nếu ứng dụng không mở, kiểm tra eboot.bin, sce_sys và ui/lang. Nếu game không xuất hiện, kiểm tra roms ở thư mục lưu trữ gốc đã chọn. Nếu giao diện vẫn là tiếng Anh, kiểm tra tệp dịch. Safe Launch có thể khôi phục thiết lập riêng của game mà không xóa bản lưu.

Không bao giờ xóa /data/prosperoeden/ vì có thể chứa bản lưu, thiết lập và khóa. Hãy sao lưu cả ổ lưu trữ ngoài.

---

Gói PS5 công khai cuối cùng thực sự được biên dịch ngày 15 tháng 10 năm 2026. Bản đăng ngày 30 tháng 10 chỉ là bản sao. Bản nháp phát hành mới không có tệp nhị phân hay trò chơi thế hệ thứ hai được xác nhận chạy trên console.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)