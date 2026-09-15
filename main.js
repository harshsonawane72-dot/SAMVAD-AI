/**
 * SAMVAD AI — shared frontend helpers
 * Landing: mobile nav
 * Assessment UI lives in assessment.js (calls mock-ai.js)
 */

// Unified API base URL configuration:
// - Uses production Cloudflare Tunnel when deployed on Vercel
// - Falls back to local http://127.0.0.1:8000 when developing locally or on file://
(function () {
  if (typeof window !== "undefined" && !window.SAMVAD_API_BASE_URL) {
    var isLocal =
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1" ||
      window.location.protocol === "file:";
    window.SAMVAD_API_BASE_URL = isLocal
      ? "http://127.0.0.1:8000"
      : "https://farmer-oriental-specialists-ringtone.trycloudflare.com";
  }
})();

const SAMVAD = {
  version: "0.1.0-prototype",
  storageKey: "samvad_demo_session",
  casesKey: "samvad_cases",
};

/**
 * Prototype localStorage helpers for assessment → dashboard cases.
 * Browser-only. No backend. No PII fields (names, phones, addresses).
 */
const CaseStore = (function () {
  "use strict";

  var KEY = SAMVAD.casesKey;

  function loadRaw() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
      console.warn("SAMVAD CaseStore: could not read localStorage.", err);
      return [];
    }
  }

  function saveRaw(list) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
      return true;
    } catch (err) {
      console.warn("SAMVAD CaseStore: could not write localStorage.", err);
      return false;
    }
  }

  function findIndex(list, caseId) {
    for (var i = 0; i < list.length; i += 1) {
      if (list[i] && list[i].caseId === caseId) return i;
    }
    return -1;
  }

  return {
    KEY: KEY,
    load: loadRaw,
    /**
     * Insert a new assessment case. Skips if the same caseId already exists
     * so re-analyze / refresh does not duplicate the row.
     */
    addIfNew: function (caseObj) {
      if (!caseObj || !caseObj.caseId) return false;
      var list = loadRaw();
      if (findIndex(list, caseObj.caseId) !== -1) return false;
      list.push(caseObj);
      return saveRaw(list);
    },
    /** Insert or replace by caseId (used for operator actions). */
    upsert: function (caseObj) {
      if (!caseObj || !caseObj.caseId) return false;
      var list = loadRaw();
      var idx = findIndex(list, caseObj.caseId);
      if (idx === -1) list.push(caseObj);
      else list[idx] = caseObj;
      return saveRaw(list);
    },
    toStorageRecord: function (item) {
      return {
        caseId: item.id || item.caseId,
        timestamp: item.datetime || item.timestamp || "",
        createdAt: item.createdAt || "",
        language: item.language || "",
        interactionType: item.interaction || item.interactionType || "",
        statement: item.statement || "",
        svi: item.svi,
        stress: item.components ? item.components.stress : item.stress,
        vulnerability: item.components
          ? item.components.vulnerability
          : item.vulnerability,
        urgency: item.components ? item.components.urgency : item.urgency,
        safety: item.components ? item.components.safetyConcern : item.safety,
        riskLevel: item.risk || item.riskLevel,
        indicators: item.indicators || [],
        recommendation: item.aiRecommendation || item.recommendation || "",
        status: item.status || "New",
        humanReviewStatus: item.humanReviewStatus || item.status || "New",
        previousStatus: item.previousStatus || "",
        supportPathway: item.supportPathway || item.recommendation || "",
        safetyFlag: !!item.safetyFlag,
        timeline: item.timeline || [],
        source: item.source || "assessment",
      };
    },
  };
})();

(function initLandingNav() {
  const header = document.querySelector(".site-header");
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector("#site-nav");

  if (!header || !toggle || !nav) return;

  function setOpen(isOpen) {
    header.classList.toggle("is-open", isOpen);
    toggle.setAttribute("aria-expanded", String(isOpen));
    toggle.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
  }

  toggle.addEventListener("click", function () {
    setOpen(!header.classList.contains("is-open"));
  });

  nav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") setOpen(false);
  });

  document.addEventListener("click", function (event) {
    if (!header.contains(event.target)) setOpen(false);
  });

  function updateCurrentNav() {
    var hash = window.location.hash || "#home";
    nav.querySelectorAll('a[href^="#"]').forEach(function (link) {
      var href = link.getAttribute("href");
      if (href === hash) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  updateCurrentNav();
  window.addEventListener("hashchange", updateCurrentNav);
})();
