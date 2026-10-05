import os
import sys

# 確保 Windows 主控台支援 UTF-8 輸出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from flask import Flask, request, abort, render_template_string

# 載入 .env 檔案中的環境變數
load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PORT = int(os.getenv("PORT", 5000))

# 匯入 Gemini AI 服務
from ai_service import GeminiService
gemini_service = GeminiService(api_key=GEMINI_API_KEY)

# 匯入 LINE Bot SDK (v3)
try:
    from linebot.v3 import WebhookHandler
    from linebot.v3.exceptions import InvalidSignatureError
    from linebot.v3.messaging import (
        Configuration,
        ApiClient,
        MessagingApi,
        ReplyMessageRequest,
        TextMessage
    )
    from linebot.v3.webhooks import (
        MessageEvent,
        TextMessageContent
    )
    LINE_SDK_AVAILABLE = True
except ImportError:
    LINE_SDK_AVAILABLE = False
    print("⚠️ 警告: 尚未安裝 line-bot-sdk 套件。請執行 pip install -r requirements.txt")

app = Flask(__name__)

if LINE_SDK_AVAILABLE and LINE_CHANNEL_SECRET:
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
else:
    handler = None
    configuration = None


@app.route("/", methods=["GET"])
def index():
    """首頁健康檢查端點：方便在瀏覽器確認伺服器與設定狀態"""
    secret_set = bool(LINE_CHANNEL_SECRET and not LINE_CHANNEL_SECRET.startswith("your_"))
    token_set = bool(LINE_CHANNEL_ACCESS_TOKEN and not LINE_CHANNEL_ACCESS_TOKEN.startswith("your_"))
    gemini_set = bool(GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your_"))

    status_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>LINE Bot x Gemini AI 伺服器狀態</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; padding: 40px; }}
            .card {{ background: white; max-width: 600px; margin: 0 auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            h1 {{ color: #06c755; margin-top: 0; }}
            .status-item {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee; }}
            .badge-ok {{ background: #e6f9ed; color: #06c755; padding: 4px 10px; border-radius: 20px; font-weight: bold; }}
            .badge-warn {{ background: #fff4e5; color: #ff9800; padding: 4px 10px; border-radius: 20px; font-weight: bold; }}
            .tip {{ margin-top: 20px; padding: 12px; background: #eef7fe; border-left: 4px solid #1877f2; font-size: 14px; line-height: 1.6; }}
            code {{ background: #f1f1f1; padding: 2px 6px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 LINE Bot x Gemini AI</h1>
            <p>伺服器運作正常 (Server is Online) ✅</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <div class="status-item">
                <span>LINE Channel Secret</span>
                <span class="{'badge-ok' if secret_set else 'badge-warn'}">{'已設定' if secret_set else '未設定 / 預設值'}</span>
            </div>
            <div class="status-item">
                <span>LINE Channel Access Token</span>
                <span class="{'badge-ok' if token_set else 'badge-warn'}">{'已設定' if token_set else '未設定 / 預設值'}</span>
            </div>
            <div class="status-item">
                <span>Google Gemini API Key</span>
                <span class="{'badge-ok' if gemini_set else 'badge-warn'}">{'已設定' if gemini_set else '未設定 / 預設值'}</span>
            </div>
            <div class="tip">
                <strong>📌 Webhook 設定說明：</strong><br>
                請將您的 Public URL 接上 <code>/callback</code>（例如：<code>https://xxxx.ngrok-free.app/callback</code>），<br>
                並填入 LINE Developers Console 的 <strong>Webhook URL</strong> 設定中，再開啟 <strong>Use Webhook</strong> 開關！
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(status_html)


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook 回調入口點"""
    if not LINE_SDK_AVAILABLE or handler is None:
        return "LINE Bot SDK not initialized. Please configure credentials.", 500

    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature. Check your LINE_CHANNEL_SECRET.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error handling webhook: {e}")
        return "Error", 500

    return "OK", 200


if LINE_SDK_AVAILABLE and handler:
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event):
        """處理使用者發送的文字訊息"""
        user_text = event.message.text.strip()
        user_id = event.source.user_id if hasattr(event.source, "user_id") else "unknown"
        print(f"\n📩 [收到 LINE 訊息] 來自使用者: {user_id}")
        print(f"💬 [問題內容]: {user_text}")

        # 向 Google Gemini 取得回應
        ai_reply = gemini_service.generate_response(user_text)
        print(f"🤖 [Gemini 回應]: {ai_reply[:80]}..." if len(ai_reply) > 80 else f"🤖 [Gemini 回應]: {ai_reply}")

        # 透過 LINE Messaging API 送出回覆
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=ai_reply)]
                )
            )


if __name__ == "__main__":
    print("=" * 60)
    print("   [LINE Bot] Google Gemini AI 伺服器啟動中...")
    print(f"   [網址] 監聽網址: http://127.0.0.1:{PORT}")
    print(f"   [Webhook] 接收路徑: http://127.0.0.1:{PORT}/callback")
    print("=" * 60)
    app.run(host="0.0.0.0", port=PORT, debug=True)
