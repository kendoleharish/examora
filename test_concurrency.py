import os
import time
import threading
from backend.app import app, get_db_connection

def run_test():
    app.config['TESTING'] = True
    client = app.test_client()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Ensure exam 3 duration is 1 minute
    cursor.execute("UPDATE examinations SET duration_minutes = 1 WHERE exam_id = 3")
    conn.commit()

    username = f"testuser_{int(time.time())}"
    res = client.post('/api/register', json={
        'student_name': 'Concurrency Test User',
        'username': username,
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'email': f'{username}@test.com'
    })
    
    cursor.execute("UPDATE students SET status = 'active' WHERE username = %s", (username,))
    conn.commit()

    client.post('/api/login', json={'username': username, 'password': 'Password123!'})
    
    client.post('/api/examinations/3/start')
    
    # Force the session to be 61 seconds old so it's expired
    cursor.execute("UPDATE student_exam_sessions SET start_time = DATE_SUB(NOW(), INTERVAL 61 SECOND) WHERE exam_id = 3 AND student_id = (SELECT student_id FROM students WHERE username = %s)", (username,))
    conn.commit()
    
    results = []
    
    def manual_submit():
        res = client.post('/api/examinations/3/submit', json={"submission_type": "MANUAL"})
        results.append(res.get_json())
        
    def auto_submit():
        res = client.post('/api/examinations/3/submit', json={"submission_type": "AUTO_TIMEOUT"})
        results.append(res.get_json())
        
    def check_session_trigger():
        # This will trigger get_examination_session which invokes the auto finalizer logic
        res = client.get('/api/examinations/3/session')
        results.append(res.get_json())
        
    # Run concurrently
    t1 = threading.Thread(target=manual_submit)
    t2 = threading.Thread(target=auto_submit)
    t3 = threading.Thread(target=check_session_trigger)
    
    t1.start(); t2.start(); t3.start()
    t1.join(); t2.join(); t3.join()
    
    print("Concurrent Execution Responses:")
    for r in results:
        print(r)
        
    # Check DB
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM student_results r
        JOIN students st ON r.student_id = st.student_id
        WHERE st.username = %s AND r.exam_id = 3
    """, (username,))
    count_res = cursor.fetchone()
    
    if count_res and count_res['count'] == 1:
        print("CONCURRENCY TEST PASSED")
    else:
        print(f"CONCURRENCY TEST FAILED: Count is {count_res['count']}")
        
    cursor.close()
    conn.close()

if __name__ == '__main__':
    run_test()
