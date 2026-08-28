import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

finalizer_code = '''
# ----------------------------------------------------
# BACKGROUND FINALIZER
# ----------------------------------------------------
import threading
import time

def finalize_expired_exam_sessions():
    # Allow server to start up before checking
    time.sleep(5)
    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Find sessions where elapsed >= duration
            cursor.execute("""
                SELECT s.student_id, s.exam_id, st.student_name, st.username 
                FROM student_exam_sessions s
                JOIN students st ON s.student_id = st.student_id
                WHERE s.status != 'submitted' 
                AND TIMESTAMPDIFF(SECOND, s.start_time, NOW()) >= s.duration_seconds
            """)
            expired = cursor.fetchall()
            cursor.close()
            conn.close()

            for sess in expired:
                student_id = sess["student_id"]
                exam_id = sess["exam_id"]
                student_name_or_username = sess.get("student_name") or sess.get("username")
                # Auto-finalize
                _internal_submit_examination(student_id, exam_id, "AUTO_TIMEOUT", {}, student_name_or_username)
        except Exception as e:
            print(f"Background finalizer error: {e}")
        
        time.sleep(10)

# Start the background daemon thread
threading.Thread(target=finalize_expired_exam_sessions, daemon=True).start()

'''

content = content.replace('# ----------------------------------------------------\n# SERVER LAUNCH\n# ----------------------------------------------------', finalizer_code + '\n# ----------------------------------------------------\n# SERVER LAUNCH\n# ----------------------------------------------------')

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Background finalizer added.')
