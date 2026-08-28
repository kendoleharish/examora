import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import sys

def test_frontend_and_api():
    print("==================================================")
    print("   EXAMORA FRONTEND & API END-TO-END VALIDATION   ")
    print("==================================================")

    # 1. Test Static Frontend Assets over HTTP Server (Port 8000)
    frontend_pages = [
        "http://127.0.0.1:8000/shared/auth.js",
        "http://127.0.0.1:8000/student_login/code.html",
        "http://127.0.0.1:8000/student_dashboard/code.html",
        "http://127.0.0.1:8000/exam_details_instructions/code.html",
        "http://127.0.0.1:8000/live_examination/code.html",
        "http://127.0.0.1:8000/submission_confirmation/code.html",
        "http://127.0.0.1:8000/exam_result_details/code.html",
        "http://127.0.0.1:8000/exam_results_analytics/code.html",
        "http://127.0.0.1:8000/student_profile/code.html",
        "http://127.0.0.1:8000/student_management/code.html",
        "http://127.0.0.1:8000/forgot_password/code.html",
        "http://127.0.0.1:8000/session_expired/code.html",
        "http://127.0.0.1:8000/404_page_not_found/code.html"
    ]

    print("\n--- 1. Testing Frontend Static Pages (Port 8000) ---")
    for url in frontend_pages:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.getcode()
                content = resp.read()
                print(f"[OK] {url} -> Status {status} ({len(content)} bytes)")
        except Exception as e:
            print(f"[FAIL] {url} -> {e}")
            return False

    # 2. Test API Endpoints & Complete Flow (Port 5000)
    print("\n--- 2. Testing Backend API Contracts with Cookie Session (Port 5000) ---")
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def api_call(endpoint, method="GET", data=None):
        url = f"http://127.0.0.1:5000{endpoint}"
        body = None
        headers = {}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with opener.open(req, timeout=5) as resp:
                res_code = resp.getcode()
                res_body = resp.read().decode("utf-8")
                return res_code, json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = err_body
            return e.code, parsed
        except Exception as e:
            return 500, str(e)

    # Test Unauthenticated access to /api/session (should be 401)
    status, res = api_call("/api/session")
    print(f"Unauthenticated /api/session -> Status {status}: {res}")
    assert status == 401, f"Expected 401, got {status}"

    # Test Login with Invalid Credentials
    status, res = api_call("/api/login", method="POST", data={"username": "invalid_user", "password": "wrong_password"})
    print(f"Invalid /api/login -> Status {status}: {res}")
    assert status == 401, f"Expected 401 for invalid login, got {status}"

    # Test Login with Valid Student Credentials (Harish / Harish2007#)
    status, res = api_call("/api/login", method="POST", data={"username": "Harish", "password": "Harish2007#"})
    print(f"Valid /api/login -> Status {status}: {res}")
    assert status == 200, f"Expected 200 for valid login, got {status}"
    assert res.get("success") is True, "Login response success should be True"

    # Test GET /api/students
    status, res = api_call("/api/students")
    print(f"GET /api/students -> Status {status}: Found {len(res.get('students', []))} students")
    assert status == 200 and res.get("success") is True

    # Test GET /api/questions
    status, res = api_call("/api/questions")
    questions = res.get("questions", [])
    print(f"GET /api/questions -> Status {status}: Found {len(questions)} questions")
    assert status == 200 and len(questions) > 0

    # Test GET /api/has-attempted
    status, res = api_call("/api/has-attempted")
    print(f"GET /api/has-attempted -> Status {status}: {res}")
    assert status == 200

    # Test GET /api/analytics
    status, res = api_call("/api/analytics")
    print(f"GET /api/analytics -> Status {status}: Avg Pct = {res.get('avg_percentage')}")
    assert status == 200

    # Test GET /api/analytics/score-distribution
    status, res = api_call("/api/analytics/score-distribution")
    print(f"GET /api/analytics/score-distribution -> Status {status}: Labels = {res.get('labels')}")
    assert status == 200

    # Test POST /api/logout
    status, res = api_call("/api/logout", method="POST")
    print(f"POST /api/logout -> Status {status}: {res}")
    assert status == 200 and res.get("success") is True

    # Test GET /api/session after logout (should be 401)
    status, res = api_call("/api/session")
    print(f"After logout /api/session -> Status {status}: {res}")
    assert status == 401

    print("\n==================================================")
    print("   ALL TESTS PASSED SUCCESSFULLY!                 ")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = test_frontend_and_api()
    sys.exit(0 if success else 1)
