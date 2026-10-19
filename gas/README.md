# 🚀 Google Apps Script (GAS) 部署教學指引

這份指南將帶您在 5 分鐘內，將 LINE Bot 部署到 Google 官方的雲端環境，享受 **7x24 小時永久免費免開機** 服務！

---

## 步驟 1：建立 Google Apps Script 專案

1. 開啟瀏覽器，前往 [Google Apps Script 官網](https://script.google.com/)。
2. 使用您的 Google 帳號登入。
3. 點選左上角的 **「新專案 (New project)」**。
4. 點擊左上方的「未命名專案」，更名為您喜歡的名稱（例如：`LINE-Gemini-Bot`）。

---

## 步驟 2：貼上程式碼

1. 將預設編輯器裡的內容清空。
2. 開啟本專案的 [`gas/Code.gs`](file:///c:/Users/user/Desktop/0921test/gas/Code.gs)，將裡面的全部程式碼複製。
3. 貼回 Google Apps Script 網頁編輯器中。
4. 按下鍵盤的 `Ctrl + S`（或點擊上方的磁碟圖示 💾）儲存專案。

---

## 步驟 3：設定金鑰（指令碼屬性，確保安全不洩漏）

請將您的 API Key 安全保存在 Google 雲端設定中：

1. 在 GAS 網頁左側選單，點選齒輪圖示 **「專案設定 (Project Settings)」**。
2. 捲動到頁面最下方的 **「指令碼屬性 (Script Properties)」** 區塊。
3. 點選 **「新增指令碼屬性 (Add script property)」**，依序新增以下 3 個鍵值（請直接使用您原本 `.env` 中的內容）：

| 屬性名稱 (Property) | 值 (Value) | 說明 |
| :--- | :--- | :--- |
| `LINE_CHANNEL_SECRET` | 您的 Channel Secret | 在 LINE Developers 的 Basic settings 取得 |
| `LINE_CHANNEL_ACCESS_TOKEN` | 您的 Channel Access Token | 在 LINE Developers 的 Messaging API 取得 |
| `GEMINI_API_KEY` | 您的 Gemini API Key | 在 Google AI Studio 取得 |

4. 填寫完畢後，點選下方 **「儲存指令碼屬性 (Save script properties)」**。

---

## 步驟 4：發布為網頁應用程式 (Web App)

1. 回到 GAS 頁面右上角，點選藍色的 **「部署 (Deploy)」** ➔ **「新增部署作業 (New deployment)」**。
2. 點選左上角齒輪旁的「選取類型」，選擇 **「網頁應用程式 (Web app)」**。
3. 設定如下：
   - **說明 (Description)**：`v1.0`
   - **執行身分 (Execute as)**：`我 (Me)`
   - **誰可以存取 (Who has access)**：⚠️ **務必選擇「所有人 (Anyone)」**（否則 LINE 無法傳送 Webhook）。
4. 點選右下角的 **「部署 (Deploy)」**。
5. （首次部署時）若跳出「需要授權 (Authorization required)」，請依提示點擊：
   - 點擊「審查權限 (Review permissions)」➔ 選擇您的 Google 帳號。
   - 點擊「進階 (Advanced)」➔ 點選「前往 LINE-Gemini-Bot (不安全)」。
   - 點擊「允許 (Allow)」。
6. 部署完成後，複製畫面上顯示的 **「網頁應用程式網址 (Web app URL)」**（網址結尾為 `/exec`）。

---

## 步驟 5：將網址貼到 LINE Developers

1. 前往 [LINE Developers Console](https://developers.line.biz/)。
2. 點進您的 Channel ➔ 切換至 **Messaging API** 分頁。
3. 找到 **Webhook settings**：
   - 在 **Webhook URL** 欄位貼上剛才複製的 Google Apps Script 網址（結尾有 `/exec`）。
   - 點擊 **Update** 儲存。
   - 點擊 **Verify** 按鈕，看到綠色 **Success** 即表示連線成功！
   - 確認下方 **Use webhook** 開關已開啟為 **Enabled**。

---

## 📱 恭喜完成！立即測試

現在你可以直接關閉電腦，打開手機 LINE 傳訊息給機器人：
- 機器人會即時解答，並在回答下方自動附上 **3 個延伸推薦問題按鈕**。
- 點擊按鈕即可自動追問，享受流暢的對話體驗！
