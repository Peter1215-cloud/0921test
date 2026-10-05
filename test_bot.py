"""
單元測試腳本：驗證服務邏輯與端點是否能正確運作
"""
import unittest
from ai_service import GeminiService
from app import app


class TestLineBotGemini(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_gemini_service_without_key(self):
        """測試未設定 API Key 時的防呆機制"""
        service = GeminiService(api_key="")
        response = service.generate_response("你好")
        self.assertIn("尚未設定", response)

    def test_gemini_service_dummy_key(self):
        """測試預設範例 Key 時的防呆機制"""
        service = GeminiService(api_key="your_gemini_api_key_here")
        response = service.generate_response("你好")
        self.assertIn("尚未設定", response)

    def test_gemini_service_empty_prompt(self):
        """測試傳入空字串時的提示"""
        service = GeminiService(api_key="AIzaSyDummyKeyForTestingOnly12345678")
        response = service.generate_response("   ")
        self.assertIn("請問有什麼我可以協助您的呢", response)

    def test_health_check_endpoint(self):
        """測試 GET / 首頁狀態檢查端點"""
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LINE Bot x Gemini AI", response.data)
        self.assertIn(b"Server is Online", response.data)

    def test_callback_without_signature(self):
        """測試 POST /callback 在沒有簽章或金鑰時回傳適當代碼"""
        response = self.app.post("/callback", data="{}")
        # 若未設定 SDK 則回傳 500，或若有 SDK 但未給簽章則回傳 400
        self.assertIn(response.status_code, [400, 500])


if __name__ == "__main__":
    unittest.main()
