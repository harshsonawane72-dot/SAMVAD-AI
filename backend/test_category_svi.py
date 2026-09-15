"""
SAMVAD AI — Category-Guided SVI Range & Contextual Scoring Test Suite

Validates:
1. "I am worried about the complaint process." -> LOW, score 0-24
2. "Mujhe kaafi stress ho raha hai aur mujhe support chahiye." -> MODERATE, score 25-49
3. "I am in a serious emotional crisis and I urgently need to talk to someone." -> HIGH or CRITICAL (within category range)
4. "I don't feel safe right now and I need immediate help." -> safety_flag=true, human_review=true, CRITICAL escalation (75-100)
5. "Please mujhe abhi kisi human support tak connect karne mein help karo." -> support_request=true, human_review=true, risk score NOT artificially inflated
6. Multilingual coverage: English, Hindi, Hinglish, Marathi
7. Category range hard bounding and explainability wording ("Possible indicators detected")
8. Independent safety escalation preservation
"""

import sys
from pathlib import Path

# Ensure UTF-8 stdout on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from category_svi import (
    PROTOTYPE_SCORE_RANGES,
    compute_category_svi,
    detect_support_request,
)
from assessment_pipeline import assess_complaint


def test_unit_category_svi_bounding():
    print("\n--- TEST 1: Unit Category SVI Bounding & Modulation ---")

    # LOW: 0-24
    res_low_min = compute_category_svi("LOW", {"stress": 0, "vulnerability": 0, "urgency": 0, "safety": 0})
    assert res_low_min["risk_category"] == "LOW"
    assert 0 <= res_low_min["svi_score"] <= 24
    assert res_low_min["svi_score"] == 0, f"Expected 0, got {res_low_min['svi_score']}"

    res_low_max = compute_category_svi("LOW", {"stress": 100, "vulnerability": 100, "urgency": 100, "safety": 100})
    assert res_low_max["risk_category"] == "LOW"
    assert 0 <= res_low_max["svi_score"] <= 24
    assert res_low_max["svi_score"] == 24, f"Expected 24, got {res_low_max['svi_score']}"
    print("PASS: LOW range strictly bounded [0, 24]")

    # MODERATE: 25-49
    res_mod_min = compute_category_svi("MODERATE", {"stress": 0, "vulnerability": 0, "urgency": 0, "safety": 0})
    assert res_mod_min["risk_category"] == "MODERATE"
    assert 25 <= res_mod_min["svi_score"] <= 49
    assert res_mod_min["svi_score"] == 25, f"Expected 25, got {res_mod_min['svi_score']}"

    res_mod_max = compute_category_svi("MODERATE", {"stress": 100, "vulnerability": 100, "urgency": 100, "safety": 100})
    assert res_mod_max["risk_category"] == "MODERATE"
    assert 25 <= res_mod_max["svi_score"] <= 49
    assert res_mod_max["svi_score"] == 49, f"Expected 49, got {res_mod_max['svi_score']}"
    print("PASS: MODERATE range strictly bounded [25, 49]")

    # HIGH: 50-74
    res_high_min = compute_category_svi("HIGH", {"stress": 0, "vulnerability": 0, "urgency": 0, "safety": 0})
    assert res_high_min["risk_category"] == "HIGH"
    assert 50 <= res_high_min["svi_score"] <= 74
    assert res_high_min["svi_score"] == 50, f"Expected 50, got {res_high_min['svi_score']}"

    res_high_max = compute_category_svi("HIGH", {"stress": 100, "vulnerability": 100, "urgency": 100, "safety": 100})
    assert res_high_max["risk_category"] == "HIGH"
    assert 50 <= res_high_max["svi_score"] <= 74
    assert res_high_max["svi_score"] == 74, f"Expected 74, got {res_high_max['svi_score']}"
    print("PASS: HIGH range strictly bounded [50, 74]")

    # CRITICAL: 75-100
    res_crit_min = compute_category_svi("CRITICAL", {"stress": 0, "vulnerability": 0, "urgency": 0, "safety": 0})
    assert res_crit_min["risk_category"] == "CRITICAL"
    assert 75 <= res_crit_min["svi_score"] <= 100
    assert res_crit_min["svi_score"] == 75, f"Expected 75, got {res_crit_min['svi_score']}"

    res_crit_max = compute_category_svi("CRITICAL", {"stress": 100, "vulnerability": 100, "urgency": 100, "safety": 100})
    assert res_crit_max["risk_category"] == "CRITICAL"
    assert 75 <= res_crit_max["svi_score"] <= 100
    assert res_crit_max["svi_score"] == 100, f"Expected 100, got {res_crit_max['svi_score']}"
    print("PASS: CRITICAL range strictly bounded [75, 100]")


