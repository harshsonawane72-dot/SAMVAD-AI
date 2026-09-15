"""
SAMVAD AI — Context-Aware Safety Understanding Layer (Step 6.6)
Provides contextual safety and vulnerability analysis for Indian languages and English.

ETHICAL AND OPERATIONAL BOUNDARIES:
- Not a clinical, diagnostic, or psychiatric assessment tool.
- Does not assess suicide, mental illness, trauma, or psychiatric conditions.
- Does not make legal judgments, culpability determinations, or credibility assessments.
- Decision-support signals for trained human personnel only. AI assists; humans decide.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------------------------------------------------------
# 1. Affirmative Safe Expressions (Positive Polarity)
# Statements matching these without negations indicate safety or resolution
# and MUST NOT trigger false safety escalations.
# -----------------------------------------------------------------------------
AFFIRMATIVE_SAFE_PATTERNS = [
    # English
    r"\bi (?:feel|am|stay|remain) safe\b",
    r"\bfeeling safe\b",
    r"\bcompletely safe\b",
    r"\bsafe and sound\b",
    r"\bin a safe place\b",
    r"\bkept safe\b",
    r"\bi am now safe\b",
    r"\bfeel safe now\b",
    r"\bnow feel safe\b",
    r"\bsafe now\b",
    # Hindi
    r"सुरक्षित महसूस (?:हो|कर) रहा",
    r"अब सुरक्षित (?:हूँ|हुँ|हैं)",
    r"सुरक्षित स्थान पर",
    r"पूरी तरह सुरक्षित",
    # Hinglish
    r"\bab safe (?:hoon|hun|hai|feel)\b",
    r"\bsafe feel ho raha\b",
    r"\bab safe lag raha\b",
    # Marathi
    r"आता सुरक्षित वाटत",
    r"सुरक्षित आहे",
    r"पूर्णपणे सुरक्षित",
]

# Negation words that invert safety when near "safe" / "सुरक्षित"
NEGATION_WORDS = {
    "not", "don't", "dont", "cannot", "can't", "cant", "unable",
    "never", "no", "nahi", "nahin", "na", "नाही", "नाहीत", "नसून"
}

# -----------------------------------------------------------------------------
# 2. Contextual Safety Concern Patterns (Paraphrases & Idiomatic Expressions)
# Categorized into:
#   - personal_safety_inability: Inability or apprehension to keep oneself safe
#   - feeling_unsafe: Explicit negated safety or feeling unsafe
#   - personal_safety_concern: Apprehension or fear for one's own safety
#   - immediate_crisis_threat: Acute immediate danger / threat
# -----------------------------------------------------------------------------

PATTERNS_PERSONAL_SAFETY_INABILITY = [
    # English
    r"(?:worried|anxious|afraid|scared|fear)\s+(?:that\s+)?(?:i\s+)?(?:may|might|will|would)?\s*(?:not\s+be\s+able|unable)\s+to\s+keep\s+(?:my\s*self|myself)\s+safe",
    r"(?:not\s+be\s+able|unable|cannot|can't|cant)\s+to\s+keep\s+(?:my\s*self|myself)\s+safe",
    r"(?:not\s+be\s+able|unable|cannot|can't|cant)\s+to\s+(?:stay|remain)\s+safe",
    r"(?:not\s+be\s+able|unable|cannot|can't|cant)\s+to\s+protect\s+(?:my\s*self|myself)",
    r"(?:hard|difficult|impossible)\s+to\s+keep\s+(?:my\s*self|myself)\s+safe",
    r"(?:fear|worry|worried)\s+(?:about|for)\s+(?:my\s*self\s+being\s+safe|keeping\s+myself\s+safe)",
    # Hindi
    r"खुद को सुरक्षित नहीं (?:रख|पा)",
    r"सुरक्षित नहीं रख (?:सकता|सकती|पाऊँगा|पाऊंगा|पाऊंगी)",
    r"सुरक्षित नहीं रह (?:सकता|सकती)",
    r"स्वयं की (?:रक्षा|सुरक्षा) नहीं",
    r"अपनी (?:सुरक्षा|हिफाजत) नहीं कर",
    # Hinglish
    r"khud ko safe nahi rakh",
    r"safe nahi reh (?:sakta|sakti)",
    r"khud ko safe nahi rakh (?:paunga|paungi|sakta|sakti)",
    r"apne aap ko safe nahi",
    # Marathi
    r"स्वतःला सुरक्षित ठेवू शकत नाही",
    r"स्वतःला सुरक्षित ठेवू शकणार नाही",
    r"स्वतःचे रक्षण करू शकत नाही",
    r"सुरक्षित राहू शकत नाही",
]

PATTERNS_FEELING_UNSAFE = [
    # English
    r"\b(?:don't|dont|do not|doesn't|does not|cannot|can't|not)\s+feel\s+safe\b",
    r"\b(?:feeling|feel|feels)\s+unsafe\b",
    r"\bnot\s+feeling\s+safe\b",
    r"\bnowhere\s+is\s+safe\b",
    r"\bno\s+longer\s+safe\b",
    # Hindi
    r"सुरक्षित महसूस नहीं हो रहा",
    r"सुरक्षित नहीं लग रहा",
    r"असुरक्षित महसूस",
    r"सुरक्षित नहीं हूँ",
    # Hinglish
    r"safe feel nahi",
    r"safe nahi lag raha",
    r"unsafe feel",
    r"safe nahi hoon",
    # Marathi
    r"सुरक्षित वाटत नाही",
    r"असुरक्षित वाटत आहे",
    r"सुरक्षित वाटत नाहीये",
]

PATTERNS_PERSONAL_SAFETY_CONCERN = [
    # English
    r"\b(?:worried|worry|fear|scared|anxious|concerned)\s+(?:about|for)\s+(?:my|our|personal)\s+safety\b",
    r"\bthreat\s+to\s+(?:my|our|personal)\s+safety\b",
    r"\bfear\s+for\s+(?:my|my\s+own)\s+safety\b",
    r"\bconcern\s+(?:about|for)\s+(?:my|our|personal)\s+safety\b",
    # Hindi
    r"अपनी सुरक्षा की (?:चिंता|फ़िक्र|फिक्र)",
    r"सुरक्षा को लेकर चिंतित",
    r"सुरक्षा को खतरा",
    r"मेरी सुरक्षा पर खतरा",
    # Hinglish
    r"meri safety ki chinta",
    r"apni safety ko lekar",
    r"safety ko khatra",
    # Marathi
    r"माझ्या सुरक्षेची काळजी",
    r"सुरक्षेबद्दल भीती",
    r"सुरक्षेला धोका",
]

PATTERNS_ACUTE_IMMEDIATE_THREAT = [
    # English
    r"\bimmediate\s+danger\b",
    r"\bserious\s+threat\b",
    r"\bcannot\s+stay\s+safe\b",
    r"\blife\s+is\s+in\s+danger\b",
    r"\blife\s+in\s+danger\b",
    r"\bextreme\s+danger\b",
    r"\bimmediate\s+protection\b",
    # Hindi
    r"तत्काल खतरा",
    r"गंभीर खतरा",
    r"जान को खतरा",
    r"जीवाला धोका",
    # Hinglish
    r"immediate danger",
    r"serious threat",
    r"jaan ko khatra",
    # Marathi
    r"तातडीने धोका",
    r"जीवाला धोका",
    r"गंभीर धोका",
]


class ContextualSafetyAnalyzer:
    """
    Context-aware intermediate safety understanding analyzer.
    Evaluates safety polarity, concept paraphrases, and context across
    English, Hindi, Hinglish, and Marathi without fragile keyword-only matching.
    """

    def __init__(self):
        # Precompile regular expressions with case-insensitivity
        self._rx_affirmative = [re.compile(p, re.IGNORECASE) for p in AFFIRMATIVE_SAFE_PATTERNS]
        self._rx_inability = [re.compile(p, re.IGNORECASE) for p in PATTERNS_PERSONAL_SAFETY_INABILITY]
        self._rx_feeling_unsafe = [re.compile(p, re.IGNORECASE) for p in PATTERNS_FEELING_UNSAFE]
        self._rx_concern = [re.compile(p, re.IGNORECASE) for p in PATTERNS_PERSONAL_SAFETY_CONCERN]
        self._rx_acute = [re.compile(p, re.IGNORECASE) for p in PATTERNS_ACUTE_IMMEDIATE_THREAT]

    def _has_preceding_negation(self, text: str, pos: int) -> bool:
        """Check if negation word appears in the 4-word window before a match position."""
        prefix = text[:pos].strip()
        tokens = re.findall(r"\w+", prefix.lower())
        window = tokens[-4:] if len(tokens) >= 4 else tokens
        return any(neg in window for neg in NEGATION_WORDS)

    def analyze(self, text: str, language: str = "english") -> Dict[str, Any]:
        """
        Analyze contextual safety meaning of text.
        Returns a structured dictionary indicating polarity, concern tier,
        specific matched cues, and explainable safety indicators.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return {
                "has_safety_concern": False,
                "tier": "NONE",
                "concern_type": None,
                "is_affirmative_safe": False,
                "matched_cues": [],
                "indicators": [],
                "component_recommendations": {},
            }

        norm = cleaned.lower()

        # 1. Check for Affirmative Safe expressions
        is_affirmative_safe = False
        affirmative_matches = []
        for rx in self._rx_affirmative:
            m = rx.search(norm)
            if m:
                # Ensure no preceding negation (e.g. "not safe now" vs "safe now")
                if not self._has_preceding_negation(norm, m.start()):
                    is_affirmative_safe = True
                    affirmative_matches.append(m.group(0))

        # 2. Check for Acute / Immediate Crisis Threats (Tier B -> CRITICAL Pathway)
        acute_matches = []
        for rx in self._rx_acute:
            m = rx.search(norm)
            if m:
                acute_matches.append(m.group(0))

        # 3. Check for Personal Safety Inability (Tier A -> Meaningful Concern / HIGH)
        inability_matches = []
        for rx in self._rx_inability:
            m = rx.search(norm)
            if m:
                inability_matches.append(m.group(0))

        # 4. Check for Feeling Unsafe / Negated Safety (Tier A -> Meaningful Concern / HIGH)
        unsafe_matches = []
        for rx in self._rx_feeling_unsafe:
            m = rx.search(norm)
            if m:
                unsafe_matches.append(m.group(0))

        # 5. Check for General Personal Safety Concerns
        concern_matches = []
        for rx in self._rx_concern:
            m = rx.search(norm)
            if m:
                concern_matches.append(m.group(0))

        # If affirmative safe and no conflicting safety concerns were detected
        if is_affirmative_safe and not (acute_matches or inability_matches or unsafe_matches or concern_matches):
            return {
                "has_safety_concern": False,
                "tier": "SAFE_AFFIRMATION",
                "concern_type": "affirmative_safe",
                "is_affirmative_safe": True,
                "matched_cues": affirmative_matches,
                "indicators": ["Affirmative safe expression detected (no safety escalation)"],
                "component_recommendations": {
                    "safety_override": 0,
                    "human_review": False,
                },
            }

        # Resolve Acute / Strong Immediate Threats (CRITICAL)
        if acute_matches:
            return {
                "has_safety_concern": True,
                "tier": "CRITICAL_ACUTE",
                "concern_type": "immediate_danger_threat",
                "is_affirmative_safe": False,
                "matched_cues": acute_matches,
                "indicators": [
                    "Safety concern indicators",
                    "Immediate threat or acute safety danger detected",
                ],
                "component_recommendations": {
                    "stress_floor": 55,
                    "vulnerability_floor": 88,
                    "urgency_floor": 88,
                    "safety_floor": 96,
                    "human_review": True,
                    "safety_flag": True,
                },
            }

        # Resolve Meaningful Contextual Safety Concerns (HIGH)
        # Covers: Inability to keep self safe, feeling unsafe, fear for personal safety
        meaningful_cues = inability_matches + unsafe_matches + concern_matches
        if meaningful_cues:
            primary_type = "personal_safety_inability" if inability_matches else (
                "feeling_unsafe" if unsafe_matches else "personal_safety_concern"
            )

            indicators = ["Safety concern indicators"]
            if inability_matches:
                indicators.append("Apprehension or inability to maintain personal safety")
            elif unsafe_matches:
                indicators.append("Contextual feeling of being unsafe")
            else:
                indicators.append("Personal safety concern or fear identified")

            indicators.append("Contextual safety concern detected (human review required)")

            return {
                "has_safety_concern": True,
                "tier": "HIGH_MEANINGFUL",
                "concern_type": primary_type,
                "is_affirmative_safe": False,
                "matched_cues": meaningful_cues,
                "indicators": indicators,
                "component_recommendations": {
                    "stress_floor": 54,           # Expression of anxiety/worry
                    "vulnerability_floor": 64,    # Inability to self-protect = elevated vulnerability
                    "urgency_floor": 42,          # Active safety concern requiring prompt human attention
                    "safety_floor": 76,           # Contextual safety concern floor
                    "human_review": True,
                    "safety_flag": True,
                },
            }

        # Baseline: No specific safety cues detected
        return {
            "has_safety_concern": False,
            "tier": "NONE",
            "concern_type": None,
            "is_affirmative_safe": False,
            "matched_cues": [],
            "indicators": [],
            "component_recommendations": {},
        }


# Singleton service instance
contextual_safety_analyzer = ContextualSafetyAnalyzer()
