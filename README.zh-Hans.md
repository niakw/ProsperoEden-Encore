# Prospero.Eden Encore — 简体中文

> 为 PS5 客厅体验设计的社区模拟器 · [English (default)](README.md) · [All 18 launcher language choices](LANGUAGES.md)

为 PS5 客厅体验设计的社区模拟器. Encore is an independent community fork with a controller-friendly launcher, game library, graphics settings and diagnostics, not an official Sony or Nintendo product.

## 快速开始

1. 从 Encore Releases 获取完整安装包并核对校验码。
2. 备份现有 PPSA99008 应用目录、/data/prosperoeden 数据以及外接存储。
3. 将整个 PPSA99008 文件夹复制到 /data/homebrew/PPSA99008/，不要只复制 eboot.bin。
4. 启动 Encore，检查 Settings → Storage 和 Language；使用自行合法获取的密钥、固件与游戏。

[从原版迁移或更新](docs/i18n/INSTALL.zh-Hans.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## 从原版迁移或更新

Encore 与原生 ProsperoEden 共用 PPSA99008 标识，不能直接作为两个独立应用安装。只替换完整应用文件，保留 /data/prosperoeden 中的存档、设置、游戏和密钥。若旧版把用户文件放在 assets/ 下，请先备份并保留到迁移结束。

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[从原版迁移或更新 — step-by-step](docs/i18n/INSTALL.zh-Hans.md) · [Full installation instructions in English](INSTALL.md)

## 兼容性及已知限制

目前只有 PS5 固件 13.60 经 Encore 实机测试；较早版本可能运行但尚未验证，未确定最低固件。部分游戏仍可能卡顿、HUD 延迟、按键映射异常或在暂停时冻结。编译通过不代表实机兼容。

Content formats in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee that a complete game will start.

## 常见问题

Switch 2 游戏目前仅在独立研究分支探索，不属于 PS5 正式版本。帧生成与自动更新也属于路线图计划，尚非已发布功能。

如界面仍是英语，请在 Settings → Language 中切换，并确认 ui/lang/ 目录完整安装。

## Community and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

本项目不提供游戏、主机密钥或固件。提交问题时不要公开个人数据。

> This translation is a concise guide for the selected launcher language. For complete technical information, use the English README and linked guides. No console performance claim is implied.
