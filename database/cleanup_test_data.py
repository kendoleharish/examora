import os
import mysql.connector

DB_CONFIG = {
    "host": os.environ.get("EXAMORA_DB_HOST", "localhost"),
    "user": os.environ.get("EXAMORA_DB_USER", "root"),
    "password": os.environ.get("EXAMORA_DB_PASSWORD", "Harish2007#"),
    "database": os.environ.get("EXAMORA_DB_NAME", "online_examination"),
    "port": int(os.environ.get("EXAMORA_DB_PORT", "3306"))
}

def cleanup():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)

    # 1. Reset questions to canonical question
    cur.execute("DELETE FROM questions WHERE qid > 1")

    # 2. Identify test students
    cur.execute("SELECT student_id, username FROM students WHERE username LIKE 'reg_stud_%' OR username LIKE 'diag_%' OR username LIKE 'journey_%'")
    test_students = cur.fetchall()

    for s in test_students:
        sid = s["student_id"]
        cur.execute("DELETE FROM student_answers WHERE student_id = %s", (sid,))
        cur.execute("DELETE FROM student_results WHERE student_id = %s", (sid,))
        cur.execute("DELETE FROM student_exam_sessions WHERE student_id = %s", (sid,))
        cur.execute("DELETE FROM students WHERE student_id = %s", (sid,))

    conn.commit()
    cur.close()
    conn.close()
    print("Test data cleanup finished successfully.")

if __name__ == "__main__":
    cleanup()
