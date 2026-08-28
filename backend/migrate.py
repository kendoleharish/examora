"""
Simple migration runner for EXAMORA backend migrations stored as SQL files in the backend folder.
Run: python migrate.py

This will execute 001_create_student_answers_and_sessions.sql against the DB configured in app.py
"""
import mysql.connector
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Harish2007#",
    "database": "online_examination",
    "port": 3306
}

import glob

def run_migration(sql_file):
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    # Split statements on semicolon - naive but sufficient for these migrations
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as e:
            print('Statement failed:', e)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    here = os.path.dirname(__file__)
    sqls = sorted(glob.glob(os.path.join(here, '*.sql')))
    if not sqls:
        print('No migration files found in', here)
    for sql_file in sqls:
        print('Running migration:', sql_file)
        run_migration(sql_file)

    # Ensure student_exam_sessions has status and submitted_at columns (compatibility across MySQL versions)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema=DATABASE() AND table_name='student_exam_sessions' AND column_name='status'")
        status_exists = cursor.fetchone()[0] > 0
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema=DATABASE() AND table_name='student_exam_sessions' AND column_name='submitted_at'")
        submitted_exists = cursor.fetchone()[0] > 0
        if not status_exists:
            print('Adding status column to student_exam_sessions')
            cursor.execute("ALTER TABLE student_exam_sessions ADD COLUMN status VARCHAR(16) DEFAULT 'active'")
        if not submitted_exists:
            print('Adding submitted_at column to student_exam_sessions')
            cursor.execute("ALTER TABLE student_exam_sessions ADD COLUMN submitted_at TIMESTAMP NULL")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print('Failed to ensure session columns:', e)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema=DATABASE() AND table_name='students' AND column_name='password_hash'")
        password_hash_exists = cursor.fetchone()[0] > 0
        if not password_hash_exists:
            print('Adding password_hash column to students')
            cursor.execute("ALTER TABLE students ADD COLUMN password_hash VARCHAR(255) NULL")
        conn.commit(); cursor.close(); conn.close()
    except Exception as e:
        print('Failed to ensure password_hash column:', e)

    print('All migrations completed.')
