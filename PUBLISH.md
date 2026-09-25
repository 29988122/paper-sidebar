# 上架步驟（由你本人操作）

商店頁面：https://chromewebstore.google.com/detail/paper-sidebar/fbomcfigjianejcinmaloifgaladakic

需要的檔案都在這個資料夾：

| 用途 | 檔案 |
|---|---|
| 套件 | `dist/paper-sidebar-1.0.1.zip`（目前版本） |
| 商店 icon 128×128 | `store/icon-128.png` |
| 小型宣傳圖 440×280 | `store/promo-440x280.png` |
| 螢幕截圖 1280×800 | `store/screenshots/*.png` |
| 說明文字 | `store/listing.en.md`、`store/listing.zh-TW.md` |

1. 開啟 Chrome 線上應用程式商店開發人員資訊主頁：https://chrome.google.com/webstore/devconsole
2. 按「新增項目」，上傳 `dist/paper-sidebar-<版本>.zip`。
3. **商店資訊**分頁：
   - 說明：貼上 `listing.en.md` 的「Detailed description」。
   - 另外新增「中文（台灣）」語系，貼上 `listing.zh-TW.md` 的「詳細說明」。
   - 類別：主題 → Minimalist（或 Colors）。
   - 語言：English。
   - 上傳 icon、宣傳圖、螢幕截圖。
4. **隱私權**分頁（如果主題也有顯示這一頁）：
   - 單一用途：Changes Chrome's colors so the vertical tab sidebar is white, with an orange marker on the current tab.
   - 權限：無；遠端程式碼：否；不收集使用者資料（勾選各項聲明）。
5. **發布**分頁：免費、所有地區、**公開**。
6. 按「提交審查」（這一步請你自己按）。審查通常幾天，最長可能幾週。
7. 核准後，在你的 Chrome 從商店安裝一次：
   - 會取代目前「自訂 Chrome」選的灰色。
   - 其他電腦只要登入同一個帳號，並在同步設定裡開啟「主題」，就會自動套用。

## 日後更新
1. 改 `palette.json` 的 `version`（例如 1.0.1）和顏色。
2. `python3 tools/build.py --zip`
3. 資訊主頁 → 套件 → 上傳新套件 → 提交審查。

## 1.0.1 更新（全白＋橘色標記）
1. 資訊主頁 → 紙白側欄 → **套件** → 上傳新套件 → 選 `dist/paper-sidebar-1.0.1.zip`。
2. **商店資訊**：
   - 刪掉舊的 3 張截圖，改上傳 `store/screenshots` 裡的新圖（`60-hero`、`61-states`、`30-before-after`）；
   - 小型宣傳圖換成新的 `store/promo-440x280.png`，icon 換成新的 `store/icon-128.png`；
   - 說明文字換成 `listing.en.md`／`listing.zh-TW.md` 的新版本。
3. 按「提交審查」。
