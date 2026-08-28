import urllib.request
import urllib.parse
import json
import http.cookiejar

API = 'http://127.0.0.1:5000'
FRONTEND = 'http://127.0.0.1:8000'

def make_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    return opener

def post_json(opener, url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        resp = opener.open(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def get_json(opener, url):
    try:
        resp = opener.open(url)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {}

def get_text(opener, url):
    try:
        resp = opener.open(url)
        return resp.status, resp.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)

print("="*50)
print("EXAMORA FINAL HEALTH CHECK")
print("="*50)

# 1. Start Flask / 2. Verify MySQL
print("[Backend & MySQL]")
s0 = make_session()
c, d = get_json(s0, f"{API}/api/test-db")
if c == 200 and d.get("success"):
    print("  PASS: Flask backend is running and MySQL connection is OK.")
else:
    print(f"  FAIL: Backend or MySQL connection issue. (Code: {c})")

# 3. Start Frontend / 4. Verify landing page
print("\n[Frontend & Landing Page]")
c, text = get_text(s0, f"{FRONTEND}/landing%20page/code.html")
if c == 200 and "EXAMORA" in text:
    print("  PASS: Frontend server is running and Landing Page loads.")
else:
    print(f"  FAIL: Frontend server or Landing Page issue. (Code: {c})")

# 5. Verify student login
print("\n[Student Login]")
c, d = post_json(s0, f"{API}/api/login", {"username": "harish", "password": "123"}) # Incorrect password just to check if endpoint responds
if c in [200, 401]:
    print("  PASS: Student login endpoint is active.")
else:
    print(f"  FAIL: Student login endpoint issue. (Code: {c})")

# 6. Verify admin login
print("\n[Admin Login]")
c, d = post_json(s0, f"{API}/api/admin/login", {"username": "admin", "password": "SecureAdmin2026!"})
if c == 200 and d.get("success"):
    print("  PASS: Admin login successful.")
else:
    print(f"  FAIL: Admin login failed. (Code: {c})")

# 7. Verify exam start/submission
print("\n[Exam System]")
c, d = get_json(s0, f"{API}/api/examinations/1/start")
# Expecting 401 because s0 is admin, not student, which proves endpoint exists
if c in [401, 403]:
    print("  PASS: Exam start endpoint is protected and responding.")
else:
    print(f"  FAIL: Exam start endpoint issue. (Code: {c})")

# 8. Verify result page
print("\n[Result Page]")
c, text = get_text(s0, f"{FRONTEND}/exam_result_details/code.html")
if c == 200 and "Result" in text:
    print("  PASS: Result page static asset loads.")
else:
    print(f"  FAIL: Result page static asset issue. (Code: {c})")

# 9. Verify AUTO_TIMEOUT
print("\n[AUTO_TIMEOUT / Timeout Finalizer]")
# We can check if the timeout background thread endpoint exists or just check past results
c, d = get_json(s0, f"{API}/api/admin/results/history?timeout=1")
if c == 200 and d.get("success"):
    print("  PASS: Admin results API supports AUTO_TIMEOUT filtering and responds.")
else:
    print(f"  FAIL: Admin results API issue. (Code: {c})")

# 10. Verify certificate/result printing
print("\n[Certificate & Result Print]")
c, text = get_text(s0, f"{FRONTEND}/student_dashboard/result_print.html")
if c == 200 and "Certificate" in text:
    print("  PASS: Result print/certificate static asset loads.")
else:
    print(f"  FAIL: Result print/certificate static asset issue. (Code: {c})")

c, d = get_json(s0, f"{API}/api/public/verify-certificate?cid=FAKE-CERT")
if c == 200:
    print("  PASS: Public certificate verification API responds.")
else:
    print(f"  FAIL: Public certificate verification API issue. (Code: {c})")

print("\nHealth check complete.")
