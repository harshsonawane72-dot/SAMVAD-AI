"""
SAMVAD AI — Step 6.6 Test Suite: Context-Aware Safety Understanding for SVI
Verifies:
1. Statement A: "I’m worried that I may not be able to keep myself safe." -> Meaningful safety concern, human review = True, HIGH risk tier.
2. Statement B: "I don't feel safe right now." -> Strong safety concern, human review = True, HIGH risk tier.
3. Statement C: "I feel safe now." -> Affirmative safe, no false escalation, LOW risk tier, human review = False.
4. Statement D: "I want information about my application status." -> Informational low risk, LOW risk tier, human review = False.
5. Multilingual safety concerns:
   - Hindi: "मुझे डर है कि मैं खुद को सुरक्षित नहीं रख पाऊँगा।" -> Meaningful safety concern, human review = True, HIGH.
   - Hinglish: "Mujhe chinta hai ki main khud ko safe nahi rakh paunga." -> Meaningful safety concern, human review = True, HIGH.
   - Marathi: "मला भीती वाटते की मी स्वतःला सुरक्षित ठेवू शकणार नाही." -> Meaningful safety concern, human review = True, HIGH.
6. Acute immediate danger statement:
   - "I do not feel safe right now. I need immediate help. I cannot stay safe and I am alone." -> CRITICAL risk tier (SVI 79).
7. Full synchronization between backend/svi_engine.py and mock-ai.js.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.svi_engine import analyze_statement


TEST_CASES = [
    {
        "id": "A",
        "name": "Personal safety inability (Target)",
        "statement": "I’m worried that I may not be able to keep myself safe.",
        "language": "english",
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "expected_safety_flag": True,
        "expected_svi_range": (50, 74),
        "check_safety_concern": True,
    },
    {
        "id": "B",
        "name": "Negated safety / feeling unsafe",
        "statement": "I don't feel safe right now.",
        "language": "english",
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "expected_safety_flag": True,
        "expected_svi_range": (50, 74),
        "check_safety_concern": True,
    },
    {
        "id": "C",
        "name": "Affirmative safe expression",
        "statement": "I feel safe now.",
        "language": "english",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_safety_flag": False,
        "expected_svi_range": (0, 24),
        "check_safety_concern": False,
    },
    {
        "id": "D",
        "name": "Informational inquiry",
        "statement": "I want information about my application status.",
        "language": "english",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "expected_safety_flag": False,
        "expected_svi_range": (0, 24),
        "check_safety_concern": False,
    },
    {
        "id": "E",
        "name": "Hindi contextual safety concern",
        "statement": "मुझे डर है कि मैं खुद को सुरक्षित नहीं रख पाऊँगा।",
        "language": "hindi",
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "expected_safety_flag": True,
        "expected_svi_range": (50, 74),
        "check_safety_concern": True,
    },
    {
        "id": "F",
        "name": "Hinglish contextual safety concern",
        "statement": "Mujhe chinta hai ki main khud ko safe nahi rakh paunga.",
        "language": "hindi",
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "expected_safety_flag": True,
        "expected_svi_range": (50, 74),
        "check_safety_concern": True,
    },
    {
        "id": "G",
        "name": "Marathi contextual safety concern",
        "statement": "मला भीती वाटते की मी स्वतःला सुरक्षित ठेवू शकणार नाही.",
        "language": "marathi",
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "expected_safety_flag": True,
        "expected_svi_range": (50, 74),
        "check_safety_concern": True,
    },
    {
        "id": "H",
        "name": "Acute immediate crisis statement",
        "statement": "I do not feel safe right now. I need immediate help. I cannot stay safe and I am alone.",
        "language": "english",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "expected_safety_flag": True,
        "expected_svi_range": (75, 100),
        "check_safety_concern": True,
    },
]


def run_mock_ai_node(statements):
    """Run mock-ai.js via Node.js to verify frontend-backend sync."""
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
            id: item.id,
            statement: item.statement,
            language: item.language,
            result: MockAI.analyze(item.statement, { language: item.language })
        };
    });
    console.log(JSON.stringify(results));
    """.replace("PATH_PLACEHOLDER", json.dumps(str(mock_ai_file)))
    proc = subprocess.run(
        ["node", "-e", node_script, json.dumps(statements)],
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(proc.stdout)


def test_step6_6_core():
    print("=" * 75)
    print("SAMVAD AI — Step 6.6 Context-Aware Safety Understanding Verification")
    print("=" * 75)

    node_results = {item["id"]: item["result"] for item in run_mock_ai_node(TEST_CASES)}

    for tc in TEST_CASES:
        t_id = tc["id"]
        stmt = tc["statement"]
        lang = tc["language"]
        print(f"\n[{t_id}] {tc['name']}")
        print(f"    Statement: \"{stmt}\"")

        py_res = analyze_statement(stmt, lang, include_semantics=False)
        js_res = node_results[t_id]

        # 1. SVI Risk level
        assert py_res["risk_level"] == tc["expected_risk"], (
            f"Risk mismatch for [{t_id}]: got {py_res['risk_level']}, expected {tc['expected_risk']}"
        )

        # 2. SVI Score range
        svi = py_res["svi"]
        min_svi, max_svi = tc["expected_svi_range"]
        assert min_svi <= svi <= max_svi, (
            f"SVI out of range for [{t_id}]: got {svi}, expected [{min_svi}, {max_svi}]"
        )

        # 3. Human review flag
        assert py_res["human_review"] == tc["expected_human_review"], (
            f"Human review mismatch for [{t_id}]: got {py_res['human_review']}, expected {tc['expected_human_review']}"
        )

        # 4. Contextual safety metadata check
        if tc["check_safety_concern"]:
            assert py_res["contextual_safety"]["has_safety_concern"] is True, (
                f"Expected has_safety_concern=True for [{t_id}]"
            )
        else:
            assert py_res["contextual_safety"]["has_safety_concern"] is False, (
                f"Expected has_safety_concern=False for [{t_id}]"
            )

        # 5. JS vs Python sync check
        assert py_res["svi"] == js_res["svi"], (
            f"SVI sync error for [{t_id}]: Py={py_res['svi']}, JS={js_res['svi']}"
        )
        assert py_res["risk_level"] == js_res["riskLevel"], (
            f"Risk sync error for [{t_id}]: Py={py_res['risk_level']}, JS={js_res['riskLevel']}"
        )
        assert py_res["human_review"] == js_res["immediateHumanReview"], (
            f"Review sync error for [{t_id}]: Py={py_res['human_review']}, JS={js_res['immediateHumanReview']}"
        )
        assert py_res["stress"] == js_res["components"]["stress"], f"Stress sync error for [{t_id}]"
        assert py_res["vulnerability"] == js_res["components"]["vulnerability"], f"Vuln sync error for [{t_id}]"
        assert py_res["urgency"] == js_res["components"]["urgency"], f"Urgency sync error for [{t_id}]"
        assert py_res["safety"] == js_res["components"]["safetyConcern"], f"Safety sync error for [{t_id}]"

        print(f"    PASS: SVI = {py_res['svi']} ({py_res['risk_level']}), Human Review = {py_res['human_review']}")
        print(f"          Components: Stress={py_res['stress']}, Vuln={py_res['vulnerability']}, Urg={py_res['urgency']}, Safety={py_res['safety']}")
        print(f"          Contextual Tier: {py_res['contextual_safety'].get('tier')}, Cues: {py_res['contextual_safety'].get('matched_cues')}")
        print(f"          Sync with mock-ai.js: 100% IDENTICAL")

    print("\n" + "=" * 75)
    print("ALL STEP 6.6 DIRECT SVI & MOCK-AI TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)


def test_step6_6_http_api():
    print("\n" + "=" * 75)
    print("SAMVAD AI — Step 6.6 HTTP POST /analyze Endpoint Verification")
    print("=" * 75)
    try:
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        use_client = True
    except Exception:
        use_client = False
        import urllib.request
        import urllib.error
        base_url = "http://127.0.0.1:8000"

    for tc in TEST_CASES:
        t_id = tc["id"]
        stmt = tc["statement"]
        lang = tc["language"]
        print(f"\n[HTTP-{t_id}] Testing POST /analyze: \"{stmt[:55]}...\"")

        if use_client:
            resp = client.post("/analyze", json={"statement": stmt, "language": lang})
            assert resp.status_code == 200, f"HTTP error {resp.status_code}"
            body = resp.json()
        else:
            payload = json.dumps({"statement": stmt, "language": lang}).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/analyze",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                assert resp.status == 200, f"HTTP error {resp.status}"

        # Assertions on API response
        assert body["risk_level"] == tc["expected_risk"], (
            f"API Risk mismatch for [{t_id}]: got {body['risk_level']}, expected {tc['expected_risk']}"
        )
        assert body["human_review"] == tc["expected_human_review"], (
            f"API Human review mismatch for [{t_id}]: got {body['human_review']}, expected {tc['expected_human_review']}"
        )
        min_svi, max_svi = tc["expected_svi_range"]
        assert min_svi <= body["svi"] <= max_svi, (
            f"API SVI mismatch for [{t_id}]: got {body['svi']}, expected [{min_svi}, {max_svi}]"
        )
        assert "contextual_safety" in body, f"contextual_safety missing in API response for [{t_id}]"
        assert "semantic_analysis" in body, f"semantic_analysis missing in API response for [{t_id}]"

        print(f"    PASS: HTTP /analyze -> SVI={body['svi']} ({body['risk_level']}), HumanReview={body['human_review']}")
        print(f"          Contextual Tier: {body['contextual_safety'].get('tier')}, Indicators: {body['indicators'][:3]}")

    print("\n" + "=" * 75)
    print("ALL STEP 6.6 HTTP API VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    test_step6_6_core()
    test_step6_6_http_api()
