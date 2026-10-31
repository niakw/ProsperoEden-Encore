# Prospero.Eden Encore — 元の版からの移行と更新 (日本語)

[← 日本語](README.ja.md) · [英語の完全なインストールガイド](../../INSTALL.md) · [すべての言語](../../LANGUAGES.md)

## はじめに

1. Encore Releases から完全な配布パッケージを入手し、チェックサムを確認します。
2. 既存の PPSA99008 アプリ、/data/prosperoeden のデータ、外部ストレージをバックアップします。
3. PPSA99008 フォルダー全体を /data/homebrew/PPSA99008/ に配置します。eboot.bin だけでは不十分です。
4. 起動後 Settings → Storage と Language を確認し、適法に取得したデータのみを使用します。

## PPSA99008 / storage

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent data
/data/prosperoeden/keys/          # legal keys
/data/prosperoeden/firmware/      # compatible firmware
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # logs
```

## 元の版からの移行と更新

Encore と元の ProsperoEden は同じアプリ ID PPSA99008 を使うため、独立した2つのアプリとしてインストールできません。アプリのファイルをすべて置き換えますが、/data/prosperoeden のセーブデータ、設定、ゲーム、鍵は削除しないでください。旧 assets/ にユーザーデータがあれば移行前にバックアップしてください。

**重要：**更新時に `/data/prosperoeden/` を削除したり外部ストレージを初期化したりしないでください。必ずバックアップし、セーブデータや鍵を上書きしないでください。

## 互換性と既知の問題

Encore を PS5 実機で確認したファームウェアは 13.60 のみです。旧版は動く可能性がありますが未確認で、最低対応版も決まっていません。カクつき、HUD の遅延、ゲーム中のボタン問題、一時停止でのフリーズが残る場合があります。ビルド成功は実機動作の保証ではありません。

## よくある質問

画面が英語のままなら Settings → Language で切り替え、ui/lang/ の言語ファイルがすべてあるか確認してください。

設定変更後にゲームが起動しなくなったら、セーブデータを消さずに一時的な **Safe Launch** を試してください。[ZIP/FFPFSC インストール](../../INSTALL.md)、[トラブルシューティング](../../TROUBLESHOOTING.md)、[サポート](../../SUPPORT.md)も参照してください。

ゲーム、暗号鍵、ファームウェアは配布しません。公開の不具合報告には個人情報を添付しないでください。
