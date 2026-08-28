import os
import sys
import mysql.connector

DB_CONFIG = {
    "host": os.environ.get("EXAMORA_DB_HOST", "localhost"),
    "user": os.environ.get("EXAMORA_DB_USER", "root"),
    "password": os.environ.get("EXAMORA_DB_PASSWORD", "Harish2007#"),
    "database": os.environ.get("EXAMORA_DB_NAME", "online_examination"),
    "port": int(os.environ.get("EXAMORA_DB_PORT", "3306"))
}

def migrate():
    print("Connecting to MySQL database...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)

    # 1. Create Admins Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """)
    print("[OK] Admins table verified/created.")

    # 2. Add 'status' and 'created_at' column to students if missing
    cur.execute("SHOW COLUMNS FROM students LIKE 'status'")
    if not cur.fetchone():
        cur.execute("ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
        print("[OK] Added 'status' column to students table.")

    cur.execute("SHOW COLUMNS FROM students LIKE 'created_at'")
    if not cur.fetchone():
        cur.execute("ALTER TABLE students ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("[OK] Added 'created_at' column to students table.")

    cur.execute("UPDATE students SET status = 'active' WHERE status IS NULL OR status = ''")

    # 3. Add 'category' column to questions if missing
    cur.execute("SHOW COLUMNS FROM questions LIKE 'category'")
    if not cur.fetchone():
        cur.execute("ALTER TABLE questions ADD COLUMN category VARCHAR(100) DEFAULT 'Computer Science & IT'")
        print("[OK] Added 'category' column to questions table.")
    else:
        print("[OK] 'category' column already exists in questions table.")

    # Set default category for questions with NULL
    cur.execute("UPDATE questions SET category = 'Computer Science & IT' WHERE category IS NULL OR category = ''")

    # 4. Verify student_exam_sessions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_exam_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL UNIQUE,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration_seconds INT NOT NULL DEFAULT 3600,
        status VARCHAR(16) DEFAULT 'active',
        submitted_at TIMESTAMP NULL
    ) ENGINE=InnoDB
    """)
    print("[OK] Student exam sessions table verified/created.")

    # 5. Verify student_results table & grade column size
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_results (
        student_id INT UNIQUE,
        student_name VARCHAR(100),
        score INT NOT NULL DEFAULT 0,
        total_marks INT NOT NULL DEFAULT 0,
        percentage FLOAT NOT NULL DEFAULT 0.0,
        grade VARCHAR(8) NOT NULL DEFAULT 'F',
        exam_date DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """)
    cur.execute("ALTER TABLE student_results MODIFY COLUMN grade VARCHAR(8) NOT NULL DEFAULT 'F'")
    print("[OK] Student results table verified/created.")

    # 6. Verify student_answers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_answers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        qid INT NOT NULL,
        selected_answer VARCHAR(16),
        correct_answer VARCHAR(16),
        marks INT DEFAULT 0,
        marks_obtained INT DEFAULT 0,
        exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """)
    print("[OK] Student answers table verified/created.")

    # 7. Verify notifications table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        title VARCHAR(150) NOT NULL,
        message TEXT NOT NULL,
        type VARCHAR(50) DEFAULT 'system',
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_student_unread (student_id, is_read)
    ) ENGINE=InnoDB
    """)
    print("[OK] Notifications table verified/created.")

    conn.commit()
    cur.close()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate()
