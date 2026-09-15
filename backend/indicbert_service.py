"""
SAMVAD AI — IndicBERT Text Understanding Layer
Provides multilingual semantic representations for Indian languages.

IMPORTANT NOTICE:
IndicBERT is used strictly as an AI-assisted text-understanding and representation layer.
It is NOT a clinically validated tool for assessing trauma, psychological stress,
mental health conditions, legal risk, or emergency triage. SVI decision-support signals
remain governed by human oversight and the validated rule-based engine.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("samvad.indicbert")

# 12 Languages supported by AI4Bharat IndicBERT
SUPPORTED_LANGUAGES = {
    "english": "en",
    "en": "en",
    "hindi": "hi",
    "hi": "hi",
    "marathi": "mr",
    "mr": "mr",
    "bengali": "bn",
    "bn": "bn",
    "gujarati": "gu",
    "gu": "gu",
    "punjabi": "pa",
    "pa": "pa",
    "telugu": "te",
    "te": "te",
    "tamil": "ta",
    "ta": "ta",
    "kannada": "kn",
    "kn": "kn",
    "malayalam": "ml",
    "ml": "ml",
    "odia": "or",
    "or": "or",
    "assamese": "as",
    "as": "as",
}

DEFAULT_MODEL_NAME = os.environ.get("INDICBERT_MODEL_NAME", "ai4bharat/IndicBERTv2-MLM-only")


class IndicBERTService:
    """
    Service wrapper for IndicBERT language model with safe lazy-loading.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._load_error: Optional[str] = None
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded and self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def load_model(self) -> bool:
        """
        Safely load tokenizer and model into memory.
        Uses AutoModel and AutoTokenizer with CPU inference by default.
        """
        if self.is_loaded:
            return True

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            logger.info("Loading IndicBERT model: %s ...", self.model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=False,
            )
            self._model = AutoModel.from_pretrained(self.model_name, low_cpu_mem_usage=False)
            self._model.eval()
            self._is_loaded = True
            self._load_error = None
            logger.info("IndicBERT model '%s' successfully loaded.", self.model_name)
            return True
        except Exception as exc:
            self._load_error = str(exc)
            self._is_loaded = False
            logger.warning("Could not load IndicBERT model '%s': %s", self.model_name, exc)
            return False

    def validate_language(self, language: Optional[str]) -> Tuple[bool, str, str]:
        """
        Validate if the requested language is supported by IndicBERT.
        """
        if not language:
            return True, "en", "english"
        norm = language.strip().lower()
        if norm in SUPPORTED_LANGUAGES:
            return True, SUPPORTED_LANGUAGES[norm], norm
        return False, "", norm

    def understand(self, text: str, language: Optional[str] = "english") -> Dict[str, Any]:
        """
        Perform text understanding and semantic representation extraction.
        Returns semantic metadata, token breakdown, and mean-pooled representation.
        """
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("Text must not be empty.")

        is_supported, lang_code, norm_lang = self.validate_language(language)
        if not is_supported:
            supported_list = ", ".join(sorted(set(k.capitalize() for k in SUPPORTED_LANGUAGES if len(k) > 2)))
            raise ValueError(
                f"Language '{language}' is not supported by IndicBERT. "
                f"Supported Indian languages: {supported_list}."
            )

        # Ensure model is loaded
        if not self.is_loaded:
            success = self.load_model()
            if not success:
                raise RuntimeError(
                    f"IndicBERT model '{self.model_name}' could not be loaded: {self._load_error}"
                )

        import torch

        try:
            # Tokenize input text
            inputs = self._tokenizer(
                cleaned_text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )

            with torch.no_grad():
                outputs = self._model(**inputs)

            # Extract last hidden state representations
            last_hidden_state = outputs.last_hidden_state  # [1, seq_len, hidden_dim]
            attention_mask = inputs["attention_mask"].unsqueeze(-1).expand(last_hidden_state.size()).float()

            # Compute mean-pooled sentence representation
            sum_embeddings = torch.sum(last_hidden_state * attention_mask, dim=1)
            sum_mask = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
            mean_pooled = (sum_embeddings / sum_mask)[0]  # [hidden_dim]

            embedding_list = mean_pooled.cpu().tolist()
            norm_val = float(torch.norm(mean_pooled, p=2).item())

            # Token inspection
            input_ids = inputs["input_ids"][0].tolist()
            tokens = self._tokenizer.convert_ids_to_tokens(input_ids)

            return {
                "status": "success",
                "model_name": self.model_name,
                "model_status": "loaded",
                "language": norm_lang,
                "language_code": lang_code,
                "language_supported": True,
                "text_length": len(cleaned_text),
                "token_count": len(tokens),
                "sequence_length": len(input_ids),
                "tokens_sample": tokens[:25],
                "embedding_dim": len(embedding_list),
                "embedding_preview": [round(x, 4) for x in embedding_list[:8]],
                "embedding_l2_norm": round(norm_val, 4),
                "metadata": {
                    "architecture": type(self._model).__name__,
                    "pooling": "mean_pooling",
                    "max_sequence_length": 512,
                    "device": str(next(self._model.parameters()).device),
                },
                "disclaimer": (
                    "IndicBERT provides multilingual semantic text representations only. "
                    "It is NOT a clinically validated classifier for trauma, mental health, "
                    "stress, legal risk, or emergency triage."
                ),
            }
        except Exception as exc:
            logger.error("IndicBERT inference error: %s", exc)
            raise RuntimeError(f"IndicBERT inference failed: {exc}") from exc

    def get_embedding_tensor(self, text: str):
        """Extract mean-pooled 1D torch tensor for text, or None if unavailable."""
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return None
        if not self.is_loaded:
            if not self.load_model():
                return None
        import torch

        inputs = self._tokenizer(
            cleaned_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        with torch.no_grad():
            outputs = self._model(**inputs)
        last_hidden_state = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"].unsqueeze(-1).expand(last_hidden_state.size()).float()
        sum_embeddings = torch.sum(last_hidden_state * attention_mask, dim=1)
        sum_mask = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
        return (sum_embeddings / sum_mask)[0]

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Extract mean-pooled vector as float list, or None if unavailable."""
        tensor = self.get_embedding_tensor(text)
        if tensor is None:
            return None
        return tensor.cpu().tolist()


# Module-level singleton instance for lazy-loading
indicbert_service = IndicBERTService()
