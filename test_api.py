import urllib.request
import urllib.error
import json
import psycopg2
from datetime import datetime, timedelta

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
VALID_TEACHER_TOKEN = "TOK-V4W5X6"   # chiara.lombardi, teacher, meeting 4
INVALID_TOKEN = "INVALID-TOKEN-123"

# We'll create a temporary principal token for testing
TEMP_PRINCIPAL_TOKEN = "TOK-TEST-PRINCIPAL"

# --- Colors for beautiful console output ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== {title} ==={Colors.RESET}")

def print_pass(msg):
    print(f"{Colors.GREEN}✓ [PASS]{Colors.RESET} {msg}")

def print_fail(msg, detail=None):
    print(f"{Colors.RED}✗ [FAIL]{Colors.RESET} {msg}")
    if detail:
        print(f"   Detail: {detail}")

def print_warn(msg):
    print(f"{Colors.YELLOW}⚠ [WARN]{Colors.RESET} {msg}")

# --- Helper to send HTTP requests ---
def send_request(method, endpoint, payload=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f"Bearer {token}"

    data = json.dumps(payload).encode('utf-8') if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body
    except urllib.error.URLError as e:
        print_fail(f"Could not connect to {BASE_URL}. Is the backend running?", str(e))
        return None, None


# --- DB helpers for test setup/teardown ---
def get_db():
    return psycopg2.connect(database="captive_portal", user="john")


def setup_principal_token():
    """Create a temporary principal token so we can test principal-only endpoints."""
    conn = get_db()
    cur = conn.cursor()
    try:
        now = datetime.now()
        expires = now + timedelta(hours=2)
        # mario.rossi is a principal, meeting 4 exists
        cur.execute(
            """
            INSERT INTO token (code, generated_at, expires_at, user_email, meeting_id)
            VALUES (%s, %s, %s, 'mario.rossi@school.it', 4)
            ON CONFLICT (code) DO UPDATE SET expires_at = %s
            """,
            [TEMP_PRINCIPAL_TOKEN, now, expires, expires]
        )
        conn.commit()
        print_pass("Created temporary principal token for testing.")
    except Exception as e:
        conn.rollback()
        print_fail(f"Could not create principal token: {e}")
    finally:
        cur.close()
        conn.close()


def teardown_principal_token():
    """Remove the temporary principal token."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM token WHERE code = %s", [TEMP_PRINCIPAL_TOKEN])
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def cleanup_test_data():
    """Remove any data created during tests."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM proposal WHERE title LIKE 'TEST-%%'")
        cur.execute("DELETE FROM meeting WHERE president_email = 'mario.rossi@school.it' AND meeting_date = '2099-06-15'")
        cur.execute("DELETE FROM token WHERE code = %s", [TEMP_PRINCIPAL_TOKEN])
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()


