"""
SAMVAD AI — Step 5B IndicBERT Test Suite
Tests:
- Empty text handling (400)
- Unsupported language handling (400)
- English text understanding
- Hindi text understanding
- Marathi text understanding
- Preservation of existing /analyze, /cases endpoints
"""

import json
import sys
import urllib.request
import urllib.error

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"


def make_request(path: str, method: str = "POST", data: dict = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else None


def test_empty_text():
    print("\n[1] Testing empty text validation...")
    status, body = make_request("/ai/understand", data={"text": "   ", "language": "Hindi"})
    print(f"Empty text status: {status}, response: {body}")
    assert status == 400, f"Expected 400, got {status}"
    assert "Text must not be empty" in str(body), "Error message mismatch"
    print("PASS: Empty text rejected with 400 Bad Request.")


def test_unsupported_language():
    print("\n[2] Testing unsupported language validation...")
    status, body = make_request("/ai/understand", data={"text": "Bonjour le monde", "language": "French"})
    print(f"Unsupported language status: {status}, response: {body}")
    assert status == 400, f"Expected 400, got {status}"
    assert "not supported" in str(body).lower(), "Expected unsupported language error message"
    print("PASS: Unsupported language rejected gracefully with 400 Bad Request.")


def test_english_text():
    print("\n[3] Testing English text semantic understanding...")
    payload = {
        "text": "I need information about the grievance redressal mechanism.",
        "language": "English"
    }
    status, body = make_request("/ai/understand", data=payload)
    print(f"English status: {status}")
    assert status == 200, f"Expected 200, got {status} ({body})"
    assert body["model_status"] == "loaded"
    assert body["language"] == "english"
    assert body["language_code"] == "en"
    assert body["embedding_dim"] == 768
    assert len(body["embedding_preview"]) > 0
    assert body["token_count"] > 0
    assert "disclaimer" in body
    print(f"PASS: English processed. Tokens: {body['token_count']}, Dim: {body['embedding_dim']}, Preview: {body['embedding_preview'][:4]}")


def test_hindi_text():
    print("\n[4] Testing Hindi text semantic understanding...")
    payload = {
        "text": "मुझे अपनी शिकायत की प्रक्रिया के बारे में जानकारी चाहिए।",
        "language": "Hindi"
    }
    status, body = make_request("/ai/understand", data=payload)
    print(f"Hindi status: {status}")
    assert status == 200, f"Expected 200, got {status} ({body})"
    assert body["model_status"] == "loaded"
    assert body["language"] == "hindi"
    assert body["language_code"] == "hi"
    assert body["embedding_dim"] == 768
    assert body["token_count"] > 0
    print(f"PASS: Hindi processed. Tokens: {body['token_count']}, Sample: {body['tokens_sample'][:5]}")


def test_marathi_text():
    print("\n[5] Testing Marathi text semantic understanding...")
    payload = {
        "text": "मला माझ्या तक्रार प्रक्रियेबद्दल माहिती हवी आहे.",
        "language": "Marathi"
    }
    status, body = make_request("/ai/understand", data=payload)
    print(f"Marathi status: {status}")
    assert status == 200, f"Expected 200, got {status} ({body})"
    assert body["model_status"] == "loaded"
    assert body["language"] == "marathi"
    assert body["language_code"] == "mr"
    assert body["embedding_dim"] == 768
    assert body["token_count"] > 0
    print(f"PASS: Marathi processed. Tokens: {body['token_count']}, Sample: {body['tokens_sample'][:5]}")


def test_existing_endpoints_preserved():
    print("\n[6] Verifying existing SVI /analyze and database /cases endpoints...")
    # Verify SVI engine untouched
    status, svi_res = make_request("/analyze", data={"statement": "I am worried about my case", "language": "english"})
    assert status == 200, f"/analyze failed with {status}"
    assert svi_res["svi"] == 10
    assert svi_res["risk_level"] == "LOW"
    print("PASS: /analyze remains fully functional with identical SVI scoring.")

    # Verify /cases endpoint
    status, cases = make_request("/cases", method="GET")
    assert status == 200, f"GET /cases failed with {status}"
    assert isinstance(cases, list)
    print(f"PASS: GET /cases returned {len(cases)} cases successfully.")


def run_all():
    print("=== SAMVAD AI: IndicBERT Step 5B Test Suite ===")
    test_empty_text()
    test_unsupported_language()
    test_english_text()
    test_hindi_text()
    test_marathi_text()
    test_existing_endpoints_preserved()
    print("\n=== ALL INDICBERT STEP 5B TESTS PASSED! ===")


if __name__ == "__main__":
    run_all()
