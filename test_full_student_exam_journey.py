import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import sys
from werkzeug.security import generate_password_hash

def run_full_journey():
    print("==================================================")
    print("   RUNNING FULL STUDENT EXAM LIFECYCLE TEST       ")
    print("==================================================")

    # 1. Setup a clean test student in DB
    from backend.app import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    # Check if student exists or create
    test_username = "journey_test_student"
    test_pass = "SecurePass123!"
    cur.execute("SELECT student_id FROM students WHERE username = %s", (test_username,))
    existing = cur.fetchone()
    if existing:
        student_id = existing["student_id"]
        # Clear previous answers, results, sessions for this student
        cur.execute("DELETE FROM student_answers WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM student_results WHERE student_id = %s", (student_id,))
        cur.execute("DELETE FROM student_exam_sessions WHERE student_id = %s", (student_id,))
        cur.execute("UPDATE students SET password_hash = %s, student_name = %s WHERE student_id = %s",
                    (generate_password_hash(test_pass), "Journey Tester", student_id))
    else:
        cur.execute("INSERT INTO students (student_name, username, password_hash, email) VALUES (%s, %s, %s, %s)",
                    ("Journey Tester", test_username, generate_password_hash(test_pass), "journey@examora.edu"))
        student_id = cur.lastrowid
    
    conn.commit()
    cur.close()
    conn.close()

    print(f"[SETUP] Prepared clean student account '{test_username}' (ID: {student_id})")

    # 2. Authenticate Session via HTTP
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def api(endpoint, method="GET", data=None):
        url = f"http://127.0.0.1:5000{endpoint}"
        body = None
        headers = {}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with opener.open(req, timeout=5) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))

    # Step 1: Login
    status, res = api("/api/login", method="POST", data={"username": test_username, "password": test_pass})
    print(f"1. Login Response: {res}")
    assert status == 200 and res.get("success") is True

    # Step 2: Check Has Attempted (should be False)
    status, res = api("/api/has-attempted")
    print(f"2. Has Attempted: {res}")
    assert status == 200 and res.get("attempted") is False

    # Step 3: Start Exam
    status, res = api("/api/start-exam", method="POST", data={"duration_seconds": 3600})
    print(f"3. Start Exam: {res}")
    assert status == 200 and res.get("success") is True

    # Step 4: Verify Session Active
    status, res = api("/api/session")
    print(f"4. Active Session: {res}")
    assert status == 200 and res.get("session", {}).get("status") == "active"
    remaining = res["session"]["remaining_seconds"]
    assert 3500 <= remaining <= 3600

    # Step 5: Get Questions
    status, res = api("/api/questions")
    questions = res.get("questions", [])
    print(f"5. Questions Retrieved: {len(questions)}")
    assert len(questions) > 0

    # Step 6: Submit Exam with Answers
    answers = {}
    for q in questions:
        answers[str(q["qid"])] = "A" # choose option A for each question
    
    status, res = api("/api/submit-exam", method="POST", data={"answers": answers})
    print(f"6. Submit Exam: {res}")
    assert status == 200 and res.get("success") is True
    result = res.get("result")
    assert result is not None
    print(f"   Score: {result.get('score')}/{result.get('total_marks')} ({result.get('percentage')}%) - Grade: {result.get('grade')}")

    # Step 7: Verify Result Endpoint
    status, res = api("/api/result")
    print(f"7. Fetch Result: {res}")
    assert status == 200 and res.get("success") is True
    assert res.get("result", {}).get("student_id") == student_id

    # Step 8: Verify Has Attempted is now True
    status, res = api("/api/has-attempted")
    print(f"8. Has Attempted After Submission: {res}")
    assert status == 200 and res.get("attempted") is True

    # Step 9: Verify Re-submission is rejected (duplicate submission protection)
    try:
        status, res = api("/api/submit-exam", method="POST", data={"answers": answers})
        print(f"9. Duplicate Submit: status={status}, res={res}")
        assert False, "Should have thrown HTTPError for duplicate submit"
    except urllib.error.HTTPError as e:
        print(f"9. Duplicate Submit Rejected as Expected (HTTP {e.code})")
        assert e.code == 400

    # Step 10: Logout
    status, res = api("/api/logout", method="POST")
    print(f"10. Logout: {res}")
    assert status == 200 and res.get("success") is True

    print("\n==================================================")
    print("   FULL LIFECYCLE VALIDATION COMPLETED 100%!      ")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = run_full_journey()
    sys.exit(0 if success else 1)
