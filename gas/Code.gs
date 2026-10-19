/**
 * ============================================================
 * LINE Bot x Google Gemini AI (Google Apps Script 版本)
 * ============================================================
 * 功能特色：
 * 1. 7x24 小時免費雲端執行，免開電腦、免本機 Tunnel
 * 2. 採用方案 A：單次 Gemini 請求同時產出主回答與 3 個延伸推薦問題
 * 3. 嚴格防幻覺機制 (溫度 0.2 + 誠實查核系統提示詞)
 * 4. 金鑰保存在「指令碼屬性 (Script Properties)」，安全不外洩
 * ============================================================
 */

// 從指令碼屬性 (Script Properties) 取得敏感金鑰
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
    const geminiApiKey = getEnv('GEMINI_API_KEY');

    // 簽章驗證（若有設定 CHANNEL_SECRET 則驗證）
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
        const userMessage = event.message.text.trim();
        const replyToken = event.replyToken;

        console.log('📩 [收到使用者提問]: ' + userMessage);

        // 呼叫 Gemini AI (單次請求同時產出主回答與追問建議)
        const aiResult = callGeminiWithQuickReplies(userMessage, geminiApiKey);
        console.log('🤖 [Gemini 回應完成]: ' + (aiResult.reply ? aiResult.reply.substring(0, 50) + '...' : ''));

        // 回傳給 LINE 使用者
        sendLineReply(replyToken, aiResult.reply, aiResult.followup_questions, channelAccessToken);
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
  const geminiSet = !!getEnv('GEMINI_API_KEY');

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>LINE Bot x Gemini GAS 狀態</title>
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
          <h2>LINE Bot 伺服器運作中 (GAS) ✅</h2>
          <div class="status ${secretSet ? 'ok' : 'warn'}">LINE_CHANNEL_SECRET: ${secretSet ? '已設定' : '未設定'}</div>
          <div class="status ${tokenSet ? 'ok' : 'warn'}">LINE_CHANNEL_ACCESS_TOKEN: ${tokenSet ? '已設定' : '未設定'}</div>
          <div class="status ${geminiSet ? 'ok' : 'warn'}">GEMINI_API_KEY: ${geminiSet ? '已設定' : '未設定'}</div>
          <p style="margin-top:20px;font-size:14px;color:#666;">請複製本網址並在 LINE Developers Webhook URL 中貼上。</p>
        </div>
      </body>
    </html>
  `;
  return HtmlService.createHtmlOutput(html);
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
 * 即時連網搜尋：透過 Google 即時新聞與時事檢索抓取網路最新資料（100% 免費無額度限制）
 */
function fetchRealtimeWebData(query) {
  try {
    const encodedQuery = encodeURIComponent(query);
    const feedUrl = `https://news.google.com/rss/search?q=${encodedQuery}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant`;
    const res = UrlFetchApp.fetch(feedUrl, { muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return '';

    const xml = res.getContentText();
    const document = XmlService.parse(xml);
    const root = document.getRootElement();
    const channel = root.getChild('channel');
    if (!channel) return '';

    const items = channel.getChildren('item');
    if (!items || items.length === 0) return '';

    let snippets = [];
    const maxItems = Math.min(items.length, 4);
    for (let i = 0; i < maxItems; i++) {
      const item = items[i];
      const title = item.getChildText('title') || '';
      const pubDate = item.getChildText('pubDate') || '';
      if (title) {
        snippets.push(`- 【最新即時報導】${title} (發布時間: ${pubDate})`);
      }
    }

    return snippets.join('\n');
  } catch (e) {
    console.warn('即時搜尋檢索失敗: ' + e.toString());
    return '';
  }
}

/**
 * 呼叫 Google Gemini REST API（方案 A：一次取得主回答 + 3 個延伸推薦問題，支援即時連網）
 */
