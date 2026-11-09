# Eden Encore — トラブルシューティング · 日本語

[概要](README.ja.md) · [インストールと更新](INSTALL.ja.md) · [設定](SETTINGS.ja-JP.md) · [トラブルシューティング](TROUBLESHOOTING.ja-JP.md) · [サポート](SUPPORT.ja-JP.md) · [アクセシビリティ](ACCESSIBILITY.ja-JP.md) · [🌐](../../LANGUAGES.md)

起動しない場合は eboot.bin、sce_sys、ui/lang の配置を確認してください。ゲームが表示されない場合は、選択したストレージの roms を確認します。英語表示のままなら翻訳ファイルを点検してください。Safe Launch はセーブを消さずに特定ゲームの設定を戻せます。

## インストールと更新

実際に公開済みのパッケージを Releases から入手し、アプリとデータを先にバックアップしてください。ZIP/FTP 方式では PPSA99008 フォルダー全体を /data/homebrew/PPSA99008/ にコピーします。FFPFSC/ShadowMountPlus 方式と混在させず、提供されている SHA-256 を確認してください。

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/keys/
/data/prosperoeden/firmware/
```

## 設定

推奨初期設定は Vulkan、テレビ出力 1440p、ゲーム内部倍率 1.25x、空間アップスケーリング FSR 1（シャープネス 50%）、FXAA、60 Hz です。テレビへの出力解像度とゲーム内部解像度は別です。フレーム生成はゲームの処理速度そのものを上げません。

## サポート

GitHub Issues には Encore のバージョン、PS5 ファームウェア、再現手順、関連する設定、個人情報を取り除いたログを記載してください。鍵、セーブデータ、個人情報は公開しないでください。

/data/prosperoeden/ を削除しないでください。設定、セーブデータ、鍵が保存されている可能性があります。外部ストレージもバックアップしてください。

---

実際にコンパイルされた最後の公開 PS5 パッケージは 2026 年 10 月 15 日版です。10 月 30 日の公開は同じパッケージの複製です。新しいプレリリースの下書きには実行バイナリも第二世代ゲームの実機動作保証もありません。

[English](../../TROUBLESHOOTING.md) · [インストールと更新](INSTALL.ja.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
