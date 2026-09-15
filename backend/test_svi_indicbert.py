"""
SAMVAD AI — Step 5C IndicBERT + SVI Auxiliary Signal Test Suite
Validates:
1. English, Hindi, and Marathi statements through POST /analyze
2. The 4 prototype tier examples (LOW, MODERATE, HIGH, CRITICAL)
3. Regression: existing SVI scores are 100% preserved
4. Auxiliary semantic_analysis structure containing category signals and disclaimer
"""

import json
import sys
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"


def query_analyze(statement: str, language: str = "english"):
    url = f"{BASE_URL}/analyze"
    payload = json.dumps({"statement": statement, "language": language}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def test_svi_regression_and_semantics():
    print("\n--- [1] Testing SVI Score Regression & Semantic Analysis ---")

    test_cases = [
        {
            "tier": "LOW",
            "statement": "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.",
            "language": "Hindi",
            "expected_svi": 10,
            "expected_risk": "LOW",
            "expected_review": False,
        },
        {
            "tier": "MODERATE",
            "statement": "Mujhe kaafi stress ho raha hai aur mujhe samajh nahi aa raha ki complaint ko kaise proceed karun. Mujhe support chahiye.",
            "language": "Hindi",
            "expected_svi": 25,
            "expected_risk": "MODERATE",
            "expected_review": False,
        },
        {
            "tier": "HIGH",
            "statement": "Mujhe bahut fear aur pressure feel ho raha hai. Mujhe lag raha hai ki main is situation ko akela handle nahi kar pa raha/rahi. Mujhe jaldi support chahiye.",
            "language": "Hindi",
            "expected_svi": 56,
            "expected_risk": "HIGH",
            "expected_review": False,
        },
        {
            "tier": "CRITICAL",
            "statement": "Mujhe abhi safe feel nahi ho raha. Mujhe immediate help chahiye aur main situation ko akela handle nahi kar sakta/sakti.",
            "language": "Hindi",
            "expected_svi": 79,
            "expected_risk": "CRITICAL",
            "expected_review": True,
        },
    ]

    for tc in test_cases:
        status, body = query_analyze(tc["statement"], tc["language"])
        assert status == 200, f"Failed for {tc['tier']}: {body}"

        # 1. Regression assertion: SVI must match prototype rule-based scores exactly
        assert body["svi"] == tc["expected_svi"], f"SVI mismatch for {tc['tier']}: got {body['svi']}, expected {tc['expected_svi']}"
        assert body["risk_level"] == tc["expected_risk"], f"Risk mismatch for {tc['tier']}: got {body['risk_level']}"
        assert body["human_review"] == tc["expected_review"], f"Human review mismatch for {tc['tier']}: got {body['human_review']}"

        # 2. Auxiliary semantic analysis assertions
        assert "semantic_analysis" in body, f"semantic_analysis missing in response for {tc['tier']}"
        sem = body["semantic_analysis"]
        assert sem["enabled"] is True, "semantic_analysis should be enabled"
        assert sem["fusion_applied"] is False, "fusion_applied must be False by default"
        assert "model" in sem
        assert "stress_signal" in sem
        assert "vulnerability_signal" in sem
        assert "urgency_signal" in sem
        assert "safety_signal" in sem
        assert "similarity" in sem["stress_signal"]
        assert "level" in sem["stress_signal"]
        assert "confidence" in sem["stress_signal"]
        assert "disclaimer" in sem

        print(f"PASS [{tc['tier']}]: SVI={body['svi']} (100% matched), Risk={body['risk_level']}")
        print(f"       IndicBERT Semantic Signals: Stress={sem['stress_signal']['similarity']} ({sem['stress_signal']['level']}), Vuln={sem['vulnerability_signal']['similarity']} ({sem['vulnerability_signal']['level']}), Urg={sem['urgency_signal']['similarity']} ({sem['urgency_signal']['level']}), Safety={sem['safety_signal']['similarity']} ({sem['safety_signal']['level']})")


def test_multilingual_coverage():
    print("\n--- [2] Testing Multilingual Coverage (English, Hindi, Marathi) ---")

    languages = [
        ("English", "I am facing severe delay and feeling very anxious and worried about my case."),
        ("Hindi", "मेरी पेंशन में बहुत देरी हो रही है और मैं बहुत परेशान और चिंतित हूँ।"),
        ("Marathi", "माझ्या तक्रारीवर काहीच कारवाई झालेली नाही, मला खूप मानसिक ताण येत आहे."),
    ]

    for lang, text in languages:
        status, body = query_analyze(text, lang)
        assert status == 200, f"Failed for {lang}: {body}"
        sem = body.get("semantic_analysis", {})
        assert sem.get("enabled") is True
        assert sem.get("language") == lang.lower()
        stress_sim = sem["stress_signal"]["similarity"]
        print(f"PASS [{lang}]: Analyzed successfully. SVI={body['svi']}, IndicBERT Stress Similarity={stress_sim} ({sem['stress_signal']['level']})")


def main():
    print("=== SAMVAD AI: Step 5C IndicBERT + SVI Auxiliary Tests ===")
    test_svi_regression_and_semantics()
    test_multilingual_coverage()
    print("\n=== ALL STEP 5C TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()
