"""
SAMVAD AI — IndicBERT Auxiliary Semantic Analysis Layer
Computes multilingual semantic alignment signals for stress, vulnerability, urgency, and safety.

IMPORTANT NOTICE:
IndicBERT is used strictly as an auxiliary semantic signal.
It does NOT generate clinical diagnoses, trauma scores, mental-health ratings,
legal assessments, or emergency triage determinations.
Final SVI score calculation remains rule-based, deterministic, and explainable.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("samvad.semantic_auxiliary")

# Feature Flags
# IndicBERT semantic layer is active to generate auxiliary signals:
INDICBERT_SEMANTIC_ENABLED = os.environ.get("INDICBERT_SEMANTIC_ENABLED", "true").lower() in ("true", "1", "yes")

# Final SVI score fusion is DISABLED by default until validated:
SVI_FUSION_ENABLED = os.environ.get("SVI_FUSION_ENABLED", "false").lower() in ("true", "1", "yes")

# Multilingual category anchor exemplars (English, Hindi, Marathi)
CATEGORY_ANCHORS = {
    "stress": [
        "I am feeling extreme stress, anxiety, worry, and pressure.",
        "Mujhe bahut stress, chinta aur dabav feel ho raha hai.",
        "मला खूप मानसिक ताण, काळजी आणि दबाव येत आहे.",
    ],
    "vulnerability": [
        "I am alone, helpless, isolated, and unable to cope on my own.",
        "Main akela aur asahay hoon, koi support nahi hai aur sambhal nahi paa raha.",
        "मी एकटा आणि असहाय्य आहे, कोणाचाही आधार नाही आणि मी परिस्थिती सांभाळू शकत नाही.",
    ],
    "urgency": [
        "I need immediate urgent emergency help right now quickly.",
        "Mujhe turant, abhi aur jaldi emergency help chahiye.",
        "मला आत्ताच, ताबडतोब आणि त्वरित मदतीची गरज आहे.",
    ],
    "safety": [
        "I am in immediate danger, unsafe, facing serious threat and cannot stay safe.",
        "Mujhe safe feel nahi ho raha, meri suraksha ko khatra hai.",
        "मला सुरक्षित वाटत नाही, माझ्या जीवाला धोका आहे आणि तातडीने संरक्षणाची गरज आहे.",
    ],
}


class SemanticAuxiliaryService:
    """
    Computes auxiliary semantic alignment signals using IndicBERT sentence embeddings.
    """

    def __init__(self):
        self._anchor_embeddings: Dict[str, List[Any]] = {}
        self._initialized = False

    def _ensure_anchor_embeddings(self, service) -> bool:
        """Lazily pre-compute and cache anchor embeddings on first use."""
        if self._initialized:
            return True

        try:
            logger.info("Pre-computing IndicBERT anchor exemplar embeddings...")
            for category, phrases in CATEGORY_ANCHORS.items():
                tensors = []
                for phrase in phrases:
                    t = service.get_embedding_tensor(phrase)
                    if t is not None:
                        tensors.append(t)
                self._anchor_embeddings[category] = tensors
            self._initialized = True
            logger.info("IndicBERT anchor exemplar embeddings ready.")
            return True
        except Exception as exc:
            logger.warning("Could not pre-compute anchor embeddings: %s", exc)
            return False

    def _calculate_category_similarity(self, user_tensor, category: str) -> float:
        """Compute highest cosine similarity between user embedding and category anchors."""
        import torch
        import torch.nn.functional as F

        anchors = self._anchor_embeddings.get(category, [])
        if not anchors:
            return 0.0

        max_sim = -1.0
        for anchor in anchors:
            sim = float(F.cosine_similarity(user_tensor.unsqueeze(0), anchor.unsqueeze(0)).item())
            if sim > max_sim:
                max_sim = sim

        # Clamp between 0.0 and 1.0
        return max(0.0, min(1.0, max_sim))

    def _similarity_level(self, sim: float) -> str:
        """Map similarity float to explainable categorical rating."""
        if sim >= 0.70:
            return "HIGH"
        if sim >= 0.55:
            return "MODERATE"
        if sim >= 0.40:
            return "MILD"
        return "LOW"

    def analyze_semantics(
        self,
        statement: str,
        language: str = "english",
        indicbert_service=None,
    ) -> Optional[Dict[str, Any]]:
        """
        Run IndicBERT auxiliary semantic analysis on a statement.
        Returns category signals without changing base SVI calculations.
        """
        if not INDICBERT_SEMANTIC_ENABLED:
            return {
                "enabled": False,
                "message": "IndicBERT semantic auxiliary layer is currently disabled.",
            }

        if indicbert_service is None:
            try:
                from .indicbert_service import indicbert_service
            except ImportError:
                from indicbert_service import indicbert_service

        cleaned_text = (statement or "").strip()
        if not cleaned_text:
            return None

        # Check if language is supported
        is_supported, lang_code, norm_lang = indicbert_service.validate_language(language)
        if not is_supported:
            return {
                "enabled": True,
                "model": indicbert_service.model_name,
                "language": language,
                "supported": False,
                "error": f"Language '{language}' is not supported by IndicBERT.",
                "disclaimer": (
                    "IndicBERT auxiliary signals are only available for supported Indian languages. "
                    "Rule-based SVI analysis continues as normal."
                ),
            }

        # Ensure model is ready
        if not indicbert_service.is_loaded:
            if not indicbert_service.load_model():
                return {
                    "enabled": True,
                    "model": indicbert_service.model_name,
                    "status": "model_unavailable",
                    "error": indicbert_service.load_error,
                    "disclaimer": "IndicBERT model unavailable. Primary rule-based SVI unaffected.",
                }

        # Ensure anchor cache is populated
        if not self._ensure_anchor_embeddings(indicbert_service):
            return {
                "enabled": True,
                "status": "anchors_unavailable",
                "disclaimer": "Anchor representations could not be computed.",
            }

        try:
            # Extract single statement embedding
            user_tensor = indicbert_service.get_embedding_tensor(cleaned_text)
            if user_tensor is None:
                return None

            stress_sim = self._calculate_category_similarity(user_tensor, "stress")
            vuln_sim = self._calculate_category_similarity(user_tensor, "vulnerability")
            urg_sim = self._calculate_category_similarity(user_tensor, "urgency")
            safety_sim = self._calculate_category_similarity(user_tensor, "safety")

            try:
                try:
                    from .contextual_safety import contextual_safety_analyzer
                except ImportError:
                    from contextual_safety import contextual_safety_analyzer
                ctx_summary = contextual_safety_analyzer.analyze(cleaned_text, norm_lang)
            except Exception:
                ctx_summary = None

            return {
                "enabled": True,
                "model": indicbert_service.model_name,
                "language": norm_lang,
                "stress_signal": {
                    "similarity": round(stress_sim, 4),
                    "level": self._similarity_level(stress_sim),
                    "confidence": round(stress_sim, 4),
                },
                "vulnerability_signal": {
                    "similarity": round(vuln_sim, 4),
                    "level": self._similarity_level(vuln_sim),
                    "confidence": round(vuln_sim, 4),
                },
                "urgency_signal": {
                    "similarity": round(urg_sim, 4),
                    "level": self._similarity_level(urg_sim),
                    "confidence": round(urg_sim, 4),
                },
                "safety_signal": {
                    "similarity": round(safety_sim, 4),
                    "level": self._similarity_level(safety_sim),
                    "confidence": round(safety_sim, 4),
                },
                "contextual_safety": ctx_summary,
                "fusion_applied": SVI_FUSION_ENABLED,
                "disclaimer": (
                    "AI-assisted auxiliary semantic representation. Not a clinical diagnosis, "
                    "psychological assessment, legal risk determination, or emergency triage classifier."
                ),
            }
        except Exception as exc:
            logger.error("Error computing auxiliary semantics: %s", exc)
            return {
                "enabled": True,
                "status": "inference_error",
                "error": str(exc),
                "disclaimer": "Inference error in auxiliary layer. Primary rule-based SVI unaffected.",
            }


# Module singleton
semantic_auxiliary_service = SemanticAuxiliaryService()
