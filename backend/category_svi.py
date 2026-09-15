"""
SAMVAD AI — Category-Guided SVI Score Range & Contextual Scoring Engine

Architecture Layer:
  RISK CATEGORY (from Trained Classifier)
  → PREDEFINED SVI SCORE RANGE
  → CONTEXTUAL INDICATORS (Stress, Vulnerability, Urgency, Safety, Support Request)
  → FINAL SVI SCORE

PROTOTYPE OPERATIONAL BOUNDARIES & DISCLAIMER:
- These score ranges and thresholds are advisory prototype values designed for human operator decision-support.
- NOT a clinical psychological assessment, psychiatric diagnosis, or legal determination.
- Formal clinical, psychological, and regulatory validation is required before real-world production deployment.
- AI assists. Trained humans decide.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

# Predefined prototype SVI score ranges
PROTOTYPE_SCORE_RANGES: Dict[str, Dict[str, int]] = {
    "LOW": {"min": 0, "max": 24},
    "MODERATE": {"min": 25, "max": 49},
    "HIGH": {"min": 50, "max": 74},
    "CRITICAL": {"min": 75, "max": 100},
}

# Human support request patterns across English, Hindi, Hinglish, and Marathi
SUPPORT_REQUEST_PATTERNS = [
    # English
    r"\b(?:talk|speak)\s+(?:to|with)\s+(?:someone|somebody|a\s+human|an\s+operator|an\s+agent|a\s+person|a\s+counselor|staff)\b",
    r"\bconnect\s+(?:me\s+)?(?:to|with)\s+(?:a\s+)?(?:human|operator|person|agent|support|team)\b",
    r"\bhuman\s+support\b",
    r"\bhuman\s+(?:assistance|agent|operator|intervention)\b",
    r"\bneed\s+(?:to\s+speak|to\s+talk)\b",
    r"\btransfer\s+(?:me\s+)?to\s+(?:a\s+)?(?:human|operator)\b",
    # Hindi
    r"किसी\s+(?:इंसान|व्यक्ति|ऑपरेटर|अधिकारी|काउंसलर)\s+से\s+बात",
    r"मानव\s+(?:सहायता|मदद|सहायक)",
    r"ऑपरेटर\s+से\s+बात",
    r"किसी\s+से\s+बात\s+करनी\s+है",
    r"किसी\s+से\s+कनेक्ट\s+कर",
    # Hinglish
    r"\bhuman\s+support\s+tak\s+connect\b",
    r"\bkisi\s+human\s+support\b",
    r"\bhuman\s+support\s+se\s+connect\b",
    r"\bkisi\s+(?:insan|person|operator)\s+se\s+baat\b",
    r"\bkisi\s+se\s+baat\s+karni\b",
    r"\boperator\s+se\s+connect\b",
    r"\bhuman\s+se\s+connect\b",
    # Marathi
    r"कोणाशीतरी\s+बोलायचे\s+आहे",
    r"कोणाशी\s+बोलायचे\s+आहे",
    r"ऑपरेटरशी\s+बोलायचे",
    r"मानवी\s+(?:मदत|सहाय्य)",
    r"ऑपरेटरशी\s+कनेक्ट",
]

_COMPILED_SUPPORT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SUPPORT_REQUEST_PATTERNS]


def detect_support_request(text: str) -> Tuple[bool, Optional[str]]:
    """
    Detect whether the complainant explicitly requested direct human assistance.
    
    CRITICAL SAFETY & ETHICAL RULE:
    A request for human support alone does NOT indicate emotional breakdown or acute danger.
    It flags the case for human operator attention without artificially inflating the
    underlying risk score to HIGH or CRITICAL.
    """
    norm = (text or "").strip().lower()
    for rx in _COMPILED_SUPPORT_PATTERNS:
        if rx.search(norm):
            return True, "Complainant requested direct human support / operator contact."
    return False, None


def compute_category_svi(
    predicted_category: str,
    component_scores: Dict[str, int],
    contextual_safety: Optional[Dict[str, Any]] = None,
    support_requested: bool = False,
    support_reason: Optional[str] = None,
    strong_safety_hit: bool = False,
    legacy_svi_score: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculate final SVI score strictly within the predicted category range,
    modulated by normalized contextual indicators and independent safety constraints.
    
    Formula:
      final_svi = category_min + round(normalized_severity * category_range)
      clamped to [category_min, category_max]
    """
    category = (predicted_category or "LOW").strip().upper()
    if category not in PROTOTYPE_SCORE_RANGES:
        category = "LOW"

    ctx_safety = contextual_safety or {}
    has_safety_concern = bool(ctx_safety.get("has_safety_concern")) or strong_safety_hit
    safety_tier = ctx_safety.get("tier", "NONE")

    # 1. Independent Safety Escalation Check
    # If independent safety rule detects acute threat, escalate category to CRITICAL.
    is_acute_crisis = (
        safety_tier == "CRITICAL_ACUTE"
        or strong_safety_hit
        or "cannot stay safe" in str(ctx_safety.get("matched_cues", "")).lower()
    )

    safety_escalated = False
    if is_acute_crisis and category != "CRITICAL":
        category = "CRITICAL"
        safety_escalated = True
    elif has_safety_concern and category in ("LOW", "MODERATE") and not ctx_safety.get("is_affirmative_safe"):
        # Personal safety inability / feeling unsafe escalates to at least HIGH
        category = "HIGH"
        safety_escalated = True

    # Affirmative safe declaration suppresses false safety escalation
    if ctx_safety.get("is_affirmative_safe") and not is_acute_crisis:
        if safety_escalated:
            category = (predicted_category or "LOW").strip().upper()
            safety_escalated = False

    # 2. Get Category Range
    score_range = PROTOTYPE_SCORE_RANGES[category]
    cat_min = score_range["min"]
    cat_max = score_range["max"]
    cat_span = cat_max - cat_min

    # 3. Calculate Normalized Contextual Severity [0.0, 1.0]
    stress = float(component_scores.get("stress", 0))
    vuln = float(component_scores.get("vulnerability", 0))
    urg = float(component_scores.get("urgency", 0))
    safe = float(component_scores.get("safetyConcern", component_scores.get("safety", 0)))

    # Weighted severity matching prototype SVI weights (0.30 stress, 0.30 vuln, 0.25 urgency, 0.15 safety)
    weighted_sum = (stress * 0.30) + (vuln * 0.30) + (urg * 0.25) + (safe * 0.15)
    normalized_severity = max(0.0, min(1.0, weighted_sum / 100.0))

    # 4. Modulate Score Within Category Range
    modulated_offset = int(math.floor((normalized_severity * cat_span) + 0.5))
    final_score = cat_min + modulated_offset

    # Ensure hard clamping within the allowed category range
    final_score = max(cat_min, min(cat_max, final_score))

    # 5. Determine Human Review and Indicators
    human_review = False
    review_reasons = []

    if category == "CRITICAL":
        human_review = True
        review_reasons.append("Critical risk category requires human operator escalation.")
    elif category == "HIGH":
        human_review = True
        review_reasons.append("High risk category recommended for priority review.")

    if has_safety_concern:
        human_review = True
        review_reasons.append("Possible safety concern indicators detected.")

    if support_requested:
        human_review = True
        review_reasons.append("Complainant requested direct human operator support.")

    if ctx_safety.get("is_affirmative_safe") and not is_acute_crisis:
        # If affirmative safe, clear safety review unless high/critical or requested support
        if not support_requested and category in ("LOW", "MODERATE"):
            human_review = False
            review_reasons = []

    human_review_reason = " ".join(review_reasons) if review_reasons else None

    # Contextual indicator tags
    indicators: List[str] = []
    indicators.append(f"Possible indicators detected: {category.lower()} risk category")

    if stress > 20:
        indicators.append("Elevated stress indicators")
    if vuln > 20:
        indicators.append("Vulnerability indicators")
    if urg > 20:
        indicators.append("Urgency indicators")
    if safe > 20 or has_safety_concern:
        indicators.append("Safety concern indicators")
    if support_requested:
        indicators.append("Direct human support requested")
    if is_acute_crisis:
        indicators.append("Immediate threat or acute safety danger detected")

    # Non-diagnostic explanation
    context_desc_parts = []
    if stress > 20:
        context_desc_parts.append("elevated stress")
    if vuln > 20:
        context_desc_parts.append("vulnerability signals")
    if urg > 20:
        context_desc_parts.append("urgency signals")
    if safe > 20 or has_safety_concern:
        context_desc_parts.append("safety concern signals")

    if context_desc_parts:
        context_desc = ", ".join(context_desc_parts)
        explanation = (
            f"Possible indicators detected: {category.lower()} risk category. "
            f"Contextual signals include {context_desc}. "
            f"Calculated SVI score is {final_score} within the prototype {cat_min}–{cat_max} range."
        )
    else:
        explanation = (
            f"Possible indicators detected: {category.lower()} risk category. "
            f"No acute distress signals detected. "
            f"Calculated SVI score is {final_score} within the prototype {cat_min}–{cat_max} range."
        )

    if support_requested:
        explanation += " Complainant has explicitly requested human support assistance."

    return {
        "risk_category": category,
        "svi_score": final_score,
        "svi_range": score_range,
        "contextual_indicators": indicators,
        "explanation": explanation,
        "human_review": human_review,
        "human_review_reason": human_review_reason,
        "safety_flag": has_safety_concern or is_acute_crisis,
        "support_request": support_requested,
        "components": {
            "stress": int(stress),
            "vulnerability": int(vuln),
            "urgency": int(urg),
            "safety": int(safe),
        },
        "svi_formula_score": legacy_svi_score,
        "normalized_contextual_severity": round(normalized_severity, 4),
        "safety_escalated": safety_escalated,
    }
