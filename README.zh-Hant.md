# Prospero.Eden Encore — 繁體中文

> 為 PS5 客廳體驗打造的社群模擬器 · [English (default)](README.md) · [All 18 launcher language choices](LANGUAGES.md)

為 PS5 客廳體驗打造的社群模擬器. Encore is an independent community fork with a controller-friendly launcher, game library, graphics settings and diagnostics, not an official Sony or Nintendo product.

## 快速開始

1. 從 Encore Releases 取得完整安裝套件並核對檢查碼。
2. 備份現有 PPSA99008 應用程式、/data/prosperoeden 資料及外接儲存裝置。
3. 將整個 PPSA99008 資料夾放到 /data/homebrew/PPSA99008/，不要只複製 eboot.bin。
4. 開啟 Encore 並檢查 Settings → Storage、Language；僅使用合法取得的金鑰、韌體與遊戲。

[從原版移轉與更新](docs/i18n/INSTALL.zh-Hant.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## 從原版移轉與更新

Encore 和原生 ProsperoEden 共用 PPSA99008 識別碼，無法直接當成兩套獨立應用程式。請更換完整的應用程式檔案，保留 /data/prosperoeden 中的存檔、設定、遊戲與金鑰。如舊版 assets/ 含有使用者資料，請先備份並保留到移轉完成。

**Application ID:** `PPSA99008`. **Application:** `/data/homebrew/PPSA99008/`. **Persistent data:** `/data/prosperoeden/`.

[從原版移轉與更新 — step-by-step](docs/i18n/INSTALL.zh-Hant.md) · [Full installation instructions in English](INSTALL.md)

## 相容性與已知限制

目前只有 PS5 韌體 13.60 經 Encore 實機測試；較早版本可能可用，但未經驗證，也沒有已確認的最低版本。部分遊戲可能卡頓、HUD 延遲、按鍵配置異常或暫停時凍結。CI 通過不代表實機可玩。

Content formats in development sources: **NSP/XCI**, experimental **NSZ/XCZ**, and direct **NRO/NSO/NCA/NAX/KIP** loaders. A recognized extension does not guarantee that a complete game will start.

## 常見問題

Switch 2 遊戲仍在獨立研究分支中探索，並未包含於現行 PS5 版本。畫格生成與自動更新也是規劃功能，尚未發佈。

若介面仍顯示英文，請到 Settings → Language 切換，並確認 ui/lang/ 語言檔已完整安裝。

## Community and credits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

本專案不提供遊戲、主機金鑰或韌體。回報問題時請勿公開私人資料。

> This translation is a concise guide for the selected launcher language. For complete technical information, use the English README and linked guides. No console performance claim is implied.