# --- Comprehensive API Test Suite ---
def run_all_tests():
    print(f"{Colors.BOLD}Starting Comprehensive API Test Suite{Colors.RESET}")
    print(f"Targeting backend at: {BASE_URL}\n")

    passed = 0
    failed = 0
    total = 0

    def check(condition, pass_msg, fail_msg, detail=None):
        nonlocal passed, failed, total
        total += 1
        if condition:
            print_pass(pass_msg)
            passed += 1
        else:
            print_fail(fail_msg, detail)
            failed += 1

    # --- SETUP ---
    print_header("SETUP: Creating principal token")
    setup_principal_token()

    # ===================================================================
    # 1. POST /login — Valid teacher token
    # ===================================================================
    print_header("Test 1: POST /login (Valid Teacher Token)")
    status, res = send_request("POST", "/login", payload={"token": VALID_TEACHER_TOKEN})
    check(
        status == 200 and res and res.get("login_status") == "OK",
        f"Login OK with teacher token {VALID_TEACHER_TOKEN}.",
        "Login failed for valid teacher token.",
        res
    )

    # ===================================================================
    # 2. POST /login — Invalid token
    # ===================================================================
    print_header("Test 2: POST /login (Invalid Token)")
    status, res = send_request("POST", "/login", payload={"token": INVALID_TOKEN})
    check(
        status == 200 and res and res.get("login_status") == "NO_AUTH",
        "Correctly rejected invalid token.",
        "Did not correctly reject invalid token.",
        res
    )

    # ===================================================================
    # 3. POST /login — Valid principal token
    # ===================================================================
    print_header("Test 3: POST /login (Valid Principal Token)")
    status, res = send_request("POST", "/login", payload={"token": TEMP_PRINCIPAL_TOKEN})
    check(
        status == 200 and res and res.get("login_status") == "OK",
        f"Login OK with principal token {TEMP_PRINCIPAL_TOKEN}.",
        "Login failed for valid principal token.",
        res
    )

    # ===================================================================
    # 4. POST /create_meeting — Teacher (should be FORBIDDEN)
    # ===================================================================
    print_header("Test 4: POST /create_meeting (Teacher → FORBIDDEN)")
    meeting_payload = {
        "meeting_date": "2099-06-15",
        "start_time": "15:00:00",
        "end_time": "17:00:00",
        "president_email": "mario.rossi@school.it"
    }
    status, res = send_request("POST", "/create_meeting", payload=meeting_payload, token=VALID_TEACHER_TOKEN)
    check(
        status == 200 and res and res.get("create_status") == "FORBIDDEN",
        "Teacher correctly denied from creating meeting.",
        "Teacher was NOT correctly denied.",
        res
    )

    # ===================================================================
    # 5. POST /create_meeting — Principal (should succeed)
    # ===================================================================
    print_header("Test 5: POST /create_meeting (Principal → OK)")
    status, res = send_request("POST", "/create_meeting", payload=meeting_payload, token=TEMP_PRINCIPAL_TOKEN)
    check(
        status == 200 and res and res.get("create_status") == "OK",
        "Principal successfully created a meeting.",
        "Principal could NOT create meeting.",
        res
    )

    # ===================================================================
    # 6. POST /create_proposal — Principal (should succeed)
    # ===================================================================
    print_header("Test 6: POST /create_proposal (Principal → OK)")
    proposal_payload = {
        "title": "TEST-Proposal-API-Check",
        "proposal_description": "Automated test proposal.",
        "attachment": "http://test.it/doc.pdf",
        "meeting_id": 4
    }
    status, res = send_request("POST", "/create_proposal", payload=proposal_payload, token=TEMP_PRINCIPAL_TOKEN)
    check(
        status == 200 and res and res.get("insert_status") == "OK",
        "Principal successfully created a proposal.",
        "Principal could NOT create proposal.",
        res
    )

    # ===================================================================
    # 7. GET /read_proposal — Teacher (should return proposal list)
    # ===================================================================
    print_header("Test 7: GET /read_proposal (Teacher → list)")
    status, res = send_request("GET", "/read_proposal", token=VALID_TEACHER_TOKEN)
    check(
        status == 200 and isinstance(res, list) and len(res) > 0,
        f"Read all proposals OK. Found {len(res) if isinstance(res, list) else '?'} proposals.",
        "Failed to read proposals list.",
        res
    )

    # ===================================================================
    # 8. GET /read_proposal/{id} — Teacher (should return single proposal)
    # ===================================================================
    print_header("Test 8: GET /read_proposal/1 (Teacher → single)")
    status, res = send_request("GET", "/read_proposal/1", token=VALID_TEACHER_TOKEN)
    check(
        status == 200 and isinstance(res, dict) and res.get("id") == 1 and "title" in res,
        f"Read proposal 1 OK: '{res.get('title')}'.",
        "Failed to read single proposal.",
        res
    )

    # ===================================================================
    # 9. GET /read_proposal/{id} — Non-existent proposal
    # ===================================================================
    print_header("Test 9: GET /read_proposal/99999 (NOT_FOUND)")
    status, res = send_request("GET", "/read_proposal/99999", token=VALID_TEACHER_TOKEN)
    check(
        status == 200 and isinstance(res, dict) and res.get("read_status") == "NOT_FOUND",
        "Non-existent proposal correctly returned NOT_FOUND.",
        "Did not return NOT_FOUND for missing proposal.",
        res
    )

    # ===================================================================
    # 10. PUT /update_proposal — Principal (should succeed)
    # ===================================================================
    print_header("Test 10: PUT /update_proposal (Principal → OK)")
    update_payload = {
        "title": "TEST-Updated-Proposal",
        "proposal_description": "Updated description via API test.",
        "attachment": "http://test.it/updated.pdf",
        "meeting_id": 4
    }
    status, res = send_request("PUT", "/update_proposal?id=1", payload=update_payload, token=TEMP_PRINCIPAL_TOKEN)
    check(
        status == 200 and res and res.get("update_status") == "OK",
        "Principal successfully updated proposal.",
        "Principal could NOT update proposal.",
        res
    )
    # Restore original proposal
    restore_payload = {
        "title": "New Lab Equipment",
        "proposal_description": "Purchase microscopes and chemistry kits for the science lab.",
        "attachment": "lab_budget.pdf",
        "meeting_id": 1
    }
    send_request("PUT", "/update_proposal?id=1", payload=restore_payload, token=TEMP_PRINCIPAL_TOKEN)

    # ===================================================================
    # 11. GET /meeting/{meeting_id}/proposals — Teacher
    # ===================================================================
    print_header("Test 11: GET /meeting/4/proposals (Teacher)")
    status, res = send_request("GET", "/meeting/4/proposals", token=VALID_TEACHER_TOKEN)
    check(
        status == 200 and isinstance(res, list) and len(res) >= 2,
        f"Meeting 4 proposals OK. Found {len(res) if isinstance(res, list) else '?'} proposals.",
        "Failed to get meeting proposals.",
        res
    )

    # ===================================================================
    # 12. GET /proposals/{id}/stats — Teacher
    # ===================================================================
    print_header("Test 12: GET /proposals/1/stats (Teacher)")
    status, res = send_request("GET", "/proposals/1/stats", token=VALID_TEACHER_TOKEN)
    check(
        status == 200 and res is not None,
        f"Proposal stats OK. Response: {res}",
        "Failed to get proposal stats.",
        res
    )

    # ===================================================================
    # 13. GET /meetings/{id}/stats — Teacher
    # ===================================================================
    print_header("Test 13: GET /meetings/4/stats (Teacher)")
    status, res = send_request("GET", "/meetings/4/stats", token=VALID_TEACHER_TOKEN)
    check(
        status == 200 and res is not None,
        f"Meeting stats OK. Response: {res}",
        "Failed to get meeting stats.",
        res
    )

    # ===================================================================
    # 14. POST /logout — Teacher
    # ===================================================================
    print_header("Test 14: POST /logout (Teacher)")
    # Use a different token we don't need anymore for logout test
    status, res = send_request("POST", "/logout", token=TEMP_PRINCIPAL_TOKEN)
    check(
        status == 200 and res and res.get("logout_status") == "OK",
        "Logout OK.",
        "Logout failed.",
        res
    )

    # ===================================================================
    # 15. POST /login after logout — Should fail (token expired)
    # ===================================================================
    print_header("Test 15: POST /login after logout (Token expired)")
    status, res = send_request("POST", "/login", payload={"token": TEMP_PRINCIPAL_TOKEN})
    check(
        status == 200 and res and res.get("login_status") == "NO_AUTH",
        "Correctly rejected logged-out token.",
        "Logged-out token was NOT rejected!",
        res
    )

    # ===================================================================
    # 16. Missing Authorization header on protected endpoints
    # ===================================================================
    print_header("Test 16: POST /create_meeting (No Auth Header)")
    status, res = send_request("POST", "/create_meeting", payload=meeting_payload)
    check(
        status == 422,
        "Correctly returned 422 for missing Authorization header.",
        f"Expected 422, got {status}.",
        res
    )

    # --- TEARDOWN ---
    print_header("TEARDOWN: Cleaning test data")
    cleanup_test_data()
    print_pass("Cleanup complete.")

    # --- Summary ---
    print("\n" + "=" * 50)
    color = Colors.GREEN if failed == 0 else Colors.RED
    print(f"{Colors.BOLD}TEST RUN COMPLETE:{Colors.RESET}")
    print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {failed}{Colors.RESET}")
    print(f"  Total:  {total}")
    print("=" * 50 + "\n")

    return failed == 0


if __name__ == "__main__":
    run_all_tests()
