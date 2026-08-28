"""
EXAMORA — Test Suite (using direct DB session setup)
"""
import urllib.request
import urllib.parse
import json
import http.cookiejar

API = 'http://127.0.0.1:5000'

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
            return e.code, {"error": "non-json response"}

passed = 0
failed = 0
def test(name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'  PASS: {name}')
    else:
        failed += 1
        print(f'  FAIL: {name} {detail}')

print('=' * 60)
print('EXAMORA RESULTS/CERTIFICATES INTEGRATION TESTS')
print('=' * 60)

# ── 1. Public Certificate Verification (no auth needed) ──
print('\n--- Public Certificate Verification (no auth) ---')
s0 = make_session()
code, data = get_json(s0, f'{API}/api/public/verify-certificate?cid=FAKE-0000-000000')
test('Invalid cert returns 200', code == 200)
test('Invalid cert not valid', not data.get('valid'))

code, data = get_json(s0, f'{API}/api/public/verify-certificate?cid=')
test('Empty cert returns 400', code == 400)

# ── 2. Admin Login ──
print('\n--- Admin Login ---')
s_admin = make_session()
code, data = post_json(s_admin, f'{API}/api/admin/login', {'username': 'admin', 'password': 'SecureAdmin2026!'})
test('Admin login', code == 200 and data.get('success'))

# ── 3. Admin Results History ──
print('\n--- Admin Results History ---')
code, data = get_json(s_admin, f'{API}/api/admin/results/history?page=1&per_page=25')
test('Admin results returns 200', code == 200)
test('Admin results success', data.get('success'))
if data.get('success'):
    results = data.get('results', [])
    test('Admin results has data', len(results) > 0)
    if results:
        r = results[0]
        test('Result has result_id', r.get('result_id') is not None)
        test('Result has student_name', r.get('student_name') is not None)
        test('Result has exam_title', r.get('exam_title') is not None)
        test('Result has email', r.get('email') is not None)
        test('Result has score', r.get('score') is not None)
        test('Result has percentage', r.get('percentage') is not None)
        test('Result has grade', r.get('grade') is not None)
        test('Result has submission_type', r.get('submission_type') is not None)
        test('Result has institution_name', r.get('institution_name') is not None)
    
    p = data.get('pagination')
    test('Pagination present', p is not None)
    test('Pagination total', p.get('total', 0) > 0)
    test('Pagination page', p.get('page') == 1)

# ── 4. Admin Filters ──
print('\n--- Admin Result Filters ---')
code, data = get_json(s_admin, f'{API}/api/admin/results/history?grade=F')
test('Grade filter works', code == 200 and data.get('success'))
if data.get('success'):
    for r in data.get('results', []):
        test(f'Grade F filter correct ({r.get("student_name")})', r.get('grade') == 'F')

code, data = get_json(s_admin, f'{API}/api/admin/results/history?timeout=1')
test('Timeout filter works', code == 200 and data.get('success'))
if data.get('success'):
    for r in data.get('results', []):
        test(f'Timeout filter correct ({r.get("student_name")})', r.get('submission_type') == 'AUTO_TIMEOUT')

# ── 5. CSV Export ──
print('\n--- CSV Export ---')
try:
    req = urllib.request.Request(f'{API}/api/admin/results/export')
    resp = s_admin.open(req)
    csv_content = resp.read().decode()
    test('CSV returns content', len(csv_content) > 0)
    test('CSV has header', 'Institution' in csv_content and 'Student' in csv_content)
    lines = csv_content.strip().split('\n')
    test('CSV has data rows', len(lines) > 1)
    # Verify no passwords in CSV
    test('No passwords in CSV', 'password' not in csv_content.lower() and 'hash' not in csv_content.lower())
except Exception as e:
    test('CSV export', False, str(e))

# ── 6. Tenant Isolation (Admin B) ──
print('\n--- Tenant Isolation ---')
s_b = make_session()
code, data = post_json(s_b, f'{API}/api/admin/login', {'username': 'admin_b', 'password': 'admin123'})
test('Admin B login', code == 200 and data.get('success'))
if code == 200 and data.get('success'):
    code, data = get_json(s_b, f'{API}/api/admin/results/history?page=1&per_page=100')
    test('Admin B can access results endpoint', code == 200)
    if data.get('success'):
        results_b = data.get('results', [])
        test('Admin B sees 0 results (no exams in B)', len(results_b) == 0)
    
    # CSV export for B
    try:
        req = urllib.request.Request(f'{API}/api/admin/results/export')
        resp = s_b.open(req)
        csv_b = resp.read().decode()
        lines_b = csv_b.strip().split('\n')
        test('Admin B CSV has header only', len(lines_b) <= 1 or (len(lines_b) == 1))
    except Exception as e:
        test('Admin B CSV export', False, str(e))

# ── Summary ──
print('\n' + '=' * 60)
print(f'RESULTS: {passed} passed, {failed} failed, {passed + failed} total')
print('=' * 60)
