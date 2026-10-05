# 五頁簡報 – LINE Bot + Gemini 方案概覽

---

## 第 1 頁 – 專案概述
- 目標：在 Windows 本機上建置 **LINE Bot**，呼叫 **Google Gemini** 回覆使用者訊息。
- 完全使用 **免費方案**（Gemini free tier、LINE Messaging API 無限制、Cloudflare quick tunnel）
- 不會儲存信用卡資訊，避免任何付費風險。
- 所有機密資訊放在 `.env`，且 `.gitignore` 已排除，確保不會洩漏至 GitHub。

---

## 第 2 頁 – 系統架構圖
```mermaid
flowchart TD
    subgraph LocalHost[本機環境]
        A[Flask App (app.py)] --> B[GeminiService (ai_service.py)]
        B --> C[Google Gemini (SDK or REST)]
    end
    D[Cloudflare Quick Tunnel] -->|公開 URL| A
    E[LINE Platform] -->|Webhook| D
    A -->|回覆| E
    click A "file:///c:/Users/user/Desktop/0921test/app.py" "app.py"
    click B "file:///c:/Users/user/Desktop/0921test/ai_service.py" "ai_service.py"
```
- **Flask** 提供 `/callback` 與健康檢查 `/` 端點。
- **Cloudflare** 產生公開 URL `https://ranch-mathematics-weekly-fired.trycloudflare.com/callback`。
- **LINE** 依此 URL 呼叫 webhook，發送訊息至 Flask，Flask 再呼叫 Gemini，最後回傳文字給使用者。

---

## 第 3 頁 – 防止幻覺 (Anti‑Hallucination) 措施
- **系統指示**：明確要求模型只能在有把握的情況下回答，否則回覆 *"抱歉，我目前沒有這方面的確切資料，建議您查閱官方最新資訊"*。
- **溫度設定**：`temperature = 0.2`（SDK、REST 均相同），降低隨機性，提升答案一致性。
- **模型備援**：`gemini-3.5-flash` 為主，失敗時自動切換至 `gemini-3.8-flash`、`gemini-1.5-pro`。
- **示例**：
  - 問題：*"2026 年的總統是誰"* → 回覆 *"抱歉，我目前沒有這方面的確切資料..."*。
  - 問題：*"台北今天的天氣"* → 正常回覆天氣資訊。

---

## 第 4 頁 – 安全與成本分析
- **憑證管理**：`.env` 包含 `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `GEMINI_API_KEY`，已加入 `.gitignore` 防止上傳。
- **Webhook 簽名驗證**：`app.py` 會檢查 `X-Line-Signature`，未通過則記錄 warning，避免偽造請求。
- **免費額度**：
  - Gemini：15 RPM、每日 1500 次請求，超過會回傳 429，並不會產生費用。
  - Cloudflare 快速隧道：免費版可持續運行，無需額外付費。
  - LINE Messaging API：基本回覆功能無付費上限。
- **風險**：只要不自行開啟付費功能（如 Gemini 的 Search、Codey 等），系統不會產生任何收費。

---

## 第 5 頁 – 部署與使用步驟 & 未來擴充
1. **環境建置**
   ```powershell
   cd C:\Users\user\Desktop\0921test
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **設定憑證**：複製 `.env.example` 為 `.env`，填入提供的金鑰。
3. **啟動服務**：執行 `start_bot.bat`，同時啟動 Flask 與 Cloudflare 隧道。
4. **測試**：在 LINE 上傳訊息，應得到 Gemini 回覆；可在瀏覽器開啟 `http://localhost:<PORT>/` 查看健康頁面。
5. **未來方向**
   - 加入 **訊息紀錄** 與 **資料庫**（SQLite / PostgreSQL）
   - 擴充 **多模型選擇**、**多語言支援**
   - 使用 **CI/CD** 自動部署至雲端（例如 Railway 或 Render）
   - 加入 **自訂指令**、**快速回覆**，提高使用者互動體驗。

---

---

*此檔案已放置於專案根目錄，其他團隊成員可直接在 VS Code 中檢視或匯出為 PDF/PowerPoint。*
