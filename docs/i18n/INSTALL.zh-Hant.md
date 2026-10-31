# Prospero.Eden Encore — 從原版移轉與更新 (繁體中文)

[← 繁體中文](README.zh-Hant.md) · [英文完整安裝指南](../../INSTALL.md) · [所有語言](../../LANGUAGES.md)

## 快速開始

1. 從 Encore Releases 取得完整安裝套件並核對檢查碼。
2. 備份現有 PPSA99008 應用程式、/data/prosperoeden 資料及外接儲存裝置。
3. 將整個 PPSA99008 資料夾放到 /data/homebrew/PPSA99008/，不要只複製 eboot.bin。
4. 開啟 Encore 並檢查 Settings → Storage、Language；僅使用合法取得的金鑰、韌體與遊戲。

## 應用程式 / PPSA99008

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

## 從原版移轉與更新

Encore 和原生 ProsperoEden 共用 PPSA99008 識別碼，無法直接當成兩套獨立應用程式。請更換完整的應用程式檔案，保留 /data/prosperoeden 中的存檔、設定、遊戲與金鑰。如舊版 assets/ 含有使用者資料，請先備份並保留到移轉完成。

**重要：**更新時請勿刪除 `/data/prosperoeden/` 或格式化外接儲存裝置。先備份，絕對不要覆寫現有存檔或金鑰。

## 相容性與已知限制

目前只有 PS5 韌體 13.60 經 Encore 實機測試；較早版本可能可用，但未經驗證，也沒有已確認的最低版本。部分遊戲可能卡頓、HUD 延遲、按鍵配置異常或暫停時凍結。CI 通過不代表實機可玩。

## 常見問題

若介面仍顯示英文，請到 Settings → Language 切換，並確認 ui/lang/ 語言檔已完整安裝。

若遊戲在變更設定後無法啟動，請嘗試單次 **Safe Launch**，不要刪除存檔。ZIP/FFPFSC 步驟請見[英文完整說明](../../INSTALL.md)，錯誤排查請見[疑難排解](../../TROUBLESHOOTING.md)及[支援](../../SUPPORT.md)。

本專案不提供遊戲、主機金鑰或韌體。回報問題時請勿公開私人資料。
