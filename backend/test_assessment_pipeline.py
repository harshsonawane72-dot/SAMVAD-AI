"""
SAMVAD AI — Step 8: Full End-to-End Assessment Pipeline Test Suite
Verifies:
1. Normal information complaint
2. Moderate distress complaint
3. High distress complaint
4. Safety concern
5. Critical safety crisis
6. Hindi Devanagari complaint
7. Marathi Devanagari complaint
8. Hinglish complaint
9. Romanized Marathi complaint
10. Mixed-language complaint
11. Semantic paraphrase
12. Irrelevant / RAG no-result case

For each case, validates:
- Language detection
- Risk classification
- SVI components & score
- Safety & human review flags
- RAG support resources retrieval
- Complete structured response schema
"""

import json
import os
from pathlib import Path
import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from assessment_pipeline import assess_complaint
from rag_service import rag_service
from main import app
from fastapi.testclient import TestClient

TEST_CASES = [
    {
        "id": "TC-01",
        "name": "Normal information inquiry",
        "text": "I want to know the status of my complaint and how to submit additional documents.",
        "language": None,
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_rag_category": "complaint_process",
    },
    {
        "id": "TC-02",
        "name": "Moderate distress complaint",
        "text": "I’ve been feeling overwhelmed for the past few days and I don’t know how to deal with this situation.",
        "language": None,
        "expected_risk": "MODERATE",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_rag_category": "support_pathways",
    },
    {
        "id": "TC-03",
        "name": "High distress / vulnerability",
        "text": "I am feeling extreme fear and pressure. I have no one to support me, I cannot handle this situation alone and I need urgent help.",
        "language": None,
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "expected_concern": False,
        "expected_rag_category": "counselling_resources",
    },
    {
        "id": "TC-04",
        "name": "Contextual safety concern",
        "text": "I don't feel safe right now and I am worried about what will happen next.",
        "language": None,
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "expected_concern": True,
        "expected_rag_category": "safety_crisis_protocol",
    },
    {
        "id": "TC-05",
        "name": "Critical acute safety threat",
        "text": "I do not feel safe right now. I need immediate help. I cannot stay safe and I am alone.",
        "language": "english",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "expected_concern": True,
        "expected_rag_category": "safety_crisis_protocol",
    },
    {
        "id": "TC-06",
        "name": "Hindi complaint",
        "text": "मुझे अपनी शिकायत की स्थिति जाननी है और प्रक्रिया की जानकारी चाहिए।",
        "language": None,
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_lang_code": "hi",
    },
    {
        "id": "TC-07",
        "name": "Marathi complaint",
        "text": "मला खूप ताण येत आहे आणि मला कोणाशी तरी बोलायचे आहे. कृपया मदत करा.",
        "language": None,
        "expected_risk": "MODERATE",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_lang_code": "mr",
    },
    {
        "id": "TC-08",
        "name": "Hinglish complaint",
        "text": "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.",
        "language": None,
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_lang_code": "hi",
    },
    {
        "id": "TC-09",
        "name": "Romanized Marathi complaint",
        "text": "Mala support pahije please mala khup tension yetoy ani kay karu samjat nahi.",
        "language": None,
        "expected_risk": "MODERATE",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_lang_code": "mr",
    },
    {
        "id": "TC-10",
        "name": "Mixed-language complaint",
        "text": "I am feeling worried mujhe process ke baare mein information chahiye but I feel safe now.",
        "language": None,
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_concern": False,
    },
    {
        "id": "TC-11",
        "name": "Semantic paraphrase of procedural help",
        "text": "I don't know how to move forward with my complaint, can someone explain the next steps?",
        "language": "english",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_rag_category": "complaint_process",
    },
    {
        "id": "TC-12",
        "name": "Irrelevant / Out-of-domain query (RAG zero-hallucination check)",
        "text": "What is the capital city of France and how is the weather today?",
        "language": "english",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_concern": False,
        "expected_rag_count": 0,
    },
]


class TestAssessmentPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_pipeline_core_cases(self):
        print("=" * 80)
        print("SAMVAD AI — Step 8 Full End-to-End Pipeline Verification")
        print("=" * 80)

        for tc in TEST_CASES:
            tc_id = tc["id"]
            name = tc["name"]
            text = tc["text"]
            lang = tc.get("language")

            print(f"\n[{tc_id}] {name}")
            print(f"       Input: \"{text[:65]}...\"")

            res = assess_complaint(
                text=text,
                language=lang,
                case_id=f"TEST-{tc_id}",
                save_to_db=True,
            )

            # 1. Structure assertions
            self.assertIn("case_id", res)
            self.assertIn("language", res)
            self.assertIn("risk_classification", res)
            self.assertIn("svi", res)
            self.assertIn("safety", res)
            self.assertIn("indicators", res)
            self.assertIn("support_resources", res)
            self.assertIn("recommendation", res)

            # 2. Risk level assertions
            expected_risk = tc.get("expected_risk")
            if expected_risk:
                self.assertEqual(
                    res["svi"]["risk_level"],
                    expected_risk,
                    f"Risk mismatch for {tc_id}: got {res['svi']['risk_level']}, expected {expected_risk}",
                )

            # 3. Safety & Human Review assertions
            expected_hr = tc.get("expected_human_review")
            if expected_hr is not None:
                self.assertEqual(
                    res["safety"]["human_review"],
                    expected_hr,
                    f"Human review mismatch for {tc_id}: got {res['safety']['human_review']}, expected {expected_hr}",
                )

            expected_concern = tc.get("expected_concern")
            if expected_concern is not None:
                self.assertEqual(
                    res["safety"]["concern_detected"],
                    expected_concern,
                    f"Safety concern mismatch for {tc_id}: got {res['safety']['concern_detected']}, expected {expected_concern}",
                )

            # 4. Language code assertions
            expected_lang = tc.get("expected_lang_code")
            if expected_lang:
                self.assertEqual(
                    res["language"]["code"],
                    expected_lang,
                    f"Language code mismatch for {tc_id}: got {res['language']['code']}, expected {expected_lang}",
                )

            # 5. RAG retrieval assertions
            if "expected_rag_count" in tc:
                self.assertEqual(len(res["support_resources"]), tc["expected_rag_count"])
            elif "expected_rag_category" in tc:
                categories = [r["category"] for r in res["support_resources"]]
                self.assertIn(
                    tc["expected_rag_category"],
                    categories,
                    f"Expected RAG category '{tc['expected_rag_category']}' in retrieved resources: {categories}",
                )

            print(f"       PASS: Lang={res['language']['name']} ({res['language']['code']}) | "
                  f"Risk={res['svi']['risk_level']} | SVI={res['svi']['score']} | "
                  f"HumanReview={res['safety']['human_review']} | "
                  f"Resources Retrieved={len(res['support_resources'])}")

    def test_http_endpoint_assess(self):
        print("\n" + "=" * 80)
        print("Testing POST /ai/assess API Endpoint via TestClient")
        print("=" * 80)

        payload = {
            "text": "I am feeling very overwhelmed and need support with my complaint process.",
            "language": None,
        }
        resp = self.client.post("/ai/assess", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("case_id", data)
        self.assertIn("svi", data)
        self.assertIn("risk_classification", data)
        self.assertIn("support_resources", data)
        self.assertGreater(len(data["support_resources"]), 0)
        print("PASS: POST /ai/assess returned valid structured assessment.")

    def test_http_endpoint_retrieve_support(self):
        print("\nTesting POST /ai/retrieve-support API Endpoint...")
        payload = {"text": "How do I check the status of my complaint?", "language": "english"}
        resp = self.client.post("/ai/retrieve-support", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["count"], 0)
        print("PASS: POST /ai/retrieve-support returned grounded resources.")

    def test_http_endpoint_classify_risk(self):
        print("\nTesting POST /ai/classify-risk API Endpoint...")
        payload = {"text": "I don't feel safe right now.", "language": "english"}
        resp = self.client.post("/ai/classify-risk", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["risk_level"], ("HIGH", "CRITICAL"))
        self.assertTrue(data["human_review"])
        print("PASS: POST /ai/classify-risk classified risk and preserved human_review.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
