# Prospero.Eden Encore — 从原版迁移或更新 (简体中文)

[← 简体中文](../../README.zh-Hans.md) · [Full English installation guide](../../INSTALL.md) · [Languages](../../LANGUAGES.md)

## 快速开始

1. 从 Encore Releases 获取完整安装包并核对校验码。
2. 备份现有 PPSA99008 应用目录、/data/prosperoeden 数据以及外接存储。
3. 将整个 PPSA99008 文件夹复制到 /data/homebrew/PPSA99008/，不要只复制 eboot.bin。
4. 启动 Encore，检查 Settings → Storage 和 Language；使用自行合法获取的密钥、固件与游戏。

## Paths / PPSA99008

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent user files
/data/prosperoeden/keys/          # legally obtained keys
/data/prosperoeden/firmware/      # compatible firmware files
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # game updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # diagnostics
```

## 从原版迁移或更新

Encore 与原生 ProsperoEden 共用 PPSA99008 标识，不能直接作为两个独立应用安装。只替换完整应用文件，保留 /data/prosperoeden 中的存档、设置、游戏和密钥。若旧版把用户文件放在 assets/ 下，请先备份并保留到迁移结束。

**Important:** Never delete `/data/prosperoeden/` or format external storage as a normal update step. Back up before migration; do not overwrite existing saves or keys.

## 兼容性及已知限制

目前只有 PS5 固件 13.60 经 Encore 实机测试；较早版本可能运行但尚未验证，未确定最低固件。部分游戏仍可能卡顿、HUD 延迟、按键映射异常或在暂停时冻结。编译通过不代表实机兼容。

## 常见问题

如界面仍是英语，请在 Settings → Language 中切换，并确认 ui/lang/ 目录完整安装。

If a title stops booting after changing settings, use **Safe Launch** for a temporary reset. For ZIP and FFPFSC/ShadowMountPlus methods see [INSTALL.md](../../INSTALL.md); for error details see [Troubleshooting](../../TROUBLESHOOTING.md) and [Support](../../SUPPORT.md).

本项目不提供游戏、主机密钥或固件。提交问题时不要公开个人数据。
