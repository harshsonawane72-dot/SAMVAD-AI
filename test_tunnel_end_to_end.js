/**
 * SAMVAD AI — Cloudflare Tunnel End-to-End & Integration Test
 * Verifies:
 * 1. Frontend dynamic base URL resolution (Vercel production vs localhost fallback)
 * 2. Public Cloudflare Tunnel reachability (/health)
 * 3. CORS preflight headers for https://samvad-ai-jet.vercel.app
 * 4. Full AI assessment pipeline via public tunnel (/ai/assess)
 * 5. Case creation and SQLite persistence (/cases)
 * 6. Dashboard case retrieval via public tunnel (GET /cases)
 * 7. Local development fallback preservation
 */

const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const TUNNEL_URL = "https://farmer-oriental-specialists-ringtone.trycloudflare.com";
const LOCAL_URL = "http://127.0.0.1:8000";
const VERCEL_ORIGIN = "https://samvad-ai-jet.vercel.app";

let passedCount = 0;
let totalCount = 0;

function assert(condition, message) {
  totalCount++;
  if (condition) {
    console.log(`  PASS: ${message}`);
    passedCount++;
  } else {
    console.error(`  FAIL: ${message}`);
    process.exitCode = 1;
  }
}

function fetchJson(url, options = {}, postData = null) {
  return new Promise((resolve, reject) => {
    const isHttps = url.startsWith("https://");
    const client = isHttps ? https : http;
    const parsed = new URL(url);

    const reqOptions = {
      hostname: parsed.hostname,
      port: parsed.port || (isHttps ? 443 : 80),
      path: parsed.pathname + parsed.search,
      method: options.method || "GET",
      headers: options.headers || {},
    };

    if (postData) {
      if (!reqOptions.headers["Content-Type"]) {
        reqOptions.headers["Content-Type"] = "application/json";
      }
      reqOptions.headers["Content-Length"] = Buffer.byteLength(postData);
    }

    const req = client.request(reqOptions, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const parsedBody = data ? JSON.parse(data) : {};
          resolve({ status: res.statusCode, headers: res.headers, data: parsedBody, raw: data });
        } catch (e) {
          resolve({ status: res.statusCode, headers: res.headers, data: null, raw: data });
        }
      });
    });

    req.on("error", reject);
    if (postData) req.write(postData);
    req.end();
  });
}

