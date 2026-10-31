# Prospero.Eden Encore — 日本語

> リビングで楽しむ PS5 エミュレーション · [English (default)](README.md) · [All launcher languages](LANGUAGES.md)

リビングで楽しむ PS5 エミュレーション. Encore is an independent community emulator fork with a controller-first launcher, library, video settings and diagnostics. It is not an official Sony or Nintendo product.

## はじめに

1. Encore Releases から完全な配布パッケージを入手し、チェックサムを確認します。
2. 既存の PPSA99008 アプリ、/data/prosperoeden のデータ、外部ストレージをバックアップします。
3. PPSA99008 フォルダー全体を /data/homebrew/PPSA99008/ に配置します。eboot.bin だけでは不十分です。
4. 起動後 Settings → Storage と Language を確認し、適法に取得したデータのみを使用します。

[元の版からの移行と更新](docs/i18n/INSTALL.ja.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## 元の版からの移行と更新

Encore と元の ProsperoEden は同じアプリ ID PPSA99008 を使うため、独立した2つのアプリとしてインストールできません。アプリのファイルをすべて置き換えますが、/data/prosperoeden のセーブデータ、設定、ゲーム、鍵は削除しないでください。旧 assets/ にユーザーデータがあれば移行前にバックアップしてください。

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[元の版からの移行と更新 — step-by-step](docs/i18n/INSTALL.ja.md) · [Full installation instructions in English](INSTALL.md)

## 互換性と既知の問題

Encore を PS5 実機で確認したファームウェアは 13.60 のみです。旧版は動く可能性がありますが未確認で、最低対応版も決まっていません。カクつき、HUD の遅延、ゲーム中のボタン問題、一時停止でのフリーズが残る場合があります。ビルド成功は実機動作の保証ではありません。

Game container support in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee a title will run.

## よくある質問

Switch 2 は別ブランチで研究中で、現在の PS5 版には含まれません。フレーム生成と自動更新も計画段階です。

画面が英語のままなら Settings → Language で切り替え、ui/lang/ の言語ファイルがすべてあるか確認してください。

## Links and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

ゲーム、暗号鍵、ファームウェアは配布しません。公開の不具合報告には個人情報を添付しないでください。

> This localized README covers essential user information. The English README remains the full technical reference; host tests do not certify PS5 performance.
