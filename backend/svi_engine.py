"""
SAMVAD AI — Backend SVI Analysis Engine
Faithfully reproduces prototype rule-based SVI calculation from mock-ai.js.

Formula:
  SVI = stress * 0.30 + vulnerability * 0.30 + urgency * 0.25 + safety * 0.15

Thresholds:
  LOW: 0 - 24
  MODERATE: 25 - 49
  HIGH: 50 - 74
  CRITICAL: 75 - 100
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from .contextual_safety import contextual_safety_analyzer
except ImportError:
    from contextual_safety import contextual_safety_analyzer

# Prototype component weights for the SVI formula
WEIGHTS = {
    "stress": 0.30,
    "vulnerability": 0.30,
    "urgency": 0.25,
    "safetyConcern": 0.15,
}

# Prototype risk thresholds (SVI 0–100)
RISK_THRESHOLDS = [
    {"level": "LOW", "min": 0, "max": 24},
    {"level": "MODERATE", "min": 25, "max": 49},
    {"level": "HIGH", "min": 50, "max": 74},
    {"level": "CRITICAL", "min": 75, "max": 100},
]

# Explainable keyword / phrase banks matching mock-ai.js
SIGNAL_BANKS = {
    "stress": [
        "emotional crisis",
        "worried",
        "stress",
        "stressed",
        "pressure",
        "overwhelmed",
        "anxious",
        "fear",
        "scared",
        "tension",
        "परेशान",
        "तनाव",
        "डर",
        "घबराहट",
        "दबाव",
        "ताण",
        "भीती",
        "काळजी",
    ],
    "vulnerability": [
        "don't know how to deal",
        "dont know how to deal",
        "don't know what to do",
        "dont know what to do",
        "unable to handle",
        "unable to cope",
        "cannot cope",
        "struggling to cope",
        "unable to manage",
        "too much for me",
        "becoming too much",
        "no one to support",
        "alone",
        "helpless",
        "vulnerable",
        "dependent",
        "no support",
        "isolated",
        "अकेला",
        "असहाय",
        "मदद नहीं",
        "कोई साथ नहीं",
        "कमजोर",
        "आधार नाही",
        "मदत",
        "मदद",
        "मदत हवी",
        "मदत पाहिजे",
        "कोणाचाही आधार नाही",
        "एकटा",
        "एकटी",
        "असहाय्य",
        "akela",
        "akeli",
        "asahay",
        "handle nahi",
        "support chahiye",
        "samajh nahi aa raha",
        "samajh nahi aa rahi",
        "kay karu samjat nahi",
        "handle karna khup difficult",
    ],
    "urgency": [
        "immediately",
        "urgent help",
        "urgent",
        "right now",
        "quickly",
        "emergency help",
        "emergency",
        "तुरंत",
        "अभी",
        "तत्काल",
        "तात्काळ",
        "त्वरित",
        "लवकर",
        "immediate help",
        "immediate",
        "jaldi",
        "abhi",
        "pahije",
    ],
    "safety": [
        "not safe",
        "unsafe",
        "immediate danger",
        "serious threat",
        "cannot stay safe",
        "मुझे सुरक्षित महसूस नहीं हो रहा",
        "तत्काल खतरा",
        "खतरा",
        "safe feel nahi",
        "safe feel nahi ho",
    ],
}

# Phrases that always raise an independent safety review flag
STRONG_SAFETY_PHRASES = [
    "not safe",
    "unsafe",
    "immediate danger",
    "serious threat",
    "cannot stay safe",
    "मुझे सुरक्षित महसूस नहीं हो रहा",
    "तत्काल खतरा",
    "safe feel nahi",
    "safe feel nahi ho",
]

RECOMMENDATIONS = {
    "LOW": "Information and general support",
    "MODERATE": "Counselling / support referral recommended",
    "HIGH": "Priority human review and appropriate counselling/legal support referral",
    "CRITICAL": "Immediate human review and appropriate emergency/protection support pathway",
}

INDICATOR_LABELS = {
    "stress": "Elevated stress indicators",
    "vulnerability": "Vulnerability indicators",
    "urgency": "Urgency indicators",
    "safety": "Safety concern indicators",
    "fearPressure": "Fear or pressure indicators",
}

MATCH_POINTS = [0, 32, 54, 70, 82, 90, 95, 98]
FEAR_PRESSURE_REGEX = re.compile(r"fear|scared|pressure|डर|दबाव", re.IGNORECASE)


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def round_score(value: float) -> int:
    """Clamps value to 0-100 and applies JavaScript Math.round equivalent."""
    clamped = clamp(value, 0.0, 100.0)
    return int(math.floor(clamped + 0.5))


def find_matches(normalized_text: str, phrases: List[str]) -> List[str]:
    """Find unique phrase matches, longest first with soft-consumption."""
    sorted_phrases = sorted(phrases, key=lambda p: len(p), reverse=True)
    matched = []
    consumed = normalized_text

    for phrase in sorted_phrases:
        needle = phrase.lower()
        if not needle:
            continue
        if needle in consumed:
            matched.append(phrase)
            consumed = consumed.replace(needle, " ", 1)

    return matched


def score_from_match_count(count: int) -> int:
    """Convert unique match count to 0-100 component score with diminishing returns."""
    if count <= 0:
        return 0
    if count < len(MATCH_POINTS):
        return MATCH_POINTS[count]
    return 100


def apply_contextual_adjustments(
    base_scores: Dict[str, int],
    matches: Dict[str, List[str]],
    strong_safety_hit: bool,
    contextual_safety: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, int], List[str]]:
    """Apply co-occurrence bonuses, contextual safety floors, and acute safety floors."""
    adjustments = []
    stress = float(base_scores["stress"])
    vulnerability = float(base_scores["vulnerability"])
    urgency = float(base_scores["urgency"])
    safety_concern = float(base_scores["safetyConcern"])

    # 1. Co-occurrence bonuses
    if matches["stress"] and matches["vulnerability"]:
        stress += 10
        vulnerability += 10
        adjustments.append("Stress + vulnerability co-occurrence (+10 each, prototype)")

    has_safety_signal = bool(matches["safety"]) or (
        contextual_safety and contextual_safety.get("has_safety_concern")
    )
    if matches["urgency"] and has_safety_signal:
        urgency += 12
        safety_concern += 14
        adjustments.append("Urgency + safety co-occurrence (+12 urgency, +14 safety, prototype)")

    if len(matches["stress"]) >= 2:
        stress += 8
        adjustments.append("Multiple distinct stress signals (+8, prototype)")

    if len(matches["vulnerability"]) >= 2:
        vulnerability += 8
        adjustments.append("Multiple distinct vulnerability signals (+8, prototype)")

    # 2. Contextual safety floors (e.g. inability to keep safe, feeling unsafe, personal safety fear)
    if contextual_safety and contextual_safety.get("has_safety_concern"):
        rec = contextual_safety.get("component_recommendations", {})
        c_type = contextual_safety.get("concern_type", "contextual_safety")
        if "stress_floor" in rec and stress < rec["stress_floor"]:
            stress = float(rec["stress_floor"])
            adjustments.append(f"Contextual safety stress floor applied (stress ≥ {rec['stress_floor']}, {c_type})")
        if "vulnerability_floor" in rec and vulnerability < rec["vulnerability_floor"]:
            vulnerability = float(rec["vulnerability_floor"])
            adjustments.append(f"Contextual safety vulnerability floor applied (vulnerability ≥ {rec['vulnerability_floor']}, {c_type})")
        if "urgency_floor" in rec and urgency < rec["urgency_floor"]:
            urgency = float(rec["urgency_floor"])
            adjustments.append(f"Contextual safety urgency floor applied (urgency ≥ {rec['urgency_floor']}, {c_type})")
        if "safety_floor" in rec and safety_concern < rec["safety_floor"]:
            safety_concern = float(rec["safety_floor"])
            adjustments.append(f"Contextual safety concern floor applied (safety ≥ {rec['safety_floor']}, {c_type})")

    # 3. Acute / Strong safety language elevates floors independently (CRITICAL pathway)
    if strong_safety_hit:
        if safety_concern < 96:
            safety_concern = 96
            adjustments.append("Strong safety phrase floor applied (safety ≥ 96, prototype)")
        if urgency < 88:
            urgency = 88
            adjustments.append("Strong safety context urgency floor (urgency ≥ 88, prototype)")
        if vulnerability < 88:
            vulnerability = 88
            adjustments.append("Strong safety context vulnerability floor (vulnerability ≥ 88, prototype)")
        if stress < 55:
            stress = 55
            adjustments.append("Strong safety context stress floor (stress ≥ 55, prototype)")

    # 4. Affirmative safe expressions suppress false safety escalation
    if contextual_safety and contextual_safety.get("is_affirmative_safe") and not strong_safety_hit:
        safety_concern = 0.0
        adjustments.append("Affirmative safe expression: safety escalation suppressed")

    scores = {
        "stress": round_score(stress),
        "vulnerability": round_score(vulnerability),
        "urgency": round_score(urgency),
        "safetyConcern": round_score(safety_concern),
    }
    return scores, adjustments


def classify_risk(svi: int) -> str:
    """Map SVI score to risk band: LOW, MODERATE, HIGH, CRITICAL."""
    level = "LOW"
    for band in RISK_THRESHOLDS:
        if band["min"] <= svi <= band["max"]:
            level = band["level"]
    return level


def build_indicators(matches: Dict[str, List[str]]) -> List[str]:
    """Generate human-readable indicator tags based on detected signals."""
    indicators = []
    if matches["stress"]:
        indicators.append(INDICATOR_LABELS["stress"])
    if any(FEAR_PRESSURE_REGEX.search(m) for m in matches["stress"]):
        indicators.append(INDICATOR_LABELS["fearPressure"])
    if matches["vulnerability"]:
        indicators.append(INDICATOR_LABELS["vulnerability"])
    if matches["urgency"]:
        indicators.append(INDICATOR_LABELS["urgency"])
    if matches["safety"]:
        indicators.append(INDICATOR_LABELS["safety"])

    # De-duplicate while preserving order
    deduped = []
    for item in indicators:
        if item not in deduped:
            deduped.append(item)
    return deduped


def analyze_statement(
    statement_text: str,
    language: str = "english",
    include_semantics: bool = True,
) -> Dict[str, Any]:
    """
    Main SVI analysis function.
    Returns calculated components, SVI score, risk level, indicators, and review recommendations.
    Integrates contextual safety understanding before scoring.
    """
    text = (statement_text or "").strip()
    if not text:
        raise ValueError("Statement must not be empty.")

    normalized = (
        text.lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    # Step 1: Intermediate Context-Aware Safety Analysis
    ctx_safety = contextual_safety_analyzer.analyze(text, language or "english")

    # Step 2: Signal bank matches
    matches = {
        "stress": find_matches(normalized, SIGNAL_BANKS["stress"]),
        "vulnerability": find_matches(normalized, SIGNAL_BANKS["vulnerability"]),
        "urgency": find_matches(normalized, SIGNAL_BANKS["urgency"]),
        "safety": find_matches(normalized, SIGNAL_BANKS["safety"]),
    }

    # If affirmative safe and not acute threat, neutralize spurious safety substring matches
    if ctx_safety.get("is_affirmative_safe"):
        matches["safety"] = []

    strong_safety_hit = (
        any(phrase.lower() in normalized for phrase in STRONG_SAFETY_PHRASES)
        or ctx_safety.get("tier") == "CRITICAL_ACUTE"
    )

    base_scores = {
        "stress": score_from_match_count(len(matches["stress"])),
        "vulnerability": score_from_match_count(len(matches["vulnerability"])),
        "urgency": score_from_match_count(len(matches["urgency"])),
        "safetyConcern": score_from_match_count(len(matches["safety"])),
    }

    components, adjustments = apply_contextual_adjustments(
        base_scores, matches, strong_safety_hit, contextual_safety=ctx_safety
    )

    svi_raw = (
        components["stress"] * WEIGHTS["stress"]
        + components["vulnerability"] * WEIGHTS["vulnerability"]
        + components["urgency"] * WEIGHTS["urgency"]
        + components["safetyConcern"] * WEIGHTS["safetyConcern"]
    )
    svi = round_score(svi_raw)
    risk_level = classify_risk(svi)

    immediate_human_review = (
        strong_safety_hit
        or len(matches["safety"]) > 0
        or bool(ctx_safety.get("has_safety_concern"))
        or risk_level == "CRITICAL"
    )
    if ctx_safety.get("is_affirmative_safe") and not strong_safety_hit:
        immediate_human_review = False

    indicators = build_indicators(matches)
    if ctx_safety.get("indicators"):
        for ind in ctx_safety["indicators"]:
            if ind not in indicators:
                indicators.append(ind)
    if not indicators:
        indicators.append("No strong prototype signals detected in the statement")

    res = {
        "statement": text,
        "language": language or "english",
        "stress": components["stress"],
        "vulnerability": components["vulnerability"],
        "urgency": components["urgency"],
        "safety": components["safetyConcern"],
        "svi": svi,
        "risk_level": risk_level,
        "risk_tier": risk_level,
        "indicators": indicators,
        "human_review": immediate_human_review,
        "recommendation": RECOMMENDATIONS.get(risk_level, "Information and general support"),
        "safety_flag": immediate_human_review,
        "contextual_safety": ctx_safety,
        "components": {
            "stress": components["stress"],
            "vulnerability": components["vulnerability"],
            "urgency": components["urgency"],
            "safety": components["safetyConcern"],
        },
        "matches": matches,
        "contextual_adjustments": adjustments,
    }

    if include_semantics:
        try:
            try:
                from .semantic_auxiliary import semantic_auxiliary_service
            except ImportError:
                from semantic_auxiliary import semantic_auxiliary_service
            semantic_res = semantic_auxiliary_service.analyze_semantics(text, language or "english")
            if semantic_res is not None:
                res["semantic_analysis"] = semantic_res
        except Exception:
            # Auxiliary signal failure must never break deterministic rule-based SVI
            pass

    return res
