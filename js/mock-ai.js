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
      "worried",
      "stress",
      "stressed",
      "pressure",
      "overwhelmed",
      "anxious",
      "fear",
      "scared",
      "परेशान",
      "तनाव",
      "डर",
      "घबराहट",
      "दबाव",
    ],
    vulnerability: [
      "alone",
      "helpless",
      "unable to cope",
      "vulnerable",
      "dependent",
      "no support",
      "isolated",
      "अकेला",
      "असहाय",
      "मदद नहीं",
      "कोई साथ नहीं",
      "कमजोर",
      // Hinglish / demo synonyms (prototype)
      "akela",
      "akeli",
      "asahay",
      "handle nahi",
      "support chahiye",
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
      // Hinglish / demo synonyms (prototype)
      "immediate help",
      "immediate",
      "jaldi",
      "abhi",
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
      // Hinglish / demo synonyms (prototype)
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

  /**
   * Small contextual boosts when signal categories co-occur.
   * Strong safety phrases also raise minimum floors (still explainable / capped).
   */
  function applyContextualAdjustments(scores, matches, strongSafetyHit) {
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

    if (matches.urgency.length && matches.safety.length) {
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
    var normalized = text.toLowerCase();

    if (!text) {
      return {
        ok: false,
        error: "Please enter a statement before analysis.",
      };
    }

    var matches = {
      stress: findMatches(normalized, SIGNAL_BANKS.stress),
      vulnerability: findMatches(normalized, SIGNAL_BANKS.vulnerability),
      urgency: findMatches(normalized, SIGNAL_BANKS.urgency),
      safety: findMatches(normalized, SIGNAL_BANKS.safety),
    };

    var strongSafetyHit = STRONG_SAFETY_PHRASES.some(function (phrase) {
      return normalized.indexOf(phrase.toLowerCase()) !== -1;
    });

    var baseScores = {
      stress: scoreFromMatchCount(matches.stress.length),
      vulnerability: scoreFromMatchCount(matches.vulnerability.length),
      urgency: scoreFromMatchCount(matches.urgency.length),
      safetyConcern: scoreFromMatchCount(matches.safety.length),
    };

    var adjusted = applyContextualAdjustments(
      baseScores,
      matches,
      strongSafetyHit
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
      riskLevel === "CRITICAL";

    var indicators = buildIndicators(matches);
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
