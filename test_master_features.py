import io
import json
import os
import unittest
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"

class HttpClient:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def request(self, method, url, data=None, json_data=None, files=None, headers=None, is_binary=False):
        req_headers = headers or {}
        body = None

        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        elif files is not None:
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
            body_bytes = io.BytesIO()
            for field_name, (filename, file_io, content_type) in files.items():
                body_bytes.write(f"--{boundary}\r\n".encode("utf-8"))
                body_bytes.write(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
                body_bytes.write(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
                body_bytes.write(file_io.read())
                body_bytes.write(b"\r\n")
            body_bytes.write(f"--{boundary}--\r\n".encode("utf-8"))
            body = body_bytes.getvalue()
        elif data is not None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode("utf-8")
            else:
                body = data

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            resp = self.opener.open(req)
            resp_bytes = resp.read()
            if is_binary:
                return resp.status, resp_bytes
            return resp.status, resp_bytes.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            err_bytes = e.read()
            if is_binary:
                return e.code, err_bytes
            return e.code, err_bytes.decode("utf-8", errors="replace")

    def get(self, url, headers=None, is_binary=False):
        return self.request("GET", url, headers=headers, is_binary=is_binary)

    def post(self, url, json=None, data=None, files=None, headers=None):
        return self.request("POST", url, data=data, json_data=json, files=files, headers=headers)

    def put(self, url, json=None, headers=None):
        return self.request("PUT", url, json_data=json, headers=headers)

    def delete(self, url, headers=None):
        return self.request("DELETE", url, headers=headers)


class TestMasterFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = HttpClient()
        cls.student = HttpClient()
        cls.test_username = "master_test_candidate"
        cls.test_password = "Password@123"
        cls.test_email = "master_candidate@examora.edu"

        # 1. Admin Login
        status, body = cls.admin.post(f"{BASE_URL}/api/admin/login", json={
            "username": "admin",
            "password": "SecureAdmin2026!"
        })
        assert status == 200, f"Admin login failed: {body}"

        # 2. Cleanup & Create Test Student via Admin
        cls.admin.post(f"{BASE_URL}/api/admin/students", json={
            "student_name": "Master Candidate",
            "username": cls.test_username,
            "email": cls.test_email,
            "password": cls.test_password,
            "status": "active"
        })

        # 3. Student Login
        status, body = cls.student.post(f"{BASE_URL}/api/login", json={
            "username": cls.test_username,
            "password": cls.test_password
        })
        assert status == 200, f"Student login failed: {body}"
        cls.student_id = json.loads(body)["student"]["student_id"]

    # ================================================================
    # 1. MULTI-EXAMINATION MANAGEMENT (ADMIN)
    # ================================================================

    def test_01_admin_create_examination(self):
        """Admin can create a new examination."""
        status, body = self.admin.post(f"{BASE_URL}/api/admin/examinations", json={
            "exam_code": "AI-301",
            "title": "Artificial Intelligence Foundations",
            "category": "Artificial Intelligence",
            "description": "Comprehensive assessment on search algorithms and machine learning.",
            "duration_minutes": 45,
            "total_marks": 5,
            "passing_percentage": 50.0,
            "status": "draft"
        })
        self.assertIn(status, [201, 409])
        if status == 201:
            data = json.loads(body)
            self.assertTrue(data["success"])
            self.assertIn("exam_id", data)

    def test_02_duplicate_exam_code_rejected(self):
        """Duplicate examination code must be rejected with 409."""
        status, body = self.admin.post(f"{BASE_URL}/api/admin/examinations", json={
            "exam_code": "CS-101",
            "title": "Duplicate CS Exam",
            "category": "Computer Science & IT",
            "duration_minutes": 60,
            "total_marks": 10
        })
        self.assertEqual(status, 409)
        self.assertFalse(json.loads(body)["success"])

    def test_03_invalid_duration_or_marks_rejected(self):
        """Non-positive duration or total marks must return 400."""
        status, body = self.admin.post(f"{BASE_URL}/api/admin/examinations", json={
            "exam_code": "INV-001",
            "title": "Invalid Exam",
            "category": "General",
            "duration_minutes": 0,
            "total_marks": -5
        })
        self.assertEqual(status, 400)

    def test_04_admin_list_examinations(self):
        """Admin can list all examinations with candidate and question counts."""
        status, body = self.admin.get(f"{BASE_URL}/api/admin/examinations")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["examinations"], list)
        self.assertGreaterEqual(len(data["examinations"]), 1)

    def test_05_admin_update_and_publish_examination(self):
        """Admin can update examination details and change status to published."""
        status, body = self.admin.get(f"{BASE_URL}/api/admin/examinations")
        exams = json.loads(body)["examinations"]
        target = next((e for e in exams if e["exam_code"] == "AI-301"), None)
        self.assertIsNotNone(target)

        exam_id = target["exam_id"]
        status, body = self.admin.put(f"{BASE_URL}/api/admin/examinations/{exam_id}", json={
            "exam_code": "AI-301",
            "title": "Artificial Intelligence Foundations (Updated)",
            "category": "Artificial Intelligence",
            "description": "Updated exam description.",
            "duration_minutes": 45,
            "total_marks": 5,
            "passing_percentage": 60.0,
            "status": "published"
        })
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["success"])

    def test_06_admin_assign_questions_to_exam(self):
        """Admin can assign questions from the question bank to an examination."""
        status, body = self.admin.get(f"{BASE_URL}/api/admin/questions")
        questions = json.loads(body)["questions"]
        qids = [q["qid"] for q in questions[:3]]

        status, body = self.admin.get(f"{BASE_URL}/api/admin/examinations")
        target = next((e for e in json.loads(body)["examinations"] if e["exam_code"] == "AI-301"), None)
        exam_id = target["exam_id"]

        status, body = self.admin.post(f"{BASE_URL}/api/admin/examinations/{exam_id}/questions", json={
            "question_ids": qids
        })
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["success"])

        # Verify assigned
        status, body = self.admin.get(f"{BASE_URL}/api/admin/examinations/{exam_id}/questions")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(len(data["assigned_questions"]), 3)

    # ================================================================
    # 2. QUESTION BANK & SECURITY (CORRECT ANSWER PROTECTION)
    # ================================================================

    def test_07_question_categories_endpoint(self):
        """GET /api/categories returns standard institutional categories."""
        status, body = self.student.get(f"{BASE_URL}/api/categories")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertIn("Computer Science & IT", data["categories"])
        self.assertIn("Mathematics", data["categories"])

    def test_08_student_questions_never_contain_correct_answer(self):
        """CRITICAL: Student question payloads MUST NOT expose correct_answer."""
        status, body = self.student.get(f"{BASE_URL}/api/examinations/1/questions")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        for q in data["questions"]:
            self.assertNotIn("correct_answer", q, "SECURITY VIOLATION: correct_answer exposed to candidate!")

    def test_09_admin_questions_contain_correct_answer(self):
        """Admin questions endpoint correctly provides correct_answer for evaluation management."""
        status, body = self.admin.get(f"{BASE_URL}/api/admin/questions")
        self.assertEqual(status, 200)
        for q in json.loads(body)["questions"]:
            self.assertIn("correct_answer", q)

    # ================================================================
    # 3. STUDENT MULTI-EXAM LIFECYCLE & AUTHORITATIVE TIMING
    # ================================================================

    def test_10_student_examinations_catalog(self):
        """Student receives active examinations with candidate attempt status."""
        status, body = self.student.get(f"{BASE_URL}/api/examinations")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["examinations"]), 1)
        for ex in data["examinations"]:
            self.assertIn(ex["student_status"], ["AVAILABLE", "IN_PROGRESS", "COMPLETED", "EXPIRED"])

    def test_11_student_start_examination_session(self):
        """Starting an examination initiates a server-authoritative timer."""
        status, body = self.student.get(f"{BASE_URL}/api/examinations")
        target = next((e for e in json.loads(body)["examinations"] if e["exam_code"] == "AI-301"), None)
        exam_id = target["exam_id"]

        status, body = self.student.post(f"{BASE_URL}/api/examinations/{exam_id}/start")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertGreater(data["remaining_seconds"], 0)

    def test_12_student_session_authoritative_status(self):
        """Active session returns correct remaining time calculated on server."""
        status, body = self.student.get(f"{BASE_URL}/api/examinations")
        target = next((e for e in json.loads(body)["examinations"] if e["exam_code"] == "AI-301"), None)
        exam_id = target["exam_id"]

        status, body = self.student.get(f"{BASE_URL}/api/examinations/{exam_id}/session")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertEqual(data["session"]["status"], "active")

    def test_13_student_submit_examination_and_scoring(self):
        """Submitting answers computes server-side score and records grade."""
        status, body = self.student.get(f"{BASE_URL}/api/examinations")
        target = next((e for e in json.loads(body)["examinations"] if e["exam_code"] == "AI-301"), None)
        exam_id = target["exam_id"]

        status, body = self.student.get(f"{BASE_URL}/api/examinations/{exam_id}/questions")
        questions = json.loads(body)["questions"]

        answers = {str(q["qid"]): "A" for q in questions}

        status, body = self.student.post(f"{BASE_URL}/api/examinations/{exam_id}/submit", json={
            "answers": answers
        })
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertIn("score", data["result"])
        self.assertIn("grade", data["result"])

    def test_14_duplicate_submission_protection(self):
        """Duplicate submission on completed exam must be rejected with 400."""
        status, body = self.student.get(f"{BASE_URL}/api/examinations")
        target = next((e for e in json.loads(body)["examinations"] if e["exam_code"] == "AI-301"), None)
        exam_id = target["exam_id"]

        status, body = self.student.post(f"{BASE_URL}/api/examinations/{exam_id}/submit", json={
            "answers": {}
        })
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body)["success"])

    def test_15_student_fetch_specific_examination_result(self):
        """Candidate can fetch specific verified examination result."""
        status, body = self.student.get(f"{BASE_URL}/api/examinations")
        target = next((e for e in json.loads(body)["examinations"] if e["exam_code"] == "AI-301"), None)
        exam_id = target["exam_id"]

        status, body = self.student.get(f"{BASE_URL}/api/examinations/{exam_id}/result")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["result"]["score"])
        self.assertIsInstance(data["answers"], list)

    # ================================================================
    # 4. PROFILE PHOTO MANAGEMENT SYSTEM
    # ================================================================

    def test_16_upload_valid_png_avatar(self):
        """Candidate can upload a valid PNG avatar."""
        # 1x1 valid PNG bytes
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        files = {"photo": ("test_avatar.png", io.BytesIO(png_bytes), "image/png")}

        status, body = self.student.post(f"{BASE_URL}/api/profile/photo", files=files)
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertIn("/api/uploads/avatars/", data["photo_url"])

        # Verify avatar file is accessible
        avatar_url = data["photo_url"]
        img_status, img_content = self.student.get(f"{BASE_URL}{avatar_url}", is_binary=True)
        self.assertEqual(img_status, 200)
        self.assertTrue(img_content.startswith(b"\x89PNG"))

    def test_17_reject_fake_extension_invalid_magic_bytes(self):
        """Uploading text disguised as JPG must be rejected by magic byte validator."""
        fake_bytes = b"Hello, this is just a text file with .jpg extension."
        files = {"photo": ("malicious.jpg", io.BytesIO(fake_bytes), "image/jpeg")}

        status, body = self.student.post(f"{BASE_URL}/api/profile/photo", files=files)
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body)["success"])

    def test_18_reject_oversized_avatar(self):
        """Uploading an avatar exceeding 2MB must be rejected."""
        oversized = b"\x89PNG\r\n\x1a\n" + (b"0" * (2 * 1024 * 1024 + 100))
        files = {"photo": ("huge.png", io.BytesIO(oversized), "image/png")}

        status, body = self.student.post(f"{BASE_URL}/api/profile/photo", files=files)
        self.assertEqual(status, 400)

    def test_19_remove_profile_photo(self):
        """Candidate can remove uploaded profile photo and restore default placeholder state."""
        status, body = self.student.delete(f"{BASE_URL}/api/profile/photo")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["success"])

        # Check profile has profile_picture = None
        status, body = self.student.get(f"{BASE_URL}/api/profile")
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(body)["student"]["profile_picture"])

    # ================================================================
    # 5. NOTIFICATIONS & BADGE ACCURACY
    # ================================================================

    def test_20_notification_lifecycle_and_unread_count(self):
        """Notifications are generated during exam actions and unread count is accurate."""
        status, body = self.student.get(f"{BASE_URL}/api/notifications")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["notifications"], list)
        self.assertIsInstance(data["unread_count"], int)

        # Mark all read
        status, body = self.student.put(f"{BASE_URL}/api/notifications/read-all")
        self.assertEqual(status, 200)

        # Verify unread_count is now 0
        status, body = self.student.get(f"{BASE_URL}/api/notifications")
        self.assertEqual(json.loads(body)["unread_count"], 0)

    # ================================================================
    # 6. BACKWARD COMPATIBLE LEGACY ROUTES
    # ================================================================

    def test_21_legacy_routes_backward_compatibility(self):
        """Legacy routes continue to work seamlessly."""
        status, _ = self.student.get(f"{BASE_URL}/api/categories")
        self.assertEqual(status, 200)

        status, _ = self.student.get(f"{BASE_URL}/api/analytics")
        self.assertEqual(status, 200)

        status, _ = self.student.get(f"{BASE_URL}/api/analytics/score-distribution")
        self.assertEqual(status, 200)

    @classmethod
    def tearDownClass(cls):
        # Clean up test candidate
        cls.admin.delete(f"{BASE_URL}/api/admin/students/{cls.student_id}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
