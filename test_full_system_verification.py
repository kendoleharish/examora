import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import sys
import secrets

FRONTEND_BASE = "http://127.0.0.1:8000"
BACKEND_BASE = "http://127.0.0.1:5000"

def create_session_client():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    def request_api(endpoint, method="GET", data=None):
        url = f"{BACKEND_BASE}{endpoint}" if endpoint.startswith("/") else f"{BACKEND_BASE}/{endpoint}"
        body = None
        headers = {"Accept": "application/json"}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with opener.open(req, timeout=5) as resp:
                status = resp.getcode()
                raw = resp.read().decode("utf-8")
                try:
                    return status, json.loads(raw)
                except Exception:
                    return status, raw
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read().decode("utf-8")
            try:
                return status, json.loads(raw)
            except Exception:
                return status, raw
    return request_api

def test_all():
    print("==================================================")
    print("   EXAMORA COMPREHENSIVE PRODUCTION SYSTEM TEST   ")
    print("==================================================")

    # ----------------------------------------------------
    # 1. TEST FRONTEND STATIC ASSETS OVER HTTP (Port 8000)
    # ----------------------------------------------------
    print("\n--- 1. Testing Frontend Static Pages (Port 8000) ---")
    pages = [
        "/shared/auth.js",
        "/student_login/code.html",
        "/student_register/code.html",
        "/admin_login/code.html",
        "/admin_dashboard/code.html",
        "/student_dashboard/code.html",
        "/exam_details_instructions/code.html",
        "/live_examination/code.html",
        "/submission_confirmation/code.html",
        "/exam_result_details/code.html",
        "/exam_results_analytics/code.html",
        "/student_profile/code.html",
        "/student_management/code.html",
        "/forgot_password/code.html",
        "/session_expired/code.html",
        "/404_page_not_found/code.html",
    ]
    for page in pages:
        url = f"{FRONTEND_BASE}{page}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                size = len(resp.read())
                print(f"[OK] {url} -> Status {code} ({size} bytes)")
                assert code == 200
        except Exception as e:
            print(f"[FAIL] {url} -> Error: {e}")
            assert False, f"Static asset {page} failed to load"

    # ----------------------------------------------------
    # 2. TEST REGISTRATION & ADMIN APPROVAL WORKFLOW
    # ----------------------------------------------------
    print("\n--- 2. Testing Student Registration & Approval Flow ---")
    anon_client = create_session_client()
    student_client = create_session_client()
    admin_client = create_session_client()

    rand_suffix = secrets.token_hex(4)
    test_uname = f"reg_stud_{rand_suffix}"
    test_email = f"stud_{rand_suffix}@examora.edu"
    test_pwd = "TestPassword2026!"

    # 2.1 Password mismatch check
    status, res = anon_client("/api/register", method="POST", data={
        "student_name": "Test Student",
        "username": test_uname,
        "email": test_email,
        "password": test_pwd,
        "confirm_password": "WrongPassword!"
    })
    print(f"2.1 Password Mismatch Validation: status={status}, res={res}")
    assert status == 400 and res.get("success") is False

    # 2.2 Valid registration (creates 'pending' account)
    status, res = anon_client("/api/register", method="POST", data={
        "student_name": "Test Student",
        "username": test_uname,
        "email": test_email,
        "password": test_pwd,
        "confirm_password": test_pwd
    })
    print(f"2.2 Valid Registration: status={status}, res={res}")
    assert status == 201 and res.get("success") is True

    # 2.3 Duplicate registration rejection
    status, res = anon_client("/api/register", method="POST", data={
        "student_name": "Test Student",
        "username": test_uname,
        "email": test_email,
        "password": test_pwd,
        "confirm_password": test_pwd
    })
    print(f"2.3 Duplicate Username/Email Rejection: status={status}, res={res}")
    assert status == 409 and res.get("success") is False

    # 2.4 Pending student login attempt (must be rejected)
    status, res = student_client("/api/login", method="POST", data={
        "username": test_uname,
        "password": test_pwd
    })
    print(f"2.4 Pending Account Login Attempt: status={status}, res={res}")
    assert status == 403 and res.get("success") is False

    # 2.5 Admin logs in
    status, res = admin_client("/api/admin/login", method="POST", data={
        "username": "admin",
        "password": "SecureAdmin2026!"
    })
    print(f"2.5 Admin Login: status={status}, res={res}")
    assert status == 200 and res.get("success") is True

    # 2.6 Admin checks student list and finds pending student
    status, res = admin_client("/api/admin/students")
    assert status == 200 and res.get("success") is True
    students = res.get("students", [])
    registered_student = next((s for s in students if s["username"] == test_uname), None)
    assert registered_student is not None, "Registered student not in admin roster"
    student_id = registered_student["student_id"]
    print(f"2.6 Admin Located Pending Student ID: {student_id} (Status: {registered_student['status']})")
    assert registered_student["status"] == "pending"

    # 2.7 Admin approves pending student
    status, res = admin_client(f"/api/admin/students/{student_id}/status", method="PUT", data={"status": "active"})
    print(f"2.7 Admin Approves Student: status={status}, res={res}")
    assert status == 200 and res.get("success") is True

    # 2.8 Student logs in successfully now that account is active
    status, res = student_client("/api/login", method="POST", data={
        "username": test_uname,
        "password": test_pwd
    })
    print(f"2.8 Approved Student Login: status={status}, res={res}")
    assert status == 200 and res.get("success") is True

    # ----------------------------------------------------
    # 3. TEST SECURITY & AUTHORIZATION BOUNDARIES
    # ----------------------------------------------------
    print("\n--- 3. Testing Security & Authorization Boundaries ---")
    
    # 3.1 Student attempts to call Admin API -> MUST RETURN 403 FORBIDDEN
    status, res = student_client("/api/admin/results")
    print(f"3.1 Student -> Admin Results API: status={status}, res={res}")
    assert status == 403 and res.get("success") is False

    status, res = student_client("/api/admin/questions")
    print(f"3.1 Student -> Admin Questions API: status={status}, res={res}")
    assert status == 403 and res.get("success") is False

    # 3.2 Unauthenticated user attempts protected student API -> MUST RETURN 401
    unauth_client = create_session_client()
    status, res = unauth_client("/api/profile")
    print(f"3.2 Unauthenticated -> Student Profile API: status={status}, res={res}")
    assert status == 401 and res.get("success") is False

    # 3.3 Student fetches questions -> MUST NOT EXPOSE correct_answer
    status, res = student_client("/api/questions")
    print(f"3.3 Student Fetches Questions: status={status}, count={len(res.get('questions', []))}")
    assert status == 200
    for q in res.get("questions", []):
        assert "correct_answer" not in q, f"CRITICAL SECURITY LEAK: correct_answer exposed in {q}"

    # ----------------------------------------------------
    # 4. TEST ADMIN QUESTION CRUD & MANAGEMENT
    # ----------------------------------------------------
    print("\n--- 4. Testing Admin Question CRUD ---")
    
    # 4.1 Admin adds a new question
    status, res = admin_client("/api/admin/questions", method="POST", data={
        "question": f"What is the time complexity of binary search? ({rand_suffix})",
        "optionA": "O(1)",
        "optionB": "O(log n)",
        "optionC": "O(n)",
        "optionD": "O(n^2)",
        "correct_answer": "B",
        "marks": 2
    })
    print(f"4.1 Admin Adds Question: status={status}, res={res}")
    assert status == 201 and res.get("success") is True
    created_qid = res.get("qid")

    # 4.2 Admin updates the question
    status, res = admin_client(f"/api/admin/questions/{created_qid}", method="PUT", data={
        "question": f"What is the average time complexity of binary search? ({rand_suffix})",
        "optionA": "O(1)",
        "optionB": "O(log n)",
        "optionC": "O(n)",
        "optionD": "O(n log n)",
        "correct_answer": "B",
        "marks": 2
    })
    print(f"4.2 Admin Updates Question: status={status}, res={res}")
    assert status == 200 and res.get("success") is True

    # ----------------------------------------------------
    # 5. TEST COMPLETE STUDENT EXAM LIFECYCLE & SCORING
    # ----------------------------------------------------
    print("\n--- 5. Testing Student Exam Lifecycle & Scoring ---")
    
    # 5.1 Check Has Attempted (False)
    status, res = student_client("/api/has-attempted")
    print(f"5.1 Has Attempted Before Exam: status={status}, attempted={res.get('attempted')}")
    assert status == 200 and res.get("attempted") is False

    # 5.2 Start Exam Session
    status, res = student_client("/api/start-exam", method="POST", data={"duration_seconds": 3600})
    print(f"5.2 Start Exam Session: status={status}, remaining={res.get('remaining_seconds')}")
    assert status == 200 and res.get("success") is True

    # 5.3 Fetch Active Session
    status, res = student_client("/api/session")
    print(f"5.3 Active Session Info: status={status}, res={res}")
    assert status == 200 and res.get("session", {}).get("status") == "active"

    # 5.4 Submit Exam Answers
    q_status, q_res = student_client("/api/questions")
    questions = q_res.get("questions", [])
    answers = {}
    for q in questions:
        # If it's our new binary search question, answer 'B' (correct)
        if q["qid"] == created_qid:
            answers[str(q["qid"])] = "B"
        else:
            answers[str(q["qid"])] = "A" # Option A for question 1 (Charles Babbage)

    status, res = student_client("/api/submit-exam", method="POST", data={"answers": answers})
    print(f"5.4 Submit Exam: status={status}, res={res}")
    assert status == 200 and res.get("success") is True
    exam_result = res.get("result")
    print(f"   Candidate Score: {exam_result.get('score')}/{exam_result.get('total_marks')} ({exam_result.get('percentage')}%) - Grade: {exam_result.get('grade')}")

    # 5.5 Duplicate submission rejected (400)
    status, res = student_client("/api/submit-exam", method="POST", data={"answers": answers})
    print(f"5.5 Duplicate Submission Rejection: status={status}, res={res}")
    assert status == 400 and res.get("success") is False

    # 5.6 Student fetches result
    status, res = student_client("/api/result")
    print(f"5.6 Student Fetches Result: status={status}, res={res}")
    assert status == 200 and res.get("result", {}).get("student_id") == student_id

    # 5.7 Admin views student detailed answer sheet
    status, res = admin_client(f"/api/admin/results/{student_id}")
    print(f"5.7 Admin Views Student Answer Sheet: status={status}, answers={len(res.get('answers', []))}")
    assert status == 200 and res.get("success") is True

    # 5.8 Admin checks aggregate analytics
    status, res = admin_client("/api/admin/analytics")
    print(f"5.8 Admin Analytics: status={status}, analytics={res.get('analytics')}")
    assert status == 200 and res.get("analytics", {}).get("total_exams_taken") >= 1

    # ----------------------------------------------------
    # 6. TEST CLEANUP OF TEMPORARY TEST DATA
    # ----------------------------------------------------
    print("\n--- 6. Cleaning Up Temporary Test Question & Student ---")
    # Clean up test question
    status, res = admin_client(f"/api/admin/questions/{created_qid}", method="DELETE")
    print(f"6.1 Deleted Test Question #{created_qid}: status={status}")
    assert status == 200

    # Clean up test student
    status, res = admin_client(f"/api/admin/students/{student_id}", method="DELETE")
    print(f"6.2 Deleted Test Student #{student_id}: status={status}")
    assert status == 200

    # ----------------------------------------------------
    # 7. TEST LOGOUT & SESSION INVALIDATION
    # ----------------------------------------------------
    print("\n--- 7. Testing Logout & Session Invalidation ---")
    status, res = student_client("/api/logout", method="POST")
    print(f"7.1 Student Logout: status={status}, res={res}")
    assert status == 200

    status, res = student_client("/api/profile")
    print(f"7.2 Post-Logout Student API Access: status={status}, res={res}")
    assert status == 401

    status, res = admin_client("/api/admin/logout", method="POST")
    print(f"7.3 Admin Logout: status={status}, res={res}")
    assert status == 200

    status, res = admin_client("/api/admin/session")
    print(f"7.4 Post-Logout Admin API Access: status={status}, res={res}")
    assert status == 401

    print("\n==================================================")
    print("   ALL TESTS PASSED 100% SUCCESSFULLY!            ")
    print("==================================================")
    return True

if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
