/**
 * SAMVAD AI — Assessment page UI logic
 * Calls MockAI.analyze() from mock-ai.js. No scoring logic here.
 */

(function initAssessmentPage() {
  "use strict";

  const form = document.querySelector("#assessment-form");
  if (!form) return;

  if (typeof MockAI === "undefined" || !MockAI.analyze) {
    console.error("MockAI engine not loaded. Include mock-ai.js before assessment.js.");
    return;
  }

  const caseIdEl = document.querySelector("#case-id");
  const caseDatetimeEl = document.querySelector("#case-datetime");
  const caseStatusEl = document.querySelector("#case-status");
  const statementInput = document.querySelector("#statement-input");
  const statementCount = document.querySelector("#statement-count");
  const consentCheckbox = document.querySelector("#consent-checkbox");
  const analyzeBtn = document.querySelector("#analyze-btn");
  const feedback = document.querySelector("#analysis-feedback");
  const loadingEl = document.querySelector("#analysis-loading");
  const formErrorEl = document.querySelector("#form-error");
  const resultSection = document.querySelector("#assessment-result");
  const newAssessmentBtn = document.querySelector("#new-assessment-btn");
  const reviewInputBtn = document.querySelector("#review-input-btn");
  const scenarioButtons = document.querySelectorAll("[data-scenario]");
  const statementPanel = document.querySelector("#statement-heading");

  const DEMO_STATEMENTS = {
    low: "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.",
    moderate:
      "Mujhe kaafi stress ho raha hai aur mujhe samajh nahi aa raha ki complaint ko kaise proceed karun. Mujhe support chahiye.",
    high: "Mujhe bahut fear aur pressure feel ho raha hai. Mujhe lag raha hai ki main is situation ko akela handle nahi kar pa raha/rahi. Mujhe jaldi support chahiye.",
    critical:
      "Mujhe abhi safe feel nahi ho raha. Mujhe immediate help chahiye aur main situation ko akela handle nahi kar sakta/sakti.",
  };

  const RISK_EXPLANATIONS = {
    LOW: "Limited vulnerability signals detected. General information and support may be appropriate.",
    MODERATE:
      "Some stress or vulnerability signals detected. Additional human support may be appropriate.",
    HIGH: "Elevated vulnerability signals detected. Priority human review is recommended.",
    CRITICAL:
      "Strong safety or vulnerability signals detected. Immediate human review is recommended.",
  };

  const maxChars = Number(statementInput.getAttribute("maxlength")) || 4000;
  let analysisTimer = null;
  let currentCaseId = "";

  // SVG ring geometry (r = 52)
  var RING_RADIUS = 52;
  var RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

  function createDemoCaseId() {
    var n = 1000 + Math.floor(Math.random() * 9000);
    return "NHAA-2026-" + n;
  }

  function formatDateTime(date) {
    try {
      return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
    } catch (err) {
      return date.toLocaleString();
    }
  }

  function detectStatementLanguage(text) {
    var cleaned = String(text || "").trim();
    if (!cleaned) return null;

    // Check for Devanagari script characters (\u0900-\u097F)
    var devanagariMatches = cleaned.match(/[\u0900-\u097F]/g);
    var devanagariCount = devanagariMatches ? devanagariMatches.length : 0;

    if (devanagariCount >= 3 || devanagariCount / cleaned.length > 0.15) {
      // Differentiate Marathi from Hindi using distinct grammatical words
      var devanagariWords = cleaned.split(/[\s,।!?.:;()"'—\-\/]+/);
      var marathiMarkers = [
        "मला", "आहे", "नाही", "नाहीत", "तक्रार", "हवी", "हवे", "माझ्या", "करायचे",
        "होते", "केले", "सांगितले", "खूप", "काही", "येत", "कसे",
        "काय", "आम्ही", "त्यांना", "त्यांच्या", "झाले", "झाली", "करतो", "करते",
        "शकतो", "शकत", "मदत"
      ];
      var isMarathi = marathiMarkers.some(function (marker) {
        return devanagariWords.indexOf(marker) !== -1;
      });
      if (isMarathi) {
        return { code: "mr", label: "Marathi" };
      }
      return { code: "hi", label: "Hindi" };
    }

    // Latin text: check for Hindi/Hinglish keywords vs English
    var hinglishMarkers =
      /\b(mujhe|apni|chahiye|hoon|hun|hai|hain|nahi|nahin|kaafi|madad|samajh|karein|kare|raha|rahi|pareshan|bahut|akela|akeli|sakta|sakti|dar|dabav|thoda|kuch|kya|kyun|aap|mera|meri|mere)\b/i;
    if (hinglishMarkers.test(cleaned)) {
      return { code: "hi", label: "Hindi" };
    }

    // Standard Latin English
    if (/[a-zA-Z]/.test(cleaned)) {
      return { code: "en", label: "English" };
    }

    return null;
  }

  function currentLanguage() {
    var detected = detectStatementLanguage(statementInput ? statementInput.value : "");
    return detected ? detected.label.toLowerCase() : "english";
  }

  var BACKEND_API_BASE =
    (typeof window !== "undefined" && window.SAMVAD_API_BASE_URL)
      ? window.SAMVAD_API_BASE_URL
      : "http://127.0.0.1:8000";

  // Automatic language detection is designed as a multilingual architecture. Actual supported languages depend on the configured language-identification, speech-recognition, and text-understanding models/services. The prototype must never claim unsupported universal language coverage.
  function detectLanguageRemote(text) {
    var cleaned = String(text || "").trim();
    if (!cleaned) {
      return Promise.resolve(null);
    }
    return fetch(BACKEND_API_BASE + "/ai/detect-language", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: cleaned }),
    })
      .then(function (res) {
        if (!res.ok) return null;
        return res.json();
      })
      .then(function (data) {
        if (data) {
          if (data.status === "success") {
            return {
              status: "success",
              code: data.language_code,
              label: data.language_name,
              confidence: data.confidence,
              method: data.detection_method,
            };
          }
          if (
            data.status === "unknown" ||
            data.language_code === "unknown" ||
            data.status === "mixed" ||
            data.language_code === "mixed"
          ) {
            return {
              status: data.status,
              code: data.language_code,
              label: data.language_name || "Unknown / Mixed",
              confidence: data.confidence || 0,
              method: data.detection_method,
            };
          }
        }
        return detectStatementLanguage(cleaned);
      })
      .catch(function () {
        return detectStatementLanguage(cleaned);
      });
  }

  function updateCharCount() {
    var len = statementInput.value.length;
    statementCount.textContent = len + " / " + maxChars + " characters";
    statementCount.classList.toggle("is-near-limit", len >= maxChars * 0.9);
  }

  function updateAnalyzeState() {
    var hasText = statementInput.value.trim().length > 0;
    var hasConsent = consentCheckbox.checked;
    analyzeBtn.disabled = !(hasText && hasConsent);
  }

  function setScenarioActive(activeBtn) {
    scenarioButtons.forEach(function (btn) {
      btn.classList.toggle("is-active", btn === activeBtn);
    });
  }

  function showFormError(message) {
    if (!formErrorEl) return;
    if (!message) {
      formErrorEl.hidden = true;
      formErrorEl.textContent = "";
      return;
    }
    formErrorEl.hidden = false;
    formErrorEl.textContent = message;
  }

  function showLoading(isLoading) {
    form.setAttribute("aria-busy", isLoading ? "true" : "false");
    if (isLoading) {
      feedback.hidden = false;
      loadingEl.hidden = false;
      if (resultSection) resultSection.hidden = true;
    } else {
      loadingEl.hidden = true;
    }
  }

  function riskClass(level) {
    return "risk-" + String(level || "LOW").toLowerCase();
  }

  function renderMatchList(matches) {
    var parts = [];
    if (!matches) {
      parts.push("Evaluated via full end-to-end AI assessment pipeline.");
      return parts;
    }
    if (matches.stress && matches.stress.length) {
      parts.push("Stress: " + matches.stress.join(", "));
    }
    if (matches.vulnerability && matches.vulnerability.length) {
      parts.push("Vulnerability: " + matches.vulnerability.join(", "));
    }
    if (matches.urgency && matches.urgency.length) {
      parts.push("Urgency: " + matches.urgency.join(", "));
    }
    if (matches.safety && matches.safety.length) {
      parts.push("Safety: " + matches.safety.join(", "));
    }
    if (!parts.length) {
      parts.push("No keyword/phrase matches in the prototype signal banks.");
    }
    return parts;
  }

  function setBar(barEl, trackEl, value) {
    var score = Math.max(0, Math.min(100, Number(value) || 0));
    if (barEl) {
      barEl.style.width = score + "%";
    }
    if (trackEl) {
      trackEl.setAttribute("aria-valuenow", String(score));
    }
  }

  function setSviRing(score) {
    var ring = document.querySelector("#svi-ring-progress");
    var ringValue = document.querySelector("#svi-ring-value");
    var clamped = Math.max(0, Math.min(100, Number(score) || 0));
    if (ringValue) ringValue.textContent = String(clamped);
    if (!ring) return;
    ring.style.strokeDasharray = String(RING_CIRCUMFERENCE);
    var offset = RING_CIRCUMFERENCE * (1 - clamped / 100);
    ring.style.strokeDashoffset = String(offset);
  }

  function weightedContribution(score, weight) {
    return Math.round(score * weight * 10) / 10;
  }

  function renderResult(result, detectedLang) {
    if (!resultSection) return;

    document.querySelector("#result-case-id").textContent = currentCaseId;
    var statusEl = document.querySelector("#result-status");
    if (statusEl) {
      if (result.isLocalFallback) {
        statusEl.textContent = "Backend unavailable — prototype/local analysis mode";
      } else {
        statusEl.textContent = "AI-Assisted Preliminary Assessment";
      }
    }
    document.querySelector("#result-svi").textContent = String(result.svi);
    document.querySelector("#svi-ring-value").textContent = String(result.svi);
    setSviRing(result.svi);

    var detectedWrap = document.querySelector("#result-language-wrap");
    var detectedEl = document.querySelector("#result-detected-language");
    if (detectedWrap && detectedEl) {
      if (detectedLang) {
        var label = detectedLang.label || detectedLang.language_name || "";
        if (
          detectedLang.status === "unknown" ||
          detectedLang.code === "unknown" ||
          detectedLang.language_code === "unknown" ||
          label === "Unknown / Mixed"
        ) {
          detectedEl.textContent = "Unknown / Mixed";
          detectedWrap.hidden = false;
        } else if (label) {
          detectedEl.textContent = label;
          detectedWrap.hidden = false;
        } else {
          detectedWrap.hidden = true;
        }
      } else {
        detectedWrap.hidden = true;
      }
    }

    var riskEl = document.querySelector("#result-risk");
    riskEl.textContent = result.riskLevel;
    riskEl.className = "result-risk-badge " + riskClass(result.riskLevel);
    riskEl.setAttribute("aria-label", "Risk level " + result.riskLevel);

    var hero = document.querySelector(".svi-hero");
    if (hero) {
      hero.className = "svi-hero " + riskClass(result.riskLevel);
    }

    document.querySelector("#risk-explanation").textContent =
      result.explanation || RISK_EXPLANATIONS[result.riskLevel] || RISK_EXPLANATIONS.LOW;

    document.querySelector("#score-stress").textContent = result.components.stress;
    document.querySelector("#score-vulnerability").textContent =
      result.components.vulnerability;
    document.querySelector("#score-urgency").textContent = result.components.urgency;
    document.querySelector("#score-safety").textContent =
      result.components.safetyConcern;

    setBar(
      document.querySelector("#bar-stress"),
      document.querySelector("#track-stress"),
      result.components.stress
    );
    setBar(
      document.querySelector("#bar-vulnerability"),
      document.querySelector("#track-vulnerability"),
      result.components.vulnerability
    );
    setBar(
      document.querySelector("#bar-urgency"),
      document.querySelector("#track-urgency"),
      result.components.urgency
    );
    setBar(
      document.querySelector("#bar-safety"),
      document.querySelector("#track-safety"),
      result.components.safetyConcern
    );

    var indicatorList = document.querySelector("#indicator-list");
    indicatorList.innerHTML = "";
    result.indicators.forEach(function (item) {
      var li = document.createElement("li");
      li.className = "indicator-tag";
      li.textContent = item;
      indicatorList.appendChild(li);
    });

    document.querySelector("#support-recommendation").textContent =
      result.recommendation;

    var resourcesCard = document.querySelector("#relevant-resources-card");
    var resourcesList = document.querySelector("#resources-list");
    var resources = result.supportResources || result.support_resources || [];
    if (resourcesCard && resourcesList) {
      resourcesList.innerHTML = "";
      if (resources && resources.length > 0) {
        resources.forEach(function (res) {
          var item = document.createElement("div");
          item.className = "resource-item";
          item.style.padding = "0.75rem";
          item.style.borderRadius = "8px";
          item.style.background = "var(--color-bg-subtle, #f8fafc)";
          item.style.border = "1px solid var(--color-border, #e2e8f0)";

          var titleEl = document.createElement("h4");
          titleEl.style.margin = "0 0 0.35rem 0";
          titleEl.style.fontSize = "0.95rem";
          titleEl.style.fontWeight = "600";
          titleEl.textContent = res.title || "Support Resource";

          var badge = document.createElement("span");
          badge.className = "demo-pill";
          badge.style.fontSize = "0.7rem";
          badge.style.marginLeft = "0.5rem";
          badge.textContent = res.category ? res.category.replace(/_/g, " ") : "Resource";
          titleEl.appendChild(badge);

          var contentEl = document.createElement("p");
          contentEl.style.margin = "0 0 0.4rem 0";
          contentEl.style.fontSize = "0.85rem";
          contentEl.style.lineHeight = "1.4";
          contentEl.textContent = res.content || "";

          var srcEl = document.createElement("small");
          srcEl.style.color = "var(--color-text-muted, #64748b)";
          srcEl.textContent = "Source: " + (res.source || "Curated Knowledge Base");

          item.appendChild(titleEl);
          item.appendChild(contentEl);
          item.appendChild(srcEl);
          resourcesList.appendChild(item);
        });
        resourcesCard.hidden = false;
      } else {
        resourcesCard.hidden = true;
      }
    }

    var safetyAlert = document.querySelector("#safety-alert");
    var showSafety =
      !!result.immediateHumanReview || result.riskLevel === "CRITICAL";
    safetyAlert.hidden = !showSafety;

    var whySignals = document.querySelector("#why-signals");
    whySignals.innerHTML = "";
    renderMatchList(result.matches).forEach(function (line) {
      var li = document.createElement("li");
      li.textContent = line;
      whySignals.appendChild(li);
    });

    if (result.contextualAdjustments && result.contextualAdjustments.length) {
      result.contextualAdjustments.forEach(function (line) {
        var li = document.createElement("li");
        li.textContent = "Adjustment: " + line;
        whySignals.appendChild(li);
      });
    }

    var weights = MockAI.WEIGHTS || {
      stress: 0.3,
      vulnerability: 0.3,
      urgency: 0.25,
      safetyConcern: 0.15,
    };

    var contributions = document.querySelector("#why-contributions");
    contributions.innerHTML = "";
    [
      {
        label: "Stress score contribution",
        score: result.components.stress,
        weight: weights.stress,
      },
      {
        label: "Vulnerability score contribution",
        score: result.components.vulnerability,
        weight: weights.vulnerability,
      },
      {
        label: "Urgency score contribution",
        score: result.components.urgency,
        weight: weights.urgency,
      },
      {
        label: "Safety Concern score contribution",
        score: result.components.safetyConcern,
        weight: weights.safetyConcern,
      },
    ].forEach(function (row) {
      var li = document.createElement("li");
      li.textContent =
        row.label +
        ": " +
        row.score +
        " × " +
        row.weight.toFixed(2) +
        " = " +
        weightedContribution(row.score, row.weight);
      contributions.appendChild(li);
    });

    document.querySelector("#prototype-model-note").textContent =
      result.explainability.prototypeNotice;

    saveCaseToStore(result, detectedLang);

    var dashLink = document.querySelector("#view-dashboard-btn");
    if (dashLink) {
      dashLink.href = "dashboard.html?case=" + encodeURIComponent(currentCaseId);
    }

    feedback.hidden = true;
    resultSection.hidden = false;
    caseStatusEl.textContent = "AI-Assisted Preliminary Assessment";
    caseStatusEl.classList.add("status-analyzed");

    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function titleCaseLabel(value) {
    var map = {
      english: "English",
      hindi: "Hindi",
      marathi: "Marathi",
      voice: "Voice",
      chat: "Chat",
      portal: "Portal",
      ivrs: "IVRS",
    };
    var key = String(value || "").toLowerCase();
    return map[key] || value || "";
  }

  function selectedInteraction() {
    var checked = form.querySelector('input[name="interaction-type"]:checked');
    return checked ? checked.value : "chat";
  }

  function statementExcerpt(text) {
    var cleaned = String(text || "").trim();
    if (cleaned.length <= 280) return cleaned;
    return cleaned.slice(0, 277) + "...";
  }

  function timeOnly(date) {
    try {
      return new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(date);
    } catch (err) {
      return "";
    }
  }

  function saveCaseToStore(result, detectedLang) {
    if (typeof CaseStore === "undefined") return;
    var now = new Date();
    var datetime = formatDateTime(now);
    var langLabel = (detectedLang && (detectedLang.label || detectedLang.language_name)) || titleCaseLabel(currentLanguage());
    if (
      detectedLang &&
      (detectedLang.status === "unknown" ||
        detectedLang.code === "unknown" ||
        detectedLang.language_code === "unknown")
    ) {
      langLabel = "Unknown / Mixed";
    }
    var record = {
      caseId: currentCaseId,
      timestamp: datetime,
      createdAt: now.toISOString(),
      language: langLabel,
      interactionType: titleCaseLabel(selectedInteraction()),
      statement: statementExcerpt(statementInput.value),
      svi: result.svi,
      stress: result.components.stress,
      vulnerability: result.components.vulnerability,
      urgency: result.components.urgency,
      safety: result.components.safetyConcern,
      riskLevel: result.riskLevel,
      indicators: result.indicators.slice(),
      recommendation: result.recommendation,
      status: "New",
      humanReviewStatus: "Pending",
      supportPathway: result.recommendation,
      safetyFlag: !!result.immediateHumanReview,
      source: "assessment",
      timeline: [
        { label: "Case received", note: datetime },
        { label: "AI-assisted assessment generated", note: "Local prototype engine" },
        { label: "Human review pending", note: "Operator decision required" },
        { label: "Support pathway recommendation", note: "Advisory only" },
      ],
    };
    CaseStore.addIfNew(record);
  }

  function resetAssessment() {
    if (analysisTimer) {
      clearTimeout(analysisTimer);
      analysisTimer = null;
    }

    form.reset();
    var chat = form.querySelector('input[name="interaction-type"][value="chat"]');
    if (chat) chat.checked = true;

    var detectedWrap = document.querySelector("#result-language-wrap");
    if (detectedWrap) detectedWrap.hidden = true;

    currentCaseId = createDemoCaseId();
    caseIdEl.textContent = currentCaseId;
    caseDatetimeEl.textContent = formatDateTime(new Date());
    caseStatusEl.textContent = "Ready for Analysis";
    caseStatusEl.classList.remove("status-analyzed");

    setScenarioActive(null);
    updateCharCount();
    updateAnalyzeState();
    showFormError("");
    feedback.hidden = true;
    loadingEl.hidden = true;
    if (resultSection) resultSection.hidden = true;
    setSviRing(0);
    latestFinalConfidence = null;
    stopVoiceInput("Voice input stopped");
    updateVoiceControlsVisibility();

    form.scrollIntoView({ behavior: "smooth", block: "start" });
    statementInput.focus();
  }

  currentCaseId = createDemoCaseId();
  caseIdEl.textContent = currentCaseId;
  caseDatetimeEl.textContent = formatDateTime(new Date());
  updateCharCount();
  updateAnalyzeState();
  setSviRing(0);

  var SpeechRecognitionCtor =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;
  var voiceStartBtn = document.querySelector("#voice-start-btn");
  var voiceStopBtn = document.querySelector("#voice-stop-btn");
  var voiceStatus = document.querySelector("#voice-status");
  var voiceBox = document.querySelector("#voice-input");

  function updateVoiceControlsVisibility() {
    var interaction = selectedInteraction();
    var isVoice = interaction === "voice";
    if (voiceBox) {
      voiceBox.hidden = !isVoice;
    }
    if (!isVoice && (isListening || wantListening || (typeof isRecordingBhashini !== "undefined" && isRecordingBhashini))) {
      stopVoiceInput("Voice input stopped");
    }
  }
  var isSwitchingLanguage = false;
  var recognition = null;
  var isListening = false;
  var wantListening = false;
  var voiceRestartTimer = null;
  var voiceRestartCount = 0;
  var lastRecognitionError = "";
  var latestFinalConfidence = null;
  var lastFinalText = "";
  var lastFinalTime = 0;
  var sessionCommittedIndex = 0;
  var LOW_CONFIDENCE_THRESHOLD = 0.45;
  var MAX_VOICE_RESTARTS = 6;
  var LANG_CODES = {
    english: "en-IN",
    hindi: "hi-IN",
    marathi: "mr-IN",
  };

  function recognitionLang() {
    var detected = detectStatementLanguage(statementInput ? statementInput.value : "");
    if (detected && LANG_CODES[detected.label.toLowerCase()]) {
      return LANG_CODES[detected.label.toLowerCase()];
    }
    var navLang = (navigator.languages && navigator.languages[0]) || navigator.language || "en-IN";
    return navLang;
  }

  function setVoiceStatus(message) {
    if (!voiceStatus) return;
    voiceStatus.textContent = message || "";
    var alertText = String(message || "").toLowerCase();
    var isAlert =
      alertText.indexOf("not supported") !== -1 ||
      alertText.indexOf("denied") !== -1 ||
      alertText.indexOf("consent") !== -1 ||
      alertText.indexOf("could not") !== -1 ||
      alertText.indexOf("no microphone") !== -1 ||
      alertText.indexOf("review the transcript") !== -1 ||
      alertText.indexOf("confidence is low") !== -1;
    voiceStatus.classList.toggle("is-alert", isAlert);
  }

  function setListeningUi(active) {
    if (voiceBox) voiceBox.classList.toggle("is-listening", active);
    if (voiceStartBtn) {
      voiceStartBtn.hidden = active;
      voiceStartBtn.setAttribute("aria-pressed", active ? "true" : "false");
      voiceStartBtn.setAttribute("data-recognition-lang", recognitionLang());
    }
    if (voiceStopBtn) voiceStopBtn.hidden = !active;
  }

  function normalizeVoiceText(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function isDuplicateSuffix(currentText, pieceText) {
    var c = String(currentText || "").trim();
    var p = String(pieceText || "").trim();
    if (!c || !p) return false;
    if (c.toLowerCase() === p.toLowerCase()) return true;

    if (c.length >= p.length) {
      var end = c.slice(-p.length);
      if (end.toLowerCase() === p.toLowerCase()) {
        if (c.length === p.length) return true;
        var prevChar = c.charAt(c.length - p.length - 1);
        if (/[\s.,!?;:\-–—\n]/.test(prevChar)) {
          return true;
        }
      }
    }
    return false;
  }

  function removeOverlappingPrefix(currentText, pieceText) {
    var c = String(currentText || "").trim();
    var p = String(pieceText || "").trim();
    if (!c || !p) return p;
    if (c.toLowerCase() === p.toLowerCase()) return "";
    if (isDuplicateSuffix(c, p)) return "";

    var maxOverlap = Math.min(c.length, p.length);
    for (var len = maxOverlap; len > 0; len -= 1) {
      var cSuffix = c.slice(-len);
      var pPrefix = p.slice(0, len);
      if (cSuffix.toLowerCase() === pPrefix.toLowerCase()) {
        var cBoundary = (len === c.length) || /[\s.,!?;:\-–—\n]/.test(c.charAt(c.length - len - 1));
        var pBoundary = (len === p.length) || /[\s.,!?;:\-–—\n]/.test(p.charAt(len));
        if (cBoundary && pBoundary) {
          return p.slice(len).trim();
        }
      }
    }
    return p;
  }

  function applyTranscript(finalText) {
    var rawPiece = normalizeVoiceText(finalText);
    if (!rawPiece) return;

    var current = statementInput.value;
    var currentTrimmed = current.trim();

    // Prevent duplicate final transcript text and overlapping repeated fragments
    var piece = removeOverlappingPrefix(currentTrimmed, rawPiece);
    if (!piece) {
      return;
    }

    if (
      lastFinalText &&
      piece.toLowerCase() === lastFinalText.toLowerCase() &&
      Date.now() - lastFinalTime < 2500
    ) {
      return;
    }

    // Preserve existing manually typed text, appending with space if needed
    var newText = "";
    if (!currentTrimmed) {
      newText = piece;
    } else if (/[\s\n]$/.test(current)) {
      newText = current + piece;
    } else {
      newText = current + " " + piece;
    }

    if (newText.length > maxChars) {
      newText = newText.slice(0, maxChars);
    }

    statementInput.value = newText;
    lastFinalText = piece;
    lastFinalTime = Date.now();

    updateCharCount();
    updateAnalyzeState();
  }

  function showInterimFeedback(interimText) {
    var live = normalizeVoiceText(interimText);
    if (!live || !wantListening) return;
    setVoiceStatus("Listening: " + live);
  }

  function confidenceWarning(confidence) {
    if (
      typeof confidence !== "number" ||
      isNaN(confidence) ||
      confidence <= 0
    ) {
      return "";
    }
    if (confidence >= LOW_CONFIDENCE_THRESHOLD) {
      return "";
    }
    return "Voice recognition confidence is low. Please review or repeat the transcript before analysis.";
  }

  function isFatalVoiceError(code) {
    return (
      code === "not-allowed" ||
      code === "service-not-allowed" ||
      code === "audio-capture" ||
      code === "language-not-supported"
    );
  }

  function clearVoiceRestart() {
    if (voiceRestartTimer) {
      clearTimeout(voiceRestartTimer);
      voiceRestartTimer = null;
    }
  }

  function stopVoiceInput(message) {
    wantListening = false;
    isSwitchingLanguage = false;
    clearVoiceRestart();
    voiceRestartCount = 0;
    sessionCommittedIndex = 0;
    lastFinalText = "";
    lastFinalTime = 0;
    if (typeof isRecordingBhashini !== "undefined" && isRecordingBhashini) {
      stopBhashiniRecording();
    }
    if (recognition && isListening) {
      try {
        recognition.stop();
      } catch (err) {
        /* already stopped */
      }
    }
    isListening = false;
    setListeningUi(false);
    if (message) setVoiceStatus(message);
  }

  function ensureRecognition() {
    if (recognition) return recognition;

    recognition = new SpeechRecognitionCtor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
      isListening = true;
      setListeningUi(true);
    };

    recognition.onresult = function (event) {
      var interimBits = [];
      var sawFinal = false;

      for (var i = sessionCommittedIndex; i < event.results.length; i += 1) {
        var result = event.results[i];
        if (!result) continue;
        var alt = result[0];
        var piece = alt && alt.transcript;

        if (result.isFinal === true) {
          sessionCommittedIndex = i + 1;
          if (piece) {
            sawFinal = true;
            applyTranscript(piece);

            // Read confidence value from final SpeechRecognition result when available
            // Do not invent confidence when the browser does not provide it
            if (
              typeof alt.confidence === "number" &&
              !isNaN(alt.confidence) &&
              alt.confidence > 0
            ) {
              latestFinalConfidence = alt.confidence;
            } else {
              latestFinalConfidence = null;
            }
          }
        } else if (piece) {
          interimBits.push(piece);
        }
      }

      if (sawFinal) {
        voiceRestartCount = 0;
        var warn = confidenceWarning(latestFinalConfidence);
        if (warn) {
          setVoiceStatus(warn);
        } else {
          detectLanguageRemote(statementInput.value).then(function (det) {
            if (det && det.status === "success" && det.label) {
              setVoiceStatus(
                "Speech converted to text. Detected Language: " + det.label + "."
              );
            } else if (interimBits.length) {
              showInterimFeedback(interimBits.join(" "));
            } else {
              setVoiceStatus(
                "Speech converted to text. Possible indicators are assessed only after Analyze."
              );
            }
          });
        }
      } else if (interimBits.length) {
        showInterimFeedback(interimBits.join(" "));
      }
    };

    recognition.onerror = function (event) {
      var code = event && event.error;
      lastRecognitionError = code || "";
      var message =
        "Voice input could not continue. Please try again or use text input.";
      if (code === "not-allowed" || code === "service-not-allowed") {
        message =
          "Microphone permission was denied. Please use text input or allow the microphone and try again.";
      } else if (code === "no-speech") {
        message = "No speech detected. Please try again or type the statement.";
      } else if (code === "audio-capture") {
        message = "No microphone was found. Please use text input.";
      } else if (code === "network") {
        message =
          "Voice input could not reach the browser recognition service. Please use text input.";
      } else if (code === "aborted") {
        if (wantListening) {
          return;
        }
        message = "Voice input stopped.";
      } else if (code === "language-not-supported") {
        message =
          "This browser does not support voice input for the detected/system language (" +
          titleCaseLabel(currentLanguage()) +
          "). Please type the statement or try English.";
      }

      if (isFatalVoiceError(code)) {
        wantListening = false;
        isSwitchingLanguage = false;
        clearVoiceRestart();
      }

      if (!wantListening) {
        setListeningUi(false);
      }
      setVoiceStatus(message);
    };

    recognition.onend = function () {
      isListening = false;

      // Handle language change restart
      if (isSwitchingLanguage) {
        isSwitchingLanguage = false;
        if (wantListening && recognition) {
          recognition.lang = recognitionLang();
          beginRecognitionSession();
        }
        return;
      }

      // Mobile safety restart: Restart ONLY when:
      // - recognition was intentionally active,
      // - user has not pressed Stop (!wantListening check),
      // - no fatal microphone/permission/language error occurred,
      // - and guarded by MAX_VOICE_RESTARTS against infinite loops
      if (!wantListening) {
        setListeningUi(false);
        return;
      }
      if (isFatalVoiceError(lastRecognitionError)) {
        wantListening = false;
        setListeningUi(false);
        return;
      }
      if (voiceRestartCount >= MAX_VOICE_RESTARTS) {
        wantListening = false;
        setListeningUi(false);
        setVoiceStatus(
          "Voice input stopped. Press Start Voice Input to continue, or type the statement."
        );
        return;
      }
      voiceRestartCount += 1;
      clearVoiceRestart();
      voiceRestartTimer = setTimeout(function () {
        voiceRestartTimer = null;
        if (!wantListening || !recognition) return;
        beginRecognitionSession();
      }, 300);
    };

    return recognition;
  }

  function beginRecognitionSession() {
    lastRecognitionError = "";
    sessionCommittedIndex = 0;
    wantListening = true;
    ensureRecognition();
    recognition.lang = recognitionLang();
    if (voiceStartBtn) {
      voiceStartBtn.setAttribute("data-recognition-lang", recognition.lang);
    }
    try {
      recognition.start();
      setListeningUi(true);
      setVoiceStatus("Listening...");
    } catch (err) {
      var errMsg = String((err && err.message) || "").toLowerCase();
      var isLangError =
        (err && err.name === "NotSupportedError") ||
        errMsg.indexOf("language") !== -1 ||
        errMsg.indexOf("not-supported") !== -1;

      if (isLangError) {
        lastRecognitionError = "language-not-supported";
        wantListening = false;
        isSwitchingLanguage = false;
        clearVoiceRestart();
        setListeningUi(false);
        setVoiceStatus(
          "This browser does not support voice input for the detected/system language (" +
          titleCaseLabel(currentLanguage()) +
          "). Please type the statement or try English."
        );
        return;
      }
      if (err && err.name === "InvalidStateError") {
        setListeningUi(true);
        return;
      }
      wantListening = false;
      isSwitchingLanguage = false;
      clearVoiceRestart();
      setListeningUi(false);
      setVoiceStatus("Voice input could not start. Please use text input.");
    }
  }

  var bhashiniConfigured = false;
  var mediaRecorder = null;
  var mediaStream = null;
  var recordedChunks = [];
  var isRecordingBhashini = false;

  function checkBhashiniStatus() {
    fetch(BACKEND_API_BASE + "/ai/transcribe")
      .then(function (res) {
        if (!res.ok) return null;
        return res.json();
      })
      .then(function (data) {
        if (data && data.status === "configured") {
          bhashiniConfigured = true;
        } else {
          bhashiniConfigured = false;
        }
      })
      .catch(function () {
        bhashiniConfigured = false;
      });
  }

  function startBhashiniRecording() {
    wantListening = true;
    recordedChunks = [];
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      fallbackToBrowserSpeech("Microphone recording not supported. Using browser speech recognition.");
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function (stream) {
        if (!wantListening) {
          stream.getTracks().forEach(function (t) { t.stop(); });
          return;
        }
        mediaStream = stream;
        try {
          var mimeType = (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported("audio/webm;codecs=opus"))
            ? "audio/webm;codecs=opus"
            : (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "");
          mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType: mimeType }) : new MediaRecorder(stream);
        } catch (e) {
          mediaRecorder = new MediaRecorder(stream);
        }

        mediaRecorder.ondataavailable = function (e) {
          if (e.data && e.data.size > 0) {
            recordedChunks.push(e.data);
          }
        };

        mediaRecorder.onerror = function (e) {
          console.warn("MediaRecorder error:", e);
          stopBhashiniRecording();
          fallbackToBrowserSpeech("Microphone recording error. Switching to browser speech.");
        };

        mediaRecorder.onstop = function () {
          isRecordingBhashini = false;
          if (mediaStream) {
            mediaStream.getTracks().forEach(function (t) { t.stop(); });
            mediaStream = null;
          }
          if (!wantListening) return;

          var audioBlob = new Blob(recordedChunks, { type: (mediaRecorder && mediaRecorder.mimeType) || "audio/webm" });
          if (audioBlob.size === 0) {
            setVoiceStatus("No audio captured. Please try again or type the statement.");
            setListeningUi(false);
            return;
          }

          sendAudioToBhashini(audioBlob);
        };

        mediaRecorder.start();
        isRecordingBhashini = true;
        setListeningUi(true);
        setVoiceStatus("Listening (Bhashini recording)... Press Stop Voice Input when finished.");
      })
      .catch(function (err) {
        console.warn("getUserMedia error:", err);
        var msg = "Microphone access could not be acquired. Please check permissions or use text input.";
        if (err && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError")) {
          msg = "Microphone permission was denied. Please use text input or allow microphone access.";
          setVoiceStatus(msg);
          wantListening = false;
          setListeningUi(false);
        } else {
          fallbackToBrowserSpeech("Bhashini recording unavailable. Falling back to browser speech recognition.");
        }
      });
  }

  function stopBhashiniRecording() {
    if (mediaRecorder && isRecordingBhashini && mediaRecorder.state !== "inactive") {
      try {
        mediaRecorder.stop();
      } catch (err) {
        /* already stopped */
      }
    }
    isRecordingBhashini = false;
    if (mediaStream) {
      mediaStream.getTracks().forEach(function (t) { t.stop(); });
      mediaStream = null;
    }
  }

  function sendAudioToBhashini(audioBlob) {
    setVoiceStatus("Transcribing speech via Bhashini...");
    var formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    var candidateLang = "hi";
    var detected = detectStatementLanguage(statementInput ? statementInput.value : "");
    if (detected && detected.code) {
      candidateLang = detected.code;
    }
    formData.append("language", candidateLang);

    fetch(BACKEND_API_BASE + "/ai/transcribe", {
      method: "POST",
      body: formData,
    })
      .then(function (res) {
        if (res.status === 503) {
          bhashiniConfigured = false;
          throw new Error("Bhashini is not configured.");
        }
        if (!res.ok) {
          throw new Error("Bhashini returned status " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        setListeningUi(false);
        wantListening = false;
        if (data && data.status === "success" && data.transcript) {
          applyTranscript(data.transcript);
          detectLanguageRemote(statementInput.value).then(function (det) {
            var langLabel = (det && det.label && det.status === "success") ? det.label : "";
            var langMsg = langLabel ? " (Detected: " + langLabel + ")" : "";
            setVoiceStatus("Speech transcribed via Bhashini" + langMsg + ". " + (data.disclaimer || ""));
          });
        } else if (data && data.status === "not_configured") {
          bhashiniConfigured = false;
          fallbackToBrowserSpeech("Bhashini credentials not configured. Falling back to browser speech.");
        } else {
          setVoiceStatus(data.message || "No transcription returned. Please review or type the statement.");
        }
      })
      .catch(function (err) {
        console.warn("Bhashini transcription error:", err);
        setListeningUi(false);
        wantListening = false;
        setVoiceStatus("Bhashini transcription unavailable (" + (err.message || "service error") + "). Falling back to browser speech or text.");
      });
  }

  function fallbackToBrowserSpeech(reasonMessage) {
    bhashiniConfigured = false;
    if (SpeechRecognitionCtor) {
      if (reasonMessage) setVoiceStatus(reasonMessage);
      beginRecognitionSession();
    } else {
      wantListening = false;
      setListeningUi(false);
      setVoiceStatus("Voice input is not supported in this browser. Please use text input.");
    }
  }

  function startVoiceInput() {
    if (!consentCheckbox.checked) {
      setVoiceStatus("Please provide consent before using voice input.");
      consentCheckbox.focus();
      return;
    }
    if (wantListening && (isListening || isRecordingBhashini)) {
      return;
    }

    voiceRestartCount = 0;
    latestFinalConfidence = null;
    lastFinalText = "";
    lastFinalTime = 0;

    // Graceful dual-route:
    // If Bhashini credentials are configured on backend and MediaRecorder is supported,
    // record audio and send to Bhashini ASR.
    // If Bhashini is not configured (or offline), fall back seamlessly to browser SpeechRecognition.
    if (bhashiniConfigured && navigator.mediaDevices && window.MediaRecorder) {
      startBhashiniRecording();
    } else {
      if (!SpeechRecognitionCtor) {
        setVoiceStatus(
          "Voice input is not supported in this browser. Please use text input."
        );
        return;
      }
      beginRecognitionSession();
    }
  }

  if (voiceStartBtn) {
    voiceStartBtn.setAttribute("data-recognition-lang", recognitionLang());
    if (!SpeechRecognitionCtor && !(navigator.mediaDevices && window.MediaRecorder)) {
      voiceStartBtn.disabled = true;
      setVoiceStatus(
        "Voice input is not supported in this browser. Please use text input."
      );
    }
    voiceStartBtn.addEventListener("click", startVoiceInput);
  }
  if (voiceStopBtn) {
    voiceStopBtn.addEventListener("click", function () {
      stopVoiceInput("Voice converted to text");
    });
  }

  // Probe Bhashini availability asynchronously in background
  checkBhashiniStatus();

  statementInput.addEventListener("input", function () {
    latestFinalConfidence = null;
    updateCharCount();
    updateAnalyzeState();
    showFormError("");
  });

  consentCheckbox.addEventListener("change", function () {
    updateAnalyzeState();
    showFormError("");
    if (!consentCheckbox.checked && (isListening || wantListening)) {
      stopVoiceInput("Please provide consent before using voice input.");
    }
  });

  var interactionRadios = form.querySelectorAll('input[name="interaction-type"]');
  interactionRadios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      updateVoiceControlsVisibility();
    });
  });
  updateVoiceControlsVisibility();

  scenarioButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.getAttribute("data-scenario");
      var text = DEMO_STATEMENTS[key];
      if (!text) return;
      if (wantListening || isListening) {
        stopVoiceInput("Voice input stopped");
      }
      latestFinalConfidence = null;
      statementInput.value = text;
      setScenarioActive(btn);
      updateCharCount();
      updateAnalyzeState();
      showFormError("");
      statementInput.focus();
    });
  });

  if (newAssessmentBtn) {
    newAssessmentBtn.addEventListener("click", function () {
      resetAssessment();
    });
  }

  if (reviewInputBtn) {
    reviewInputBtn.addEventListener("click", function () {
      var target = statementPanel || statementInput;
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      statementInput.focus();
    });
  }

  function sendCaseToBackend(statementText, detectedLang) {
    if (!statementText || !consentCheckbox.checked) return;

    var langName = (detectedLang && (detectedLang.label || detectedLang.language_name))
      ? (detectedLang.label || detectedLang.language_name).toLowerCase()
      : currentLanguage();
    if (
      detectedLang &&
      (detectedLang.status === "unknown" ||
        detectedLang.code === "unknown" ||
        detectedLang.language_code === "unknown")
    ) {
      langName = "unknown";
    }

    var payload = {
      case_id: currentCaseId,
      statement: statementText,
      language: langName,
      interaction_type: selectedInteraction(),
      consent: !!consentCheckbox.checked,
    };

    fetch(BACKEND_API_BASE + "/cases", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then(function (response) {
        if (!response.ok) {
          console.warn("SAMVAD Backend /cases returned status " + response.status);
          return null;
        }
        return response.json();
      })
      .then(function (data) {
        if (data) {
          console.log("SAMVAD AI Backend: Case successfully recorded", data);
        }
      })
      .catch(function (err) {
        console.warn(
          "SAMVAD AI Backend: Could not sync case to " + BACKEND_API_BASE + "/cases",
          err
        );
      });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    if (wantListening || isListening) {
      stopVoiceInput();
    }

    var statement = statementInput.value.trim();
    if (!statement) {
      showFormError("Please enter a statement before analysis.");
      statementInput.focus();
      return;
    }

    if (!consentCheckbox.checked) {
      showFormError("Please provide consent before analysis.");
      consentCheckbox.focus();
      return;
    }

    var warn = confidenceWarning(latestFinalConfidence);
    if (warn) setVoiceStatus(warn);

    if (analysisTimer) {
      clearTimeout(analysisTimer);
      analysisTimer = null;
    }

    showFormError("");
    analyzeBtn.disabled = true;
    showLoading(true);

    // Automatic language detection via backend service with local heuristic fallback
    detectLanguageRemote(statement).then(function (detectedLang) {
      var langForAnalyze = "english";
      if (detectedLang && (detectedLang.label || detectedLang.code)) {
        var lower = (detectedLang.label || "").toLowerCase();
        var code = (detectedLang.code || "").toLowerCase();
        if (code === "hi" || lower === "hindi") {
          langForAnalyze = "hindi";
        } else if (code === "mr" || lower === "marathi") {
          langForAnalyze = "marathi";
        } else if (code === "en" || lower === "english") {
          langForAnalyze = "english";
        } else {
          langForAnalyze = code || "english";
        }
      }

      analysisTimer = setTimeout(function () {
        fetch(BACKEND_API_BASE + "/ai/assess", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: statement,
            language: langForAnalyze,
            case_id: currentCaseId,
            interaction_type: selectedInteraction(),
            consent: true,
          }),
        })
          .then(function (resp) {
            if (!resp.ok) throw new Error("Backend HTTP " + resp.status);
            return resp.json();
          })
          .then(function (data) {
            showLoading(false);
            var result = {
              ok: true,
              svi: data.svi.score,
              riskLevel: data.svi.risk_level || data.risk_classification.risk_level,
              components: {
                stress: data.svi.stress,
                vulnerability: data.svi.vulnerability,
                urgency: data.svi.urgency,
                safetyConcern: data.svi.safety,
              },
              indicators: data.indicators || [],
              recommendation: data.recommendation || "Information and general support",
              immediateHumanReview: data.human_review !== undefined ? data.human_review : (data.safety ? data.safety.human_review : false),
              humanReviewReason: data.human_review_reason,
              supportRequest: data.support_request,
              explanation: data.explanation,
              sviRange: data.svi_range,
              supportResources: data.support_resources || [],
              isLocalFallback: false,
            };
            var langInfo = data.language
              ? { code: data.language.code, label: data.language.name, confidence: data.language.confidence }
              : detectedLang;
            renderResult(result, langInfo);
            updateAnalyzeState();
            analysisTimer = null;
          })
          .catch(function (err) {
            console.warn("Backend /ai/assess unavailable, falling back to local analysis mode:", err);
            var result = MockAI.analyze(statement, {
              language: langForAnalyze,
            });
            result.isLocalFallback = true;
            if (!result.ok) {
              showLoading(false);
              feedback.hidden = true;
              showFormError(result.error || "Please enter a statement before analysis.");
              updateAnalyzeState();
              analysisTimer = null;
              return;
            }
            showLoading(false);
            renderResult(result, detectedLang);
            sendCaseToBackend(statement, detectedLang);
            updateAnalyzeState();
            analysisTimer = null;
          });
      }, 500);
    });
  });
})();
