import os
import sys
import argparse
import secrets
import string
import mysql.connector
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    "host": os.environ.get("EXAMORA_DB_HOST", "localhost"),
    "user": os.environ.get("EXAMORA_DB_USER", "root"),
    "password": os.environ.get("EXAMORA_DB_PASSWORD", "Harish2007#"),
    "database": os.environ.get("EXAMORA_DB_NAME", "online_examination"),
    "port": int(os.environ.get("EXAMORA_DB_PORT", "3306"))
}

def generate_secure_password(length=14):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(chars) for _ in range(length))

def setup_admin(username, password, full_name, email):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT admin_id, username FROM admins WHERE username = %s", (username,))
    existing = cur.fetchone()
    
    password_hash = generate_password_hash(password)

    if existing:
        cur.execute(
            "UPDATE admins SET password_hash = %s, full_name = %s, email = %s WHERE admin_id = %s",
            (password_hash, full_name, email, existing["admin_id"])
        )
        print(f"[OK] Administrator '{username}' credentials updated successfully.")
    else:
        cur.execute(
            "INSERT INTO admins (username, password_hash, full_name, email) VALUES (%s, %s, %s, %s)",
            (username, password_hash, full_name, email)
        )
        print(f"[OK] Administrator '{username}' created successfully.")

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EXAMORA Admin Account Setup Tool")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", help="Admin password (if omitted, will generate a secure random password)")
    parser.add_argument("--name", default="System Administrator", help="Admin full name")
    parser.add_argument("--email", default="admin@examora.edu", help="Admin email")

    args = parser.parse_args()

    pwd = args.password
    generated = False
    if not pwd:
        pwd = generate_secure_password()
        generated = True

    setup_admin(args.username, pwd, args.name, args.email)

    if generated:
        print("--------------------------------------------------")
        print(f"Generated Administrator Credentials:")
        print(f"Username: {args.username}")
        print(f"Password: {pwd}")
        print("IMPORTANT: Save this password immediately.")
        print("--------------------------------------------------")
