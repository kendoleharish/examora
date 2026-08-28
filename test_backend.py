import unittest
import json
import time

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

try:
    from app import app
except ImportError:
    app = None

class TestBackend(unittest.TestCase):
    def setUp(self):
        if app is None:
            self.skipTest("Flask app not available")
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_public_exam_code(self):
        resp = self.client.get('/api/examinations/code/INVALID123')
        self.assertEqual(resp.status_code, 404)
        data = json.loads(resp.data)
        self.assertFalse(data["success"])

    def test_02_register_with_institution(self):
        timestamp = int(time.time())
        payload = {
            "student_name": f"Test Student {timestamp}",
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "institution_id": 1
        }
        resp = self.client.post('/api/register', json=payload)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertTrue(data["success"])

if __name__ == '__main__':
    unittest.main()
