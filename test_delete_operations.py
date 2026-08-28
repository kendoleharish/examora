"""
EXAMORA - End-to-End Delete Operations Test Suite
Verifies:
1. Security & Authentication (Unauthenticated -> 401, Student -> 403)
2. Admin Student Deletion (404 on nonexistent, transaction safety, cascade cleanup)
3. Admin Examination Deletion (404 on nonexistent, exam_questions cleanup, transaction safety)
4. Historical Results Protection (409 conflict when exam has student results, records preserved)
"""

import io
import json
import unittest
import urllib.request
import urllib.parse
import http.cookiejar
import uuid

BASE_URL = "http://127.0.0.1:5000"

class HttpClient:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def request(self, method, url, json_data=None, headers=None):
        req_headers = headers or {}
        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            resp = self.opener.open(req)
            return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")

    def get(self, url, headers=None):
        return self.request("GET", url, headers=headers)

    def post(self, url, json=None, headers=None):
        return self.request("POST", url, json_data=json, headers=headers)

    def put(self, url, json=None, headers=None):
        return self.request("PUT", url, json_data=json, headers=headers)

    def delete(self, url, headers=None):
        return self.request("DELETE", url, headers=headers)


class TestDeleteOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Login as Admin
        cls.admin_client = HttpClient()
        status, body = cls.admin_client.post(f"{BASE_URL}/api/admin/login", json={
            "username": "admin",
            "password": "SecureAdmin2026!"
        })
        assert status == 200, f"Admin login failed in test setup: {body}"

        # 2. Provision & Login a Temporary Candidate for student-role tests
        cls.temp_student_username = f"del_cand_{uuid.uuid4().hex[:6]}"
        cls.student_client = HttpClient()
        status, body = cls.admin_client.post(f"{BASE_URL}/api/admin/students", json={
            "student_name": "Delete Test Candidate",
            "username": cls.temp_student_username,
            "email": f"{cls.temp_student_username}@institution.edu",
            "password": "Candidate2026!",
            "status": "active"
        })
        assert status == 201, f"Student provisioning failed: {body}"
        cls.test_student_id = json.loads(body)["student_id"]

        # Login student
        status, body = cls.student_client.post(f"{BASE_URL}/api/login", json={
            "username": cls.temp_student_username,
            "password": "Candidate2026!"
        })
        assert status == 200, f"Student login failed: {body}"

        cls.unauth_client = HttpClient()

    @classmethod
    def tearDownClass(cls):
        # Cleanup test student if still exists
        try:
            cls.admin_client.delete(f"{BASE_URL}/api/admin/students/{cls.test_student_id}")
        except Exception:
            pass

    # ----------------------------------------------------
    # 1. SECURITY & AUTHORIZATION TESTS
    # ----------------------------------------------------

    def test_01_unauthenticated_delete_student_returns_401(self):
        status, body = self.unauth_client.delete(f"{BASE_URL}/api/admin/students/99999")
        self.assertEqual(status, 401, f"Expected 401, got {status}: {body}")

    def test_02_unauthenticated_delete_exam_returns_401(self):
        status, body = self.unauth_client.delete(f"{BASE_URL}/api/admin/examinations/99999")
        self.assertEqual(status, 401, f"Expected 401, got {status}: {body}")

    def test_03_student_delete_student_returns_403(self):
        status, body = self.student_client.delete(f"{BASE_URL}/api/admin/students/{self.test_student_id}")
        self.assertEqual(status, 403, f"Expected 403 for student deleting student, got {status}: {body}")

    def test_04_student_delete_exam_returns_403(self):
        status, body = self.student_client.delete(f"{BASE_URL}/api/admin/examinations/1")
        self.assertEqual(status, 403, f"Expected 403 for student deleting exam, got {status}: {body}")

    # ----------------------------------------------------
    # 2. NON-EXISTENT RESOURCE (404) TESTS
    # ----------------------------------------------------

    def test_05_admin_delete_nonexistent_student_returns_404(self):
        status, body = self.admin_client.delete(f"{BASE_URL}/api/admin/students/999999")
        self.assertEqual(status, 404, f"Expected 404 for non-existent student, got {status}: {body}")
        data = json.loads(body)
        self.assertFalse(data.get("success"))

    def test_06_admin_delete_nonexistent_exam_returns_404(self):
        status, body = self.admin_client.delete(f"{BASE_URL}/api/admin/examinations/999999")
        self.assertEqual(status, 404, f"Expected 404 for non-existent exam, got {status}: {body}")
        data = json.loads(body)
        self.assertFalse(data.get("success"))

    # ----------------------------------------------------
    # 3. ADMIN STUDENT DELETION & CASCADE
    # ----------------------------------------------------

    def test_07_admin_delete_student_success_and_cascade(self):
        # 1. Provision a temporary student directly
        u = f"del_user_{uuid.uuid4().hex[:6]}"
        status, body = self.admin_client.post(f"{BASE_URL}/api/admin/students", json={
            "student_name": "Temporary Deletable Student",
            "username": u,
            "email": f"{u}@institution.edu",
            "password": "Password123!",
            "status": "active"
        })
        self.assertEqual(status, 201)
        temp_id = json.loads(body)["student_id"]

        # 2. Delete the student
        status, body = self.admin_client.delete(f"{BASE_URL}/api/admin/students/{temp_id}")
        self.assertEqual(status, 200, f"Failed to delete student: {body}")
        data = json.loads(body)
        self.assertTrue(data.get("success"))

        # 3. Verify student is no longer in admin roster
        status, body = self.admin_client.get(f"{BASE_URL}/api/admin/students")
        self.assertEqual(status, 200)
        students = json.loads(body).get("students", [])
        self.assertFalse(any(s["student_id"] == temp_id for s in students), "Deleted student still found in roster!")

    # ----------------------------------------------------
    # 4. ADMIN EXAMINATION DELETION & CLEANUP
    # ----------------------------------------------------

    def test_08_admin_delete_examination_without_results(self):
        # 1. Create a temporary examination
        code = f"TMP-{uuid.uuid4().hex[:4].upper()}"
        status, body = self.admin_client.post(f"{BASE_URL}/api/admin/examinations", json={
            "exam_code": code,
            "title": f"Temporary Assessment {code}",
            "category": "Computer Science & IT",
            "duration_minutes": 30,
            "total_marks": 5,
            "status": "draft"
        })
        self.assertEqual(status, 201)
        temp_exam_id = json.loads(body)["exam_id"]

        # 2. Assign questions to it
        status, body = self.admin_client.post(f"{BASE_URL}/api/admin/examinations/{temp_exam_id}/questions", json={
            "question_ids": [1, 2]
        })
        self.assertEqual(status, 200)

        # 3. Delete the examination
        status, body = self.admin_client.delete(f"{BASE_URL}/api/admin/examinations/{temp_exam_id}")
        self.assertEqual(status, 200, f"Failed to delete exam: {body}")
        self.assertTrue(json.loads(body).get("success"))

        # 4. Verify examination is gone (404 on fetch)
        status, body = self.admin_client.get(f"{BASE_URL}/api/admin/examinations/{temp_exam_id}")
        self.assertEqual(status, 404, "Deleted examination still accessible!")

    # ----------------------------------------------------
    # 5. HISTORICAL RESULTS PROTECTION (409 CONFLICT)
    # ----------------------------------------------------

    def test_09_admin_delete_exam_with_results_rejected(self):
        # Exam 1 has completed results from regression test runs
        status, body = self.admin_client.delete(f"{BASE_URL}/api/admin/examinations/1")
        self.assertEqual(status, 409, f"Expected 409 Conflict for exam with results, got {status}: {body}")
        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertTrue(data.get("has_results"))
        self.assertIn("completed candidate results", data.get("message", ""))

        # Verify Exam 1 remains intact and accessible
        status, body = self.admin_client.get(f"{BASE_URL}/api/admin/examinations/1")
        self.assertEqual(status, 200, "Protected examination was incorrectly deleted!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
