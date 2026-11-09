# Eden Encore — 设置 · 简体中文

[概览](README.zh-Hans.md) · [安装与更新](INSTALL.zh-Hans.md) · [设置](SETTINGS.zh-Hans.md) · [问题排查](TROUBLESHOOTING.zh-Hans.md) · [支持](SUPPORT.zh-Hans.md) · [无障碍](ACCESSIBILITY.zh-Hans.md) · [🌐](../../LANGUAGES.md)

推荐初始配置为 Vulkan、1440p 电视输出、1.25x 游戏内部渲染倍率、空间 FSR 1（锐度 50%）、FXAA 和 60 Hz。电视输出分辨率与游戏内部渲染分辨率不同。帧生成并不会提高游戏的实际模拟速度。

## Vulkan / FSR 1 — 设置

| `Minimum` | `Recommended` | `High` |
| --- | --- | --- |
| `Vulkan` · `1080p` · `1×` · `Bilinear` · `60 Hz` | `Vulkan` · `1440p` · `1.25×` · `FSR 1` · `FXAA` · `60 Hz` | `Vulkan` · `2160p` · `1.5×` · `Bicubic` · `FXAA` · `60 Hz` |

## 设置 · Touchpad

游戏中短按 Touchpad 可打开 Encore 快速设置；中央系统按钮保留给主机使用。该菜单包含图形设置、按键映射、FPS 和诊断信息。部分修改需要重启游戏。语言在 Settings → Language 中选择，但不是所有翻译目录语言都能从菜单选取。

## 无障碍

放大文字、高对比度、减少动态效果可在无障碍设置中分别开启，默认全部关闭。启动器可用并不代表每款游戏内部都具备无障碍功能。

## 问题排查

若应用无法启动，请检查 eboot.bin、sce_sys 与 ui/lang。若游戏列表为空，请检查所选存储根目录下的 roms。若菜单仍为英语，请检查翻译文件。Safe Launch 可在不删除存档的情况下重置单个游戏设置。

## 支持

在 GitHub Issues 中提供 Encore 版本、PS5 固件、复现步骤、相关设置以及脱敏日志。请勿公开密钥、游戏存档或个人资料。

切勿删除 /data/prosperoeden/，其中可能包含存档、设置和密钥。也请备份外部存储。

---

上一份真正编译并公开发布的 PS5 安装包日期为 2026 年 10 月 15 日；10 月 30 日发布的是相同文件的副本。新的预发布草稿不含可执行文件，也不表示第二代游戏已在主机上验证。

[English](../../SETTINGS.md) · [安装与更新](INSTALL.zh-Hans.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