def test_support_request_isolation():
    print("\n--- TEST 2: Human Support Request Detection & Isolation ---")
    phrases = [
        "Please mujhe abhi kisi human support tak connect karne mein help karo.",
        "I want to speak with an operator directly.",
        "Connect me to human agent please.",
        "मला ऑपरेटरशी बोलायचे आहे",
    ]
    for p in phrases:
        req, reason = detect_support_request(p)
        assert req is True, f"Failed to detect support request in: '{p}'"
        assert reason is not None
        print(f"PASS: Support request detected: '{p[:40]}...' -> {reason}")

    # Verify support request alone does NOT inflate a LOW statement to HIGH/CRITICAL
    pure_support = "Please mujhe abhi kisi human support tak connect karne mein help karo."
    res = assess_complaint(pure_support, save_to_db=False)
    assert res["support_request"] is True, "support_request must be True"
    assert res["human_review"] is True, "human_review must be True for human operator handling"
    assert res["risk_category"] in ("LOW", "MODERATE"), (
        f"Support request alone must NOT inflate risk category to HIGH/CRITICAL. Got: {res['risk_category']}"
    )
    assert res["svi_score"] <= 49, f"Risk score must remain in LOW/MODERATE range. Got: {res['svi_score']}"
    assert "Possible indicators detected" in res["explanation"]
    print(f"PASS: Isolated support request: Category={res['risk_category']}, Score={res['svi_score']}, HumanReview={res['human_review']}")


def test_required_scenarios():
    print("\n--- TEST 3: Required Core Scenarios ---")

    # Scenario 1: "I am worried about the complaint process." -> LOW (0-24)
    s1 = "I am worried about the complaint process."
    r1 = assess_complaint(s1, save_to_db=False)
    assert r1["risk_category"] == "LOW", f"Expected LOW, got {r1['risk_category']}"
    assert 0 <= r1["svi_score"] <= 24, f"Expected 0-24, got {r1['svi_score']}"
    assert r1["svi_range"] == {"min": 0, "max": 24}
    assert "Possible indicators detected" in r1["explanation"]
    print(f"PASS Scenario 1: '{s1}' -> {r1['risk_category']} (Score: {r1['svi_score']}) in {r1['svi_range']}")

    # Scenario 2: "Mujhe kaafi stress ho raha hai aur mujhe support chahiye." -> MODERATE (25-49)
    s2 = "Mujhe kaafi stress ho raha hai aur mujhe support chahiye."
    r2 = assess_complaint(s2, save_to_db=False)
    assert r2["risk_category"] == "MODERATE", f"Expected MODERATE, got {r2['risk_category']}"
    assert 25 <= r2["svi_score"] <= 49, f"Expected 25-49, got {r2['svi_score']}"
    assert r2["svi_range"] == {"min": 25, "max": 49}
    print(f"PASS Scenario 2: '{s2}' -> {r2['risk_category']} (Score: {r2['svi_score']}) in {r2['svi_range']}")

    # Scenario 3: "I am in a serious emotional crisis and I urgently need to talk to someone." -> HIGH or CRITICAL
    s3 = "I am in a serious emotional crisis and I urgently need to talk to someone."
    r3 = assess_complaint(s3, save_to_db=False)
    assert r3["risk_category"] in ("HIGH", "CRITICAL"), f"Expected HIGH or CRITICAL, got {r3['risk_category']}"
    cat_min = r3["svi_range"]["min"]
    cat_max = r3["svi_range"]["max"]
    assert cat_min <= r3["svi_score"] <= cat_max, f"Score {r3['svi_score']} must remain within {r3['svi_range']}"
    assert r3["human_review"] is True, "Emotional crisis must trigger human review"
    print(f"PASS Scenario 3: '{s3}' -> {r3['risk_category']} (Score: {r3['svi_score']}) in {r3['svi_range']}")

    # Scenario 4: "I don't feel safe right now and I need immediate help." -> Safety flag, human_review=true, CRITICAL escalation
    s4 = "I don't feel safe right now and I need immediate help."
    r4 = assess_complaint(s4, save_to_db=False)
    assert r4["safety_flag"] is True, "safety_flag must be True"
    assert r4["human_review"] is True, "human_review must be True"
    assert r4["risk_category"] == "CRITICAL", f"Expected CRITICAL, got {r4['risk_category']}"
    assert 75 <= r4["svi_score"] <= 100, f"Expected 75-100, got {r4['svi_score']}"
    print(f"PASS Scenario 4: '{s4}' -> SafetyFlag={r4['safety_flag']}, HumanReview={r4['human_review']}, Category={r4['risk_category']} (Score: {r4['svi_score']})")