async function runTests() {
  console.log("=== SAMVAD AI: CLOUDFLARE TUNNEL END-TO-END VALIDATION ===\n");

  // TEST 1: Frontend base URL resolution in main.js
  console.log("Test 1: Frontend API Base URL Configuration & Resolution");
  const mainJsContent = fs.readFileSync(path.join(__dirname, "main.js"), "utf8");

  // Simulate Vercel production browser environment
  let mockWindowVercel = {
    location: { hostname: "samvad-ai-jet.vercel.app", protocol: "https:" }
  };
  let mockDoc = {
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener: () => { },
  };
  const evalFunc = new Function("window", "document", mainJsContent + "\nreturn window.SAMVAD_API_BASE_URL;");
  const resolvedVercelBase = evalFunc(mockWindowVercel, mockDoc);
  assert(
    resolvedVercelBase === TUNNEL_URL,
    `Production Vercel resolves to Cloudflare tunnel: ${resolvedVercelBase}`
  );

  // Simulate Localhost browser environment
  let mockWindowLocal = {
    location: { hostname: "localhost", protocol: "http:" }
  };
  const resolvedLocalBase = evalFunc(mockWindowLocal, mockDoc);
  assert(
    resolvedLocalBase === LOCAL_URL,
    `Localhost resolves to local backend: ${resolvedLocalBase}`
  );

  // TEST 2: Public Cloudflare Tunnel /health check
  console.log("\nTest 2: Public Cloudflare Tunnel /health check");
  const healthRes = await fetchJson(`${TUNNEL_URL}/health`);
  assert(healthRes.status === 200, `Tunnel /health returned HTTP 200 (Got: ${healthRes.status})`);
  assert(healthRes.data && healthRes.data.status === "healthy", "Backend status is healthy");

  // TEST 3: CORS verification from Vercel Origin
  console.log("\nTest 3: CORS Headers Verification");
  const corsRes = await fetchJson(`${TUNNEL_URL}/ai/assess`, {
    method: "OPTIONS",
    headers: {
      "Origin": VERCEL_ORIGIN,
      "Access-Control-Request-Method": "POST",
      "Access-Control-Request-Headers": "Content-Type",
    },
  });
  assert(corsRes.status === 200, `CORS preflight returned HTTP 200 (Got: ${corsRes.status})`);
  const allowOrigin = corsRes.headers["access-control-allow-origin"];
  assert(
    allowOrigin === VERCEL_ORIGIN,
    `Access-Control-Allow-Origin matches Vercel: ${allowOrigin}`
  );

  // TEST 4: Unified AI Assessment via Public Tunnel
  console.log("\nTest 4: Unified AI Assessment Pipeline via Tunnel (/ai/assess)");
  const statementText = "Main bohot pareshan hoon, mujhe emergency support ki zaroorat hai";
  const assessPayload = JSON.stringify({
    text: statementText,
    language: "hi",
    interaction_mode: "chat",
    is_voice: false,
  });

  const assessRes = await fetchJson(
    `${TUNNEL_URL}/ai/assess`,
    {
      method: "POST",
      headers: { "Origin": VERCEL_ORIGIN }
    },
    assessPayload
  );

  assert(assessRes.status === 200, `AI assess endpoint returned HTTP 200 (Got: ${assessRes.status})`);
  const assessData = assessRes.data;
  assert(assessData && assessData.case_id, `Generated case_id: ${assessData ? assessData.case_id : "none"}`);
  assert(assessData && assessData.risk_classification, "Contains IndicBERT risk classification");
  assert(assessData && typeof assessData.svi.score === "number", `Computed SVI score: ${assessData.svi.score}`);
  assert(Array.isArray(assessData.support_resources), `Retrieved ${assessData.support_resources.length} support resources via RAG`);

  // TEST 5: Persist Case into SQLite via Tunnel
  console.log("\nTest 5: Case Persistence into SQLite (/cases)");
  const newCaseId = `NHAA-TEST-${Date.now().toString(36).toUpperCase()}`;
  const casePayload = JSON.stringify({
    case_id: newCaseId,
    statement: statementText,
    language: "Hindi",
    interaction_type: "Chat",
    consent: true,
  });

  const createCaseRes = await fetchJson(
    `${TUNNEL_URL}/cases`,
    {
      method: "POST",
      headers: { "Origin": VERCEL_ORIGIN }
    },
    casePayload
  );

  assert(createCaseRes.status === 200 || createCaseRes.status === 201, `Case creation returned HTTP ${createCaseRes.status}`);
  assert(createCaseRes.data && createCaseRes.data.case_id === newCaseId, `Case saved with case_id: ${newCaseId}`);

  // TEST 6: Dashboard Case Retrieval via Public Tunnel (GET /cases)
  console.log("\nTest 6: Operator Dashboard Case Retrieval (GET /cases)");
  const getCasesRes = await fetchJson(`${TUNNEL_URL}/cases`, {
    headers: { "Origin": VERCEL_ORIGIN }
  });

  assert(getCasesRes.status === 200, `GET /cases returned HTTP 200 (Got: ${getCasesRes.status})`);
  assert(Array.isArray(getCasesRes.data), `Retrieved ${getCasesRes.data.length} cases from SQLite`);
  const foundCase = getCasesRes.data.find(c => c.case_id === newCaseId);
  assert(!!foundCase, `Newly created case ${newCaseId} successfully retrieved by Dashboard query`);
  assert(foundCase && foundCase.statement === statementText, "Statement preserved accurately without corruption");

  // TEST 7: Localhost Dev Fallback Check
  console.log("\nTest 7: Localhost Development Endpoint Check");
  const localHealth = await fetchJson(`${LOCAL_URL}/health`);
  assert(localHealth.status === 200, `Local backend is independently responsive on http://127.0.0.1:8000`);

  console.log(`\n==================================================`);
  console.log(`RESULTS: ${passedCount} / ${totalCount} CHECKS PASSED`);
  console.log(`==================================================\n`);

  if (passedCount !== totalCount) {
    process.exit(1);
  }
}

runTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
