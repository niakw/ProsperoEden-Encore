# Prospero.Eden Encore — 简体中文

> 为 PS5 客厅体验设计的社区模拟器 · [English (default)](README.md) · [所有语言](LANGUAGES.md)

Encore 是独立开发的社区模拟器分支，包含手柄友好的启动器、游戏库、图形设置和诊断工具，并非索尼或任天堂官方产品。

## 快速开始

1. 从 Encore Releases 获取完整安装包并核对校验码。
2. 备份现有 PPSA99008 应用目录、/data/prosperoeden 数据以及外接存储。
3. 将整个 PPSA99008 文件夹复制到 /data/homebrew/PPSA99008/，不要只复制 eboot.bin。
4. 启动 Encore，检查 Settings → Storage 和 Language；使用自行合法获取的密钥、固件与游戏。

[从原版迁移或更新](docs/i18n/INSTALL.zh-Hans.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## 从原版迁移或更新

Encore 与原生 ProsperoEden 共用 PPSA99008 标识，不能直接作为两个独立应用安装。只替换完整应用文件，保留 /data/prosperoeden 中的存档、设置、游戏和密钥。若旧版把用户文件放在 assets/ 下，请先备份并保留到迁移结束。

**应用标识 :** `PPSA99008`. **应用目录 :** `/data/homebrew/PPSA99008/`. **持久数据 :** `/data/prosperoeden/`.

[从原版迁移或更新 — 分步指南](docs/i18n/INSTALL.zh-Hans.md) · [英语完整安装说明](INSTALL.md)

## 兼容性及已知限制

目前只有 PS5 固件 13.60 经 Encore 实机测试；较早版本可能运行但尚未验证，未确定最低固件。部分游戏仍可能卡顿、HUD 延迟、按键映射异常或在暂停时冻结。编译通过不代表实机兼容。

开发版支持 NSP/XCI 游戏容器，实验性支持 NSZ/XCZ；NRO/NSO/NCA/NAX/KIP 为直接加载格式，识别扩展名并不保证游戏能够启动。

## 常见问题

Switch 2 游戏目前仅在独立研究分支探索，不属于 PS5 正式版本。帧生成与自动更新也属于路线图计划，尚非已发布功能。

如界面仍是英语，请在 Settings → Language 中切换，并确认 ui/lang/ 目录完整安装。

## 社区与致谢

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

本项目不提供游戏、主机密钥或固件。提交问题时不要公开个人数据。

> 此译文提供主要使用说明。完整技术信息以英语 README 为准；主机端测试不能证明 PS5 实机性能。
