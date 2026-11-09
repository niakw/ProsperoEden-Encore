# Eden Encore — 设置 · 简体中文

[概览](README.zh-Hans.md) · [安装与更新](INSTALL.zh-Hans.md) · [设置](SETTINGS.zh-Hans.md) · [问题排查](TROUBLESHOOTING.zh-Hans.md) · [支持](SUPPORT.zh-Hans.md) · [无障碍](ACCESSIBILITY.zh-Hans.md) · [Languages](../../LANGUAGES.md)

推荐初始配置为 Vulkan、1440p 电视输出、1.25x 游戏内部渲染倍率、空间 FSR 1（锐度 50%）、FXAA 和 60 Hz。电视输出分辨率与游戏内部渲染分辨率不同。帧生成并不会提高游戏的实际模拟速度。

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** 推荐初始配置为 Vulkan、1440p 电视输出、1.25x 游戏内部渲染倍率、空间 FSR 1（锐度 50%）、FXAA 和 60 Hz。电视输出分辨率与游戏内部渲染分辨率不同。帧生成并不会提高游戏的实际模拟速度。

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## 无障碍

放大文字、高对比度、减少动态效果可在无障碍设置中分别开启，默认全部关闭。启动器可用并不代表每款游戏内部都具备无障碍功能。

## 问题排查

若应用无法启动，请检查 eboot.bin、sce_sys 与 ui/lang。若游戏列表为空，请检查所选存储根目录下的 roms。若菜单仍为英语，请检查翻译文件。Safe Launch 可在不删除存档的情况下重置单个游戏设置。

切勿删除 /data/prosperoeden/，其中可能包含存档、设置和密钥。也请备份外部存储。

---

上一份真正编译并公开发布的 PS5 安装包日期为 2026 年 10 月 15 日；10 月 30 日发布的是相同文件的副本。新的预发布草稿不含可执行文件，也不表示第二代游戏已在主机上验证。

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)