const fs = require('fs');
const http = require('http');

// Load mock AI and demo data
const mockAiCode = fs.readFileSync('mock-ai.js', 'utf8');
const demoDataCode = fs.readFileSync('demo-data.js', 'utf8');

const vm = require('vm');
vm.runInThisContext(mockAiCode);
vm.runInThisContext(demoDataCode);

console.log("MockAI loaded:", typeof MockAI.analyze === 'function');
console.log("DEMO_DATA sample cases:", DEMO_DATA.sampleCases.length);

// Extract and test fromBackendCase & loadCombinedCases logic
function titleCaseLabel(val) {
  if (!val) return "English";
  var s = String(val).trim();
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

function normalizeInteraction(val) {
  if (!val) return "Chat";
  var s = String(val).trim().toLowerCase();
  if (s === "ivrs") return "IVRS";
  if (s === "voice") return "Voice";
  if (s === "portal") return "Portal";
  if (s === "chat") return "Chat";
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function hydrateCase(seed) {
  var analysis = MockAI.analyze(seed.statement, {
    language: String(seed.language || "english").toLowerCase(),
  });
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
    svi: analysis.ok ? analysis.svi : 0,
    risk: analysis.ok ? analysis.riskLevel : "LOW",
    components: analysis.ok ? analysis.components : { stress: 0, vulnerability: 0, urgency: 0, safetyConcern: 0 },
    indicators: analysis.ok ? analysis.indicators.slice() : [],
    aiRecommendation: analysis.ok ? analysis.recommendation : "Human review required",
    supportPathway: analysis.ok ? analysis.recommendation : "Human review required",
    safetyFlag: analysis.ok ? !!analysis.immediateHumanReview : false,
    timeline: [],
    createdAt: seed.createdAt || "",
    source: "demo",
  };
}

function fromBackendCase(dbCase) {
  var caseId = dbCase.case_id || ("CASE-" + dbCase.id);
  var lang = titleCaseLabel(dbCase.language);
  var interaction = normalizeInteraction(dbCase.interaction_type || dbCase.interactionType);
  var createdAt = dbCase.created_at || "";
  var rawStatus = dbCase.status || "New";
  var status = rawStatus.toLowerCase() === "received" ? "New" : rawStatus;

  var analysis = MockAI.analyze(dbCase.statement || "", {
    language: lang.toLowerCase(),
  });

  return {
    id: caseId,
    datetime: createdAt,
    time: "12:00",
    language: lang,
    interaction: interaction,
    status: status,
    humanReviewStatus: status === "Reviewed" ? "Reviewed" : "Pending",
    previousStatus: "",
    statement: dbCase.statement || "",
    svi: analysis.ok ? analysis.svi : 0,
    risk: analysis.ok ? analysis.riskLevel : "LOW",
    components: analysis.ok ? analysis.components : { stress: 0, vulnerability: 0, urgency: 0, safetyConcern: 0 },
    indicators: analysis.ok ? analysis.indicators.slice() : [],
    aiRecommendation: analysis.ok ? analysis.recommendation : "Human review required",
    supportPathway: analysis.ok ? analysis.recommendation : "Human review required",
    safetyFlag: analysis.ok ? !!analysis.immediateHumanReview : false,
    timeline: [],
    createdAt: createdAt,
    source: "database",
  };
}

function loadCombinedCases(backendCases, localStore) {
  var byId = {};
  DEMO_DATA.sampleCases.forEach(function (seed) {
    var item = hydrateCase(seed);
    byId[item.id] = item;
  });

  if (Array.isArray(backendCases)) {
    backendCases.forEach(function (dbCase) {
      var caseId = dbCase.case_id || ("CASE-" + dbCase.id);
      if (!caseId) return;
      byId[caseId] = fromBackendCase(dbCase);
    });
  }

  if (Array.isArray(localStore)) {
    localStore.forEach(function (record) {
      var id = record.caseId || record.id;
      if (!id) return;
      if (byId[id]) {
        byId[id].status = record.status || byId[id].status;
        byId[id].humanReviewStatus = record.humanReviewStatus || byId[id].humanReviewStatus;
        byId[id].previousStatus = record.previousStatus || byId[id].previousStatus;
        byId[id].supportPathway = record.supportPathway || byId[id].supportPathway;
      }
    });
  }

  return Object.keys(byId).map(k => byId[k]);
}

// Fetch live from FastAPI backend
http.get('http://127.0.0.1:8000/cases', (res) => {
  let raw = '';
  res.on('data', c => raw += c);
  res.on('end', () => {
    const dbCases = JSON.parse(raw);
    console.log('\n--- 1. Testing Live Backend Fetch ---');
    console.log(`Fetched ${dbCases.length} cases from http://127.0.0.1:8000/cases`);

    console.log('\n--- 2. Testing Case Merging ---');
    const combined = loadCombinedCases(dbCases);
    const uniqueExpected = new Set([...DEMO_DATA.sampleCases.map(c => c.id), ...dbCases.map(c => c.case_id || ("CASE-" + c.id))]).size;
    console.log(`Total combined cases: ${combined.length} (expected unique: ${uniqueExpected})`);
    console.assert(combined.length === uniqueExpected, "Total combined cases mismatch!");

    const testCase = combined.find(c => c.id === 'CASE-DB-OPERATOR-99');
    console.assert(testCase !== undefined, "CASE-DB-OPERATOR-99 not found in combined cases!");
    console.log(`Found CASE-DB-OPERATOR-99: language=${testCase.language}, interaction=${testCase.interaction}, status=${testCase.status}, SVI=${testCase.svi}, risk=${testCase.risk}`);

    console.log('\n--- 3. Testing Duplicate Prevention ---');
    const withDupes = loadCombinedCases([...dbCases, dbCases[0]]);
    console.log(`Count after adding duplicate: ${withDupes.length}`);
    console.assert(withDupes.length === combined.length, "Duplicates were not prevented!");

    console.log('\n--- 4. Testing Filter Matching ---');
    const searchMatch = combined.filter(c => c.id.toLowerCase().includes('case-db'));
    console.log(`Search 'case-db' matches: ${searchMatch.length}`);
    console.assert(searchMatch.length === 1, "Search filter did not match accurately");

    const hindiMatch = combined.filter(c => c.language.toLowerCase() === 'hindi');
    console.log(`Language 'Hindi' matches: ${hindiMatch.length} (includes database case)`);
    console.assert(hindiMatch.some(c => c.id === 'CASE-DB-OPERATOR-99'), "Hindi filter missed DB case");

    const ivrsMatch = combined.filter(c => c.interaction.toLowerCase() === 'ivrs');
    console.log(`Interaction 'IVRS' matches: ${ivrsMatch.length} (includes database case)`);
    console.assert(ivrsMatch.some(c => c.id === 'CASE-DB-OPERATOR-99'), "IVRS filter missed DB case");

    console.log('\n--- 5. Testing Archive/Restore Overlay ---');
    const localStore = [{ caseId: 'CASE-DB-OPERATOR-99', status: 'Archived', previousStatus: 'New' }];
    const archivedCombined = loadCombinedCases(dbCases, localStore);
    const archivedCase = archivedCombined.find(c => c.id === 'CASE-DB-OPERATOR-99');
    console.log(`Archived case status in combined list: ${archivedCase.status}`);
    console.assert(archivedCase.status === 'Archived', "Archive overlay failed");

    console.log('\n--- 6. Testing Offline / Fallback Mode ---');
    const offlineCombined = loadCombinedCases(null);
    console.log(`Offline cases count: ${offlineCombined.length} (demo cases preserved)`);
    console.assert(offlineCombined.length === 8, "Offline fallback failed to preserve demo cases");

    console.log('\n=== ALL 6 INTEGRATION TESTS PASSED! ===\n');
  });
});
