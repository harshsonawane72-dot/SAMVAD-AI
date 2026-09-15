import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False

def make_request(path, method="GET", data=None):
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

def start_server():
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.join(os.path.dirname(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if not wait_for_server(BASE_URL):
        p.terminate()
        raise RuntimeError("FastAPI server failed to start")
    return p

def run_tests():
    print("=== Step 3 Verification Suite ===")

    # 1. Start Server Process 1
    print("\n[1] Starting FastAPI Server (Process 1)...")
    proc1 = start_server()
    print("Process 1 is running on port 8000.")

    try:
        # Test validation: empty statement
        print("\n[2] Testing invalid empty statement...")
        status, body = make_request("/cases", method="POST", data={"statement": "   ", "consent": True})
        print(f"Empty statement response: status={status}, body={body}")
        assert status == 400, f"Expected 400 for empty statement, got {status}"
        assert "Statement must not be empty" in str(body), "Error message mismatch"
        print("PASS: Empty statement rejected with 400.")

        # Test validation: consent=False
        print("\n[3] Testing invalid consent=False...")
        status, body = make_request("/cases", method="POST", data={"statement": "Valid statement", "consent": False})
        print(f"Consent False response: status={status}, body={body}")
        assert status == 400, f"Expected 400 for consent=False, got {status}"
        assert "Consent must be true" in str(body), "Error message mismatch"
        print("PASS: consent=False rejected with 400.")

        # Test valid POST /cases
        test_case_id = f"CASE-STEP3-TEST-{int(time.time())}"
        print(f"\n[4] Testing valid POST /cases with case_id={test_case_id}...")
        sample_payload = {
            "case_id": test_case_id,
            "statement": "Farmer crop insurance claim delay in rural district.",
            "language": "english",
            "interaction_type": "voice",
            "consent": True
        }
        status, body = make_request("/cases", method="POST", data=sample_payload)
        print(f"POST /cases response: status={status}, body={body}")
        assert status in (200, 201), f"Expected 200/201, got {status}"
        assert body["case_id"] == test_case_id
        assert body["statement"] == sample_payload["statement"]
        assert body["language"] == "english"
        assert body["interaction_type"] == "voice"
        assert body["consent"] is True
        assert body["status"] == "received"
        assert "created_at" in body
        assert "id" in body
        print("PASS: POST /cases successfully created case.")

        # Test GET /cases
        print("\n[5] Testing GET /cases...")
        status, cases = make_request("/cases", method="GET")
        print(f"GET /cases returned {len(cases)} cases.")
        matched = [c for c in cases if c["case_id"] == test_case_id]
        assert len(matched) == 1, "Created case not found in GET /cases"
        print("PASS: GET /cases contains the newly submitted case.")

    finally:
        print("\n[6] Stopping Server Process 1...")
        proc1.terminate()
        proc1.wait()
        time.sleep(1)

    # 2. Restart Server Process 2 to test persistence
    print("\n[7] Starting FastAPI Server (Process 2) to test SQLite persistence across restart...")
    proc2 = start_server()
    print("Process 2 is running on port 8000.")

    try:
        # Test GET /cases again
        print("\n[8] Testing GET /cases after server restart...")
        status, cases_after_restart = make_request("/cases", method="GET")
        print(f"GET /cases after restart returned {len(cases_after_restart)} cases.")
        matched_after = [c for c in cases_after_restart if c["case_id"] == test_case_id]
        assert len(matched_after) == 1, "Case did not persist across server restart!"
        persisted_case = matched_after[0]
        print(f"PASS: Case {test_case_id} successfully persisted in SQLite across server restart!")
        print(f"Persisted data: {json.dumps(persisted_case, indent=2)}")

    finally:
        print("\n[9] Stopping Server Process 2...")
        proc2.terminate()
        proc2.wait()

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
