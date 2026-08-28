import os
import time
from backend.app import app, get_db_connection

def run_test():
    app.config['TESTING'] = True
    client = app.test_client()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Ensure exam 3 duration is 1 minute
    cursor.execute("UPDATE examinations SET duration_minutes = 1 WHERE exam_id = 3")
    conn.commit()

    # Get a valid QID for exam 3
    cursor.execute("SELECT qid FROM exam_questions WHERE exam_id = 3 LIMIT 1")
    q = cursor.fetchone()
    if not q:
        cursor.execute("SELECT qid FROM questions LIMIT 1")
        q = cursor.fetchone()
    valid_qid = q['qid'] if q else 1

    # 2. Register and Login a fresh test user
    username = f"testuser_{int(time.time())}"
    res = client.post('/api/register', json={
        'student_name': 'Test User',
        'username': username,
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'email': f'{username}@test.com'
    })
    
    cursor.execute("UPDATE students SET status = 'active' WHERE username = %s", (username,))
    conn.commit()

    res = client.post('/api/login', json={'username': username, 'password': 'Password123!'})
    
    # 3. Start Exam 3
    res = client.post('/api/examinations/3/start')
    
    # 4. Autosave an answer
    res = client.post('/api/examinations/3/autosave', json={'qid': valid_qid, 'selected_answer': 'A'})
    print('Autosave:', res.get_json())

    # 5. Wait past deadline without reopening
    print("Waiting 70 seconds to let the 1-minute exam timeout and background finalizer run...")
    time.sleep(70)

    # 6. Verify in Database
    cursor.execute("""
        SELECT s.status, s.submission_type, s.submitted_at, r.score 
        FROM student_exam_sessions s
        LEFT JOIN student_results r ON s.student_id = r.student_id AND s.exam_id = r.exam_id
        JOIN students st ON s.student_id = st.student_id
        WHERE st.username = %s AND s.exam_id = 3
    """, (username,))
    db_res = cursor.fetchone()
    print("Database Verification Result:")
    print(db_res)
    
    if db_res and db_res['status'] == 'submitted' and db_res['submission_type'] == 'AUTO_TIMEOUT' and db_res['submitted_at'] is not None and db_res['score'] is not None:
        print("BROWSER-CLOSED TEST PASSED")
    else:
        print("BROWSER-CLOSED TEST FAILED")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    run_test()
