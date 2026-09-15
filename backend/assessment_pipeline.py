"""
SAMVAD AI — Step 8: Unified Assessment Pipeline Service
Coordinates Language Detection, Risk Classification, Context-Aware SVI,
Independent Safety Verification, and RAG Support Retrieval.

OPERATIONAL BOUNDARIES:
- Decision support for human operators only.
- AI assists; humans decide.
- Does NOT diagnose psychiatric conditions, make legal determinations, or emergency triage actions.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

try:
    from .database import SessionLocal, ensure_schema_columns
    from .models import Case
    from .language_detection import detect_language
    from .risk_classifier import risk_classifier_service
    from .svi_engine import analyze_statement
    from .contextual_safety import contextual_safety_analyzer
    from .rag_service import rag_service
    from .category_svi import compute_category_svi, detect_support_request, PROTOTYPE_SCORE_RANGES
except ImportError:
    from database import SessionLocal, ensure_schema_columns
    from models import Case
    from language_detection import detect_language
    from risk_classifier import risk_classifier_service
    from svi_engine import analyze_statement
    from contextual_safety import contextual_safety_analyzer
    from rag_service import rag_service
    from category_svi import compute_category_svi, detect_support_request, PROTOTYPE_SCORE_RANGES

logger = logging.getLogger("samvad.assessment_pipeline")


def assess_complaint(
    text: str,
    language: Optional[str] = None,
    case_id: Optional[str] = None,
    interaction_type: str = "chat",
    consent: bool = True,
    save_to_db: bool = True,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Execute the full end-to-end SAMVAD AI assessment pipeline on a natural complaint.
    1. Automatic Language Detection
    2. Neural Risk Classification (IndicBERT + trained MLP head)
    3. Context-Aware Component & SVI Baseline Calculation
    4. Support Request & Independent Safety Verification
    5. Category-Guided SVI Range & Contextual Scoring Layer
    6. RAG Semantic Knowledge Retrieval
    7. Database Persistence
    """
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        raise ValueError("Complaint text must not be empty.")

    # 1. Language Detection
    if not language or language.lower() in ("auto", "unknown"):
        det = detect_language(cleaned_text)
        lang_code = det.get("language_code", "en")
        lang_name = det.get("language_name", "English")
        lang_conf = det.get("confidence", 0.0)
    else:
        # Caller provided language
        l_norm = language.strip().lower()
        if l_norm in ("hi", "hindi"):
            lang_code, lang_name = "hi", "Hindi"
        elif l_norm in ("mr", "marathi"):
            lang_code, lang_name = "mr", "Marathi"
        elif l_norm in ("en", "english"):
            lang_code, lang_name = "en", "English"
        else:
            lang_code, lang_name = l_norm, l_norm.capitalize()
        lang_conf = 1.0

    # 2. Risk Classification (IndicBERT-based semantic classification)
    risk_res = risk_classifier_service.classify(cleaned_text, lang_name.lower())

    # 3. Context-Aware Component & SVI Baseline Calculation (preserved baseline formula)
    svi_res = analyze_statement(cleaned_text, lang_name.lower(), include_semantics=False)

    # 4. Contextual Safety Analysis
    ctx_safety = contextual_safety_analyzer.analyze(cleaned_text, lang_name.lower())

    # 5. Direct Human Support Request Detection
    support_requested, support_reason = detect_support_request(cleaned_text)

    # 6. Category-Guided SVI Scoring Layer (Calibrated within Classifier Range)
    cat_svi = compute_category_svi(
        predicted_category=risk_res["risk_level"],
        component_scores=svi_res["components"],
        contextual_safety=ctx_safety,
        support_requested=support_requested,
        support_reason=support_reason,
        strong_safety_hit=svi_res.get("safety_flag", False),
        legacy_svi_score=svi_res["svi"],
    )

    # Harmonized Indicators
    merged_indicators = []
    for ind in cat_svi.get("contextual_indicators", []):
        if ind not in merged_indicators:
            merged_indicators.append(ind)
    for ind in svi_res.get("indicators", []):
        if ind not in merged_indicators:
            merged_indicators.append(ind)
    for ind in risk_res.get("indicators", []):
        if ind not in merged_indicators:
            merged_indicators.append(ind)

    # 7. RAG Knowledge & Support Retrieval
    rag_res = rag_service.retrieve(cleaned_text, lang_name.lower(), top_k=3)
    support_resources = rag_res.get("results", [])

    # Assign or generate Case ID
    active_case_id = case_id or f"NHAA-2026-{uuid.uuid4().hex[:6].upper()}"

    # 8. Database Persistence
    if save_to_db:
        should_close = False
        if db is None:
            ensure_schema_columns()
            db = SessionLocal()
            should_close = True

        try:
            existing = db.query(Case).filter(Case.case_id == active_case_id).first()
            if existing:
                existing.statement = cleaned_text
                existing.language = lang_name.lower()
                existing.interaction_type = interaction_type or "chat"
                existing.consent = consent
                existing.status = "received"
                existing.risk_level = cat_svi["risk_category"]
                existing.svi_score = cat_svi["svi_score"]
                existing.human_review = cat_svi["human_review"]
                existing.indicators = json.dumps(merged_indicators)
                db.commit()
            else:
                new_case = Case(
                    case_id=active_case_id,
                    statement=cleaned_text,
                    language=lang_name.lower(),
                    interaction_type=interaction_type or "chat",
                    consent=consent,
                    status="received",
                    created_at=datetime.now(timezone.utc).isoformat(),
                    risk_level=cat_svi["risk_category"],
                    svi_score=cat_svi["svi_score"],
                    human_review=cat_svi["human_review"],
                    indicators=json.dumps(merged_indicators),
                )
                db.add(new_case)
                db.commit()
        except Exception as db_err:
            logger.warning("Could not persist case %s to database: %s", active_case_id, db_err)
        finally:
            if should_close and db is not None:
                db.close()

    # Check for tier disagreement between Classifier category and Legacy SVI formula
    has_disagreement = (cat_svi["risk_category"] != svi_res["risk_level"])
    disagreement_info = {
        "has_disagreement": has_disagreement,
        "classifier_tier": cat_svi["risk_category"],
        "svi_formula_tier": svi_res["risk_level"],
        "note": (
            f"Classifier predicted {cat_svi['risk_category']} (calibrated score: {cat_svi['svi_score']}) "
            f"while baseline SVI keyword formula computed {svi_res['risk_level']} (Score: {svi_res['svi']})."
            if has_disagreement else "Classifier risk level and SVI tier are in agreement."
        ),
    }

    # 9. Final Combined Response Structure
    return {
        "case_id": active_case_id,
        "language": {
            "code": lang_code,
            "name": lang_name,
            "confidence": round(lang_conf, 4),
        },
        "risk_category": cat_svi["risk_category"],
        "svi_score": cat_svi["svi_score"],
        "svi_range": cat_svi["svi_range"],
        "contextual_indicators": merged_indicators,
        "explanation": cat_svi["explanation"],
        "human_review": cat_svi["human_review"],
        "human_review_reason": cat_svi["human_review_reason"],
        "safety_flag": cat_svi["safety_flag"],
        "support_request": cat_svi["support_request"],
        "risk_classification": {
            "risk_level": cat_svi["risk_category"],
            "raw_classifier_level": risk_res["risk_level"],
            "confidence": risk_res["confidence"],
            "probabilities": risk_res["probabilities"],
            "trained": risk_res.get("trained", False),
        },
        "svi": {
            "score": cat_svi["svi_score"],
            "risk_level": cat_svi["risk_category"],
            "range": cat_svi["svi_range"],
            "stress": cat_svi["components"]["stress"],
            "vulnerability": cat_svi["components"]["vulnerability"],
            "urgency": cat_svi["components"]["urgency"],
            "safety": cat_svi["components"]["safety"],
            "formula_score": svi_res["svi"],
            "formula_risk_level": svi_res["risk_level"],
        },
        "tier_disagreement": disagreement_info,
        "safety": {
            "concern_detected": cat_svi["safety_flag"],
            "human_review": cat_svi["human_review"],
            "tier": ctx_safety.get("tier", "NONE"),
        },
        "indicators": merged_indicators,
        "support_resources": support_resources,
        "recommendation": svi_res.get("recommendation", "General information and support"),
        "disclaimer": (
            "AI-assisted prototype decision support for trained human operators. "
            "Not a clinical psychological assessment or autonomous triage system."
        ),
    }
