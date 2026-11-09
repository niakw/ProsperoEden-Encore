# Eden Encore — 設定 · 繁體中文

[概覽](README.zh-Hant.md) · [安裝與更新](INSTALL.zh-Hant.md) · [設定](SETTINGS.zh-Hant.md) · [問題排除](TROUBLESHOOTING.zh-Hant.md) · [支援](SUPPORT.zh-Hant.md) · [無障礙](ACCESSIBILITY.zh-Hant.md) · [🌐](../../LANGUAGES.md)

建議的初始設定為 Vulkan、1440p 電視輸出、1.25x 遊戲內部渲染倍率、空間 FSR 1（銳利度 50%）、FXAA 與 60 Hz。電視輸出解析度不同於遊戲內部渲染解析度。影格生成不會提升遊戲本身的模擬速度。

## Vulkan / FSR 1 — 設定

| `Minimum` | `Recommended` | `High` |
| --- | --- | --- |
| `Vulkan` · `1080p` · `1×` · `Bilinear` · `60 Hz` | `Vulkan` · `1440p` · `1.25×` · `FSR 1` · `FXAA` · `60 Hz` | `Vulkan` · `2160p` · `1.5×` · `Bicubic` · `FXAA` · `60 Hz` |

## 設定 · Touchpad

遊戲中短按 Touchpad 可開啟 Encore 快速設定；中央系統按鈕保留給主機使用。選單包含圖形、按鍵對應、FPS 與診斷資訊。部分設定變更需要重新啟動遊戲。語言可從 Settings → Language 選擇，但不是所有翻譯目錄語言都可在選單中選取。

## 無障礙

放大文字、高對比及減少動態效果可於無障礙設定中分別啟用，預設全部關閉。啟動器容易操作不代表每款遊戲內部都支援無障礙功能。

## 問題排除

無法啟動時，請確認 eboot.bin、sce_sys 與 ui/lang。若沒有列出遊戲，請檢查所選儲存根目錄的 roms。若選單仍顯示英文，請確認翻譯檔。Safe Launch 可在不刪除存檔的情況下重設單一遊戲設定。

## 支援

在 GitHub Issues 中提供 Encore 版本、PS5 韌體版本、重現步驟、相關設定及去識別化日誌。請勿公開金鑰、遊戲存檔或個人資料。

切勿刪除 /data/prosperoeden/，其中可能存放設定、存檔與金鑰。請同時備份外部儲存空間。

---

最後一份真正完成編譯並公開的 PS5 安裝包日期為 2026 年 10 月 15 日；10 月 30 日發布的是相同內容的副本。新的預發布草稿沒有執行檔，也不代表第二代遊戲已通過主機驗證。

[English](../../SETTINGS.md) · [安裝與更新](INSTALL.zh-Hant.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
