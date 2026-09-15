"""
SAMVAD AI — Step 5D: Bhashini Speech-to-Text Integration Tests
Validates Bhashini adapter, POST /ai/transcribe endpoint, language mapping,
configuration handling, and ensures zero regression on existing endpoints.
"""

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient

try:
    from backend.main import app
    from backend.bhashini_service import BhashiniService, bhashini_service
except ImportError:
    from main import app
    from bhashini_service import BhashiniService, bhashini_service


class TestBhashiniIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Dummy 1-second silent WAV header for valid audio testing
        self.dummy_wav = (
            b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
            b"\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        )

    def test_01_language_normalization(self):
        """Test language mapping for English, Hindi, Marathi and invalid inputs."""
        svc = BhashiniService()
        self.assertEqual(svc.normalize_language("en"), "en")
        self.assertEqual(svc.normalize_language("English"), "en")
        self.assertEqual(svc.normalize_language("ENGLISH"), "en")
        self.assertEqual(svc.normalize_language("hi"), "hi")
        self.assertEqual(svc.normalize_language("Hindi"), "hi")
        self.assertEqual(svc.normalize_language("mr"), "mr")
        self.assertEqual(svc.normalize_language("Marathi"), "mr")

        with self.assertRaises(ValueError):
            svc.normalize_language("french")
        with self.assertRaises(ValueError):
            svc.normalize_language("de")
        with self.assertRaises(ValueError):
            svc.normalize_language("")

    def test_02_audio_validation(self):
        """Test audio validation and format detection."""
        svc = BhashiniService()
        # Valid formats
        self.assertEqual(svc.validate_audio("test.wav", "audio/wav", self.dummy_wav), "wav")
        self.assertEqual(svc.validate_audio("test.mp3", "audio/mpeg", b"fake-mp3-bytes"), "mp3")
        self.assertEqual(svc.validate_audio("test.webm", "audio/webm", b"fake-webm-bytes"), "webm")
        self.assertEqual(svc.validate_audio("recording", "video/webm", b"fake-webm-bytes"), "webm")

        # Empty audio bytes
        with self.assertRaises(ValueError):
            svc.validate_audio("test.wav", "audio/wav", b"")

        # Invalid extensions
        with self.assertRaises(ValueError):
            svc.validate_audio("document.txt", "text/plain", b"Hello world")
        with self.assertRaises(ValueError):
            svc.validate_audio("script.py", "text/x-python", b"print(1)")

    def test_03_unsupported_language_endpoint(self):
        """POST /ai/transcribe should return 400 Bad Request for unsupported language."""
        files = {"file": ("test.wav", io.BytesIO(self.dummy_wav), "audio/wav")}
        data = {"language": "french"}
        res = self.client.post("/ai/transcribe", files=files, data=data)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unsupported language", res.json()["detail"])

    def test_04_empty_audio_file_endpoint(self):
        """POST /ai/transcribe should return 400 Bad Request for empty audio."""
        files = {"file": ("test.wav", io.BytesIO(b""), "audio/wav")}
        data = {"language": "hi"}
        res = self.client.post("/ai/transcribe", files=files, data=data)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Audio file must not be empty", res.json()["detail"])

    def test_05_invalid_audio_type_endpoint(self):
        """POST /ai/transcribe should return 400 Bad Request for non-audio file."""
        files = {"file": ("notes.txt", io.BytesIO(b"Some text"), "text/plain")}
        data = {"language": "hi"}
        res = self.client.post("/ai/transcribe", files=files, data=data)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid audio format", res.json()["detail"])

    def test_06_unconfigured_bhashini_endpoint(self):
        """POST /ai/transcribe when unconfigured should return HTTP 503 with not_configured."""
        # Ensure environment has no keys
        with patch.dict(os.environ, {}, clear=True):
            # Create fresh instance without keys
            with patch.object(bhashini_service, "is_configured", return_value=False):
                files = {"file": ("test.wav", io.BytesIO(self.dummy_wav), "audio/wav")}
                data = {"language": "hi"}
                res = self.client.post("/ai/transcribe", files=files, data=data)
                self.assertEqual(res.status_code, 503)
                body = res.json()
                self.assertEqual(body.get("status"), "not_configured")
                self.assertEqual(body.get("provider"), "Bhashini")
                self.assertEqual(body.get("message"), "Bhashini credentials are not configured.")
                self.assertEqual(body.get("supported_languages"), ["en", "hi", "mr"])
                self.assertIn("accuracy depends on audio quality", body.get("disclaimer", ""))

    def test_07_service_response_structure_when_configured(self):
        """Test Bhashini service when configured and mock API returns a valid transcript."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pipelineResponse": [
                {
                    "taskType": "asr",
                    "output": [
                        {
                            "source": "मला त्वरित मदत हवी आहे"
                        }
                    ]
                }
            ]
        }

        # Mock configured environment and httpx.Client post
        with patch.dict(os.environ, {"BHASHINI_API_KEY": "dummy_test_key_12345", "BHASHINI_USER_ID": "dummy_user"}):
            test_svc = BhashiniService()
            self.assertTrue(test_svc.is_configured())

            with patch("httpx.Client.post", return_value=mock_response):
                result = test_svc.transcribe(
                    audio_bytes=self.dummy_wav,
                    language="Marathi",
                    filename="sample.wav",
                    content_type="audio/wav",
                )

                self.assertEqual(result["status"], "success")
                self.assertEqual(result["provider"], "Bhashini")
                self.assertEqual(result["language"], "mr")
                self.assertEqual(result["transcript"], "मला त्वरित मदत हवी आहे")
                self.assertIn("accuracy depends on audio quality", result["disclaimer"])
                # Ensure credentials were not leaked
                self.assertNotIn("dummy_test_key_12345", str(result))

    def test_08_existing_endpoint_regression(self):
        """Ensure GET /health, POST /ai/understand, POST /analyze, and GET /cases remain intact."""
        # 1. GET /health
        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "healthy")

        # 2. POST /analyze (SVI Engine unchanged)
        res_analyze = self.client.post(
            "/analyze",
            json={"statement": "I feel severe pain and danger", "language": "english"},
        )
        self.assertEqual(res_analyze.status_code, 200)
        data = res_analyze.json()
        self.assertIn("svi", data)
        self.assertIn("risk_tier", data)
        self.assertIn("semantic_analysis", data)

        # 3. POST /ai/understand (IndicBERT layer unchanged)
        res_ai = self.client.post(
            "/ai/understand",
            json={"text": "मला तातडीची मदत हवी आहे", "language": "Marathi"},
        )
        self.assertEqual(res_ai.status_code, 200)
        self.assertEqual(res_ai.json()["language_code"], "mr")
        self.assertEqual(res_ai.json()["language"], "marathi")

        # 4. GET /cases
        res_cases = self.client.get("/cases")
        self.assertEqual(res_cases.status_code, 200)
        self.assertIsInstance(res_cases.json(), list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
