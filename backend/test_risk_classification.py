"""
SAMVAD AI — Step 9: Risk Classification Test Suite
Comprehensive testing of the IndicBERT Neural Risk Classifier:
1. LOW information request
2. MODERATE sustained distress
3. HIGH serious distress
4. CRITICAL safety concern
5. Hindi input
6. Marathi input
7. Hinglish input
8. Romanized Marathi input
9. Mixed-language input
10. Natural paraphrases
11. Safety override (human_review == True)
12. Empty input validation
13. Unsupported input / symbols
14. Checkpoint load verification (trained == True)
"""

import json
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from main import app
from risk_classifier import risk_classifier_service

BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT_PATH = BASE_DIR / "models" / "risk_classifier_head.pt"
METADATA_PATH = BASE_DIR / "models" / "risk_classifier_metadata.json"
EVAL_PATH = BASE_DIR / "models" / "risk_classifier_evaluation.json"


class TestRiskClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Ensure service initializes and loads checkpoint
        risk_classifier_service._ensure_model()

    def test_01_checkpoint_loaded_and_trained(self):
        """14. Checkpoint verification: trained == True and metadata exists."""
        self.assertTrue(CHECKPOINT_PATH.exists(), f"Checkpoint file missing at {CHECKPOINT_PATH}")
        self.assertTrue(METADATA_PATH.exists(), f"Metadata file missing at {METADATA_PATH}")
        self.assertTrue(EVAL_PATH.exists(), f"Evaluation results file missing at {EVAL_PATH}")

        # Check metadata contents
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["model_name"], "ai4bharat/IndicBERTv2-MLM-only + MLP Head")
        self.assertGreaterEqual(meta["dataset_size"], 240)
        self.assertIn("accuracy", meta["test_metrics"])
        self.assertIn("macro_f1", meta["test_metrics"])

        # Check service status
        res = risk_classifier_service.classify("I want to know the status of my complaint.")
        self.assertTrue(res["trained"], "risk_classifier_service must report trained == True")
        self.assertIn("ai4bharat/IndicBERTv2-MLM-only", res["model"])

    def test_02_low_information_request(self):
        """1. LOW information request."""
        stmt = "I want to check the status of my grievance and find out the next procedural step."
        res = risk_classifier_service.classify(stmt, "english")
        self.assertEqual(res["risk_level"], "LOW")
        self.assertFalse(res["human_review"])
        self.assertGreater(res["probabilities"]["LOW"], 0.5)

    def test_03_moderate_sustained_distress(self):
        """2. MODERATE sustained distress / overwhelmed."""
        stmt = "I’ve been feeling overwhelmed for the past few days and I don’t know how to deal with this situation."
        res = risk_classifier_service.classify(stmt, "english")
        self.assertEqual(res["risk_level"], "MODERATE")
        self.assertGreater(res["probabilities"]["MODERATE"], 0.4)

    def test_04_high_serious_distress(self):
        """3. HIGH serious distress / acute vulnerability."""
        stmt = "I am feeling extreme fear and pressure. I have no one to support me and I cannot cope with this."
        res = risk_classifier_service.classify(stmt, "english")
        self.assertEqual(res["risk_level"], "HIGH")
        self.assertTrue(res["human_review"])

    def test_05_critical_safety_concern(self):
        """4. CRITICAL safety concern / acute emergency."""
        stmt = "I do not feel safe right now. I need immediate help. I cannot stay safe and I am alone."
        res = risk_classifier_service.classify(stmt, "english")
        self.assertEqual(res["risk_level"], "CRITICAL")
        self.assertTrue(res["human_review"])

    def test_06_hindi_complaint(self):
        """5. Hindi complaint classification."""
        stmt = "मुझे अपनी शिकायत की वर्तमान स्थिति जाननी है।"
        res = risk_classifier_service.classify(stmt, "hindi")
        self.assertEqual(res["risk_level"], "LOW")
        self.assertFalse(res["human_review"])

    def test_07_marathi_complaint(self):
        """6. Marathi complaint classification."""
        stmt = "मला खूप ताण येत आहे आणि मला कोणाशी तरी बोलायचे आहे. कृपया मदत करा."
        res = risk_classifier_service.classify(stmt, "marathi")
        self.assertEqual(res["risk_level"], "MODERATE")

    def test_08_hinglish_complaint(self):
        """7. Hinglish complaint classification."""
        stmt = "Mujhe apni complaint ke process ke baare mein information chahiye."
        res = risk_classifier_service.classify(stmt, "hindi")
        self.assertEqual(res["risk_level"], "LOW")

    def test_09_romanized_marathi_complaint(self):
        """8. Romanized Marathi complaint classification."""
        stmt = "Mala support pahije please mala khup tension yetoy ani kay karu samjat nahiye."
        res = risk_classifier_service.classify(stmt, "marathi")
        self.assertEqual(res["risk_level"], "MODERATE")

    def test_10_mixed_language_complaint(self):
        """9. Mixed-language complaint classification."""
        stmt = "I am feeling worried mujhe process ke baare mein information chahiye, bohot tension ho rahi hai."
        res = risk_classifier_service.classify(stmt, "hindi")
        self.assertIn(res["risk_level"], ("LOW", "MODERATE"))

    def test_11_natural_paraphrases(self):
        """10. Unseen natural paraphrases generalization."""
        # Unseen LOW paraphrase
        low_para = "Could you kindly guide me through the stages of tracking my grievance status online?"
        low_res = risk_classifier_service.classify(low_para, "english")
        self.assertEqual(low_res["risk_level"], "LOW")

        # Unseen CRITICAL paraphrase
        crit_para = "I do not feel safe in my own dwelling right now, please send emergency intervention immediately."
        crit_res = risk_classifier_service.classify(crit_para, "english")
        self.assertEqual(crit_res["risk_level"], "CRITICAL")
        self.assertTrue(crit_res["human_review"])

    def test_12_safety_override(self):
        """11. Safety override: Contextual safety cues must mandate human_review == True."""
        stmt = "I don't feel safe right now."
        res = risk_classifier_service.classify(stmt, "english")
        # Personal safety inability/fear must floor at HIGH or CRITICAL and demand human_review
        self.assertIn(res["risk_level"], ("HIGH", "CRITICAL"))
        self.assertTrue(res["human_review"], "Safety cues MUST require human_review == True")

    def test_13_empty_input_validation(self):
        """12. Empty input must raise error in service and return HTTP 400 in API."""
        with self.assertRaises(ValueError):
            risk_classifier_service.classify("   ")

        resp = self.client.post("/ai/classify-risk", json={"statement": "   "})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Text must not be empty", resp.json()["detail"])

    def test_14_unsupported_input_noise(self):
        """13. Unsupported input or noise should not crash and should return valid structure."""
        stmt = "12345 !@#$%^ &*()_+"
        res = risk_classifier_service.classify(stmt, "english")
        self.assertIn("risk_level", res)
        self.assertIn("probabilities", res)
        self.assertIn(res["risk_level"], ("LOW", "MODERATE", "HIGH", "CRITICAL"))

    def test_15_api_classify_risk_contract(self):
        """Step 11 API contract verification for POST /ai/classify-risk."""
        resp = self.client.post(
            "/ai/classify-risk",
            json={"statement": "I need help with my complaint status."},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("risk_level", body)
        self.assertIn("confidence", body)
        self.assertIn("probabilities", body)
        self.assertIn("LOW", body["probabilities"])
        self.assertIn("MODERATE", body["probabilities"])
        self.assertIn("HIGH", body["probabilities"])
        self.assertIn("CRITICAL", body["probabilities"])
        self.assertTrue(body["trained"])
        self.assertIn("ai4bharat/IndicBERTv2-MLM-only", body["model"])


if __name__ == "__main__":
    unittest.main()
