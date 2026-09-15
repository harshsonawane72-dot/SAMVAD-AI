"""
Comparative test suite:
Compares FastAPI backend /analyze responses with mock-ai.js outputs for the exact same statements.
"""

import json
import subprocess
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

# Statements representing all 4 risk tiers + empty
TEST_STATEMENTS = [
    {
        "tier": "LOW",
        "statement": "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.",
        "language": "hindi",
    },
    {
        "tier": "MODERATE",
        "statement": "Mujhe kaafi stress ho raha hai aur mujhe samajh nahi aa raha ki complaint ko kaise proceed karun. Mujhe support chahiye.",
        "language": "hindi",
    },
    {
        "tier": "HIGH",
        "statement": "Mujhe bahut fear aur pressure feel ho raha hai. Mujhe lag raha hai ki main is situation ko akela handle nahi kar pa raha/rahi. Mujhe jaldi support chahiye.",
        "language": "hindi",
    },
    {
        "tier": "CRITICAL",
        "statement": "Mujhe abhi safe feel nahi ho raha. Mujhe immediate help chahiye aur main situation ko akela handle nahi kar sakta/sakti.",
        "language": "hindi",
    },
    {
        "tier": "ENGLISH_CRITICAL",
        "statement": "I do not feel safe right now. I need immediate help. I cannot stay safe and I am alone.",
        "language": "english",
    },
]


def get_mock_ai_results():
    """Run Node.js script to execute mock-ai.js on the test statements and return JSON."""
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent
    mock_ai_file = (base_dir / "mock-ai.js") if (base_dir / "mock-ai.js").exists() else (base_dir.parent / "mock-ai.js")
    node_script = """
    const fs = require('fs');
    const vm = require('vm');
    const code = fs.readFileSync(PATH_PLACEHOLDER, 'utf8');
    vm.runInThisContext(code);

    const statements = JSON.parse(process.argv[1]);
    const results = statements.map(item => {
        return {
            tier: item.tier,
            statement: item.statement,
            language: item.language,
            result: MockAI.analyze(item.statement, { language: item.language })
        };
    });
    console.log(JSON.stringify(results));
    """.replace("PATH_PLACEHOLDER", json.dumps(str(mock_ai_file)))
    proc = subprocess.run(
        ["node", "-e", node_script, json.dumps(TEST_STATEMENTS)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def query_backend_analyze(statement, language="english"):
    url = f"{BASE_URL}/analyze"
    payload = json.dumps({"statement": statement, "language": language}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def test_empty_statement_validation():
    print("\n--- Test Empty Statement Validation ---")
    status, body = query_backend_analyze("   ", "english")
    print(f"Empty statement response: status={status}, body={body}")
    assert status == 400, f"Expected 400, got {status}"
    assert "Statement must not be empty" in str(body), "Error message mismatch"
    print("PASS: Empty statement rejected with HTTP 400.")


def test_cases_endpoints_intact():
    print("\n--- Test Existing /cases Endpoints Still Work ---")
    req = urllib.request.Request(f"{BASE_URL}/cases", method="GET")
    with urllib.request.urlopen(req) as resp:
        cases = json.loads(resp.read().decode("utf-8"))
        print(f"GET /cases returned {len(cases)} cases.")
        assert resp.status == 200
    print("PASS: Existing /cases endpoint is healthy and untouched.")


def main():
    print("=== Step 5A: SVI Analysis Comparison Verification ===")

    test_empty_statement_validation()
    test_cases_endpoints_intact()

    mock_results = get_mock_ai_results()

    print("\n--- Comparing Backend /analyze vs mock-ai.js ---")
    for item in mock_results:
        tier = item["tier"]
        statement = item["statement"]
        language = item["language"]
        js_res = item["result"]

        status, py_res = query_backend_analyze(statement, language)
        assert status == 200, f"Backend failed for {tier}: status={status}"

        print(f"\n[{tier}] Statement: \"{statement[:60]}...\"")
        print(f"  MockAI.js: SVI={js_res['svi']}, Risk={js_res['riskLevel']}, Components={js_res['components']}, HumanReview={js_res['immediateHumanReview']}")
        print(f"  Backend:   SVI={py_res['svi']}, Risk={py_res['risk_level']}, Stress={py_res['stress']}, Vuln={py_res['vulnerability']}, Urg={py_res['urgency']}, Safety={py_res['safety']}, HumanReview={py_res['human_review']}")

        # Strict Assertions between JS and Python
        assert py_res["stress"] == js_res["components"]["stress"], f"Stress mismatch for {tier}: Py={py_res['stress']}, JS={js_res['components']['stress']}"
        assert py_res["vulnerability"] == js_res["components"]["vulnerability"], f"Vulnerability mismatch for {tier}: Py={py_res['vulnerability']}, JS={js_res['components']['vulnerability']}"
        assert py_res["urgency"] == js_res["components"]["urgency"], f"Urgency mismatch for {tier}: Py={py_res['urgency']}, JS={js_res['components']['urgency']}"
        assert py_res["safety"] == js_res["components"]["safetyConcern"], f"Safety mismatch for {tier}: Py={py_res['safety']}, JS={js_res['components']['safetyConcern']}"
        assert py_res["svi"] == js_res["svi"], f"SVI mismatch for {tier}: Py={py_res['svi']}, JS={js_res['svi']}"
        assert py_res["risk_level"] == js_res["riskLevel"], f"Risk Level mismatch for {tier}: Py={py_res['risk_level']}, JS={js_res['riskLevel']}"
        assert py_res["human_review"] == js_res["immediateHumanReview"], f"Human Review mismatch for {tier}: Py={py_res['human_review']}, JS={js_res['immediateHumanReview']}"
        assert py_res["indicators"] == js_res["indicators"], f"Indicators mismatch for {tier}: Py={py_res['indicators']}, JS={js_res['indicators']}"

        print(f"  --> MATCH: 100% identical results for {tier}!")

    print("\n=== ALL STEP 5A VERIFICATION TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()
