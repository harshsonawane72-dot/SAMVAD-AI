"""
SAMVAD AI — Trainable Natural Complaint Risk Classification Layer
Provides neural risk classification on top of IndicBERT semantic representations.

OPERATIONAL BOUNDARIES:
- Not a clinical, diagnostic, or psychiatric assessment classifier.
- Does not assess suicide, mental illness, or legal culpability.
- Decision-support signal for human operators only.
"""

import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("samvad.risk_classifier")

BASE_DIR = Path(__file__).resolve().parent
_env_model_path = os.environ.get("RISK_CLASSIFIER_WEIGHTS_PATH")
MODEL_PATH = Path(_env_model_path) if _env_model_path else (BASE_DIR / "models" / "risk_classifier_head.pt")

CLASSES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}


class RiskClassifierService:
    """
    Neural Risk Classifier combining IndicBERT text representations with
    contextual safety and SVI calibrated scoring.
    """

    def __init__(self):
        self._model = None
        self._is_initialized = False
        self._is_trained = False
        self._training_reason = "No checkpoint loaded."

    def _build_model(self):
        """Construct PyTorch neural classification head."""
        try:
            import torch
            import torch.nn as nn

            class IndicBERTRiskClassifier(nn.Module):
                def __init__(self, input_dim: int = 768, num_classes: int = 4):
                    super().__init__()
                    self.layer_norm = nn.LayerNorm(input_dim)
                    self.dropout1 = nn.Dropout(0.2)
                    self.dense1 = nn.Linear(input_dim, 128)
                    self.activation = nn.GELU()
                    self.dropout2 = nn.Dropout(0.1)
                    self.dense2 = nn.Linear(128, num_classes)

                def forward(self, x: torch.Tensor) -> torch.Tensor:
                    x = self.layer_norm(x)
                    x = self.dropout1(x)
                    x = self.dense1(x)
                    x = self.activation(x)
                    x = self.dropout2(x)
                    logits = self.dense2(x)
                    return logits

            return IndicBERTRiskClassifier()
        except Exception as exc:
            logger.warning("PyTorch module initialization error: %s", exc)
            return None

    def _ensure_model(self):
        if self._is_initialized and self._model is not None:
            return True
        self._model = self._build_model()
        if self._model is None:
            self._is_trained = False
            self._training_reason = "PyTorch module could not be constructed."
            return False

        # Load weights if available
        if MODEL_PATH.exists():
            try:
                import torch
                state_dict = torch.load(MODEL_PATH, weights_only=True)
                self._model.load_state_dict(state_dict)
                self._model.eval()
                self._is_initialized = True
                self._is_trained = True
                self._training_reason = f"Loaded trained weights from {MODEL_PATH.name}."
                logger.info("Loaded trained risk classifier weights from %s", MODEL_PATH)
                return True
            except Exception as e:
                self._is_trained = False
                self._training_reason = f"Checkpoint load failed: {e}"
                logger.warning("Could not load weights: %s", e)

        self._model.eval()
        self._is_initialized = True
        self._is_trained = False
        self._training_reason = f"Checkpoint not found at {MODEL_PATH}."
        return True

    def _get_embedding(self, text: str):
        """Extract mean-pooled embedding tensor from IndicBERT or fallback."""
        try:
            from .indicbert_service import indicbert_service
        except ImportError:
            from indicbert_service import indicbert_service

        t = None
        try:
            t = indicbert_service.get_embedding_tensor(text)
        except Exception:
            t = None

        if t is not None:
            import torch.nn.functional as F
            return F.normalize(t.unsqueeze(0), p=2, dim=1)[0]

        import torch
        vec = torch.zeros(768, dtype=torch.float32)
        words = re.findall(r"\w+", text.lower())
        for idx, word in enumerate(words):
            h = hash(word) % 768
            vec[h] += 1.0 / (idx + 1.0)
        norm = torch.norm(vec, p=2)
        if norm > 1e-6:
            vec = vec / norm
        return vec

    def classify(self, text: str, language: str = "english") -> Dict[str, Any]:
        """
        Classify natural human complaint into LOW, MODERATE, HIGH, or CRITICAL.
        Combines semantic language representation with contextual safety constraints.
        """
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("Complaint text must not be empty.")

        # 1. Independent Contextual Safety Evaluation
        try:
            from .contextual_safety import contextual_safety_analyzer
        except ImportError:
            from contextual_safety import contextual_safety_analyzer

        ctx_safety = contextual_safety_analyzer.analyze(cleaned_text, language or "english")

        # 2. Extract semantic embedding
        emb = self._get_embedding(cleaned_text)

        # 3. Neural inference
        self._ensure_model()
        import torch
        import torch.nn.functional as F

        with torch.no_grad():
            if self._model is not None:
                logits = self._model(emb.unsqueeze(0))[0]
            else:
                logits = torch.zeros(4)

        probs = F.softmax(logits, dim=-1).cpu().tolist()

        prob_dict = {
            "LOW": round(probs[0], 4),
            "MODERATE": round(probs[1], 4),
            "HIGH": round(probs[2], 4),
            "CRITICAL": round(probs[3], 4),
        }

        # Select highest probability class from trained model
        predicted_idx = int(torch.argmax(logits).item())
        predicted_level = IDX_TO_CLASS[predicted_idx]
        confidence = round(probs[predicted_idx], 4)

        # Step 9 Safety Boundary: Contextual Safety Floor
        # The neural classifier must NOT suppress safety cues.
        if ctx_safety.get("tier") == "CRITICAL_ACUTE":
            predicted_level = "CRITICAL"
        elif ctx_safety.get("has_safety_concern") and predicted_level in ("LOW", "MODERATE"):
            predicted_level = "HIGH"

        # Affirmative safe declaration suppresses false safety escalation
        if ctx_safety.get("is_affirmative_safe") and ctx_safety.get("tier") != "CRITICAL_ACUTE":
            # Keep predicted class if not escalated, but prevent safety floor escalation
            if predicted_level in ("HIGH", "CRITICAL") and not any(w in cleaned_text.lower() for w in ["threat", "hurt", "danger", "bleed", "kill"]):
                predicted_level = "LOW"

        human_review = (
            predicted_level == "CRITICAL"
            or bool(ctx_safety.get("has_safety_concern"))
            or predicted_level == "HIGH"
        )
        if ctx_safety.get("is_affirmative_safe") and ctx_safety.get("tier") != "CRITICAL_ACUTE":
            human_review = False

        indicators = ["Possible indicators detected: " + predicted_level.lower() + " risk category"]
        if ctx_safety.get("indicators"):
            for ind in ctx_safety["indicators"]:
                if ind not in indicators:
                    indicators.append(ind)

        return {
            "risk_level": predicted_level,
            "confidence": confidence,
            "probabilities": prob_dict,
            "model": "ai4bharat/IndicBERTv2-MLM-only + MLP Head",
            "trained": self._is_trained,
            "training_status": self._training_reason,
            "human_review": human_review,
            "indicators": indicators,
            "contextual_safety": ctx_safety,
            "disclaimer": (
                "AI-assisted prototype classification. Not a clinical psychiatric assessment, "
                "mental health diagnosis, or legal determination. Human operator review required."
            ),
        }


# Singleton instance
risk_classifier_service = RiskClassifierService()
