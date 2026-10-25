/**
 * ============================================================
 * LINE Bot x Google Apps Script (混合雲 + 本機模型架構)
 * ============================================================
 * 核心功能：
 * 1. 訊息開頭為「查 ...」：
 *    ➔ 轉發給跑在您本機電腦上的本地模型 (Ollama + 聯網搜尋)
 *    ➔ 回傳條理分明的解答並【附上參考來源】
 * 2. 其他任何一般訊息：
 *    ➔ 自動記入您的 Google 試算表 (待辦清單：時間、發送者、內容)
 *    ➔ LINE 秒回「✅ 已為您記入待辦事項：...」
 * ============================================================
 */

// 從指令碼屬性 (Script Properties) 取得環境設定
function getEnv(key) {
  return PropertiesService.getScriptProperties().getProperty(key) || '';
}

// 您的 Google 試算表 ID
const SPREADSHEET_ID = getEnv('SPREADSHEET_ID') || '1SjhS3ydHQgqLSFAL0020NupwkZjGrV4of_-4Uaf50ko';

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
        const userId = (event.source && event.source.userId) ? event.source.userId : 'unknown';

        console.log('📩 [收到使用者訊息]: ' + userText);

        // 分流判斷：是否以「查」開頭
        if (userText.startsWith('查') || userText.startsWith('查 ') || userText.startsWith('搜尋') || userText.startsWith('搜尋 ')) {
          // 取出「查」後面的關鍵字
          const query = userText.replace(/^(查|搜尋)\s*/, '').trim();

          if (!query) {
            sendSimpleReply(replyToken, '請問您想查詢什麼呢？請輸入「查 [欲查詢內容]」，例如：「查 東華大學 陳文盛教授」。', channelAccessToken);
          } else {
            // 轉發給本機電腦的本地模型進行聯網搜尋與回答
            const searchReply = queryLocalServer(query, localServerUrl);
            sendSimpleReply(replyToken, searchReply, channelAccessToken);
          }

        } else {
          // 其他一般訊息 ➔ 記錄到 Google 試算表待辦清單
          const todoResult = appendTodoToSheet(SPREADSHEET_ID, userId, userText);
          const replyText = `✅ 已為您記入待辦事項！\n\n📌 內容：${userText}\n🕒 時間：${todoResult.time}`;
          sendSimpleReply(replyToken, replyText, channelAccessToken);
        }
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
        <title>LINE Bot 混合雲狀態</title>
        <style>
          body { font-family: -apple-system, sans-serif; background: #f0f2f5; padding: 30px; }
          .card { background: white; max-width: 550px; margin: auto; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
          h2 { color: #06c755; margin-top: 0; }
          .status { padding: 8px 12px; margin: 8px 0; border-radius: 6px; }
          .ok { background: #e6f9ed; color: #06c755; }
          .warn { background: #fff4e5; color: #ff9800; }
        </style>
      </head>
      <body>
        <div class="card">
          <h2>LINE Bot 混合雲服務運作中 ✅</h2>
          <div class="status ${secretSet ? 'ok' : 'warn'}">LINE_CHANNEL_SECRET: ${secretSet ? '已設定' : '未設定'}</div>
          <div class="status ${tokenSet ? 'ok' : 'warn'}">LINE_CHANNEL_ACCESS_TOKEN: ${tokenSet ? '已設定' : '未設定'}</div>
          <div class="status ${localSet ? 'ok' : 'warn'}">LOCAL_SERVER_URL (本機通道): ${localSet ? '已設定' : '未設定 (請填入本機 Tunnel 網址)'}</div>
          <div class="status ok">SPREADSHEET_ID: ${SPREADSHEET_ID}</div>
          <p style="margin-top:20px;font-size:14px;color:#666;">
            - 輸入「查 [關鍵字]」：由本機模型聯網回答並附來源。<br>
            - 輸入其他文字：自動記入 Google 試算表待辦清單。
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
    return '⚠️ 尚未設定本機通道網址 (LOCAL_SERVER_URL)。請先在電腦執行 start_local_server.bat 並將網址填入指令碼屬性。';
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
 * 將待辦事項寫入 Google 試算表
 */
function appendTodoToSheet(spreadsheetId, userId, todoContent) {
  const now = new Date();
  const timeStr = Utilities.formatDate(now, 'Asia/Taipei', 'yyyy/MM/dd HH:mm:ss');

  try {
    const ss = SpreadsheetApp.openById(spreadsheetId);
    let sheet = ss.getActiveSheet();

    // 如果是全新空白工作表，自動寫入表頭
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['記錄時間', '傳訊者 ID', '待辦事項內容', '狀態']);
      sheet.getRange(1, 1, 1, 4).setFontWeight('bold').setBackground('#f3f3f3');
    }

    sheet.appendRow([timeStr, userId, todoContent, '待處理']);
    console.log(`✅ 成功寫入試算表: [${timeStr}] ${todoContent}`);
    return { success: true, time: timeStr };

  } catch (e) {
    console.error('寫入試算表失敗: ' + e.toString());
    return { success: false, time: timeStr };
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

/**
 * 快速手動授權與測試試算表寫入
 * （請在 GAS 編輯器上方選擇此函式，並點擊一次「執行 ▶️」即可完成授權）
 */
function testSheetAuth() {
  const now = new Date();
  const timeStr = Utilities.formatDate(now, 'Asia/Taipei', 'yyyy/MM/dd HH:mm:ss');
  const result = appendTodoToSheet(SPREADSHEET_ID, '手動測試', '這是一筆手動授權測試待辦');
  console.log('測試寫入結果: ' + JSON.stringify(result));
}

