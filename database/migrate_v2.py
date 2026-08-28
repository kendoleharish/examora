"""
EXAMORA Database Migration v2
Idempotent, repeatable migration to upgrade database schema for:
1. Multi-examination architecture (`examinations`, `exam_questions`)
2. Student profile picture support (`students.profile_picture`)
3. Exam ID tracking in sessions, results, and answers (`student_exam_sessions`, `student_results`, `student_answers`)
4. Safe seed of default CS-101 assessment linking existing questions.
"""

import os
import mysql.connector

DB_CONFIG = {
    "host": os.environ.get("EXAMORA_DB_HOST", "localhost"),
    "user": os.environ.get("EXAMORA_DB_USER", "root"),
    "password": os.environ.get("EXAMORA_DB_PASSWORD", "Harish2007#"),
    "database": os.environ.get("EXAMORA_DB_NAME", "online_examination"),
    "port": int(os.environ.get("EXAMORA_DB_PORT", "3306"))
}


def run_migration():
    print("Connecting to database...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # 1. Add profile_picture to students table if not exists
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'students' AND COLUMN_NAME = 'profile_picture'
    """, (DB_CONFIG["database"],))
    if not cursor.fetchone():
        print("Adding profile_picture column to students table...")
        cursor.execute("ALTER TABLE students ADD COLUMN profile_picture VARCHAR(255) NULL DEFAULT NULL AFTER email")
        conn.commit()
    else:
        print("[OK] students.profile_picture already exists.")

    # 2. Create examinations table if not exists
    print("Creating examinations table if not exists...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examinations (
            exam_id INT AUTO_INCREMENT PRIMARY KEY,
            exam_code VARCHAR(50) NOT NULL UNIQUE,
            title VARCHAR(150) NOT NULL,
            category VARCHAR(100) NOT NULL DEFAULT 'Computer Science & IT',
            description TEXT,
            duration_minutes INT NOT NULL DEFAULT 60,
            total_marks INT NOT NULL DEFAULT 10,
            passing_percentage FLOAT NOT NULL DEFAULT 50.0,
            attempt_limit INT NOT NULL DEFAULT 1,
            status VARCHAR(20) NOT NULL DEFAULT 'published',
            start_date DATETIME NULL,
            end_date DATETIME NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_exam_status (status),
            INDEX idx_exam_category (category)
        ) ENGINE=InnoDB;
    """)
    conn.commit()
    print("[OK] examinations table verified.")

    # 3. Create exam_questions table if not exists
    print("Creating exam_questions junction table if not exists...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            exam_id INT NOT NULL,
            qid INT NOT NULL,
            question_order INT DEFAULT 0,
            UNIQUE KEY uq_exam_qid (exam_id, qid),
            INDEX idx_exam_id (exam_id),
            INDEX idx_qid (qid)
        ) ENGINE=InnoDB;
    """)
    conn.commit()
    print("[OK] exam_questions table verified.")

    # 4. Add exam_id column to student_exam_sessions if not exists
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'student_exam_sessions' AND COLUMN_NAME = 'exam_id'
    """, (DB_CONFIG["database"],))
    if not cursor.fetchone():
        print("Adding exam_id column to student_exam_sessions...")
        cursor.execute("ALTER TABLE student_exam_sessions ADD COLUMN exam_id INT NOT NULL DEFAULT 1 AFTER student_id")
        try:
            cursor.execute("SHOW INDEX FROM student_exam_sessions WHERE Key_name = 'student_id'")
            if cursor.fetchone():
                cursor.execute("ALTER TABLE student_exam_sessions DROP INDEX student_id")
        except Exception as e:
            print("Note on student_exam_sessions index:", e)
        cursor.execute("ALTER TABLE student_exam_sessions ADD UNIQUE KEY uq_student_exam (student_id, exam_id)")
        conn.commit()
    else:
        print("[OK] student_exam_sessions.exam_id already exists.")

    # 5. Add exam_id column to student_results if not exists
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'student_results' AND COLUMN_NAME = 'exam_id'
    """, (DB_CONFIG["database"],))
    if not cursor.fetchone():
        print("Adding exam_id column to student_results...")
        cursor.execute("ALTER TABLE student_results ADD COLUMN exam_id INT NOT NULL DEFAULT 1 AFTER student_id")
        try:
            cursor.execute("SHOW INDEX FROM student_results WHERE Key_name = 'student_id'")
            if cursor.fetchone():
                cursor.execute("ALTER TABLE student_results DROP INDEX student_id")
        except Exception as e:
            print("Note on student_results index:", e)
        cursor.execute("ALTER TABLE student_results ADD UNIQUE KEY uq_student_exam_result (student_id, exam_id)")
        conn.commit()
    else:
        print("[OK] student_results.exam_id already exists.")

    # 6. Add exam_id column to student_answers if not exists
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'student_answers' AND COLUMN_NAME = 'exam_id'
    """, (DB_CONFIG["database"],))
    if not cursor.fetchone():
        print("Adding exam_id column to student_answers...")
        cursor.execute("ALTER TABLE student_answers ADD COLUMN exam_id INT NOT NULL DEFAULT 1 AFTER student_id")
        cursor.execute("ALTER TABLE student_answers ADD INDEX idx_student_exam_qid (student_id, exam_id, qid)")
        conn.commit()
    else:
        print("[OK] student_answers.exam_id already exists.")

    # 7. Seed / verify default CS-101 Assessment in examinations table
    cursor.execute("SELECT exam_id FROM examinations WHERE exam_code = 'CS-101'")
    cs_exam = cursor.fetchone()
    if not cs_exam:
        print("Seeding default CS-101 examination...")
        cursor.execute("""
            INSERT INTO examinations (
                exam_code, title, category, description, duration_minutes, total_marks, passing_percentage, attempt_limit, status
            ) VALUES (
                'CS-101', 
                'General Computer Science & IT Assessment', 
                'Computer Science & IT', 
                'Standardized assessment covering computer systems, algorithms, problem solving, hardware architecture, and data structures.',
                60,
                10,
                50.0,
                1,
                'published'
            )
        """)
        conn.commit()
        cs_exam_id = cursor.lastrowid
        print(f"Created default CS-101 exam with ID #{cs_exam_id}")
    else:
        cs_exam_id = cs_exam["exam_id"]
        print(f"[OK] Default CS-101 examination exists with ID #{cs_exam_id}.")

    # 8. Link all current questions to CS-101 in exam_questions
    cursor.execute("SELECT qid FROM questions")
    all_qids = [r["qid"] for r in cursor.fetchall()]
    print(f"Linking {len(all_qids)} questions to default exam CS-101 (#{cs_exam_id})...")
    for order, qid in enumerate(all_qids, start=1):
        cursor.execute("""
            INSERT IGNORE INTO exam_questions (exam_id, qid, question_order)
            VALUES (%s, %s, %s)
        """, (cs_exam_id, qid, order))
    conn.commit()

    # Recalculate total_marks for CS-101
    cursor.execute("""
        SELECT COALESCE(SUM(q.marks), 10) as total_marks 
        FROM exam_questions eq 
        JOIN questions q ON eq.qid = q.qid 
        WHERE eq.exam_id = %s
    """, (cs_exam_id,))
    total_marks_row = cursor.fetchone()
    if total_marks_row:
        total_m = int(total_marks_row["total_marks"] or 10)
        cursor.execute("UPDATE examinations SET total_marks = %s WHERE exam_id = %s", (total_m, cs_exam_id))
        conn.commit()

    # Also seed a secondary sample published exam for multi-exam showcase if none exists
    cursor.execute("SELECT exam_id FROM examinations WHERE exam_code = 'MATH-201'")
    if not cursor.fetchone():
        print("Seeding secondary assessment (MATH-201)...")
        cursor.execute("""
            INSERT INTO examinations (
                exam_code, title, category, description, duration_minutes, total_marks, passing_percentage, attempt_limit, status
            ) VALUES (
                'MATH-201', 
                'Discrete Mathematics & Logic Foundations', 
                'Mathematics', 
                'Evaluation of discrete mathematics, boolean logic, propositional calculus, and proof techniques.',
                45,
                5,
                50.0,
                1,
                'published'
            )
        """)
        conn.commit()
        print("[OK] Seeded MATH-201 examination.")

    cursor.close()
    conn.close()
    print("Migration v2 completed successfully!")


if __name__ == "__main__":
    run_migration()
