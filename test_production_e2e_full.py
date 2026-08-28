import os
import sys
import uuid
import json
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar

BACKEND_BASE = "http://127.0.0.1:5000"
FRONTEND_BASE = "http://127.0.0.1:8000"

def create_session_client():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def request(endpoint, method="GET", data=None, params=None):
        url = f"{BACKEND_BASE}{endpoint}" if endpoint.startswith("/") else f"{BACKEND_BASE}/{endpoint}"
        if params:
            qs = urllib.parse.urlencode(params)
            url += f"?{qs}"

        body = None
        headers = {"Accept": "application/json"}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with opener.open(req, timeout=5) as response:
                status = response.getcode()
                raw = response.read().decode("utf-8")
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
        except Exception as e:
            return 0, str(e)

    return request

def run_all_e2e_tests():
    print("=" * 60)
    print("   EXAMORA COMPLETE A-to-Z SYSTEM VERIFICATION (31 SUITES)")
    print("=" * 60)

    # ----------------------------------------------------
    # 1. Verify Frontend Assets on Port 8000
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
        "/404_page_not_found/code.html"
    ]
    for page in pages:
        url = f"{FRONTEND_BASE}{page}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as res:
                assert res.getcode() == 200, f"Page {url} returned status {res.getcode()}"
                content_len = len(res.read())
                print(f"[OK] {page} -> Status 200 ({content_len} bytes)")
        except Exception as e:
            print(f"[FAIL] {page} -> {e}")
            return False

    # ----------------------------------------------------
    # 2. Registration Validation & Account Lifecycle
    # ----------------------------------------------------
    print("\n--- 2. Student Registration & Validation ---")
    student_client = create_session_client()
    admin_client = create_session_client()
    unauth_client = create_session_client()

    unique_id = str(uuid.uuid4())[:8]
    test_uname = f"e2e_stud_{unique_id}"
    test_email = f"e2e_{unique_id}@examora.edu"
    test_pass = "SecurePass123!"

    # 2.1 Password mismatch check
    status, res = student_client("/api/register", method="POST", data={
        "student_name": "E2E Candidate",
        "username": test_uname,
        "email": test_email,
        "password": test_pass,
        "confirm_password": "WrongPassword!"
    })
    print(f"2.1 Password Mismatch Validation: status={status}, msg={res.get('message')}")
    assert status == 400 and res.get("success") is False

    # 2.2 Valid registration (sets pending)
    status, res = student_client("/api/register", method="POST", data={
        "student_name": "E2E Candidate",
        "username": test_uname,
        "email": test_email,
        "password": test_pass,
        "confirm_password": test_pass
    })
    print(f"2.2 Valid Registration: status={status}, msg={res.get('message')}")
    assert status == 201 and res.get("success") is True

    # 2.3 Duplicate registration rejection
    status, res = student_client("/api/register", method="POST", data={
        "student_name": "Duplicate Candidate",
        "username": test_uname,
        "email": test_email,
        "password": test_pass,
        "confirm_password": test_pass
    })
    print(f"2.3 Duplicate Rejection: status={status}, msg={res.get('message')}")
    assert status == 409 and res.get("success") is False

    # 2.4 Pending account login attempt (rejected 403)
    status, res = student_client("/api/login", method="POST", data={
        "username": test_uname,
        "password": test_pass
    })
    print(f"2.4 Pending Login Attempt: status={status}, msg={res.get('message')}")
    assert status == 403 and res.get("success") is False

    # ----------------------------------------------------
    # 3. Admin Authentication & Student Approval
    # ----------------------------------------------------
    print("\n--- 3. Admin Approval Flow ---")
    status, res = admin_client("/api/admin/login", method="POST", data={
        "username": "admin",
        "password": "SecureAdmin2026!"
    })
    print(f"3.1 Admin Login: status={status}, admin={res.get('admin', {}).get('username')}")
    assert status == 200 and res.get("success") is True

    # Find pending student ID
    status, res = admin_client("/api/admin/students")
    assert status == 200 and res.get("success") is True
    pending_list = [s for s in res.get("students", []) if s["username"] == test_uname]
    assert len(pending_list) == 1, "Registered student not found in admin roster"
    student_id = pending_list[0]["student_id"]
    print(f"3.2 Located Pending Student ID #{student_id} (Status: {pending_list[0]['status']})")
    assert pending_list[0]["status"] == "pending"

    # Admin Approves Student
    status, res = admin_client(f"/api/admin/students/{student_id}/status", method="PUT", data={"status": "active"})
    print(f"3.3 Admin Approves Student: status={status}, msg={res.get('message')}")
    assert status == 200 and res.get("success") is True

    # Approved Student Logs In
    status, res = student_client("/api/login", method="POST", data={
        "username": test_uname,
        "password": test_pass
    })
    print(f"3.4 Approved Student Login: status={status}, student_id={res.get('student', {}).get('student_id')}")
    assert status == 200 and res.get("success") is True
    assert res["student"]["status"] == "active"

    # ----------------------------------------------------
    # 4. Student Notifications & Profile System
    # ----------------------------------------------------
    print("\n--- 4. Notifications & Profile System ---")
    status, res = student_client("/api/notifications")
    print(f"4.1 Student Notifications: status={status}, count={len(res.get('notifications', []))}, unread={res.get('unread_count')}")
    assert status == 200 and res.get("success") is True
    assert res.get("unread_count", 0) >= 2  # Registration + Approval notifications

    notif_id = res["notifications"][0]["id"]
    # Mark single notification as read
    status, res = student_client(f"/api/notifications/{notif_id}/read", method="PUT")
    print(f"4.2 Mark Single Read: status={status}, msg={res.get('message')}")
    assert status == 200 and res.get("success") is True

    # Mark all notifications as read
    status, res = student_client("/api/notifications/read-all", method="PUT")
    print(f"4.3 Mark All Read: status={status}, msg={res.get('message')}")
    assert status == 200 and res.get("success") is True

    # Verify unread_count is now 0
    status, res = student_client("/api/notifications")
    print(f"4.4 Post-Read Notifications: unread_count={res.get('unread_count')}")
    assert status == 200 and res.get("unread_count") == 0

    # Student Profile
    status, res = student_client("/api/profile")
    print(f"4.5 Student Profile: status={status}, name={res.get('student', {}).get('student_name')}, registered={res.get('student', {}).get('created_at')}")
    assert status == 200 and res.get("success") is True

    # ----------------------------------------------------
    # 5. Question Categories & Question Bank CRUD
    # ----------------------------------------------------
    print("\n--- 5. Categories & Question Management ---")
    status, res = student_client("/api/categories")
    print(f"5.1 Available Categories: status={status}, categories={res.get('categories')}")
    assert status == 200 and res.get("success") is True

    # Admin Adds Question with Category
    status, res = admin_client("/api/admin/questions", method="POST", data={
        "category": "Database Systems",
        "question": f"What is the primary purpose of normalization? ({unique_id})",
        "optionA": "Reduce Data Redundancy",
        "optionB": "Increase Storage Overhead",
        "optionC": "Eliminate Indexing",
        "optionD": "Encrypt Data",
        "correct_answer": "A",
        "marks": 2
    })
    print(f"5.2 Admin Adds Question with Category: status={status}, qid={res.get('qid')}")
    assert status == 201 and res.get("success") is True
    new_qid = res.get("qid")

    # Admin Filters Questions by Category
    status, res = admin_client("/api/admin/questions", params={"category": "Database Systems"})
    print(f"5.3 Admin Category Filter: status={status}, found={len(res.get('questions', []))}")
    assert status == 200 and any(q["qid"] == new_qid for q in res.get("questions", []))

    # Student Fetches Questions (Verify Category is present, correct_answer is excluded)
    status, res = student_client("/api/questions")
    print(f"5.4 Student Fetches Questions: status={status}, count={len(res.get('questions', []))}")
    assert status == 200 and res.get("success") is True
    for q in res.get("questions", []):
        assert "correct_answer" not in q, f"SECURITY VIOLATION: correct_answer exposed in student question {q['qid']}!"
        assert "category" in q, f"Missing category in question {q['qid']}"

    # ----------------------------------------------------
    # 6. Security Boundaries & Role Enforcement
    # ----------------------------------------------------
    print("\n--- 6. Security Boundaries ---")
    # Student accessing admin routes -> 403 Forbidden
    status, res = student_client("/api/admin/results")
    print(f"6.1 Student -> Admin Results: status={status}")
    assert status == 403

    status, res = student_client("/api/admin/students")
    print(f"6.2 Student -> Admin Students: status={status}")
    assert status == 403

    # Unauthenticated accessing student protected routes -> 401 Unauthorized
    status, res = unauth_client("/api/profile")
    print(f"6.3 Unauthenticated -> Student Profile: status={status}")
    assert status == 401

    # ----------------------------------------------------
    # 7. Examination Lifecycle & Scoring
    # ----------------------------------------------------
    print("\n--- 7. Live Examination Lifecycle ---")
    # 7.1 Start Exam Session
    status, res = student_client("/api/start-exam", method="POST", data={"duration_seconds": 3600})
    print(f"7.1 Start Exam: status={status}, remaining={res.get('remaining_seconds')}")
    assert status == 200 and res.get("success") is True

    # 7.2 Session Info
    status, res = student_client("/api/session")
    print(f"7.2 Active Session: status={status}, remaining={res.get('session', {}).get('remaining_seconds')}")
    assert status == 200 and res.get("session", {}).get("status") == "active"

    # 7.3 Submit Exam Answers
    _, admin_q_res = admin_client("/api/admin/questions")
    answers = {str(q["qid"]): q["correct_answer"] for q in admin_q_res.get("questions", [])}
    status, res = student_client("/api/submit-exam", method="POST", data={"answers": answers})
    print(f"7.3 Submit Exam: status={status}, result={res.get('result')}")
    assert status == 200 and res.get("success") is True
    result_data = res.get("result", {})
    assert result_data.get("percentage") == 100.0
    assert result_data.get("grade") == "A+"
    assert result_data.get("status") == "PASSED"

    # 7.4 Duplicate Submission Rejection
    status, res = student_client("/api/submit-exam", method="POST", data={"answers": answers})
    print(f"7.4 Duplicate Submission Rejection: status={status}, msg={res.get('message')}")
    assert status == 400 and res.get("success") is False

    # 7.5 Student Fetches Result
    status, res = student_client("/api/result")
    print(f"7.5 Student Fetches Result: status={status}, score={res.get('result', {}).get('score')}/{res.get('result', {}).get('total_marks')}")
    assert status == 200 and res.get("success") is True

    # 7.6 Admin Views Candidate Answer Sheet
    status, res = admin_client(f"/api/admin/results/{student_id}")
    print(f"7.6 Admin Answer Sheet: status={status}, answers={len(res.get('answers', []))}")
    assert status == 200 and res.get("success") is True
    assert len(res.get("answers", [])) >= 2

    # 7.7 Admin Analytics
    status, res = admin_client("/api/admin/analytics")
    print(f"7.7 Admin Analytics: status={status}, analytics={res.get('analytics')}")
    assert status == 200 and res.get("success") is True

    # ----------------------------------------------------
    # 8. Account Disable & Session Invalidation
    # ----------------------------------------------------
    print("\n--- 8. Disabled Student Access & Logout ---")
    # Admin disables student
    status, res = admin_client(f"/api/admin/students/{student_id}/status", method="PUT", data={"status": "disabled"})
    print(f"8.1 Admin Disables Student: status={status}")
    assert status == 200

    # Disabled student attempting protected API -> 403
    status, res = student_client("/api/profile")
    print(f"8.2 Disabled Student Access Rejection: status={status}")
    assert status == 403

    # Cleanup temporary question & student
    status, res = admin_client(f"/api/admin/questions/{new_qid}", method="DELETE")
    print(f"8.3 Deleted Test Question #{new_qid}: status={status}")
    assert status == 200

    status, res = admin_client(f"/api/admin/students/{student_id}", method="DELETE")
    print(f"8.4 Deleted Test Student #{student_id}: status={status}")
    assert status == 200

    # Admin Logout
    status, res = admin_client("/api/admin/logout", method="POST")
    print(f"8.5 Admin Logout: status={status}")
    assert status == 200

    # Post-logout admin access -> 401
    status, res = admin_client("/api/admin/session")
    print(f"8.6 Post-Logout Admin Access: status={status}")
    assert status == 401

    print("\n" + "=" * 60)
    print("   ALL 31 SYSTEM SCENARIOS PASSED 100% SUCCESSFULLY!   ")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_all_e2e_tests()
    if not success:
        sys.exit(1)
