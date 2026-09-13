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

  function selectedLanguage() {
    var checked = form.querySelector('input[name="language"]:checked');
    return checked ? checked.value : "english";
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
    if (matches.stress.length) {
      parts.push("Stress: " + matches.stress.join(", "));
    }
    if (matches.vulnerability.length) {
      parts.push("Vulnerability: " + matches.vulnerability.join(", "));
    }
    if (matches.urgency.length) {
      parts.push("Urgency: " + matches.urgency.join(", "));
    }
    if (matches.safety.length) {
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

  function renderResult(result) {
    if (!resultSection) return;

    document.querySelector("#result-case-id").textContent = currentCaseId;
    document.querySelector("#result-svi").textContent = String(result.svi);
    document.querySelector("#svi-ring-value").textContent = String(result.svi);
    setSviRing(result.svi);

    var riskEl = document.querySelector("#result-risk");
    riskEl.textContent = result.riskLevel;
    riskEl.className = "result-risk-badge " + riskClass(result.riskLevel);
    riskEl.setAttribute("aria-label", "Risk level " + result.riskLevel);

    var hero = document.querySelector(".svi-hero");
    if (hero) {
      hero.className = "svi-hero " + riskClass(result.riskLevel);
    }

    document.querySelector("#risk-explanation").textContent =
      RISK_EXPLANATIONS[result.riskLevel] || RISK_EXPLANATIONS.LOW;

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

    saveCaseToStore(result);

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

  function saveCaseToStore(result) {
    if (typeof CaseStore === "undefined") return;
    var now = new Date();
    var datetime = formatDateTime(now);
    var record = {
      caseId: currentCaseId,
      timestamp: datetime,
      createdAt: now.toISOString(),
      language: titleCaseLabel(selectedLanguage()),
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
    var english = form.querySelector('input[name="language"][value="english"]');
    if (english) english.checked = true;

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
    return LANG_CODES[selectedLanguage()] || "en-IN";
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
        } else if (interimBits.length) {
          showInterimFeedback(interimBits.join(" "));
        } else {
          setVoiceStatus(
            "Speech converted to text. Possible indicators are assessed only after Analyze."
          );
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
          "This browser does not support voice input for the selected language (" +
          titleCaseLabel(selectedLanguage()) +
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
          "This browser does not support voice input for the selected language (" +
          titleCaseLabel(selectedLanguage()) +
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

  function startVoiceInput() {
    if (!SpeechRecognitionCtor) {
      setVoiceStatus(
        "Voice input is not supported in this browser. Please use text input."
      );
      return;
    }
    if (!consentCheckbox.checked) {
      setVoiceStatus("Please provide consent before using voice input.");
      consentCheckbox.focus();
      return;
    }
    if (wantListening && isListening) {
      return;
    }

    voiceRestartCount = 0;
    latestFinalConfidence = null;
    lastFinalText = "";
    lastFinalTime = 0;
    beginRecognitionSession();
  }

  if (voiceStartBtn) {
    voiceStartBtn.setAttribute("data-recognition-lang", recognitionLang());
    if (!SpeechRecognitionCtor) {
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

  form.querySelectorAll('input[name="language"]').forEach(function (radio) {
    radio.addEventListener("change", function () {
      var lang = recognitionLang();
      if (voiceStartBtn) {
        voiceStartBtn.setAttribute("data-recognition-lang", lang);
      }

      var wasActive = wantListening || isListening;
      if (!wasActive) {
        if (recognition) {
          recognition.lang = lang;
        }
        setVoiceStatus(
          "Voice language set to " +
          titleCaseLabel(selectedLanguage()) +
          " (" +
          lang +
          ")."
        );
        return;
      }

      // Recognition was active before language change:
      // Stop recognition safely, update recognition.lang, and restart only because it was active
      isSwitchingLanguage = true;
      wantListening = true;
      voiceRestartCount = 0;
      lastRecognitionError = "";
      clearVoiceRestart();
      if (recognition) {
        recognition.lang = lang;
      }
      setVoiceStatus(
        "Voice language set to " +
        titleCaseLabel(selectedLanguage()) +
        " (" +
        lang +
        "). Restarting..."
      );

      if (recognition && isListening) {
        try {
          recognition.stop();
        } catch (err) {
          isSwitchingLanguage = false;
          beginRecognitionSession();
        }
      } else {
        isSwitchingLanguage = false;
        beginRecognitionSession();
      }
    });
  });

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

    analysisTimer = setTimeout(function () {
      var result = MockAI.analyze(statement, {
        language: selectedLanguage(),
      });

      if (!result.ok) {
        showLoading(false);
        feedback.hidden = true;
        showFormError(result.error || "Please enter a statement before analysis.");
        updateAnalyzeState();
        analysisTimer = null;
        return;
      }

      showLoading(false);
      renderResult(result);
      updateAnalyzeState();
      analysisTimer = null;
    }, 1200);
  });
})();
