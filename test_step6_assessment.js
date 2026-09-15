/**
 * SAMVAD AI — Step 6.5: Multilingual Language Detection & STT Flow Verification
 */

const fs = require("fs");
const path = require("path");
const http = require("http");

console.log("=== SAMVAD AI: Step 6.5 Multilingual Language Detection & Flow Tests ===");

// 1. Verify assessment.html does NOT contain manual language radio selection
const htmlContent = fs.readFileSync(path.join(__dirname, "assessment.html"), "utf8");

if (htmlContent.includes('name="language"')) {
  console.error("FAIL: assessment.html still contains input[name='language']!");
  process.exit(1);
} else {
  console.log("PASS: assessment.html has no manual Preferred Language radio buttons.");
}

if (htmlContent.includes("Preferred Language")) {
  console.error("FAIL: assessment.html still contains 'Preferred Language' label/legend!");
  process.exit(1);
} else {
  console.log("PASS: 'Preferred Language' user selection successfully removed.");
}

// 2. Verify assessment.html contains result-language-wrap (hidden by default)
if (!htmlContent.includes('id="result-language-wrap" hidden')) {
  console.error("FAIL: assessment.html missing id='result-language-wrap' hidden!");
  process.exit(1);
} else {
  console.log("PASS: assessment.html contains #result-language-wrap with hidden attribute.");
}

// 3. Verify developer architecture documentation comment in assessment.js
const jsContent = fs.readFileSync(path.join(__dirname, "assessment.js"), "utf8");
const archComment =
  "Automatic language detection is designed as a multilingual architecture. Actual supported languages depend on the configured language-identification, speech-recognition, and text-understanding models/services. The prototype must never claim unsupported universal language coverage.";

if (!jsContent.includes(archComment)) {
  console.error("FAIL: Developer architecture comment missing in assessment.js!");
  process.exit(1);
} else {
  console.log("PASS: Developer architecture comment correctly present in assessment.js.");
}

// 4. Verify detectLanguageRemote and detectStatementLanguage functions
if (!jsContent.includes("function detectLanguageRemote(")) {
  console.error("FAIL: detectLanguageRemote function missing in assessment.js!");
  process.exit(1);
} else {
  console.log("PASS: detectLanguageRemote function defined in assessment.js.");
}

const detectFnMatch = jsContent.match(/function detectStatementLanguage\(text\) \{([\s\S]*?)\n  \}/);
if (!detectFnMatch) {
  console.error("FAIL: detectStatementLanguage not found in assessment.js!");
  process.exit(1);
}
const detectStatementLanguage = new Function("text", detectFnMatch[1]);

// 5. Test synchronous fallback logic
const fallbackTests = [
  { text: "I am feeling very worried about my situation and I need support.", expected: "English" },
  { text: "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.", expected: "Hindi" },
  { text: "Mujhe kaafi stress ho raha hai aur mujhe madad chahiye.", expected: "Hindi" },
  { text: "मुझे अपनी शिकायत की प्रक्रिया के बारे में जानकारी चाहिए।", expected: "Hindi" },
  { text: "मला माझ्या तक्रार प्रक्रियेबद्दल माहिती हवी आहे. मी खूप चिंतेत आहे.", expected: "Marathi" },
  { text: "मला त्वरित मदत हवी आहे आणि मी खूप घाबरलो आहे.", expected: "Marathi" },
  { text: "12345 !@#$", expected: null },
  { text: "", expected: null },
];

fallbackTests.forEach((t) => {
  const res = detectStatementLanguage(t.text);
  const label = res ? res.label : null;
  if (label === t.expected) {
    console.log(`PASS (local fallback): "${t.text.slice(0, 35)}..." -> Detected: ${label}`);
  } else {
    console.error(`FAIL (local fallback): "${t.text.slice(0, 35)}..." -> Expected: ${t.expected}, Got: ${label}`);
    process.exit(1);
  }
});

// 6. Verify existing STT safeguards in assessment.js
const safeguards = [
  { name: "Consent check before voice input", check: jsContent.includes("!consentCheckbox.checked") },
  { name: "Low confidence threshold", check: jsContent.includes("LOW_CONFIDENCE_THRESHOLD = 0.45") },
  { name: "Max voice restarts protection", check: jsContent.includes("MAX_VOICE_RESTARTS = 6") },
  { name: "Duplicate suffix prevention", check: jsContent.includes("function isDuplicateSuffix(") },
  { name: "Overlapping prefix removal", check: jsContent.includes("function removeOverlappingPrefix(") },
  { name: "Mobile restart protection", check: jsContent.includes("voiceRestartCount >=") },
  { name: "Manual typed text preservation", check: jsContent.includes("// Preserve existing manually typed text") },
  { name: "Voice transcript triggers language detection", check: jsContent.includes("detectLanguageRemote(statementInput.value)") },
  { name: "Typed statement submit triggers language detection", check: jsContent.includes("detectLanguageRemote(statement)") },
];

