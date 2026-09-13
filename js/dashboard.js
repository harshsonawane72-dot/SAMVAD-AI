/**
 * SAMVAD AI — Human Operator Dashboard
 * Uses MockAI.analyze() for SVI scores. No scoring logic here.
 * Mock state only — no backend, no external calls.
 */

(function initDashboard() {
  "use strict";

  var tableBody = document.querySelector("#case-table-body");
  if (!tableBody) return;

  if (typeof MockAI === "undefined" || !MockAI.analyze) {
    console.error("MockAI engine not loaded. Include mock-ai.js before dashboard.js.");
    return;
  }

  if (typeof DEMO_DATA === "undefined" || !DEMO_DATA.sampleCases) {
    console.error("DEMO_DATA not loaded. Include demo-data.js before dashboard.js.");
    return;
  }

  var cases = loadCombinedCases();
  var selectedId = null;

  var searchEl = document.querySelector("#filter-search");
  var riskEl = document.querySelector("#filter-risk");
  var languageEl = document.querySelector("#filter-language");
  var interactionEl = document.querySelector("#filter-interaction");
  var statusEl = document.querySelector("#filter-status");

  function fromStoredCase(record) {
    var language = record.language || "";
    var interaction = record.interactionType || record.interaction || "";
    var timestamp = record.timestamp || record.datetime || "";
    var createdAt = record.createdAt || "";
    var status = record.status || "New";
    var recommendation = record.recommendation || record.supportPathway || "";

    return {
      id: record.caseId || record.id,
      datetime: timestamp,
      time: formatTimeLabel(timestamp, createdAt),
      language: language,
      interaction: interaction,
      status: status,
      humanReviewStatus: record.humanReviewStatus || status,
      previousStatus: record.previousStatus || "",
      statement: record.statement || "",
      svi: Number(record.svi) || 0,
      risk: record.riskLevel || record.risk || "LOW",
      components: {
        stress: Number(record.stress) || 0,
        vulnerability: Number(record.vulnerability) || 0,
        urgency: Number(record.urgency) || 0,
        safetyConcern: Number(record.safety) || 0,
      },
      indicators: Array.isArray(record.indicators) ? record.indicators.slice() : [],
      aiRecommendation: recommendation,
      supportPathway: record.supportPathway || recommendation,
      safetyFlag: !!record.safetyFlag,
      timeline: Array.isArray(record.timeline)
        ? record.timeline.slice()
        : defaultTimeline({ datetime: timestamp, status: status }),
      createdAt: createdAt,
      source: record.source || "assessment",
    };
  }

  function formatTimeLabel(timestamp, createdAt) {
    if (createdAt) {
      try {
        return new Intl.DateTimeFormat(undefined, {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }).format(new Date(createdAt));
      } catch (err) {
        /* fall through */
      }
    }
    if (!timestamp) return "—";
    var parts = String(timestamp).split(",");
    return parts.length > 1 ? parts[parts.length - 1].trim() : timestamp;
  }

  function sortNewestFirst(list) {
    return list.sort(function (a, b) {
      var ta = Date.parse(a.createdAt || "") || 0;
      var tb = Date.parse(b.createdAt || "") || 0;
      return tb - ta;
    });
  }

  function loadCombinedCases() {
    var byId = {};
    DEMO_DATA.sampleCases.forEach(function (seed) {
      var item = hydrateCase(seed);
      byId[item.id] = item;
    });

    if (typeof CaseStore !== "undefined") {
      CaseStore.load().forEach(function (record) {
        var item = fromStoredCase(record);
        if (item.id) byId[item.id] = item;
      });
    }

    return sortNewestFirst(
      Object.keys(byId).map(function (key) {
        return byId[key];
      })
    );
  }

  function persistCase(item) {
    if (typeof CaseStore === "undefined") return;
    CaseStore.upsert(CaseStore.toStorageRecord(item));
  }

  function queryCaseId() {
    try {
      var params = new URLSearchParams(window.location.search);
      return params.get("case");
    } catch (err) {
      return null;
    }
  }

  function hydrateCase(seed) {
    var analysis = MockAI.analyze(seed.statement, {
      language: String(seed.language || "english").toLowerCase(),
    });

    var risk = analysis.ok ? analysis.riskLevel : "LOW";
    var svi = analysis.ok ? analysis.svi : 0;
    var components = analysis.ok
      ? analysis.components
      : { stress: 0, vulnerability: 0, urgency: 0, safetyConcern: 0 };
    var indicators = analysis.ok ? analysis.indicators.slice() : [];
    var recommendation = analysis.ok ? analysis.recommendation : "Human review required";
    var safetyFlag = analysis.ok ? !!analysis.immediateHumanReview : false;

    return {
      id: seed.id,
      datetime: seed.datetime,
      time: seed.time,
      language: seed.language,
      interaction: seed.interaction,
      status: seed.status,
      humanReviewStatus: seed.status === "Reviewed" ? "Reviewed" : "Pending",
      previousStatus: "",
      statement: seed.statement,
      svi: svi,
      risk: risk,
      components: components,
      indicators: indicators,
      aiRecommendation: recommendation,
      supportPathway: recommendation,
      safetyFlag: safetyFlag,
      timeline: defaultTimeline(seed),
      createdAt: seed.createdAt || "",
      source: "demo",
    };
  }

  function defaultTimeline(seed) {
    return [
      { label: "Case received", note: seed.datetime },
      { label: "AI-assisted assessment generated", note: "Local prototype engine" },
      {
        label:
          seed.status === "Reviewed"
            ? "Human review recorded"
            : "Human review pending",
        note: "Operator decision required",
      },
      { label: "Support pathway recommendation", note: "Advisory only" },
    ];
  }

  function nowStamp() {
    try {
      return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date());
    } catch (err) {
      return new Date().toLocaleString();
    }
  }

  function riskClass(level) {
    return "risk-" + String(level || "LOW").toLowerCase();
  }

  function isArchived(item) {
    return item && item.status === "Archived";
  }

  function isActiveStatus(status) {
    return status === "New" || status === "Under Review" || status === "Reviewed";
  }

  function matchesFilters(item) {
    var query = (searchEl.value || "").trim().toLowerCase();
    if (query && item.id.toLowerCase().indexOf(query) === -1) return false;
    if (riskEl.value !== "all" && item.risk !== riskEl.value) return false;
    if (languageEl.value !== "all" && item.language !== languageEl.value) return false;
    if (interactionEl.value !== "all" && item.interaction !== interactionEl.value) {
      return false;
    }

    var statusFilter = statusEl.value;
    if (statusFilter === "all") {
      if (!isActiveStatus(item.status)) return false;
    } else if (statusFilter === "Archived") {
      if (!isArchived(item)) return false;
    } else if (item.status !== statusFilter) {
      return false;
    }
    return true;
  }

  function filteredCases() {
    return cases.filter(matchesFilters);
  }

  function findCase(id) {
    for (var i = 0; i < cases.length; i += 1) {
      if (cases[i].id === id) return cases[i];
    }
    return null;
  }

  function updateSummary() {
    var active = 0;
    var critical = 0;
    var high = 0;
    var awaiting = 0;

    cases.forEach(function (item) {
      if (isArchived(item)) return;
      if (item.status === "New" || item.status === "Under Review") active += 1;
      if (item.risk === "CRITICAL") critical += 1;
      if (item.risk === "HIGH") high += 1;
      if (item.status === "New") awaiting += 1;
    });

    setText("stat-active", String(active));
    setText("stat-critical", String(critical));
    setText("stat-high", String(high));
    setText("stat-awaiting", String(awaiting));
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function setBar(id, value) {
    var el = document.getElementById(id);
    if (!el) return;
    var score = Math.max(0, Math.min(100, Number(value) || 0));
    el.style.width = score + "%";
  }

  function renderTable() {
    var rows = filteredCases();
    tableBody.innerHTML = "";

    var countEl = document.querySelector("#table-count");
    var emptyEl = document.querySelector("#empty-queue");
    if (countEl) {
      countEl.textContent =
        rows.length + (rows.length === 1 ? " demo case" : " demo cases");
    }
    if (emptyEl) {
      emptyEl.hidden = rows.length > 0;
      emptyEl.textContent =
        statusEl.value === "Archived"
          ? "No archived cases in this prototype queue."
          : "No matching demo cases. Try a different Case ID or filter.";
    }
    var tableScroll = document.querySelector(".table-scroll");
    if (tableScroll) tableScroll.hidden = rows.length === 0;

    rows.forEach(function (item) {
      var tr = document.createElement("tr");
      tr.tabIndex = 0;
      tr.setAttribute("role", "button");
      tr.setAttribute("data-case-id", item.id);
      tr.setAttribute("aria-label", "Open case " + item.id + ", risk " + item.risk);
      if (item.id === selectedId) {
        tr.classList.add("is-selected");
        tr.setAttribute("aria-current", "true");
      }

      tr.innerHTML =
        "<td><strong>" +
        escapeHtml(item.id) +
        "</strong></td>" +
        "<td>" +
        escapeHtml(item.time) +
        "</td>" +
        "<td>" +
        escapeHtml(item.language) +
        "</td>" +
        "<td>" +
        escapeHtml(item.interaction) +
        "</td>" +
        "<td>" +
        escapeHtml(String(item.svi)) +
        "</td>" +
        '<td><span class="result-risk-badge ' +
        riskClass(item.risk) +
        '">' +
        escapeHtml(item.risk) +
        "</span></td>" +
        "<td>" +
        escapeHtml(item.status) +
        "</td>" +
        "<td>" +
        escapeHtml(shortPathway(item.supportPathway)) +
        "</td>";

      tableBody.appendChild(tr);
    });
  }

  function shortPathway(text) {
    if (!text) return "—";
    if (text.length <= 42) return text;
    return text.slice(0, 40) + "…";
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderDetail(item) {
    var empty = document.querySelector("#detail-empty");
    var content = document.querySelector("#detail-content");
    if (!item) {
      if (empty) empty.hidden = false;
      if (content) content.hidden = true;
      return;
    }

    if (empty) empty.hidden = true;
    if (content) content.hidden = false;

    setText("detail-id", item.id);
    setText("detail-datetime", item.datetime);
    setText("detail-language", item.language);
    setText("detail-interaction", item.interaction);
    setText("detail-statement", item.statement);
    setText("detail-svi", String(item.svi));
    setText("detail-stress", String(item.components.stress));
    setText("detail-vulnerability", String(item.components.vulnerability));
    setText("detail-urgency", String(item.components.urgency));
    setText("detail-safety", String(item.components.safetyConcern));
    setText("detail-pathway", item.supportPathway);

    var riskBadge = document.querySelector("#detail-risk");
    if (riskBadge) {
      riskBadge.textContent = item.risk;
      riskBadge.className = "result-risk-badge " + riskClass(item.risk);
      riskBadge.setAttribute("aria-label", "Risk level " + item.risk);
    }

    setBar("detail-bar-stress", item.components.stress);
    setBar("detail-bar-vulnerability", item.components.vulnerability);
    setBar("detail-bar-urgency", item.components.urgency);
    setBar("detail-bar-safety", item.components.safetyConcern);

    var list = document.querySelector("#detail-indicators");
    if (list) {
      list.innerHTML = "";
      item.indicators.forEach(function (label) {
        var li = document.createElement("li");
        li.className = "indicator-tag";
        li.textContent = label;
        list.appendChild(li);
      });
    }

    var safetyPanel = document.querySelector("#critical-safety-panel");
    var showSafety = item.risk === "CRITICAL" || item.safetyFlag;
    if (safetyPanel) safetyPanel.hidden = !showSafety;

    var timeline = document.querySelector("#detail-timeline");
    if (timeline) {
      timeline.innerHTML = "";
      item.timeline.forEach(function (entry) {
        var li = document.createElement("li");
        li.innerHTML =
          "<strong>" +
          escapeHtml(entry.label) +
          "</strong>" +
          (entry.note
            ? '<span class="audit-note">' + escapeHtml(entry.note) + "</span>"
            : "");
        timeline.appendChild(li);
      });
    }

    var feedback = document.querySelector("#action-feedback");
    if (feedback && !feedback.dataset.keep) feedback.textContent = "";
    if (feedback) delete feedback.dataset.keep;

    var archived = isArchived(item);
    var reviewActions = document.querySelector("#review-actions");
    var archiveBtn = document.querySelector("#archive-case-btn");
    var restoreBtn = document.querySelector("#restore-case-btn");
    if (reviewActions) reviewActions.hidden = archived;
    if (archiveBtn) archiveBtn.hidden = archived;
    if (restoreBtn) restoreBtn.hidden = !archived;
  }

  function selectCase(id) {
    selectedId = id;
    renderTable();
    renderDetail(findCase(id));
  }

  function applyAction(action) {
    var item = findCase(selectedId);
    var feedback = document.querySelector("#action-feedback");
    if (!item) {
      if (feedback) feedback.textContent = "Select a case first.";
      return;
    }
    if (isArchived(item)) {
      if (feedback) {
        feedback.textContent = "Restore this case before recording other actions.";
      }
      return;
    }

    var stamp = nowStamp();
    var message = "";

    if (action === "reviewed") {
      item.status = "Reviewed";
      item.humanReviewStatus = "Reviewed";
      item.timeline.push({
        label: "Marked as reviewed by human operator",
        note: stamp,
      });
      message = "Case marked as Reviewed (local prototype state).";
    } else if (action === "counselling") {
      item.supportPathway = "Counselling / support referral (assigned by operator)";
      if (item.status === "New") item.status = "Under Review";
      item.humanReviewStatus = item.status;
      item.timeline.push({
        label: "Operator assigned counselling support",
        note: stamp,
      });
      message = "Counselling assignment recorded locally. No external referral was sent.";
    } else if (action === "legal") {
      item.supportPathway = "Legal aid referral (assigned by operator)";
      if (item.status === "New") item.status = "Under Review";
      item.humanReviewStatus = item.status;
      item.timeline.push({
        label: "Operator assigned legal aid",
        note: stamp,
      });
      message = "Legal aid assignment recorded locally. No external referral was sent.";
    } else if (action === "protection") {
      item.supportPathway =
        "Medical / protection support pathway (assigned by operator)";
      if (item.status === "New") item.status = "Under Review";
      item.humanReviewStatus = item.status;
      item.timeline.push({
        label: "Operator assigned medical/protection support",
        note: stamp,
      });
      message =
        "Medical/protection assignment recorded locally. No emergency service was contacted.";
    } else if (action === "more-info") {
      item.status = "Under Review";
      item.humanReviewStatus = "Under Review";
      item.timeline.push({
        label: "Operator requested more information",
        note: stamp,
      });
      message = "Request for more information recorded in the prototype audit timeline.";
    }

    persistCase(item);

    if (feedback) {
      feedback.textContent = message;
      feedback.dataset.keep = "1";
    }

    updateSummary();
    renderTable();
    renderDetail(item);
  }

  function archiveSelectedCase() {
    var item = findCase(selectedId);
    var feedback = document.querySelector("#action-feedback");
    if (!item) {
      if (feedback) feedback.textContent = "Select a case first.";
      return;
    }
    if (isArchived(item)) return;

    item.previousStatus = isActiveStatus(item.status) ? item.status : "Reviewed";
    item.status = "Archived";
    item.humanReviewStatus = "Archived";
    item.timeline.push({
      label: "Case archived by human operator",
      note: nowStamp(),
    });
    persistCase(item);

    if (feedback) {
      feedback.textContent = "Case archived. It is hidden from the active case list.";
      feedback.dataset.keep = "1";
    }

    closeArchiveDialog();
    updateSummary();
    renderTable();
    renderDetail(item);
  }

  function restoreSelectedCase() {
    var item = findCase(selectedId);
    var feedback = document.querySelector("#action-feedback");
    if (!item) {
      if (feedback) feedback.textContent = "Select a case first.";
      return;
    }
    if (!isArchived(item)) return;

    var restored = isActiveStatus(item.previousStatus)
      ? item.previousStatus
      : "Reviewed";
    item.status = restored;
    item.humanReviewStatus = restored;
    item.timeline.push({
      label: "Case restored by human operator",
      note: nowStamp(),
    });
    persistCase(item);

    if (feedback) {
      feedback.textContent = "Case restored to the active case list.";
      feedback.dataset.keep = "1";
    }

    if (statusEl.value === "Archived") statusEl.value = "all";
    updateSummary();
    renderTable();
    renderDetail(item);
  }

  var archiveDialog = document.querySelector("#archive-dialog");
  var archiveLastFocus = null;

  function openArchiveDialog() {
    if (!findCase(selectedId) || isArchived(findCase(selectedId))) return;
    archiveLastFocus = document.activeElement;
    if (archiveDialog) archiveDialog.hidden = false;
    var cancelBtn = document.querySelector("#archive-cancel-btn");
    if (cancelBtn) cancelBtn.focus();
  }

  function closeArchiveDialog() {
    if (archiveDialog) archiveDialog.hidden = true;
    if (archiveLastFocus && archiveLastFocus.focus) archiveLastFocus.focus();
  }

  tableBody.addEventListener("click", function (event) {
    var row = event.target.closest("tr[data-case-id]");
    if (!row) return;
    selectCase(row.getAttribute("data-case-id"));
  });

  tableBody.addEventListener("keydown", function (event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    var row = event.target.closest("tr[data-case-id]");
    if (!row) return;
    event.preventDefault();
    selectCase(row.getAttribute("data-case-id"));
  });

  document.querySelectorAll("[data-action]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      applyAction(btn.getAttribute("data-action"));
    });
  });

  var archiveBtn = document.querySelector("#archive-case-btn");
  var restoreBtn = document.querySelector("#restore-case-btn");
  var archiveCancelBtn = document.querySelector("#archive-cancel-btn");
  var archiveConfirmBtn = document.querySelector("#archive-confirm-btn");

  if (archiveBtn) {
    archiveBtn.addEventListener("click", openArchiveDialog);
  }
  if (restoreBtn) {
    restoreBtn.addEventListener("click", restoreSelectedCase);
  }
  if (archiveCancelBtn) {
    archiveCancelBtn.addEventListener("click", closeArchiveDialog);
  }
  if (archiveConfirmBtn) {
    archiveConfirmBtn.addEventListener("click", archiveSelectedCase);
  }
  document.querySelectorAll("[data-archive-cancel]").forEach(function (el) {
    el.addEventListener("click", closeArchiveDialog);
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && archiveDialog && !archiveDialog.hidden) {
      closeArchiveDialog();
    }
  });

  [searchEl, riskEl, languageEl, interactionEl, statusEl].forEach(function (el) {
    if (!el) return;
    el.addEventListener("input", function () {
      renderTable();
    });
    el.addEventListener("change", function () {
      renderTable();
    });
  });

  updateSummary();
  renderTable();
  renderDetail(null);

  var focusId = queryCaseId();
  if (focusId && findCase(focusId)) {
    selectCase(focusId);
  }
})();
