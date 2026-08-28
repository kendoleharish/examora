import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Harish2007#",
    "database": "online_examination"
}

def migrate():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Create audit_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        actor_id INT,
        actor_role VARCHAR(50),
        institution_id INT,
        action VARCHAR(100),
        target_id VARCHAR(50),
        metadata JSON,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Add settings columns to institutions if they don't exist
    cursor.execute("SHOW COLUMNS FROM institutions LIKE 'primary_color'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE institutions ADD COLUMN primary_color VARCHAR(20) DEFAULT '#0061A4'")
        cursor.execute("ALTER TABLE institutions ADD COLUMN secondary_color VARCHAR(20) DEFAULT '#535F70'")
        cursor.execute("ALTER TABLE institutions ADD COLUMN website VARCHAR(255)")
        cursor.execute("ALTER TABLE institutions ADD COLUMN timezone VARCHAR(100) DEFAULT 'UTC'")
    
    # Make sure we have a second institution for testing
    cursor.execute("SELECT institution_id FROM institutions WHERE institution_name = 'Institution B'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO institutions (institution_name, primary_color) VALUES ('Institution B', '#B3261E')")
        inst_b_id = cursor.lastrowid
        # Create an admin for Institution B
        from werkzeug.security import generate_password_hash
        pwd = generate_password_hash("admin123")
        cursor.execute("INSERT INTO admins (username, password_hash, full_name, institution_id, role) VALUES ('admin_b', %s, 'Admin B', %s, 'ADMIN')", (pwd, inst_b_id))
        
        # Create a student for Institution B
        cursor.execute("INSERT INTO students (username, password_hash, student_name, institution_id, email) VALUES ('student_b', %s, 'Student B', %s, 'studentb@example.com')", (pwd, inst_b_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Multi-tenant DB migration successful.")

if __name__ == '__main__':
    migrate()
