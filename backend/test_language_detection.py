"""
SAMVAD AI — Language Detection Unit & Integration Test Suite
Step 6.5 Verification

Tests:
1. English text detection
2. Hindi Devanagari text detection
3. Marathi Devanagari text detection
4. Hinglish / Romanized Hindi detection
5. Mixed-language text & script handling
6. Empty text handling
7. Symbols and numbers handling
8. Ambiguous/short text handling
9. Low-confidence handling (no guessing)
10. HTTP Endpoint POST /ai/detect-language
11. Regression: POST /analyze (SVI calculation unchanged)
12. Regression: POST /cases & GET /cases (SQLite persistence unchanged)
13. Regression: POST /ai/understand (IndicBERT layer unchanged)
14. Regression: GET /ai/transcribe (Bhashini status unchanged)
"""

import json
import os
import sys
import unittest
from urllib.error import HTTPError
import urllib.request

from fastapi.testclient import TestClient

# Ensure backend directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from language_detection import detect_language, language_detector
from main import app


class TestLanguageDetectionUnit(unittest.TestCase):
    """Unit tests for language detection service logic."""

    def test_english_detection(self):
        text = "I am feeling very worried about my situation and I need immediate support."
        res = detect_language(text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["language_code"], "en")
        self.assertEqual(res["language_name"], "English")
        self.assertGreaterEqual(res["confidence"], 0.70)

    def test_hindi_devanagari_detection(self):
        text = "मुझे अपनी शिकायत की प्रक्रिया के बारे में जानकारी चाहिए और मदद चाहिए।"
        res = detect_language(text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["language_code"], "hi")
        self.assertEqual(res["language_name"], "Hindi")
        self.assertGreaterEqual(res["confidence"], 0.75)

    def test_marathi_devanagari_detection(self):
        text = "मला माझ्या तक्रार प्रक्रियेबद्दल माहिती हवी आहे आणि त्वरित मदत पाहिजे."
        res = detect_language(text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["language_code"], "mr")
        self.assertEqual(res["language_name"], "Marathi")
        self.assertGreaterEqual(res["confidence"], 0.75)

    def test_hinglish_detection(self):
        text = "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon."
        res = detect_language(text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["language_code"], "hi")
        self.assertEqual(res["language_name"], "Hindi")
        self.assertIn("hinglish", res["detection_method"].lower())

    def test_romanized_marathi_detection(self):
        text = "Mala support pahije please mala khup bhiti vatat ahe"
        res = detect_language(text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["language_code"], "mr")
        self.assertEqual(res["language_name"], "Marathi")

    def test_mixed_language_scripts(self):
        text = "This is completely mixed मुझे समझ नहीं आ रहा I need help"
        res = detect_language(text)
        # Should detect as mixed or return structured representation
        self.assertIn(res["status"], ["success", "mixed", "unknown"])
        self.assertIn(res["language_code"], ["mixed", "hi", "en"])

    def test_empty_and_whitespace_text(self):
        for empty_val in ["", "   ", "\n\t  \n"]:
            res = detect_language(empty_val)
            self.assertEqual(res["status"], "unknown")
            self.assertEqual(res["language_code"], "unknown")
            self.assertEqual(res["confidence"], 0.0)

    def test_symbols_and_numbers_only(self):
        for sym_val in ["12345 67890", "!@#$%^&*()", "123 !@# 456"]:
            res = detect_language(sym_val)
            self.assertEqual(res["status"], "unknown")
            self.assertEqual(res["language_code"], "unknown")
            self.assertEqual(res["confidence"], 0.0)

    def test_ambiguous_short_text(self):
        # 2-character ambiguous input
        res = detect_language("ok")
        # Should either resolve or safely provide low/moderate confidence
        self.assertIn(res["status"], ["success", "unknown"])
        if res["status"] == "unknown":
            self.assertEqual(res["language_code"], "unknown")

    def test_never_guess_arbitrary_language_on_noise(self):
        noise = "??? ... --- === +++ 999"
        res = detect_language(noise)
        self.assertEqual(res["status"], "unknown")
        self.assertEqual(res["language_code"], "unknown")


class TestLanguageDetectionApiIntegration(unittest.TestCase):
    """Integration tests via FastAPI TestClient."""

    def setUp(self):
        self.client = TestClient(app)

    def test_endpoint_detect_language_english(self):
        resp = self.client.post(
            "/ai/detect-language",
            json={"text": "I need immediate assistance with water supply."},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["language_code"], "en")
        self.assertEqual(data["language_name"], "English")
        self.assertIn("confidence", data)
        self.assertIn("detection_method", data)

    def test_endpoint_detect_language_hindi(self):
        resp = self.client.post(
            "/ai/detect-language",
            json={"text": "मुझे पानी की समस्या के लिए तुरंत मदद चाहिए।"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["language_code"], "hi")
        self.assertEqual(data["language_name"], "Hindi")

    def test_endpoint_detect_language_marathi(self):
        resp = self.client.post(
            "/ai/detect-language",
            json={"text": "मला त्वरित मदतीची गरज आहे आणि खूप भीती वाटत आहे."},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["language_code"], "mr")
        self.assertEqual(data["language_name"], "Marathi")

    def test_endpoint_detect_language_symbols_unknown(self):
        resp = self.client.post(
            "/ai/detect-language",
            json={"text": "12345 !@#$%"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "unknown")
        self.assertEqual(data["language_code"], "unknown")
        self.assertEqual(data["language_name"], "Unknown / Mixed")

    def test_regression_analyze_endpoint(self):
        """Verify SVI scoring remains identical and fully functional."""
        resp = self.client.post(
            "/analyze",
            json={
                "statement": "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.",
                "language": "hindi",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("svi", data)
        self.assertIn("risk_level", data)
        self.assertIn("components", data)
        self.assertEqual(data["svi"], 10)
        self.assertEqual(data["risk_level"], "LOW")

    def test_regression_cases_endpoint(self):
        """Verify SQLite persistence for cases remains fully functional."""
        case_payload = {
            "statement": "Test automatic multilingual case statement",
            "language": "Hindi",
            "interaction_type": "Chat",
            "consent": True,
        }
        post_resp = self.client.post("/cases", json=case_payload)
        self.assertEqual(post_resp.status_code, 200)
        created = post_resp.json()
        self.assertIn("case_id", created)

        get_resp = self.client.get("/cases")
        self.assertEqual(get_resp.status_code, 200)
        cases = get_resp.json()
        self.assertGreater(len(cases), 0)

    def test_regression_ai_understand_endpoint(self):
        """Verify IndicBERT /ai/understand endpoint remains intact."""
        resp = self.client.post(
            "/ai/understand",
            json={"text": "मुझे मदद चाहिए", "language": "Hindi"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["model_status"], "loaded")
        self.assertEqual(data["embedding_dim"], 768)

    def test_regression_ai_transcribe_status(self):
        """Verify Bhashini /ai/transcribe status endpoint remains intact."""
        resp = self.client.get("/ai/transcribe")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["provider"], "Bhashini")
        self.assertEqual(data["status"], "not_configured")


if __name__ == "__main__":
    unittest.main(verbosity=2)
