import urllib.request
import json
import time
import mysql.connector

def req(url, data=None, cookies=''):
    req = urllib.request.Request(url)
    if data:
        req.data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    if cookies:
        req.add_header('Cookie', cookies)
    try:
        res = urllib.request.urlopen(req)
        c = res.headers.get('Set-Cookie', '')
        return json.loads(res.read()), c
    except Exception as e:
        return {"success": False, "error": str(e)}, ''

# 1. Update database: Create a 30-second exam or modify exam 3
try:
    conn = mysql.connector.connect(host='localhost',user='root',password='Harish2007#',database='online_examination')
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE examinations SET duration_minutes = 0.5 WHERE exam_id = 3")
    conn.commit()
    print("Set exam 3 duration to 30 seconds.")
except Exception as e:
    print(f"DB Error: {e}")

# 2. Register and Login a fresh test user
username = f"testuser_{int(time.time())}"
base_url = 'http://127.0.0.1:5000'
r, c = req(f'{base_url}/api/register', {'username': username, 'password': 'Password123!', 'full_name': 'Test User', 'email': f'{username}@test.com'})
print('Register:', r)

# Approve student manually so they can login
try:
    cursor.execute("UPDATE students SET status = 'approved' WHERE username = %s", (username,))
    conn.commit()
    print(f"Approved student {username}")
except Exception as e:
    print(f"DB Error: {e}")

r, c = req(f'{base_url}/api/login', {'username': username, 'password': 'Password123!'})
print('Login:', r)
sess_cookie = c.split(';')[0] if c else ''

# 3. Start Exam 3
r, _ = req(f'{base_url}/api/examinations/3/start', {}, sess_cookie)
print('Start exam:', r)
if not r.get('success'):
    print("Exam start failed.")

# 4. Autosave an answer (Assume QID 9 belongs to exam 3)
r, _ = req(f'{base_url}/api/examinations/3/autosave', {'qid': 9, 'selected_answer': 'A'}, sess_cookie)
print('Autosave:', r)

# 5. Wait past deadline without reopening
print("Waiting 35 seconds to let the exam timeout and background finalizer run...")
time.sleep(35)

# 6. Verify in Database
try:
    cursor.execute("""
        SELECT s.status, s.submission_type, s.submitted_at, r.score 
        FROM student_exam_sessions s
        LEFT JOIN student_results r ON s.student_id = r.student_id AND s.exam_id = r.exam_id
        JOIN students st ON s.student_id = st.student_id
        WHERE st.username = %s AND s.exam_id = 3
    """, (username,))
    res = cursor.fetchone()
    print("Database Verification Result:")
    print(res)
    if res and res['status'] == 'submitted' and res['submission_type'] == 'AUTO_TIMEOUT' and res['submitted_at'] is not None and res['score'] is not None:
        print("BROWSER-CLOSED TEST PASSED")
    else:
        print("BROWSER-CLOSED TEST FAILED")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Verify DB Error: {e}")
