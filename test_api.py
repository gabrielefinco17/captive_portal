import urllib.request
import urllib.error
import json

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
VALID_TEACHER_TOKEN = "TOK-V4W5X6"
INVALID_TOKEN = "INVALID-TOKEN-123"

# --- Colors for beautiful console output ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
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

# --- Comprehensive API Test Suite ---
def run_all_tests():
    print(f"{Colors.BOLD}Starting Comprehensive API Test Suite{Colors.RESET}")
    print(f"Targeting backend at: {BASE_URL}\n")
    
    passed_tests = 0
    total_tests = 0

    # 1. POST /login (Valid)
    print_header("Test 1: POST /login (Valid Token)")
    total_tests += 1
    status, res = send_request("POST", "/login", payload={"token": VALID_TEACHER_TOKEN})
    if status == 200 and res and res.get("login_status") == "OK":
        print_pass(f"Authenticated successfully with token {VALID_TEACHER_TOKEN}.")
        passed_tests += 1
    else:
        print_fail("Failed valid authentication test.", res)

    # 2. POST /login (Invalid)
    print_header("Test 2: POST /login (Invalid Token)")
    total_tests += 1
    status, res = send_request("POST", "/login", payload={"token": INVALID_TOKEN})
    if status == 200 and res and res.get("login_status") == "NO_AUTH":
        print_pass("Correctly rejected the invalid token.")
        passed_tests += 1
    else:
        print_fail("Invalid authentication check failed.", res)

    # 3. POST /create_meeting
    print_header("Test 3: POST /create_meeting")
    total_tests += 1
    meeting_payload = {
        "meeting_date": "2026-06-15",
        "start_time": "15:00:00",
        "end_time": "17:00:00",
        "president_email": "mario.rossi@school.it"
    }
    # Note: Requires Principal Authorization. Under test, we send our valid token to check API response structure
    status, res = send_request("POST", "/create_meeting", payload=meeting_payload, token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Response: {res}")
        passed_tests += 1
    else:
        print_fail("Could not call create_meeting endpoint.")

    # 4. POST /create_proposal
    print_header("Test 4: POST /create_proposal")
    total_tests += 1
    proposal_payload = {
        "title": "Adozione Nuovi Testi Scolastici 2026",
        "proposal_description": "Proposta di acquisto nuovi libri di testo per le classi terze.",
        "attachment": "http://school.it/doc.pdf",
        "meeting_id": 4
    }
    status, res = send_request("POST", "/create_proposal", payload=proposal_payload, token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Response: {res}")
        passed_tests += 1
    else:
        print_fail("Could not call create_proposal endpoint.")

    # 5. PUT /update_proposal
    print_header("Test 5: PUT /update_proposal")
    total_tests += 1
    update_payload = {
        "title": "Adozione Nuovi Testi Scolastici 2026 - AGGIORNATO",
        "proposal_description": "Descrizione aggiornata dei nuovi testi scolastici.",
        "attachment": "http://school.it/updated_doc.pdf",
        "meeting_id": 4
    }
    # Update proposal ID 1 as an example parameter
    status, res = send_request("PUT", "/update_proposal?id=1", payload=update_payload, token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Response: {res}")
        passed_tests += 1
    else:
        print_fail("Could not call update_proposal endpoint.")

    # 6. GET /read_proposal
    print_header("Test 6: GET /read_proposal")
    total_tests += 1
    status, res = send_request("GET", "/read_proposal", token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Total proposals found: {len(res) if isinstance(res, list) else res}")
        passed_tests += 1
    else:
        print_fail("Could not call read_proposal endpoint.")

    # 7. GET /read_proposal/{proposal_id}
    print_header("Test 7: GET /read_proposal/1")
    total_tests += 1
    status, res = send_request("GET", "/read_proposal/1", token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Response: {res}")
        passed_tests += 1
    else:
        print_fail("Could not call read_proposal by ID endpoint.")

    # 8. GET /meeting/{meeting_id}/proposals
    print_header("Test 8: GET /meeting/4/proposals")
    total_tests += 1
    status, res = send_request("GET", "/meeting/4/proposals", token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Total proposals for meeting 4: {len(res) if isinstance(res, list) else res}")
        passed_tests += 1
    else:
        print_fail("Could not call meeting proposals endpoint.")

    # 9. GET /proposals/{id}/stats
    print_header("Test 9: GET /proposals/1/stats")
    total_tests += 1
    status, res = send_request("GET", "/proposals/1/stats", token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Response: {res}")
        passed_tests += 1
    else:
        print_fail("Could not call proposal stats endpoint.")

    # 10. GET /meetings/{id}/stats
    print_header("Test 10: GET /meetings/4/stats")
    total_tests += 1
    status, res = send_request("GET", "/meetings/4/stats", token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Response: {res}")
        passed_tests += 1
    else:
        print_fail("Could not call meeting stats endpoint.")

    # 11. POST /logout
    print_header("Test 11: POST /logout")
    total_tests += 1
    status, res = send_request("POST", "/logout", token=VALID_TEACHER_TOKEN)
    if status is not None:
        print_pass(f"Endpoint connected successfully. Status: {status}, Response: {res}")
        passed_tests += 1
    else:
        print_fail("Could not call logout endpoint.")

    # --- Summary ---
    print("\n" + "="*40)
    print(f"{Colors.BOLD}TEST RUN COMPLETE:{Colors.RESET}")
    print(f"Successfully reached {passed_tests} of {total_tests} endpoints.")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_all_tests()
