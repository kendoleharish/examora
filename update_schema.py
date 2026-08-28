import mysql.connector

try:
    conn = mysql.connector.connect(host='localhost', user='root', password='Harish2007#', database='online_examination')
    cursor = conn.cursor()

    # 1. Add submission_type to student_exam_sessions
    try:
        cursor.execute("ALTER TABLE student_exam_sessions ADD COLUMN submission_type VARCHAR(50) DEFAULT 'MANUAL'")
        print("Added submission_type to student_exam_sessions")
    except Exception as e:
        print(f"Skipped student_exam_sessions alter (may already exist): {e}")

    # 2. Add submission_type to student_results
    try:
        cursor.execute("ALTER TABLE student_results ADD COLUMN submission_type VARCHAR(50) DEFAULT 'MANUAL'")
        print("Added submission_type to student_results")
    except Exception as e:
        print(f"Skipped student_results alter (may already exist): {e}")

    # 3. Add saved_at to student_answers
    try:
        cursor.execute("ALTER TABLE student_answers ADD COLUMN saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        print("Added saved_at to student_answers")
    except Exception as e:
        print(f"Skipped student_answers add saved_at (may already exist): {e}")

    # 4. Remove duplicates in student_answers and add UNIQUE index
    try:
        cursor.execute("""
            DELETE t1 FROM student_answers t1
            INNER JOIN student_answers t2 
            WHERE t1.id < t2.id AND t1.student_id = t2.student_id AND t1.exam_id = t2.exam_id AND t1.qid = t2.qid
        """)
        conn.commit()
        cursor.execute("ALTER TABLE student_answers ADD UNIQUE INDEX uq_student_exam_qid (student_id, exam_id, qid)")
        print("Added unique index to student_answers")
    except Exception as e:
        print(f"Skipped adding unique index to student_answers (may already exist): {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database schema update complete.")

except Exception as e:
    print(f"Error: {e}")
