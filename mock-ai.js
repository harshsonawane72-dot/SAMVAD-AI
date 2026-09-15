/**
 * SAMVAD AI — Prototype rule-based SVI analysis engine (local only)
 *
 * IMPORTANT:
 * - Not a clinical or psychological assessment tool.
 * - Not clinically validated.
 * - Decision-support signals for trained human operators only.
 * - All processing stays in the browser (no external APIs).
 * - Weights and thresholds are PROTOTYPE VALUES ONLY.
 */

const MockAI = (function () {
  "use strict";

  /** Prototype component weights for the SVI formula */
  const WEIGHTS = {
    stress: 0.3,
    vulnerability: 0.3,
    urgency: 0.25,
    safetyConcern: 0.15,
  };

  /** Prototype risk thresholds (SVI 0–100) */
  const RISK_THRESHOLDS = [
    { level: "LOW", min: 0, max: 24 },
    { level: "MODERATE", min: 25, max: 49 },
    { level: "HIGH", min: 50, max: 74 },
    { level: "CRITICAL", min: 75, max: 100 },
  ];

  /**
   * Explainable keyword / phrase banks.
   * Includes English + Hindi Devanagari + common Hinglish romanizations
   * so SIH demo statements produce transparent, inspectable matches.
   */
  const SIGNAL_BANKS = {
    stress: [
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
    vulnerability: [
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
    urgency: [
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
    safety: [
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
  };

  /** Phrases that always raise an independent safety review flag */
  const STRONG_SAFETY_PHRASES = [
    "not safe",
    "unsafe",
    "immediate danger",
    "serious threat",
    "cannot stay safe",
    "मुझे सुरक्षित महसूस नहीं हो रहा",
    "तत्काल खतरा",
    "safe feel nahi",
    "safe feel nahi ho",
  ];

  const RECOMMENDATIONS = {
    LOW: "Information and general support",
    MODERATE: "Counselling / support referral recommended",
    HIGH: "Priority human review and appropriate counselling/legal support referral",
    CRITICAL:
      "Immediate human review and appropriate emergency/protection support pathway",
  };

  const INDICATOR_LABELS = {
    stress: "Elevated stress indicators",
    vulnerability: "Vulnerability indicators",
    urgency: "Urgency indicators",
    safety: "Safety concern indicators",
    fearPressure: "Fear or pressure indicators",
  };

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function roundScore(value) {
    return Math.round(clamp(value, 0, 100));
  }

  /**
   * Find unique phrase matches (longest phrases checked first to reduce
   * double-counting nested phrases such as "urgent" inside "urgent help").
   */
  function findMatches(normalizedText, phrases) {
    var sorted = phrases.slice().sort(function (a, b) {
      return b.length - a.length;
    });
    var matched = [];
    var consumed = normalizedText;

    sorted.forEach(function (phrase) {
      var needle = phrase.toLowerCase();
      if (!needle) return;
      if (consumed.indexOf(needle) === -1) return;
      matched.push(phrase);
      // Soft-consume: replace first occurrence so nested shorter terms count less often
      consumed = consumed.replace(needle, " ");
    });

    return matched;
  }

  /**
   * Convert unique match count → 0–100 component score.
   * Diminishing returns + hard cap keep repeated wording from inflating scores.
   */
  function scoreFromMatchCount(count) {
    if (count <= 0) return 0;
    // Prototype curve: 1 signal ≈ low-moderate cue; several distinct signals escalate faster.
    var points = [0, 32, 54, 70, 82, 90, 95, 98];
    if (count < points.length) return points[count];
    return 100;
  }

  const CONTEXTUAL_SAFETY = {
    affirmative: [
      /\bi (?:feel|am|stay|remain) safe\b/i,
      /\bfeeling safe\b/i,
      /\bcompletely safe\b/i,
      /\bsafe and sound\b/i,
      /\bin a safe place\b/i,
      /\bkept safe\b/i,
      /\bi am now safe\b/i,
      /\bfeel safe now\b/i,
      /\bnow feel safe\b/i,
      /\bsafe now\b/i,
      /सुरक्षित महसूस (?:हो|कर) रहा/i,
      /अब सुरक्षित (?:हूँ|हुँ|हैं)/i,
      /सुरक्षित स्थान पर/i,
      /पूरी तरह सुरक्षित/i,
      /\bab safe (?:hoon|hun|hai|feel)\b/i,
      /\bsafe feel ho raha\b/i,
      /\bab safe lag raha\b/i,
      /आता सुरक्षित वाटत/i,
      /सुरक्षित आहे/i,
      /पूर्णपणे सुरक्षित/i,
    ],
    inability: [
      /(?:worried|anxious|afraid|scared|fear)\s+(?:that\s+)?(?:i\s+)?(?:may|might|will|would)?\s*(?:not\s+be\s+able|unable)\s+to\s+keep\s+(?:my\s*self|myself)\s+safe/i,
      /(?:not\s+be\s+able|unable|cannot|can't|cant)\s+to\s+keep\s+(?:my\s*self|myself)\s+safe/i,
      /(?:not\s+be\s+able|unable|cannot|can't|cant)\s+to\s+(?:stay|remain)\s+safe/i,
      /(?:not\s+be\s+able|unable|cannot|can't|cant)\s+to\s+protect\s+(?:my\s*self|myself)/i,
      /(?:hard|difficult|impossible)\s+to\s+keep\s+(?:my\s*self|myself)\s+safe/i,
      /(?:fear|worry|worried)\s+(?:about|for)\s+(?:my\s*self\s+being\s+safe|keeping\s+myself\s+safe)/i,
      /खुद को सुरक्षित नहीं (?:रख|पा)/i,
      /सुरक्षित नहीं रख (?:सकता|सकती|पाऊँगा|पाऊंगा|पाऊंगी)/i,
      /सुरक्षित नहीं रह (?:सकता|सकती)/i,
      /स्वयं की (?:रक्षा|सुरक्षा) नहीं/i,
      /अपनी (?:सुरक्षा|हिफाजत) नहीं कर/i,
      /khud ko safe nahi rakh/i,
      /safe nahi reh (?:sakta|sakti)/i,
      /khud ko safe nahi rakh (?:paunga|paungi|sakta|sakti)/i,
      /apne aap ko safe nahi/i,
      /स्वतःला सुरक्षित ठेवू शकत नाही/i,
      /स्वतःला सुरक्षित ठेवू शकणार नाही/i,
      /स्वतःचे रक्षण करू शकत नाही/i,
      /सुरक्षित राहू शकत नाही/i,
    ],
    feelingUnsafe: [
      /\b(?:don't|dont|do not|doesn't|does not|cannot|can't|not)\s+feel\s+safe\b/i,
      /\b(?:feeling|feel|feels)\s+unsafe\b/i,
      /\bnot\s+feeling\s+safe\b/i,
      /\bnowhere\s+is\s+safe\b/i,
      /\bno\s+longer\s+safe\b/i,
      /सुरक्षित महसूस नहीं हो रहा/i,
      /सुरक्षित नहीं लग रहा/i,
      /असुरक्षित महसूस/i,
      /सुरक्षित नहीं हूँ/i,
      /safe feel nahi/i,
      /safe nahi lag raha/i,
      /unsafe feel/i,
      /safe nahi hoon/i,
      /सुरक्षित वाटत नाही/i,
      /असुरक्षित वाटत आहे/i,
      /सुरक्षित वाटत नाहीये/i,
    ],
    concern: [
      /\b(?:worried|worry|fear|scared|anxious|concerned)\s+(?:about|for)\s+(?:my|our|personal)\s+safety\b/i,
      /\bthreat\s+to\s+(?:my|our|personal)\s+safety\b/i,
      /\bfear\s+for\s+(?:my|my\s+own)\s+safety\b/i,
      /\bconcern\s+(?:about|for)\s+(?:my|our|personal)\s+safety\b/i,
      /अपनी सुरक्षा की (?:चिंता|फ़िक्र|फिक्र)/i,
      /सुरक्षा को लेकर चिंतित/i,
      /सुरक्षा को खतरा/i,
      /मेरी सुरक्षा पर खतरा/i,
      /meri safety ki chinta/i,
      /apni safety ko lekar/i,
      /safety ko khatra/i,
      /माझ्या सुरक्षेची काळजी/i,
      /सुरक्षेबद्दल भीती/i,
      /सुरक्षेला धोका/i,
    ],
    acute: [
      /\bimmediate\s+danger\b/i,
      /\bserious\s+threat\b/i,
      /\bcannot\s+stay\s+safe\b/i,
      /\blife\s+is\s+in\s+danger\b/i,
      /\blife\s+in\s+danger\b/i,
      /\bextreme\s+danger\b/i,
      /\bimmediate\s+protection\b/i,
      /तत्काल खतरा/i,
      /गंभीर खतरा/i,
      /जान को खतरा/i,
      /जीवाला धोका/i,
      /immediate danger/i,
      /serious threat/i,
      /jaan ko khatra/i,
      /तातडीने धोका/i,
      /जीवाला धोका/i,
      /गंभीर धोका/i,
    ],
  };

  function evaluateContextualSafety(text) {
    var cleaned = String(text || "").trim();
    if (!cleaned) {
      return { hasSafetyConcern: false, isAffirmativeSafe: false, indicators: [] };
    }
    var norm = cleaned.toLowerCase();
    var negationWords = ["not", "don't", "dont", "cannot", "can't", "cant", "unable", "never", "no", "nahi", "nahin", "na", "नाही", "नाहीत"];

    var isAffirmative = false;
    CONTEXTUAL_SAFETY.affirmative.forEach(function (rx) {
      var m = rx.exec(norm);
      if (m) {
        var prefix = norm.substring(0, m.index).trim();
        var tokens = prefix.split(/\s+/);
        var windowTokens = tokens.slice(Math.max(0, tokens.length - 4));
        var hasNeg = windowTokens.some(function (w) { return negationWords.indexOf(w) !== -1; });
        if (!hasNeg) isAffirmative = true;
      }
    });

    var acuteHits = CONTEXTUAL_SAFETY.acute.some(function (rx) { return rx.test(norm); });
    var inabilityHits = CONTEXTUAL_SAFETY.inability.some(function (rx) { return rx.test(norm); });
    var unsafeHits = CONTEXTUAL_SAFETY.feelingUnsafe.some(function (rx) { return rx.test(norm); });
    var concernHits = CONTEXTUAL_SAFETY.concern.some(function (rx) { return rx.test(norm); });

    if (isAffirmative && !(acuteHits || inabilityHits || unsafeHits || concernHits)) {
      return {
        hasSafetyConcern: false,
        tier: "SAFE_AFFIRMATION",
        isAffirmativeSafe: true,
        indicators: ["Affirmative safe expression detected (no safety escalation)"],
        recommendations: { safetyOverride: 0 }
      };
    }

    if (acuteHits) {
      return {
        hasSafetyConcern: true,
        tier: "CRITICAL_ACUTE",
        concernType: "immediate_danger_threat",
        isAffirmativeSafe: false,
        indicators: ["Safety concern indicators", "Immediate threat or acute safety danger detected"],
        recommendations: { stressFloor: 55, vulnFloor: 88, urgencyFloor: 88, safetyFloor: 96 }
      };
    }

    if (inabilityHits || unsafeHits || concernHits) {
      var primaryType = inabilityHits ? "personal_safety_inability" : (unsafeHits ? "feeling_unsafe" : "personal_safety_concern");
      var indicators = ["Safety concern indicators"];
      if (inabilityHits) {
        indicators.push("Apprehension or inability to maintain personal safety");
      } else if (unsafeHits) {
        indicators.push("Contextual feeling of being unsafe");
      } else {
        indicators.push("Personal safety concern or fear identified");
      }
      indicators.push("Contextual safety concern detected (human review required)");

      return {
        hasSafetyConcern: true,
        tier: "HIGH_MEANINGFUL",
        concernType: primaryType,
        isAffirmativeSafe: false,
        indicators: indicators,
        recommendations: { stressFloor: 54, vulnFloor: 64, urgencyFloor: 42, safetyFloor: 76 }
      };
    }

    return { hasSafetyConcern: false, isAffirmativeSafe: false, indicators: [] };
  }

  /**
   * Small contextual boosts when signal categories co-occur.
   * Strong safety phrases also raise minimum floors (still explainable / capped).
   */
  function applyContextualAdjustments(scores, matches, strongSafetyHit, contextualSafety) {
    var adjustments = [];
    var next = {
      stress: scores.stress,
      vulnerability: scores.vulnerability,
      urgency: scores.urgency,
      safetyConcern: scores.safetyConcern,
    };

    if (matches.stress.length && matches.vulnerability.length) {
      next.stress += 10;
      next.vulnerability += 10;
      adjustments.push(
        "Stress + vulnerability co-occurrence (+10 each, prototype)"
      );
    }

    var hasSafetySignal = matches.safety.length > 0 || (contextualSafety && contextualSafety.hasSafetyConcern);
    if (matches.urgency.length && hasSafetySignal) {
      next.urgency += 12;
      next.safetyConcern += 14;
      adjustments.push(
        "Urgency + safety co-occurrence (+12 urgency, +14 safety, prototype)"
      );
    }

    if (matches.stress.length >= 2) {
      next.stress += 8;
      adjustments.push("Multiple distinct stress signals (+8, prototype)");
    }

    if (matches.vulnerability.length >= 2) {
      next.vulnerability += 8;
      adjustments.push(
        "Multiple distinct vulnerability signals (+8, prototype)"
      );
    }

    // Contextual safety floors
    if (contextualSafety && contextualSafety.hasSafetyConcern && contextualSafety.recommendations) {
      var rec = contextualSafety.recommendations;
      var cType = contextualSafety.concernType || "contextual_safety";
      if (rec.stressFloor && next.stress < rec.stressFloor) {
        next.stress = rec.stressFloor;
        adjustments.push("Contextual safety stress floor applied (stress ≥ " + rec.stressFloor + ", " + cType + ")");
      }
      if (rec.vulnFloor && next.vulnerability < rec.vulnFloor) {
        next.vulnerability = rec.vulnFloor;
        adjustments.push("Contextual safety vulnerability floor applied (vulnerability ≥ " + rec.vulnFloor + ", " + cType + ")");
      }
      if (rec.urgencyFloor && next.urgency < rec.urgencyFloor) {
        next.urgency = rec.urgencyFloor;
        adjustments.push("Contextual safety urgency floor applied (urgency ≥ " + rec.urgencyFloor + ", " + cType + ")");
      }
      if (rec.safetyFloor && next.safetyConcern < rec.safetyFloor) {
        next.safetyConcern = rec.safetyFloor;
        adjustments.push("Contextual safety concern floor applied (safety ≥ " + rec.safetyFloor + ", " + cType + ")");
      }
    }

    // Strong safety language elevates floors independently of overall SVI class.
    if (strongSafetyHit) {
      if (next.safetyConcern < 96) {
        next.safetyConcern = 96;
        adjustments.push(
          "Strong safety phrase floor applied (safety ≥ 96, prototype)"
        );
      }
      if (next.urgency < 88) {
        next.urgency = 88;
        adjustments.push(
          "Strong safety context urgency floor (urgency ≥ 88, prototype)"
        );
      }
      if (next.vulnerability < 88) {
        next.vulnerability = 88;
        adjustments.push(
          "Strong safety context vulnerability floor (vulnerability ≥ 88, prototype)"
        );
      }
      if (next.stress < 55) {
        next.stress = 55;
        adjustments.push(
          "Strong safety context stress floor (stress ≥ 55, prototype)"
        );
      }
    }

    if (contextualSafety && contextualSafety.isAffirmativeSafe && !strongSafetyHit) {
      next.safetyConcern = 0;
      adjustments.push("Affirmative safe expression: safety escalation suppressed");
    }

    next.stress = roundScore(next.stress);
    next.vulnerability = roundScore(next.vulnerability);
    next.urgency = roundScore(next.urgency);
    next.safetyConcern = roundScore(next.safetyConcern);

    return { scores: next, adjustments: adjustments };
  }

  function classifyRisk(svi) {
    var level = "LOW";
    RISK_THRESHOLDS.forEach(function (band) {
      if (svi >= band.min && svi <= band.max) level = band.level;
    });
    return level;
  }

  function buildIndicators(matches) {
    var indicators = [];
    if (matches.stress.length) indicators.push(INDICATOR_LABELS.stress);
    if (
      matches.stress.some(function (m) {
        return /fear|scared|pressure|डर|दबाव/i.test(m);
      })
    ) {
      indicators.push(INDICATOR_LABELS.fearPressure);
    }
    if (matches.vulnerability.length) {
      indicators.push(INDICATOR_LABELS.vulnerability);
    }
    if (matches.urgency.length) indicators.push(INDICATOR_LABELS.urgency);
    if (matches.safety.length) indicators.push(INDICATOR_LABELS.safety);

    // De-duplicate while preserving order
    return indicators.filter(function (item, index, arr) {
      return arr.indexOf(item) === index;
    });
  }

  /**
   * Analyze a complainant statement locally.
   * @param {string} statementText
   * @param {{ language?: string }=} options
   * @returns {object} explainable prototype result
   */
  function analyze(statementText, options) {
    options = options || {};
    var text = String(statementText || "").trim();
    var normalized = text
      .toLowerCase()
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[\u201C\u201D]/g, '"');

    if (!text) {
      return {
        ok: false,
        error: "Please enter a statement before analysis.",
      };
    }

    var ctxSafety = evaluateContextualSafety(text);

    var matches = {
      stress: findMatches(normalized, SIGNAL_BANKS.stress),
      vulnerability: findMatches(normalized, SIGNAL_BANKS.vulnerability),
      urgency: findMatches(normalized, SIGNAL_BANKS.urgency),
      safety: findMatches(normalized, SIGNAL_BANKS.safety),
    };

    if (ctxSafety.isAffirmativeSafe) {
      matches.safety = [];
    }

    var strongSafetyHit = STRONG_SAFETY_PHRASES.some(function (phrase) {
      return normalized.indexOf(phrase.toLowerCase()) !== -1;
    }) || ctxSafety.tier === "CRITICAL_ACUTE";

    var baseScores = {
      stress: scoreFromMatchCount(matches.stress.length),
      vulnerability: scoreFromMatchCount(matches.vulnerability.length),
      urgency: scoreFromMatchCount(matches.urgency.length),
      safetyConcern: scoreFromMatchCount(matches.safety.length),
    };

    var adjusted = applyContextualAdjustments(
      baseScores,
      matches,
      strongSafetyHit,
      ctxSafety
    );
    var components = adjusted.scores;

    var sviRaw =
      components.stress * WEIGHTS.stress +
      components.vulnerability * WEIGHTS.vulnerability +
      components.urgency * WEIGHTS.urgency +
      components.safetyConcern * WEIGHTS.safetyConcern;
    var svi = roundScore(sviRaw);
    var riskLevel = classifyRisk(svi);

    // Independent of overall SVI — safety phrases always escalate human review
    var immediateHumanReview =
      strongSafetyHit ||
      matches.safety.length > 0 ||
      Boolean(ctxSafety.hasSafetyConcern) ||
      riskLevel === "CRITICAL";

    if (ctxSafety.isAffirmativeSafe && !strongSafetyHit) {
      immediateHumanReview = false;
    }

    var indicators = buildIndicators(matches);
    if (ctxSafety.indicators && ctxSafety.indicators.length) {
      ctxSafety.indicators.forEach(function (ind) {
        if (indicators.indexOf(ind) === -1) indicators.push(ind);
      });
    }
    if (!indicators.length) {
      indicators.push("No strong prototype signals detected in the statement");
    }

    return {
      ok: true,
      language: options.language || "english",
      components: components,
      baseScores: baseScores,
      matches: matches,
      svi: svi,
      riskLevel: riskLevel,
      indicators: indicators,
      recommendation: RECOMMENDATIONS[riskLevel],
      immediateHumanReview: immediateHumanReview,
      safetyFlagMessage: immediateHumanReview
        ? "Immediate human review recommended."
        : null,
      contextualAdjustments: adjusted.adjustments,
      contextualSafety: ctxSafety,
      explainability: {
        formula:
          "SVI = Stress (30%) + Vulnerability (30%) + Urgency (25%) + Safety Concern (15%)",
        weights: WEIGHTS,
        thresholds: RISK_THRESHOLDS,
        prototypeNotice:
          "Prototype scoring model — requires expert validation before real-world deployment.",
        method:
          "Local keyword/phrase matching with capped component scores and small co-occurrence adjustments. Not a clinical diagnosis.",
      },
      humanInTheLoop: {
        principle: "AI assists. Humans decide.",
        note: "This prototype provides decision-support signals only. Final assessment and support decisions must be made by trained human personnel.",
      },
      privacyNote:
        "Prototype demo only. Do not enter real personal, medical, legal or identifying information.",
    };
  }

  return {
    analyze: analyze,
    WEIGHTS: WEIGHTS,
    RISK_THRESHOLDS: RISK_THRESHOLDS,
  };
})();
