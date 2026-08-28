import mysql.connector
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Harish2007#",
    "database": "online_examination"
}

def migrate():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proctoring_events (
        event_id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        student_id INT NOT NULL,
        exam_id INT NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        severity VARCHAR(20) DEFAULT 'LOW',
        confidence FLOAT DEFAULT NULL,
        metadata JSON DEFAULT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_session (session_id),
        INDEX idx_student_exam (student_id, exam_id)
    )
    """)
    
    # Check if 'proctoring_enabled' column exists in 'examinations'
    cursor.execute("SHOW COLUMNS FROM examinations LIKE 'proctoring_enabled'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE examinations ADD COLUMN proctoring_enabled BOOLEAN DEFAULT FALSE")
        
    conn.commit()
    cursor.close()
    conn.close()
    print("Proctoring DB migration successful.")

if __name__ == '__main__':
    migrate()