function callGeminiWithQuickReplies(userMessage, apiKey) {
  if (!apiKey) {
    return {
      reply: '⚠️ 尚未設定 GEMINI_API_KEY，請於 Google Apps Script 的「指令碼屬性」填入 API Key。',
      followup_questions: []
    };
  }

  // 取得現在時間供防幻覺時間錨定
  const now = new Date();
  const currentDate = Utilities.formatDate(now, 'Asia/Taipei', 'yyyy年MM月dd日');

  // 即時連網抓取最新資料
  const webContext = fetchRealtimeWebData(userMessage);
  let promptWithWeb = userMessage;
  if (webContext) {
    promptWithWeb = `【聯網即時檢索到的最新資料】：\n${webContext}\n\n【使用者提問】：\n${userMessage}`;
  }

  const systemInstruction = 
    `你是一個嚴謹、誠實、條理分明的 LINE 智慧助理。今天是 ${currentDate}。\n\n` +
    `【最高核心準則 - 杜絕虛構與瞎編】：\n` +
    `1. 你的所有回答必須基於真實事實與客觀知識，嚴格禁止憑空捏造任何不存在的人名、事件、店名、營業時間、法規或數據。\n` +
    `2. 如果你對使用者的提問缺乏確切資訊、不確定真實性，或問題涉及尚未發生的未來事件，請誠實明確地回答「抱歉，我目前沒有這方面的確切資料，建議您查閱官方最新資訊」，絕對不可自行揣測。\n` +
    `3. 請一律使用台灣繁體中文回應。\n\n` +
    `【輸出格式要求】：\n` +
    `請務必且只能輸出合法 JSON 格式，不得包含 markdown 語法（例如不要輸出 \`\`\`json 標記）：\n` +
    `{\n` +
    `  "reply": "給使用者的完整回答內容（繁體中文、排版清晰易讀）",\n` +
    `  "followup_questions": ["推薦追問1", "推薦追問2", "推薦追問3"]\n` +
    `}\n` +
    `注意：followup_questions 陣列請給出 3 個使用者最可能想繼續追問的問題，每個問題請控制在 15 字以內。`;

  const payload = {
    contents: [
      {
        parts: [{ text: promptWithWeb }]
      }
    ],
    systemInstruction: {
      parts: [{ text: systemInstruction }]
    },
    generationConfig: {
      temperature: 0.2,
      responseMimeType: "application/json"
    }
  };

  // 支援的模型清單（依序嘗試，確保高可用性）
  const candidateModels = ['gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-2.5-flash'];

  for (let m = 0; m < candidateModels.length; m++) {
    const modelName = candidateModels[m];
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;

    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };

    try {
      const response = UrlFetchApp.fetch(apiUrl, options);
      const responseCode = response.getResponseCode();
      const responseText = response.getContentText();

      if (responseCode === 200) {
        const resData = JSON.parse(responseText);
        const candidates = resData.candidates || [];
        if (candidates.length > 0 && candidates[0].content && candidates[0].content.parts.length > 0) {
          const rawJsonText = candidates[0].content.parts[0].text;
          try {
            const parsed = JSON.parse(rawJsonText);
            return {
              reply: parsed.reply || '沒有內容',
              followup_questions: Array.isArray(parsed.followup_questions) ? parsed.followup_questions.slice(0, 3) : []
            };
          } catch (e) {
            return {
              reply: rawJsonText,
              followup_questions: []
            };
          }
        }
      } else {
        console.warn(`[${modelName}] API 回應 HTTP ${responseCode}，嘗試下一個備援模型...`);
      }
    } catch (err) {
      console.warn(`[${modelName}] 連線異常: ` + err.toString());
    }
  }

  return { reply: '❌ AI 服務暫時無法回應，請稍後再試。', followup_questions: [] };
}

/**
 * 透過 LINE Messaging API 發送回覆 (包含 Quick Reply 按鈕)
 */
function sendLineReply(replyToken, replyText, followupQuestions, accessToken) {
  if (!accessToken) {
    console.warn('⚠️ LINE_CHANNEL_ACCESS_TOKEN 未設定，無法發送回覆');
    return;
  }

  const lineApiUrl = 'https://api.line.me/v2/bot/message/reply';

  // 建立訊息本體
  const messageObj = {
    type: 'text',
    text: replyText
  };

  // 若有推薦的後續問題，包裝為 QuickReplyItem
  if (followupQuestions && followupQuestions.length > 0) {
    const items = [];
    for (let i = 0; i < followupQuestions.length; i++) {
      const q = String(followupQuestions[i]).trim();
      if (!q) continue;

      // LINE QuickReply label 上限 20 字元
      const labelText = q.length > 20 ? q.substring(0, 20) : q;

      items.push({
        type: 'action',
        action: {
          type: 'message',
          label: labelText,
          text: q
        }
      });
    }

    if (items.length > 0) {
      messageObj.quickReply = {
        items: items
      };
    }
  }

  const payload = {
    replyToken: replyToken,
    messages: [messageObj]
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
    const response = UrlFetchApp.fetch(lineApiUrl, options);
    const code = response.getResponseCode();
    if (code !== 200) {
      console.error(`LINE Reply 失敗 (${code}): ` + response.getContentText());
    } else {
      console.log('✅ LINE 訊息與按鈕發送成功');
    }
  } catch (err) {
    console.error('發送 LINE 訊息異常: ' + err.toString());
  }
}
