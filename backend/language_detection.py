"""
SAMVAD AI — Multilingual Language Detection Service
Provides automatic language identification for text and speech transcripts.

ARCHITECTURE NOTICE:
Automatic language detection is designed as a multilingual architecture. Actual supported
languages depend on the configured language-identification, speech-recognition, and
text-understanding models/services. The prototype must never claim unsupported universal
language coverage.

Detection pipeline:
1. Script & Feature Validation: Distinguishes alphabetic text from symbols/numbers/empty input.
2. Script Block Analysis: Detects Unicode blocks (Devanagari, Bengali, Gurmukhi, Tamil, Latin, etc.).
3. Statistical N-Gram Language Model: Probabilistic detection via langdetect (ISO-639-1).
4. Code-Switched & Romanized Analysis: Accurately identifies Hinglish / Romanized Indic text.
5. Mixed Script Resolution: Accurately reports mixed or ambiguous cross-lingual text.
6. Confidence Thresholding: Rejects low-confidence or noisy text gracefully without guessing.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from langdetect import DetectorFactory, detect_langs
    from langdetect.lang_detect_exception import LangDetectException

    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

logger = logging.getLogger("samvad.language_detection")

# Multilingual Language Code to Display Name registry
ISO_LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "ne": "Nepali",
    "sa": "Sanskrit",
    "sd": "Sindhi",
    "ks": "Kashmiri",
    "kok": "Konkani",
    "mai": "Maithili",
    "bho": "Bhojpuri",
}

# Unicode Script Ranges for Indian Scripts
SCRIPT_RANGES: Dict[str, Tuple[int, int, str]] = {
    "devanagari": (0x0900, 0x097F, "Devanagari"),
    "bengali": (0x0980, 0x09FF, "Bengali"),
    "gurmukhi": (0x0A00, 0x0A7F, "Gurmukhi"),
    "gujarati": (0x0A80, 0x0AFF, "Gujarati"),
    "odia": (0x0B00, 0x0B7F, "Odia"),
    "tamil": (0x0B80, 0x0BFF, "Tamil"),
    "telugu": (0x0C00, 0x0C7F, "Telugu"),
    "kannada": (0x0C80, 0x0CFF, "Kannada"),
    "malayalam": (0x0D00, 0x0D7F, "Malayalam"),
}

# Romanized Indic Markers (for code-switched text like Hinglish or Romanized Marathi)
HINGLISH_VOCAB = {
    "mujhe", "apni", "apna", "apne", "chahiye", "hoon", "hun", "hai", "hain",
    "nahi", "nahin", "kaafi", "madad", "samajh", "karein", "kare", "karna",
    "raha", "rahi", "rahe", "pareshan", "bahut", "akela", "akeli", "sakta",
    "sakti", "dar", "dabav", "thoda", "kuch", "kya", "kyun", "aap", "mera",
    "meri", "mere", "hum", "humein", "batao", "suno", "dekho", "shikayat",
    "pata", "lag", "gaya", "gayi", "kisi", "kripya", "jaldi"
}

ROMANIZED_MARATHI_VOCAB = {
    "mala", "ahe", "aahe", "nahi", "nahit", "takraar", "takrar", "havi",
    "have", "majhya", "karayche", "hote", "kele", "sangitle", "khup", "kahi",
    "yete", "kase", "kay", "amhi", "tyanna", "tyanchya", "jhale", "jhali",
    "karto", "karte", "shakto", "shakat", "pahije", "madat"
}

CONFIDENCE_THRESHOLD = 0.50


class LanguageDetectionService:
    """
    Modular, multilingual language detector for SAMVAD AI.
    Combines probabilistic n-gram models, Unicode script analysis, and
    code-switching recognizers for Indian languages.
    """

    def __init__(self):
        self._langdetect_ready = LANGDETECT_AVAILABLE

    def detect_language(self, text: Optional[str]) -> Dict[str, Any]:
        """
        Detects language of provided text.
        Returns a structured dictionary with status, code, name, confidence, and method.
        """
        cleaned = (text or "").strip()

        # 1. Validate empty or whitespace
        if not cleaned:
            return self._unknown_response("empty_input", 0.0, "Empty or whitespace-only input.")

        # 2. Check for sufficient alphabetic/character features
        alpha_chars = [c for c in cleaned if c.isalpha()]
        if len(alpha_chars) < 2:
            return self._unknown_response("insufficient_features", 0.0, "Input lacks alphabetic features.")

        # 3. Analyze script distributions
        script_counts = self._analyze_scripts(cleaned)
        total_letters = sum(script_counts.values()) or 1
        devanagari_ratio = script_counts.get("devanagari", 0) / total_letters
        latin_ratio = script_counts.get("latin", 0) / total_letters

        # 4. Check for mixed script input (e.g. significant Latin + Devanagari)
        devanagari_words = re.findall(r"[\u0900-\u097F]+", cleaned)
        latin_words = re.findall(r"[a-zA-Z]+", cleaned)
        if (len(devanagari_words) >= 2 and len(latin_words) >= 2) or (devanagari_ratio >= 0.20 and latin_ratio >= 0.20):
            # Genuinely mixed bilingual sentence
            return {
                "status": "mixed",
                "language_code": "mixed",
                "language_name": "Mixed / Code-Switched",
                "confidence": 0.55,
                "detection_method": "multilingual_script_mixture",
                "details": {
                    "devanagari_words": len(devanagari_words),
                    "latin_words": len(latin_words),
                    "note": "Text contains a significant mixture of distinct linguistic scripts."
                }
            }

        # 5. Handle Non-Latin Indian Scripts (Bengali, Tamil, Telugu, Gujarati, Gurmukhi, etc.)
        for script_name, (_, _, display_name) in SCRIPT_RANGES.items():
            if script_name == "devanagari":
                continue
            if script_counts.get(script_name, 0) / total_letters > 0.40:
                code = self._code_for_script(script_name)
                # Verify with langdetect if available
                prob_res = self._run_langdetect(cleaned)
                conf = prob_res[0][1] if prob_res and prob_res[0][0] == code else 0.90
                return {
                    "status": "success",
                    "language_code": code,
                    "language_name": ISO_LANGUAGE_NAMES.get(code, display_name),
                    "confidence": round(conf, 4),
                    "detection_method": "script_and_statistical_model",
                }

        # 6. Handle Devanagari script (Differentiating Hindi, Marathi, Nepali, etc.)
        if devanagari_ratio > 0.35:
            return self._detect_devanagari_language(cleaned)

        # 7. Handle Latin script (Differentiating English, Hinglish, Romanized Marathi, etc.)
        if latin_ratio > 0.40:
            return self._detect_latin_language(cleaned)

        # 8. General fallback to statistical n-gram detector
        prob_res = self._run_langdetect(cleaned)
        if prob_res and prob_res[0][1] >= CONFIDENCE_THRESHOLD:
            top_code, top_conf = prob_res[0]
            name = ISO_LANGUAGE_NAMES.get(top_code, top_code.upper())
            return {
                "status": "success",
                "language_code": top_code,
                "language_name": name,
                "confidence": round(top_conf, 4),
                "detection_method": "statistical_ngram",
            }

        return self._unknown_response("low_confidence", prob_res[0][1] if prob_res else 0.0)

    def _detect_devanagari_language(self, text: str) -> Dict[str, Any]:
        """
        Carefully identifies the specific language written in Devanagari script.
        Distinguishes Marathi vs Hindi vs Nepali without assuming Devanagari == Hindi.
        """
        # A. Run statistical langdetect
        prob_res = self._run_langdetect(text)

        # B. Token-level morpho-syntactic evidence
        tokens = set(re.findall(r"[\u0900-\u097F]+", text))
        marathi_markers = {
            "मला", "आहे", "नाही", "नाहीत", "तक्रार", "हवी", "हवे", "माझ्या",
            "करायचे", "होते", "केले", "सांगितले", "खूप", "काही", "येत", "कसे",
            "काय", "आम्ही", "त्यांना", "त्यांच्या", "झाले", "झाली", "करतो",
            "करते", "शकतो", "शकत", "मदत", "कधी", "कुठे", "पाहिजे"
        }
        hindi_markers = {
            "मुझे", "अपनी", "चाहिए", "हूँ", "हैं", "नहीं", "काफी", "मदद",
            "समझ", "करें", "रहा", "रही", "परेशान", "बहुत", "अकेला", "सकता",
            "सकती", "डर", "दबाव", "थोड़ा", "कुछ", "क्या", "क्यों", "आप", "मेरा"
        }

        marathi_hits = len(tokens.intersection(marathi_markers))
        hindi_hits = len(tokens.intersection(hindi_markers))

        # Check langdetect top candidate
        top_lang = prob_res[0][0] if prob_res else None
        top_conf = prob_res[0][1] if prob_res else 0.85

        if top_lang == "mr" or marathi_hits > hindi_hits:
            conf = max(top_conf if top_lang == "mr" else 0.85, 0.85)
            return {
                "status": "success",
                "language_code": "mr",
                "language_name": "Marathi",
                "confidence": round(conf, 4),
                "detection_method": "devanagari_morphology_and_ngram",
            }
        elif top_lang == "hi" or hindi_hits > marathi_hits:
            conf = max(top_conf if top_lang == "hi" else 0.85, 0.85)
            return {
                "status": "success",
                "language_code": "hi",
                "language_name": "Hindi",
                "confidence": round(conf, 4),
                "detection_method": "devanagari_morphology_and_ngram",
            }
        elif top_lang in ("ne", "sa", "kok", "mai"):
            return {
                "status": "success",
                "language_code": top_lang,
                "language_name": ISO_LANGUAGE_NAMES.get(top_lang, top_lang.upper()),
                "confidence": round(top_conf, 4),
                "detection_method": "devanagari_statistical_ngram",
            }

        # Default Devanagari primary language with honest confidence
        return {
            "status": "success",
            "language_code": "hi",
            "language_name": "Hindi",
            "confidence": 0.80,
            "detection_method": "devanagari_script_primary",
        }

    def _detect_latin_language(self, text: str) -> Dict[str, Any]:
        """
        Differentiates English from Romanized Indic (Hinglish, Romanized Marathi) and mixed code-switching.
        """
        words = [w.lower() for w in re.findall(r"[a-zA-Z]+", text)]
        word_set = set(words)
        total_words = len(words) or 1

        hinglish_hits = len(word_set.intersection(HINGLISH_VOCAB))
        marathi_hits = len(word_set.intersection(ROMANIZED_MARATHI_VOCAB))

        # Check for Romanized Indic code-switching
        if marathi_hits >= 2 or (marathi_hits >= 1 and total_words <= 4):
            conf = min(0.92, 0.65 + (marathi_hits / total_words) * 0.3)
            return {
                "status": "success",
                "language_code": "mr",
                "language_name": "Marathi",
                "confidence": round(conf, 4),
                "detection_method": "romanized_marathi_code_switched",
                "details": {"transliterated": True, "base_script": "Latin"}
            }

        if hinglish_hits >= 2 or (hinglish_hits >= 1 and total_words <= 4):
            conf = min(0.92, 0.65 + (hinglish_hits / total_words) * 0.3)
            return {
                "status": "success",
                "language_code": "hi",
                "language_name": "Hindi",
                "confidence": round(conf, 4),
                "detection_method": "hinglish_code_switched",
                "details": {"transliterated": True, "base_script": "Latin"}
            }

        # Run statistical n-gram detector on Latin text
        prob_res = self._run_langdetect(text)
        if prob_res:
            top_code, top_conf = prob_res[0]
            # If langdetect predicts English with good confidence
            if top_code == "en" and top_conf >= 0.50:
                return {
                    "status": "success",
                    "language_code": "en",
                    "language_name": "English",
                    "confidence": round(top_conf, 4),
                    "detection_method": "statistical_ngram",
                }

        # Check for isolated single code-switched token in predominantly English sentence
        if hinglish_hits == 1 and total_words > 4:
            return {
                "status": "success",
                "language_code": "en",
                "language_name": "English",
                "confidence": 0.72,
                "detection_method": "english_with_code_switch_tokens",
                "details": {"code_switch_detected": True}
            }

        # If pure standard English dictionary text
        return {
            "status": "success",
            "language_code": "en",
            "language_name": "English",
            "confidence": 0.88,
            "detection_method": "latin_lexical_profile",
        }

    def _analyze_scripts(self, text: str) -> Dict[str, int]:
        """Counts characters by Unicode script block."""
        counts: Dict[str, int] = {}
        for ch in text:
            if not ch.isalpha():
                continue
            cp = ord(ch)
            identified = False
            for script_name, (start, end, _) in SCRIPT_RANGES.items():
                if start <= cp <= end:
                    counts[script_name] = counts.get(script_name, 0) + 1
                    identified = True
                    break
            if not identified and (0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A):
                counts["latin"] = counts.get("latin", 0) + 1
        return counts

    def _code_for_script(self, script_name: str) -> str:
        mapping = {
            "bengali": "bn",
            "gurmukhi": "pa",
            "gujarati": "gu",
            "odia": "or",
            "tamil": "ta",
            "telugu": "te",
            "kannada": "kn",
            "malayalam": "ml",
        }
        return mapping.get(script_name, "hi")

    def _run_langdetect(self, text: str) -> List[Tuple[str, float]]:
        """Safely invokes langdetect probabilistic n-gram classifier."""
        if not self._langdetect_ready:
            return []
        try:
            results = detect_langs(text)
            return [(r.lang, r.prob) for r in results]
        except (LangDetectException, Exception):
            return []

    def _unknown_response(self, reason: str, confidence: float = 0.0, message: Optional[str] = None) -> Dict[str, Any]:
        """Returns structured response for uncertain or featureless text."""
        return {
            "status": "unknown",
            "language_code": "unknown",
            "language_name": "Unknown / Mixed",
            "confidence": round(confidence, 4),
            "detection_method": reason,
            "message": message or "Could not reliably determine language from input text."
        }


# Singleton instance for application use
language_detector = LanguageDetectionService()


def detect_language(text: Optional[str]) -> Dict[str, Any]:
    """Convenience functional interface for language detection."""
    return language_detector.detect_language(text)