safeguards.forEach((sg) => {
  if (sg.check) {
    console.log(`PASS: Safeguard verified: ${sg.name}`);
  } else {
    console.error(`FAIL: Missing safeguard: ${sg.name}`);
    process.exit(1);
  }
});

// 7. Live Backend Tests: POST /ai/detect-language and GET /ai/transcribe
function postJson(path, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const req = http.request(
      {
        hostname: "127.0.0.1",
        port: 8000,
        path: path,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(data),
        },
      },
      (res) => {
        let body = "";
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          try {
            resolve({ status: res.statusCode, body: JSON.parse(body) });
          } catch (e) {
            reject(e);
          }
        });
      }
    );
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

function getJson(path) {
  return new Promise((resolve, reject) => {
    const req = http.get({ hostname: "127.0.0.1", port: 8000, path: path }, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(body) });
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on("error", reject);
  });
}

async function runLiveTests() {
  console.log("\n--- Running Live Backend Endpoint Tests ---");

  // GET /ai/transcribe
  const transcribeRes = await getJson("/ai/transcribe");
  console.log(`PASS: GET /ai/transcribe returned status=${transcribeRes.status}, provider=${transcribeRes.body.provider}, status=${transcribeRes.body.status}`);
  if (transcribeRes.body.status !== "not_configured") {
    console.error("FAIL: Expected status 'not_configured' for unconfigured Bhashini.");
    process.exit(1);
  }

  // POST /ai/detect-language: English
  const enRes = await postJson("/ai/detect-language", { text: "I need immediate help with this issue." });
  console.log(`PASS: POST /ai/detect-language (English) -> ${enRes.body.language_name} (${enRes.body.language_code}) [conf: ${enRes.body.confidence}]`);
  if (enRes.body.language_code !== "en") {
    console.error("FAIL: Expected en, got " + enRes.body.language_code);
    process.exit(1);
  }

  // POST /ai/detect-language: Hindi Devanagari
  const hiRes = await postJson("/ai/detect-language", { text: "मुझे तुरंत सहायता चाहिए।" });
  console.log(`PASS: POST /ai/detect-language (Hindi) -> ${hiRes.body.language_name} (${hiRes.body.language_code}) [conf: ${hiRes.body.confidence}]`);
  if (hiRes.body.language_code !== "hi") {
    console.error("FAIL: Expected hi, got " + hiRes.body.language_code);
    process.exit(1);
  }

  // POST /ai/detect-language: Marathi Devanagari
  const mrRes = await postJson("/ai/detect-language", { text: "मला त्वरित मदतीची गरज आहे आणि खूप भीती वाटत आहे." });
  console.log(`PASS: POST /ai/detect-language (Marathi) -> ${mrRes.body.language_name} (${mrRes.body.language_code}) [conf: ${mrRes.body.confidence}]`);
  if (mrRes.body.language_code !== "mr") {
    console.error("FAIL: Expected mr, got " + mrRes.body.language_code);
    process.exit(1);
  }

  // POST /ai/detect-language: Hinglish
  const hinglishRes = await postJson("/ai/detect-language", { text: "Mujhe help chahiye please call me" });
  console.log(`PASS: POST /ai/detect-language (Hinglish) -> ${hinglishRes.body.language_name} (${hinglishRes.body.language_code}) [conf: ${hinglishRes.body.confidence}]`);
  if (hinglishRes.body.language_code !== "hi") {
    console.error("FAIL: Expected hi for Hinglish, got " + hinglishRes.body.language_code);
    process.exit(1);
  }

  // POST /ai/detect-language: Symbols/Numbers (No fake guessing)
  const symRes = await postJson("/ai/detect-language", { text: "12345 !@#$%^" });
  console.log(`PASS: POST /ai/detect-language (Symbols) -> status=${symRes.body.status}, lang=${symRes.body.language_name}`);
  if (symRes.body.status !== "unknown" || symRes.body.language_code !== "unknown") {
    console.error("FAIL: Expected unknown for symbols, got " + JSON.stringify(symRes.body));
    process.exit(1);
  }

  console.log("\n=== ALL STEP 6.5 VERIFICATION TESTS PASSED SUCCESSFULLY! ===");
}

runLiveTests().catch((err) => {
  console.error("FAIL: Live test execution error:", err);
  process.exit(1);
});