def test_multilingual_coverage():
    print("\n--- TEST 4: Multilingual Statements (English, Hindi, Hinglish, Marathi) ---")
    cases = [
        ("English Mild", "I need information regarding the status of my complaint.", "en", "LOW", 0, 24),
        ("Hindi Moderate", "मुझे शिकायत की प्रक्रिया समझ नहीं आ रही है और तनाव महसूस हो रहा है।", "hi", "MODERATE", 25, 49),
        ("Hinglish Safety", "mujhe safe feel nahi ho raha, please immediate help karo", "hi", "CRITICAL", 75, 100),
        ("Marathi Distress", "मला त्वरित मदत हवी आहे आणि मी खूप घाबरलो आहे कोणाचाही आधार नाही", "mr", "HIGH", 50, 100),
    ]

    for label, text, lang, exp_cat, min_s, max_s in cases:
        res = assess_complaint(text, language=lang, save_to_db=False)
        score = res["svi_score"]
        cat = res["risk_category"]
        assert min_s <= score <= max_s, f"[{label}] Score {score} not in range [{min_s}, {max_s}]"
        # Check required keys
        for key in ["risk_category", "svi_score", "svi_range", "contextual_indicators", "explanation", "human_review", "human_review_reason", "safety_flag", "support_request"]:
            assert key in res, f"Missing required response key: {key}"
        print(f"PASS [{label}]: Lang={res['language']['name']}, Category={cat}, Score={score} in [{min_s}, {max_s}]")


def test_response_structure():
    print("\n--- TEST 5: Complete Response Schema Validation ---")
    res = assess_complaint("Testing complete response structure", save_to_db=False)
    expected_keys = [
        "case_id",
        "language",
        "risk_category",
        "svi_score",
        "svi_range",
        "contextual_indicators",
        "explanation",
        "human_review",
        "human_review_reason",
        "safety_flag",
        "support_request",
        "risk_classification",
        "svi",
        "tier_disagreement",
        "safety",
        "indicators",
        "support_resources",
        "recommendation",
        "disclaimer",
    ]
    for k in expected_keys:
        assert k in res, f"Missing schema key: {k}"
    assert isinstance(res["svi_range"], dict) and "min" in res["svi_range"] and "max" in res["svi_range"]
    assert isinstance(res["svi_score"], int)
    assert res["svi_range"]["min"] <= res["svi_score"] <= res["svi_range"]["max"]
    print("PASS: Response schema conforms 100% to specifications.")


if __name__ == "__main__":
    test_unit_category_svi_bounding()
    test_support_request_isolation()
    test_required_scenarios()
    test_multilingual_coverage()
    test_response_structure()
    print("\n==================================================")
    print("ALL CATEGORY-GUIDED SVI TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
