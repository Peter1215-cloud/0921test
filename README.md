# 🤖 LINE Bot 串接免費 Google Gemini AI

這是一個使用 **Python Flask** 開發的 LINE 智慧問答機器人，後端串接 Google 官方最新、完全免費的 **Gemini AI (Gemini 2.5 Flash / 1.5 Flash)**。使用者在 LINE 聊天室中發問，AI 即會透過繁體中文以極快的速度解答！

---

## 🌟 費用說明 (100% 免費)
- **Google Gemini API**：[Google AI Studio](https://aistudio.google.com/) 提供免費額度（每分鐘 15 次請求、每日 1,500 次），**無需綁定信用卡**。
- **LINE Messaging API**：LINE 官方帳號的「**回覆訊息 (Reply API)**」完全免費且不限額度（不佔用每月 200 則的發訊額度）。
- **測試工具**：Python、Flask 與 ngrok 皆提供免費方案。

---

## 📁 檔案結構

```
0921test/
├── app.py              # Flask Webhook 主伺服器
├── ai_service.py       # Google Gemini AI 調用模組
├── test_bot.py         # 單元測試腳本
├── requirements.txt    # 相依套件清單
├── .env.example        # 環境變數設定範本
├── .gitignore          # Git 忽略設定
└── README.md           # 完整使用說明書
```

---

## 🚀 快速上手教學 (五大步驟)

### 第一步：取得 Google Gemini 免費 API Key
1. 前往 [Google AI Studio](https://aistudio.google.com/)。
2. 使用任一 Google 帳號登入。
3. 點選左上方或畫面中的 **「Get API key」** -> **「Create API key」**。
4. 複製產生的金鑰（以 `AIzaSy...` 開頭），稍後會用到。

---

### 第二步：申請 LINE Messaging API 帳號與憑證
1. 前往 [LINE Developers Console](https://developers.line.biz/) 並登入個人 LINE 帳號。
2. 建立一個 **Provider**（提供者，名稱自訂，例如 `MyBot`）。
3. 在 Provider 內點擊 **「Create a new channel」**，選擇 **「Messaging API」**：
   - 填寫 Channel name（機器人名稱）、Channel description（介紹）、Category（分類）等基本資訊。
4. 建立完成後，進入該 Channel：
   - 在 **「Basic settings」** 分頁最下方找到 **Channel secret**，點擊複製。
   - 在 **「Messaging API」** 分頁最下方找到 **Channel access token (long-lived)**，點擊 **「Issue」** 產生並複製該 Token。
5. **重要設定（避免機器人自言自語）**：
   - 在「Messaging API」分頁找到 **LINE Official Account features**。
   - 點擊 **Auto-reply messages** 旁的 **Edit**。
   - 在開啟的 LINE 官方帳號後台中，將 **「自動回應訊息」改為「關閉 (Disabled)」**，並確認 **「Webhook」設定為「開啟 (Enabled)」**。

---

### 第三步：設定專案環境變數
1. 在專案資料夾複製 `.env.example` 並更名為 `.env`：
   ```powershell
   Copy-Item .env.example .env
   ```
2. 使用文字編輯器（如 VS Code、記事本）開啟 `.env`，填入前兩步取得的金鑰：
   ```env
   LINE_CHANNEL_SECRET=貼上你的_Channel_Secret
   LINE_CHANNEL_ACCESS_TOKEN=貼上你的_Channel_Access_Token
   GEMINI_API_KEY=貼上你的_Gemini_API_Key
   PORT=5000
   ```

---

### 第四步：安裝套件並啟動伺服器
1. 安裝所需 Python 套件：
   ```powershell
   pip install -r requirements.txt
   ```
2. 啟動伺服器：
   ```powershell
   python app.py
   ```
3. 開啟瀏覽器訪問 [http://127.0.0.1:5000](http://127.0.0.1:5000)，確認看到：
   - `伺服器運作正常 (Server is Online) ✅`
   - 三項金鑰皆顯示為綠色「已設定」狀態。

---

### 第五步：使用 ngrok 建立公開網址並設定 LINE Webhook
LINE 伺服器需要一個公開的 HTTPS 網址才能將訊息推送到你本機的伺服器。

1. 下載並安裝免費的 [ngrok](https://ngrok.com/)。
2. 在另一個終端機視窗執行：
   ```powershell
   ngrok http 5000
   ```
3. 複製 ngrok 產生的 `Forwarding` HTTPS 網址，例如：
   `https://1234-56-78-90.ngrok-free.app`
4. 回到 [LINE Developers Console] 的 **Messaging API** 分頁：
   - 找到 **Webhook settings**。
   - 在 **Webhook URL** 欄位貼上網址並加上 `/callback`，例如：
     `https://1234-56-78-90.ngrok-free.app/callback`
   - 點擊 **Update** 儲存。
   - 點擊 **Verify** 按鈕，若出現 **Success** 代表串接成功！
   - 將 **Use webhook** 開關切換為 **開啟 (Enabled)**。

---

## 📱 實機測試
1. 在 LINE Developers 的 **Messaging API** 分頁中，可以看到專屬的 **QR code**。
2. 用手機 LINE 掃描該 QR code 將機器人加為好友。
3. 傳送任意問題（例如：「請用繁體中文推薦我台北 3 家必吃的牛肉麵，並說明原因」）。
4. 機器人將立即為您解答！

---

## 🧪 執行自動測試
若想確認程式碼邏輯與健康端點運作無誤，可執行：
```powershell
python -m unittest test_bot.py
```
