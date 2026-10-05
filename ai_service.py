import os
import requests
from typing import Optional
from dotenv import load_dotenv

# 自動載入 .env 設定
load_dotenv()

class GeminiService:
    """負責與 Google Gemini API 進行通訊的服務類別"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash"):
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.fallback_models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
        self.system_instruction = (
            "你是一個友善、熱心、幽默且知識淵博的 LINE 智慧助理。"
            "請一律使用台灣習慣的繁體中文回應使用者的問題，回答內容需條理分明、簡明扼要、易於在手機螢幕上閱讀。"
        )
        self._init_client()

    def _init_client(self):
        """初始化 Gemini SDK 客戶端，若尚未安裝套件則標記為使用 REST API 模式"""
        self.client = None
        self.mode = "rest"
        if not self.api_key:
            return

        try:
            # 優先嘗試最新官方 google-genai SDK
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.mode = "google_genai"
        except ImportError:
            try:
                # 次之嘗試舊版 google-generativeai SDK
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=self.system_instruction
                )
                self.mode = "legacy_genai"
            except ImportError:
                # 若皆無，直接使用 requests REST API
                self.mode = "rest"

    def generate_response(self, user_prompt: str) -> str:
        """
        傳入使用者輸入的 prompt，向 Gemini AI 獲取回答文字
        """
        if not self.api_key or self.api_key.startswith("your_"):
            return "⚠️ 尚未設定有效的 GEMINI_API_KEY！請在 .env 檔案中填入由 Google AI Studio 免費申請的 API Key。"

        if not user_prompt.strip():
            return "請問有什麼我可以協助您的呢？歡迎隨時提問！"

        try:
            if self.mode == "google_genai":
                from google.genai import types
                
                # 嘗試主要模型與備用模型
                models_to_try = [self.model_name] + [m for m in self.fallback_models if m != self.model_name]
                last_error = None

                for model in models_to_try:
                    try:
                        response = self.client.models.generate_content(
                            model=model,
                            contents=user_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=self.system_instruction,
                                temperature=0.7,
                            ),
                        )
                        if response and response.text:
                            return response.text.strip()
                    except Exception as err:
                        last_error = err
                        print(f"[GeminiService] 模型 {model} 呼叫失敗: {err}，嘗試備用模型...")
                        continue

                raise last_error or RuntimeError("所有可用 Gemini 模型皆無回應")

            elif self.mode == "legacy_genai":
                response = self.client.generate_content(user_prompt)
                if response and response.text:
                    return response.text.strip()

            else:
                # REST API 備用模式
                return self._call_rest_api(user_prompt)

            return "抱歉，目前暫時無法取得 AI 回覆，請稍後再試。"

        except Exception as e:
            print(f"[GeminiService] 處理錯誤: {e}")
            return f"❌ 處理您的問題時發生錯誤：{str(e)[:100]}... 請稍後重試。"

    def _call_rest_api(self, prompt: str) -> str:
        """直接透過 Google Gemini REST API 進行呼叫"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": self.system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000
            }
        }
        res = requests.post(url, json=payload, timeout=30)
        res_data = res.json()

        if res.status_code == 200:
            candidates = res_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return "無法解析 AI 回覆內容。"
        else:
            err_msg = res_data.get("error", {}).get("message", res.text)
            raise RuntimeError(f"Google API HTTP {res.status_code}: {err_msg}")
