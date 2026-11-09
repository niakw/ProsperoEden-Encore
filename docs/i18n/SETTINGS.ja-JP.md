# Eden Encore — 設定 · 日本語

[概要](README.ja.md) · [インストールと更新](INSTALL.ja-JP.md) · [設定](SETTINGS.ja-JP.md) · [トラブルシューティング](TROUBLESHOOTING.ja-JP.md) · [サポート](SUPPORT.ja-JP.md) · [アクセシビリティ](ACCESSIBILITY.ja-JP.md) · [Languages](../../LANGUAGES.md)

推奨初期設定は Vulkan、テレビ出力 1440p、ゲーム内部倍率 1.25x、空間アップスケーリング FSR 1（シャープネス 50%）、FXAA、60 Hz です。テレビへの出力解像度とゲーム内部解像度は別です。フレーム生成はゲームの処理速度そのものを上げません。

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** 推奨初期設定は Vulkan、テレビ出力 1440p、ゲーム内部倍率 1.25x、空間アップスケーリング FSR 1（シャープネス 50%）、FXAA、60 Hz です。テレビへの出力解像度とゲーム内部解像度は別です。フレーム生成はゲームの処理速度そのものを上げません。

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## アクセシビリティ

大きい文字、高コントラスト、動きの軽減はアクセシビリティ設定で個別に有効にできます。初期状態はすべてオフです。ランチャーで操作できることは、すべてのゲームのアクセシビリティを保証しません。

## トラブルシューティング

起動しない場合は eboot.bin、sce_sys、ui/lang の配置を確認してください。ゲームが表示されない場合は、選択したストレージの roms を確認します。英語表示のままなら翻訳ファイルを点検してください。Safe Launch はセーブを消さずに特定ゲームの設定を戻せます。

/data/prosperoeden/ を削除しないでください。設定、セーブデータ、鍵が保存されている可能性があります。外部ストレージもバックアップしてください。

---

実際にコンパイルされた最後の公開 PS5 パッケージは 2026 年 10 月 15 日版です。10 月 30 日の公開は同じパッケージの複製です。新しいプレリリースの下書きには実行バイナリも第二世代ゲームの実機動作保証もありません。

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)