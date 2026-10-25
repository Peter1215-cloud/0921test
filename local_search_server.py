import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
LOCAL_MODEL = "qwen2.5-coder:3b"

def search_web(query: str, max_results: int = 4):
    """透過免付費即時新聞與公開資料來源檢索相關網頁摘要與來源網址"""
    results = []
    try:
        encoded_q = urllib.parse.quote(query)
        feed_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        res = requests.get(feed_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            items = root.findall(".//item")[:max_results]
            for it in items:
                title = it.find("title").text if it.find("title") is not None else ""
                link = it.find("link").text if it.find("link") is not None else ""
                pub_date = it.find("pubDate").text if it.find("pubDate") is not None else ""
                if title:
                    results.append({
                        "title": title.strip(),
                        "link": link.strip(),
                        "date": pub_date.strip()
                    })
    except Exception as e:
        print(f"⚠️ 網路搜尋錯誤: {e}")
    return results

def query_local_ollama(prompt: str, model: str = LOCAL_MODEL) -> str:
    """呼叫本機 Ollama 模型進行推論"""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }
        res = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        if res.status_code == 200:
            return res.json().get("response", "").strip()
        else:
            return f"本機 Ollama 回應錯誤 (HTTP {res.status_code})"
    except Exception as e:
        return f"連線至本地 Ollama 失敗: {e}"

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "Local LLM Web Search Server",
        "model": LOCAL_MODEL
    }), 200

@app.route("/search", methods=["POST"])
def search_and_answer():
    """
    接收 GAS 傳過來的查詢請求：
    JSON: { "query": "使用者要查的內容" }
    """
    data = request.get_json(force=True, silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"reply": "請提供要查詢的關鍵字。"}), 400

    print(f"\n🔍 [收到查詢請求]: {query}")

    # 1. 本地聯網搜尋
    search_items = search_web(query, max_results=4)

    # 2. 組合提示詞
    if search_items:
        context_str = "\n".join([
            f"- 標題：{item['title']}\n  連結：{item['link']}"
            for item in search_items
        ])
        prompt = (
            f"你是一個客觀、誠實且專業的繁體中文智慧助理。\n"
            f"以下是聯網檢索到的最新參考資料：\n{context_str}\n\n"
            f"請根據上述資料與你的客觀知識，針對問題：「{query}」進行條理分明、繁體中文的解答。\n"
            f"要求：\n"
            f"1. 回答要簡明扼要、切中重點。\n"
            f"2. 務必客觀真實，切勿瞎編。"
        )
    else:
        prompt = (
            f"你是一個客觀、誠實且專業的繁體中文智慧助理。\n"
            f"請針對問題：「{query}」以繁體中文條理分明地進行解答。\n"
            f"若該問題涉及未知資訊請客觀說明。"
        )

    print(f"🤖 正在使用本地模型 ({LOCAL_MODEL}) 生成解答...")
    answer = query_local_ollama(prompt, model=LOCAL_MODEL)

    # 3. 附上參考來源
    if search_items:
        sources_text = "\n\n📚 【參考來源】：\n" + "\n".join([
            f"{idx+1}. {item['title']}\n🔗 {item['link']}"
            for idx, item in enumerate(search_items)
        ])
        final_reply = answer + sources_text
    else:
        final_reply = answer

    print(f"✅ 生成完成，準備回傳給 GAS！")
    return jsonify({
        "reply": final_reply,
        "query": query,
        "model": LOCAL_MODEL
    }), 200

if __name__ == "__main__":
    port = 5001
    print("=" * 60)
    print("   [Local Search Server] 本地模型聯網搜尋伺服器啟動中...")
    print(f"   監聽網址: http://127.0.0.1:{port}")
    print(f"   本地模型: {LOCAL_MODEL}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
