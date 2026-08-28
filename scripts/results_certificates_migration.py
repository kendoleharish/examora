"""
EXAMORA — Results, Certificates & Reporting: Database Migration
Idempotent — safe to rerun.
"""
import mysql.connector, random, string
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Harish2007#",
    "database": "online_examination"
}

def migrate():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # ── Record pre-migration counts ──
    tables = ['student_results', 'students', 'examinations', 'institutions', 'student_answers', 'student_exam_sessions']
    print("=== PRE-MIGRATION COUNTS ===")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) as c FROM {t}")
        print(f"  {t}: {cursor.fetchone()['c']}")
    
    # ── 1. Add result_id PK to student_results if missing ──
    cursor.execute("SHOW COLUMNS FROM student_results LIKE 'result_id'")
    if not cursor.fetchone():
        print("\n[MIGRATION] Adding result_id AUTO_INCREMENT PK to student_results...")
        cursor.execute("ALTER TABLE student_results ADD COLUMN result_id INT AUTO_INCREMENT PRIMARY KEY FIRST")
        conn.commit()
        print("  ✓ result_id column added.")
    else:
        print("\n[SKIP] result_id already exists on student_results.")
    
    # ── 2. Add certificates_enabled to institutions if missing ──
    cursor.execute("SHOW COLUMNS FROM institutions LIKE 'certificates_enabled'")
    if not cursor.fetchone():
        print("[MIGRATION] Adding certificates_enabled to institutions...")
        cursor.execute("ALTER TABLE institutions ADD COLUMN certificates_enabled TINYINT(1) DEFAULT 1")
        conn.commit()
        print("  ✓ certificates_enabled added (default=1).")
    else:
        print("[SKIP] certificates_enabled already exists.")
    
    # ── 3. Create certificates table ──
    cursor.execute("SHOW TABLES LIKE 'certificates'")
    if not cursor.fetchone():
        print("[MIGRATION] Creating certificates table...")
        cursor.execute("""
            CREATE TABLE certificates (
                certificate_id VARCHAR(20) NOT NULL,
                result_id INT NOT NULL,
                student_id INT NOT NULL,
                exam_id INT NOT NULL,
                institution_id INT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (certificate_id),
                UNIQUE KEY uq_cert_result (result_id),
                KEY idx_cert_student (student_id),
                KEY idx_cert_institution (institution_id),
                CONSTRAINT fk_cert_result FOREIGN KEY (result_id) REFERENCES student_results(result_id) ON DELETE CASCADE,
                CONSTRAINT fk_cert_institution FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        conn.commit()
        print("  ✓ certificates table created.")
    else:
        print("[SKIP] certificates table already exists.")

    # ── 4. Verify post-migration counts ──
    print("\n=== POST-MIGRATION COUNTS ===")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) as c FROM {t}")
        print(f"  {t}: {cursor.fetchone()['c']}")
    
    cursor.execute("SELECT COUNT(*) as c FROM certificates")
    print(f"  certificates: {cursor.fetchone()['c']}")
    
    # Verify result_id was assigned
    cursor.execute("SELECT result_id, student_id, exam_id FROM student_results ORDER BY result_id")
    rows = cursor.fetchall()
    print(f"\n  student_results result_id assignments:")
    for r in rows:
        print(f"    result_id={r['result_id']}, student_id={r['student_id']}, exam_id={r['exam_id']}")
    
    cursor.close()
    conn.close()
    print("\n✓ Migration complete. All existing data preserved.")

if __name__ == '__main__':
    migrate()
