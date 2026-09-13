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
  var recognition = null;
  var isListening = false;
  var voiceBaseText = "";
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
      alertText.indexOf("no microphone") !== -1;
    voiceStatus.classList.toggle("is-alert", isAlert);
  }

  function setListeningUi(active) {
    isListening = active;
    if (voiceBox) voiceBox.classList.toggle("is-listening", active);
    if (voiceStartBtn) {
      voiceStartBtn.hidden = active;
      voiceStartBtn.setAttribute("aria-pressed", active ? "true" : "false");
      voiceStartBtn.setAttribute("data-recognition-lang", recognitionLang());
    }
    if (voiceStopBtn) voiceStopBtn.hidden = !active;
  }

  function applyTranscript(finalText, interimText) {
    var pieces = [];
    if (voiceBaseText) pieces.push(voiceBaseText);
    if (finalText) pieces.push(finalText);
    if (interimText) pieces.push(interimText);
    statementInput.value = pieces.join(" ").replace(/\s+/g, " ").trim();
    if (statementInput.value.length > maxChars) {
      statementInput.value = statementInput.value.slice(0, maxChars);
    }
    updateCharCount();
    updateAnalyzeState();
  }

  function stopVoiceInput(message) {
    if (recognition && isListening) {
      try {
        recognition.stop();
      } catch (err) {
        /* already stopped */
      }
    }
    setListeningUi(false);
    if (message) setVoiceStatus(message);
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

    voiceBaseText = statementInput.value.trim();
    if (!recognition) {
      recognition = new SpeechRecognitionCtor();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onresult = function (event) {
        var finalBits = [];
        var interimBits = [];
        for (var i = 0; i < event.results.length; i += 1) {
          var piece = event.results[i][0] && event.results[i][0].transcript;
          if (!piece) continue;
          if (event.results[i].isFinal) finalBits.push(piece);
          else interimBits.push(piece);
        }
        applyTranscript(finalBits.join(" "), interimBits.join(" "));
        if (finalBits.length) {
          setVoiceStatus("Speech converted to text. Possible indicators are assessed only after Analyze.");
        }
      };

      recognition.onerror = function (event) {
        var code = event && event.error;
        var message = "Voice input could not continue. Please try again or use text input.";
        if (code === "not-allowed" || code === "service-not-allowed") {
          message = "Microphone permission was denied. Please use text input or allow the microphone and try again.";
        } else if (code === "no-speech") {
          message = "No speech detected. Please try again or type the statement.";
        } else if (code === "audio-capture") {
          message = "No microphone was found. Please use text input.";
        } else if (code === "network") {
          message = "Voice input could not reach the browser recognition service. Please use text input.";
        } else if (code === "aborted") {
          message = "Voice input stopped.";
        }
        setListeningUi(false);
        setVoiceStatus(message);
      };

      recognition.onend = function () {
        if (isListening) {
          setListeningUi(false);
          setVoiceStatus("Voice input stopped");
        }
      };
    }

    recognition.lang = recognitionLang();
    if (voiceStartBtn) {
      voiceStartBtn.setAttribute("data-recognition-lang", recognition.lang);
    }

    try {
      recognition.start();
      setListeningUi(true);
      setVoiceStatus("Listening...");
    } catch (err) {
      setListeningUi(false);
      setVoiceStatus("Voice input could not start. Please use text input.");
    }
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
      if (voiceStartBtn) voiceStartBtn.setAttribute("data-recognition-lang", lang);
      if (recognition) recognition.lang = lang;
      if (!isListening) {
        setVoiceStatus("Voice language set to " + lang + ".");
      }
    });
  });

  statementInput.addEventListener("input", function () {
    updateCharCount();
    updateAnalyzeState();
    showFormError("");
  });

  consentCheckbox.addEventListener("change", function () {
    updateAnalyzeState();
    showFormError("");
    if (!consentCheckbox.checked && isListening) {
      stopVoiceInput("Please provide consent before using voice input.");
    }
  });

  scenarioButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.getAttribute("data-scenario");
      var text = DEMO_STATEMENTS[key];
      if (!text) return;
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
