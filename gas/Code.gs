/**
 * ============================================================
 * LINE Bot x Google Apps Script (純本地模型聯網查詢架構)
 * ============================================================
 * 核心功能：
 * 1. 收到任何查詢問題（包含「查 ...」或直接提問）：
 *    ➔ 自動轉發給跑在您本機電腦上的本地模型 (Ollama + 聯網搜尋)
 *    ➔ 回傳條理分明的客觀解答，並在文末【附上點擊來源網址】
 * 2. 移除所有試算表依賴，不再需要複雜的權限設定！
 * ============================================================
 */

// 從指令碼屬性 (Script Properties) 取得環境設定
function getEnv(key) {
  return PropertiesService.getScriptProperties().getProperty(key) || '';
}

/**
 * Webhook 入口點：處理 LINE 發送過來的 POST 請求
 */
function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return ContentService.createTextOutput(JSON.stringify({ status: 'no post data' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    const requestData = JSON.parse(e.postData.contents);
    const events = requestData.events || [];

    // 若為 LINE Developers 的 Verify 測試請求（events 為空），直接回傳 200 OK
    if (events.length === 0) {
      return ContentService.createTextOutput('OK').setMimeType(ContentService.MimeType.TEXT);
    }

    const channelSecret = getEnv('LINE_CHANNEL_SECRET');
    const channelAccessToken = getEnv('LINE_CHANNEL_ACCESS_TOKEN');
    const localServerUrl = getEnv('LOCAL_SERVER_URL'); // 本機 Cloudflare Tunnel 網址

    // 數位簽章驗證
    if (channelSecret) {
      const signature = e.headers ? (e.headers['X-Line-Signature'] || e.headers['x-line-signature']) : null;
      if (signature && !verifySignature(e.postData.contents, signature, channelSecret)) {
        console.warn('❌ 數位簽章驗證失敗');
        return ContentService.createTextOutput('Invalid signature').setMimeType(ContentService.MimeType.TEXT);
      }
    }

    for (let i = 0; i < events.length; i++) {
      const event = events[i];

      // 只處理文字訊息事件
      if (event.type === 'message' && event.message && event.message.type === 'text') {
        const userText = event.message.text.trim();
        const replyToken = event.replyToken;

        console.log('📩 [收到使用者查詢]: ' + userText);

        // 去除可能的前綴「查」或「搜尋」
        const query = userText.replace(/^(查|搜尋)\s*/, '').trim() || userText;

        // 轉發給本機電腦的本地模型進行聯網搜尋與回答
        const searchReply = queryLocalServer(query, localServerUrl);
        sendSimpleReply(replyToken, searchReply, channelAccessToken);
      }
    }

    return ContentService.createTextOutput(JSON.stringify({ status: 'success' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    console.error('❌ doPost 處理錯誤: ' + error.toString());
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * 簡易 GET 檢查端點：用瀏覽器開啟時可確認狀態
 */
function doGet(e) {
  const secretSet = !!getEnv('LINE_CHANNEL_SECRET');
  const tokenSet = !!getEnv('LINE_CHANNEL_ACCESS_TOKEN');
  const localSet = !!getEnv('LOCAL_SERVER_URL');

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>LINE Bot 查詢狀態</title>
        <style>
          body { font-family: -apple-system, sans-serif; background: #f0f2f5; padding: 30px; }
          .card { background: white; max-width: 500px; margin: auto; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
          h2 { color: #06c755; margin-top: 0; }
          .status { padding: 8px 12px; margin: 8px 0; border-radius: 6px; }
          .ok { background: #e6f9ed; color: #06c755; }
          .warn { background: #fff4e5; color: #ff9800; }
        </style>
      </head>
      <body>
        <div class="card">
          <h2>LINE Bot 本機查詢服務運作中 ✅</h2>
          <div class="status ${secretSet ? 'ok' : 'warn'}">LINE_CHANNEL_SECRET: ${secretSet ? '已設定' : '未設定'}</div>
          <div class="status ${tokenSet ? 'ok' : 'warn'}">LINE_CHANNEL_ACCESS_TOKEN: ${tokenSet ? '已設定' : '未設定'}</div>
          <div class="status ${localSet ? 'ok' : 'warn'}">LOCAL_SERVER_URL (本機通道): ${localSet ? '已設定' : '未設定'}</div>
          <p style="margin-top:20px;font-size:14px;color:#666;">
            收到問題將自動由本機本地模型 (Ollama) 聯網查詢並附上來源。
          </p>
        </div>
      </body>
    </html>
  `;
  return HtmlService.createHtmlOutput(html);
}

/**
 * 轉發查詢至本機模型伺服器
 */
function queryLocalServer(query, localServerUrl) {
  if (!localServerUrl) {
    return '⚠️ 尚未設定本機通道網址 (LOCAL_SERVER_URL)。\n請在 Google Apps Script 的「專案設定 ➔ 指令碼屬性」填入本機 Tunnel 網址。';
  }

  // 清除結尾的斜線
  const cleanUrl = localServerUrl.replace(/\/+$/, '');
  const targetUrl = `${cleanUrl}/search`;

  const payload = {
    query: query
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const res = UrlFetchApp.fetch(targetUrl, options);
    const code = res.getResponseCode();
    if (code === 200) {
      const data = JSON.parse(res.getContentText());
      return data.reply || '本機模型未產生回應。';
    } else {
      console.warn(`本機伺服器回應 HTTP ${code}: ${res.getContentText()}`);
      return `⚠️ 本機伺服器處理失敗 (HTTP ${code})，請確認電腦端是否正常運作。`;
    }
  } catch (err) {
    console.error('連線本機伺服器失敗: ' + err.toString());
    return '⚠️ 目前無法連線至您的本機電腦伺服器。\n請確認：\n1. 電腦是否開機並連網\n2. 是否已執行 start_local_server.bat 啟動連線通道';
  }
}

/**
 * 透過 LINE Messaging API 發送單一文字回覆
 */
function sendSimpleReply(replyToken, text, accessToken) {
  if (!accessToken) return;

  const url = 'https://api.line.me/v2/bot/message/reply';
  const payload = {
    replyToken: replyToken,
    messages: [
      {
        type: 'text',
        text: text
      }
    ]
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + accessToken
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    UrlFetchApp.fetch(url, options);
  } catch (e) {
    console.error('LINE 發送失敗: ' + e.toString());
  }
}

/**
 * 驗證 LINE 數位簽章 (HMAC-SHA256)
 */
function verifySignature(bodyString, signature, channelSecret) {
  const expectedHash = Utilities.computeHmacSha256Signature(bodyString, channelSecret);
  const expectedSignature = Utilities.base64Encode(expectedHash);
  return signature === expectedSignature;
}
