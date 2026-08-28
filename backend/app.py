import os
import re
import uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, request, session, send_from_directory
from flask_cors import CORS
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("EXAMORA_SECRET_KEY", "examora-secure-session-key-2026")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CORS(app, supports_credentials=True)

DB_CONFIG = {
    "host": os.environ.get("EXAMORA_DB_HOST", "localhost"),
    "user": os.environ.get("EXAMORA_DB_USER", "root"),
    "password": os.environ.get("EXAMORA_DB_PASSWORD", "Harish2007#"),
    "database": os.environ.get("EXAMORA_DB_NAME", "online_examination"),
    "port": int(os.environ.get("EXAMORA_DB_PORT", "3306"))
}

# Avatar upload storage configuration
UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
AVATARS_DIR = os.path.join(UPLOAD_ROOT, "avatars")
os.makedirs(AVATARS_DIR, exist_ok=True)
ALLOWED_AVATAR_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB



import json
def log_audit(actor_id, actor_role, institution_id, action, target_id, metadata=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        meta_str = json.dumps(metadata) if metadata else None
        cursor.execute("""
            INSERT INTO audit_logs (actor_id, actor_role, institution_id, action, target_id, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (actor_id, actor_role, institution_id, action, str(target_id), meta_str))
        conn.commit()
        cursor.close(); conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def create_notification(student_id, title, message, notif_type="system"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "INSERT INTO notifications (student_id, title, message, type, is_read, created_at) VALUES (%s, %s, %s, %s, FALSE, NOW())",
            (student_id, title, message, notif_type)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to create notification for student #{student_id}: {e}")


def broadcast_notification_to_all_active_students(title, message, notif_type="exam"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT student_id FROM students WHERE status = 'active'")
        active_students = cursor.fetchall()
        for s in active_students:
            cursor.execute(
                "INSERT INTO notifications (student_id, title, message, type, is_read, created_at) VALUES (%s, %s, %s, %s, FALSE, NOW())",
                (s["student_id"], title, message, notif_type)
            )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to broadcast notification: {e}")


# ----------------------------------------------------
# AUTHENTICATION & AUTHORIZATION HELPERS
# ----------------------------------------------------

def get_authenticated_student():
    student_id = session.get("student_id")
    if student_id is None:
        return None
    try:
        student_id = int(student_id)
    except (TypeError, ValueError):
        return None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT student_id, institution_id, student_name, username, email, profile_picture, status, created_at FROM students WHERE student_id = %s",
            (student_id,)
        )
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        return student
    except Exception:
        return None


def require_student_auth():
    student_id = session.get("student_id")
    if student_id is None:
        return None, (jsonify({"success": False, "message": "Authentication required."}), 401)

    student = get_authenticated_student()
    if not student:
        session.clear()
        return None, (jsonify({"success": False, "message": "Invalid or expired student session."}), 401)

    if student.get("status") != "active":
        msg = "Account pending approval." if student.get("status") == "pending" else "Account has been disabled."
        return None, (jsonify({"success": False, "message": msg, "status": student.get("status")}), 403)

    # If client submitted student_id in query, verify it matches session
    req_student_id = request.args.get("student_id")
    if req_student_id is not None:
        try:
            if int(req_student_id) != student["student_id"]:
                return None, (jsonify({"success": False, "message": "Unauthorized student access."}), 403)
        except (ValueError, TypeError):
            return None, (jsonify({"success": False, "message": "Invalid student identifier."}), 400)

    return student, None


def get_authenticated_admin():
    admin_id = session.get("admin_id")
    is_admin = session.get("is_admin")
    if not admin_id or not is_admin:
        return None

    try:
        admin_id = int(admin_id)
    except (TypeError, ValueError):
        return None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT admin_id, institution_id, role, username, full_name, email FROM admins WHERE admin_id = %s",
            (admin_id,)
        )
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        return admin
    except Exception:
        return None


def require_admin_auth():
    admin = get_authenticated_admin()
    if not admin:
        if session.get("student_id"):
            return None, (jsonify({"success": False, "message": "Administrator privileges required."}), 403)
        return None, (jsonify({"success": False, "message": "Administrator authentication required."}), 401)
    return admin, None


# ----------------------------------------------------
# TENANT HELPERS
# ----------------------------------------------------
def get_tenant_where(admin, alias=""):
    if not admin or admin.get("role") == "SUPER_ADMIN":
        return " WHERE 1=1 "
    col = f"{alias}.institution_id" if alias else "institution_id"
    return f" WHERE {col} = {int(admin['institution_id'])} "

def get_tenant_and(admin, alias=""):
    if not admin or admin.get("role") == "SUPER_ADMIN":
        return " "
    col = f"{alias}.institution_id" if alias else "institution_id"
    return f" AND {col} = {int(admin['institution_id'])} "


# ----------------------------------------------------
# PUBLIC HEALTH & DIAGNOSTIC ENDPOINTS
# ----------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "system": "EXAMORA Online Examination System",
        "version": "3.0.0"
    })

@app.route("/frontend/<path:filename>")
def serve_frontend(filename):
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
    return send_from_directory(frontend_dir, filename)


@app.route("/api/test-db")
def test_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({
            "success": True,
            "message": "Database connected successfully!",
            "database": db_name
        })
    except Exception:
        return jsonify({
            "success": False,
            "message": "Database connection unavailable."
        }), 500


# ----------------------------------------------------
# FILE UPLOAD / AVATAR SERVING
# ----------------------------------------------------

@app.route("/api/uploads/avatars/<path:filename>")
def serve_avatar(filename):
    safe_name = os.path.basename(filename)
    return send_from_directory(AVATARS_DIR, safe_name)


# ----------------------------------------------------
# STUDENT REGISTRATION & AUTHENTICATION
# ----------------------------------------------------

@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True) or {}
        student_name = (data.get("student_name") or "").strip()
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        confirm_password = data.get("confirm_password") or ""
        institution_id = data.get("institution_id")
        
        # Default to 1 if not provided for backward compatibility
        try:
            institution_id = int(institution_id) if institution_id else 1
        except ValueError:
            institution_id = 1

        if not student_name or not username or not email or not password:
            return jsonify({"success": False, "message": "All fields are required."}), 400

        if password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match."}), 400

        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, email):
            return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT student_id FROM students WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Username already exists. Please choose another."}), 409

        cursor.execute("SELECT student_id FROM students WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already exists."}), 409

        pwd_hash = generate_password_hash(password)
        cursor.execute(
            """INSERT INTO students (institution_id, student_name, username, email, password_hash, status, created_at) 
               VALUES (%s, %s, %s, %s, %s, 'pending', NOW())""",
            (institution_id, student_name, username, email, pwd_hash)
        )
        new_student_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        create_notification(
            new_student_id,
            "Account Registration Received",
            "Your examination account request has been submitted and is pending administrator review and approval.",
            "account"
        )

        return jsonify({
            "success": True,
            "message": "Account created successfully! Your registration is pending administrator approval before you can log in."
        }), 201

    except Exception:
        return jsonify({"success": False, "message": "Registration failed. Please try again later."}), 500


@app.route("/api/login", methods=["POST"])
def student_login():
    try:
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT student_id, student_name, username, email, password_hash, profile_picture, status FROM students WHERE username = %s",
            (username,)
        )
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        if not student or not student.get("password_hash"):
            return jsonify({"success": False, "message": "Invalid username or password!"}), 401

        if not check_password_hash(student["password_hash"], password):
            return jsonify({"success": False, "message": "Invalid username or password!"}), 401

        status = student.get("status") or "active"
        if status == "pending":
            return jsonify({
                "success": False,
                "message": "Your account registration is pending administrator approval. Please contact your institution administrator."
            }), 403

        if status == "disabled":
            return jsonify({
                "success": False,
                "message": "Your student account has been disabled. Please contact your institution administrator."
            }), 403

        session.clear()
        session["student_id"] = student["student_id"]
        session["student_name"] = student.get("student_name") or ""
        session["username"] = student.get("username") or ""
        session["role"] = "student"

        student_payload = {
            "student_id": student["student_id"],
            "student_name": student.get("student_name"),
            "username": student.get("username"),
            "email": student.get("email"),
            "profile_picture": student.get("profile_picture"),
            "status": status
        }

        return jsonify({
            "success": True,
            "message": "Login successful!",
            "student": student_payload
        })

    except Exception:
        return jsonify({"success": False, "message": "Login failed. Please try again later."}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out."})


# ----------------------------------------------------
# ADMIN AUTHENTICATION
# ----------------------------------------------------

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    try:
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT admin_id, username, full_name, email, password_hash FROM admins WHERE username = %s",
            (username,)
        )
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if not admin or not admin.get("password_hash"):
            return jsonify({"success": False, "message": "Invalid administrator credentials."}), 401

        if not check_password_hash(admin["password_hash"], password):
            return jsonify({"success": False, "message": "Invalid administrator credentials."}), 401

        session.clear()
        session["admin_id"] = admin["admin_id"]
        session["admin_username"] = admin["username"]
        session["admin_name"] = admin["full_name"]
        session["is_admin"] = True
        session["role"] = "admin"

        return jsonify({
            "success": True,
            "message": "Administrator login successful.",
            "admin": {
                "admin_id": admin["admin_id"],
                "username": admin["username"],
                "full_name": admin["full_name"],
                "email": admin["email"]
            }
        })

    except Exception:
        return jsonify({"success": False, "message": "Administrator login failed."}), 500


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return jsonify({"success": True, "message": "Administrator logged out successfully."})


@app.route("/api/admin/session")
def admin_session():
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    return jsonify({
        "success": True,
        "admin": {
            "admin_id": admin["admin_id"],
            "username": admin["username"],
            "full_name": admin["full_name"],
            "email": admin["email"]
        }
    })


# ----------------------------------------------------
# NOTIFICATIONS API (Student Protected)
# ----------------------------------------------------

@app.route("/api/notifications")
def get_notifications():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, message, type, is_read, created_at FROM notifications WHERE student_id = %s ORDER BY created_at DESC LIMIT 30",
            (student_id,)
        )
        notifs = cursor.fetchall()

        cursor.execute(
            "SELECT COUNT(*) as unread FROM notifications WHERE student_id = %s AND is_read = FALSE",
            (student_id,)
        )
        unread_row = cursor.fetchone()
        unread_count = int(unread_row["unread"] or 0) if unread_row else 0

        cursor.close()
        conn.close()

        for n in notifs:
            if n.get("created_at"):
                n["created_at"] = str(n["created_at"])
            n["is_read"] = bool(n.get("is_read"))

        return jsonify({
            "success": True,
            "notifications": notifs,
            "unread_count": unread_count
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch notifications."}), 500


@app.route("/api/notifications/<int:nid>/read", methods=["PUT"])
def mark_notification_read(nid):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE id = %s AND student_id = %s",
            (nid, student_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Notification marked as read."})
    except Exception:
        return jsonify({"success": False, "message": "Failed to update notification."}), 500


@app.route("/api/notifications/read-all", methods=["PUT"])
def mark_all_notifications_read():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE student_id = %s AND is_read = FALSE",
            (student_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "All notifications marked as read."})
    except Exception:
        return jsonify({"success": False, "message": "Failed to mark notifications as read."}), 500


# ----------------------------------------------------
# STUDENT PROFILE & AVATAR PHOTO SYSTEM
# ----------------------------------------------------

@app.route("/api/students")
def get_students():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT student_id, student_name, username, email, profile_picture FROM students WHERE student_id = %s",
            (student["student_id"],)
        )
        students = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "students": students
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch student record."}), 500


@app.route("/api/profile", methods=["GET", "PUT"])
def student_profile():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]

    if request.method == "GET":
        return jsonify({
            "success": True,
            "student": {
                "student_id": student["student_id"],
                "student_name": student["student_name"],
                "username": student["username"],
                "email": student["email"],
                "profile_picture": student.get("profile_picture"),
                "status": student["status"],
                "created_at": str(student.get("created_at") or "")
            }
        })

    # PUT: Update profile details
    data = request.get_json(silent=True) or {}
    new_name = (data.get("student_name") or "").strip()
    new_email = (data.get("email") or "").strip().lower()

    if not new_name or not new_email:
        return jsonify({"success": False, "message": "Name and email are required."}), 400

    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, new_email):
        return jsonify({"success": False, "message": "Please provide a valid email address."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT student_id FROM students WHERE email = %s AND student_id != %s", (new_email, student_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email is already in use by another account."}), 409

        cursor.execute("UPDATE students SET student_name = %s, email = %s WHERE student_id = %s", (new_name, new_email, student_id))
        conn.commit()
        cursor.close()
        conn.close()

        session["student_name"] = new_name
        return jsonify({"success": True, "message": "Profile updated successfully!"})
    except Exception:
        return jsonify({"success": False, "message": "Failed to update profile."}), 500


@app.route("/api/profile/photo", methods=["POST", "DELETE"])
def profile_photo():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]

    if request.method == "DELETE":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT profile_picture FROM students WHERE student_id = %s", (student_id,))
            row = cursor.fetchone()
            if row and row.get("profile_picture"):
                old_file = os.path.basename(row["profile_picture"])
                old_path = os.path.join(AVATARS_DIR, old_file)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass

            cursor.execute("UPDATE students SET profile_picture = NULL WHERE student_id = %s", (student_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "Profile picture removed successfully."})
        except Exception:
            return jsonify({"success": False, "message": "Failed to remove profile picture."}), 500

    # POST: Upload Photo
    if "photo" not in request.files:
        return jsonify({"success": False, "message": "No photo file provided."}), 400

    file = request.files["photo"]
    if not file or file.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    # Validate file extension
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        return jsonify({"success": False, "message": "Invalid image format. Allowed formats: JPEG, PNG, WEBP."}), 400

    # Read content & validate file size (max 2MB)
    content = file.read()
    if len(content) > MAX_AVATAR_BYTES:
        return jsonify({"success": False, "message": "File size exceeds 2MB limit. Please upload a smaller image."}), 400

    if len(content) < 16:
        return jsonify({"success": False, "message": "Invalid or corrupted image file."}), 400

    # Validate image magic signature
    is_valid_image = False
    if content.startswith(b"\xff\xd8\xff"):  # JPEG
        is_valid_image = True
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):  # PNG
        is_valid_image = True
    elif content[:4] == b"RIFF" and content[8:12] == b"WEBP":  # WEBP
        is_valid_image = True

    if not is_valid_image:
        return jsonify({"success": False, "message": "File content does not match a valid image format."}), 400

    # Generate safe unique filename
    safe_avatar_name = f"avatar_{student_id}_{uuid.uuid4().hex[:12]}.{ext}"
    dest_path = os.path.join(AVATARS_DIR, safe_avatar_name)

    try:
        with open(dest_path, "wb") as f:
            f.write(content)

        photo_url = f"/api/uploads/avatars/{safe_avatar_name}"

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Check and remove old photo file
        cursor.execute("SELECT profile_picture FROM students WHERE student_id = %s", (student_id,))
        row = cursor.fetchone()
        if row and row.get("profile_picture"):
            old_file = os.path.basename(row["profile_picture"])
            old_path = os.path.join(AVATARS_DIR, old_file)
            if os.path.exists(old_path) and old_file != safe_avatar_name:
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        cursor.execute("UPDATE students SET profile_picture = %s WHERE student_id = %s", (photo_url, student_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Profile picture updated successfully!",
            "photo_url": photo_url
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to save profile picture."}), 500


# ----------------------------------------------------
# STUDENT MULTI-EXAMINATION LIFECYCLE
# ----------------------------------------------------

@app.route("/api/examinations")
def get_examinations_list():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT e.exam_id, e.exam_code, e.title, e.category, e.description,
                   e.duration_minutes, e.total_marks, e.passing_percentage, e.attempt_limit, e.status,
                   e.start_date, e.end_date,
                   COUNT(DISTINCT eq.qid) AS question_count,
                   ses.status AS session_status,
                   ses.start_time,
                   ses.duration_seconds,
                   TIMESTAMPDIFF(SECOND, ses.start_time, NOW()) AS elapsed_seconds,
                   sr.score, sr.total_marks as result_total_marks, sr.percentage, sr.grade
            FROM examinations e
            LEFT JOIN exam_questions eq ON e.exam_id = eq.exam_id
            LEFT JOIN student_exam_sessions ses ON e.exam_id = ses.exam_id AND ses.student_id = %s
            LEFT JOIN student_results sr ON e.exam_id = sr.exam_id AND sr.student_id = %s
            WHERE e.status IN ('published', 'active')
            GROUP BY e.exam_id
            ORDER BY e.exam_id ASC
        """, (student_id, student_id))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        exams = []
        for r in rows:
            duration_sec = int(r.get("duration_seconds") or (r["duration_minutes"] * 60))
            elapsed = int(r.get("elapsed_seconds") or 0)
            session_st = r.get("session_status")
            has_result = r.get("score") is not None

            if has_result or session_st == "submitted":
                student_status = "COMPLETED"
            elif session_st == "active" and elapsed < duration_sec + 60:
                student_status = "IN_PROGRESS"
            elif session_st == "expired" or (r.get("start_time") and elapsed >= duration_sec + 60):
                student_status = "EXPIRED"
            else:
                student_status = "AVAILABLE"

            remaining = max(0, duration_sec - elapsed) if session_st == "active" else duration_sec

            exams.append({
                "exam_id": r["exam_id"],
                "exam_code": r["exam_code"],
                "title": r["title"],
                "category": r["category"],
                "description": r.get("description") or "",
                "duration_minutes": r["duration_minutes"],
                "total_marks": r["total_marks"],
                "passing_percentage": float(r.get("passing_percentage") or 50.0),
                "attempt_limit": r["attempt_limit"],
                "question_count": int(r.get("question_count") or 0),
                "status": r["status"],
                "student_status": student_status,
                "remaining_seconds": remaining,
                "score": r.get("score"),
                "percentage": r.get("percentage"),
                "grade": r.get("grade")
            })

        return jsonify({"success": True, "examinations": exams})
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch examinations."}), 500


@app.route("/api/examinations/<int:exam_id>")
def get_examination_detail(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT e.exam_id, e.exam_code, e.title, e.category, e.description,
                   e.duration_minutes, e.total_marks, e.passing_percentage, e.attempt_limit, e.status,
                   COUNT(DISTINCT eq.qid) AS question_count,
                   ses.status AS session_status,
                   ses.start_time,
                   ses.duration_seconds,
                   TIMESTAMPDIFF(SECOND, ses.start_time, NOW()) AS elapsed_seconds,
                   sr.score, sr.percentage, sr.grade
            FROM examinations e
            LEFT JOIN exam_questions eq ON e.exam_id = eq.exam_id
            LEFT JOIN student_exam_sessions ses ON e.exam_id = ses.exam_id AND ses.student_id = %s
            LEFT JOIN student_results sr ON e.exam_id = sr.exam_id AND sr.student_id = %s
            WHERE e.exam_id = %s
            GROUP BY e.exam_id
        """, (student_id, student_id, exam_id))
        exam = cursor.fetchone()
        cursor.close()
        conn.close()

        if not exam:
            return jsonify({"success": False, "message": "Examination not found."}), 404

        duration_sec = int(exam.get("duration_seconds") or (exam["duration_minutes"] * 60))
        elapsed = int(exam.get("elapsed_seconds") or 0)
        session_st = exam.get("session_status")
        has_result = exam.get("score") is not None

        if has_result or session_st == "submitted":
            student_status = "COMPLETED"
        elif session_st == "active" and elapsed < duration_sec + 60:
            student_status = "IN_PROGRESS"
        elif session_st == "expired" or (exam.get("start_time") and elapsed >= duration_sec + 60):
            student_status = "EXPIRED"
        else:
            student_status = "AVAILABLE"

        remaining = max(0, duration_sec - elapsed) if session_st == "active" else duration_sec

        return jsonify({
            "success": True,
            "examination": {
                "exam_id": exam["exam_id"],
                "exam_code": exam["exam_code"],
                "title": exam["title"],
                "category": exam["category"],
                "description": exam.get("description") or "",
                "duration_minutes": exam["duration_minutes"],
                "total_marks": exam["total_marks"],
                "passing_percentage": float(exam.get("passing_percentage") or 50.0),
                "attempt_limit": exam["attempt_limit"],
                "question_count": int(exam.get("question_count") or 0),
                "status": exam["status"],
                "student_status": student_status,
                "remaining_seconds": remaining,
                "score": exam.get("score"),
                "percentage": exam.get("percentage"),
                "grade": exam.get("grade")
            }
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch examination details."}), 500



@app.route("/api/examinations/code/<exam_code>", methods=["GET"])
def get_exam_by_code(exam_code):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.exam_id, e.institution_id, e.title, e.description, e.duration_minutes, e.total_marks, e.status, i.institution_name
            FROM examinations e
            LEFT JOIN institutions i ON e.institution_id = i.institution_id
            WHERE e.exam_code = %s
        """, (exam_code,))
        exam = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not exam:
            return jsonify({"success": False, "message": "Invalid Exam Code."}), 404
            
        if exam["status"] != "published":
            return jsonify({"success": False, "message": "Exam is not currently available."}), 403
            
        student = get_authenticated_student()
        is_authenticated = bool(student)
        
        return jsonify({
            "success": True, 
            "exam": exam,
            "is_authenticated": is_authenticated
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/examinations/<int:exam_id>/start", methods=["POST"])
def start_examination(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT exam_id, title, duration_minutes, status FROM examinations WHERE exam_id = %s", (exam_id,))
        exam = cursor.fetchone()
        if not exam:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Examination not found."}), 404

        if exam["status"] not in ["published", "active"]:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "This examination is not currently open."}), 400

        duration_seconds = int(exam["duration_minutes"] * 60)

        # 1. Check if already attempted
        cursor.execute("SELECT COUNT(*) AS cnt FROM student_results WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        r = cursor.fetchone()
        if r and r.get("cnt", 0) > 0:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "You have already completed this examination."}), 400

        # 2. Check existing session
        cursor.execute(
            "SELECT id, start_time, duration_seconds, status, TIMESTAMPDIFF(SECOND, start_time, NOW()) AS elapsed_seconds FROM student_exam_sessions WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        )
        sess = cursor.fetchone()

        if sess:
            elapsed = int(sess.get("elapsed_seconds") or 0)
            duration = int(sess.get("duration_seconds") or duration_seconds)
            status = sess.get("status") or "active"
            remaining = max(0, duration - elapsed)

            if status == "submitted":
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "You have already completed this examination."}), 400

            if status == "expired" or remaining <= 0:
                if status != "submitted":
                    student_name_or_username = student.get("student_name") or student.get("username")
                    _internal_submit_examination(student_id, exam_id, "AUTO_TIMEOUT", {}, student_name_or_username)
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "Exam session has expired."}), 400

            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "Exam session active.", "remaining_seconds": remaining, "exam_id": exam_id})

        # Insert new session
        cursor.execute(
            "INSERT INTO student_exam_sessions (student_id, exam_id, duration_seconds, status, start_time) VALUES (%s, %s, %s, 'active', NOW())",
            (student_id, exam_id, duration_seconds)
        )
        conn.commit()
        cursor.close()
        conn.close()

        create_notification(
            student_id,
            f"Examination Started: {exam['title']}",
            f"Your assessment session has started with a server-authoritative timer of {exam['duration_minutes']} minutes.",
            "exam"
        )

        return jsonify({"success": True, "message": "Exam started.", "remaining_seconds": duration_seconds, "exam_id": exam_id})

    except Exception:
        return jsonify({"success": False, "message": "Failed to start examination session."}), 500


@app.route("/api/examinations/<int:exam_id>/session")
def get_examination_session(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, start_time, duration_seconds, status, submitted_at, TIMESTAMPDIFF(SECOND, start_time, NOW()) AS elapsed_seconds FROM student_exam_sessions WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        )
        sess = cursor.fetchone()
        cursor.close()
        conn.close()

        if not sess:
            return jsonify({"success": False, "message": "No active session for this examination."}), 404

        start_time = sess.get("start_time")
        duration_seconds = int(sess.get("duration_seconds") or 0)
        status = sess.get("status") or "active"
        elapsed = int(sess.get("elapsed_seconds") or 0)
        remaining = max(0, duration_seconds - elapsed)

        # Auto-finalize if expired and not yet submitted
        if remaining <= 0 and status != "submitted":
            student_name_or_username = student.get("student_name") or student.get("username")
            _internal_submit_examination(student_id, exam_id, "AUTO_TIMEOUT", {}, student_name_or_username)
            status = "submitted"
            remaining = 0

        return jsonify({
            "success": True,
            "session": {
                "exam_id": exam_id,
                "status": status,
                "remaining_seconds": remaining,
                "start_time": str(start_time),
                "duration_seconds": duration_seconds,
                "submitted_at": str(sess.get("submitted_at")) if sess.get("submitted_at") else None
            }
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to retrieve examination session."}), 500


@app.route("/api/examinations/<int:exam_id>/questions")
def get_examination_questions(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Strip correct_answer completely from student payload
        cursor.execute("""
            SELECT q.qid, q.category, q.question, q.optionA, q.optionB, q.optionC, q.optionD, q.marks
            FROM exam_questions eq
            JOIN questions q ON eq.qid = q.qid
            WHERE eq.exam_id = %s
            ORDER BY eq.question_order ASC, q.qid ASC
        """, (exam_id,))
        questions = cursor.fetchall()

        # Fallback if no questions linked yet
        if not questions:
            cursor.execute("SELECT qid, category, question, optionA, optionB, optionC, optionD, marks FROM questions ORDER BY qid ASC")
            questions = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "exam_id": exam_id, "questions": questions})
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch examination questions."}), 500



@app.route("/api/examinations/<int:exam_id>/autosave", methods=["POST"])
def autosave_examination(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    qid = data.get("qid")
    selected = data.get("selected_answer", "").strip()
    answer_text = data.get("answer_text", "")
    answer_json = data.get("answer_json")

    if not qid:
        return jsonify({"success": False, "message": "Question ID (qid) is required."}), 400

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, duration_seconds, status, TIMESTAMPDIFF(SECOND, start_time, NOW()) AS elapsed_seconds FROM student_exam_sessions WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        )
        sess = cursor.fetchone()
        if not sess:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "No active exam session found."}), 400

        if sess.get("status") == "submitted":
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "EXAM_EXPIRED"}), 400

        duration_seconds = int(sess.get("duration_seconds") or 3600)
        elapsed = int(sess.get("elapsed_seconds") or 0)

        if elapsed >= duration_seconds:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "EXAM_EXPIRED"}), 400

        cursor.execute("SELECT type, marks, correct_answer FROM questions WHERE qid = %s", (qid,))
        q = cursor.fetchone()
        if not q:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Question not found."}), 404
        
        q_type = q.get("type", "MCQ")
        q_marks = int(q.get("marks") or 1)
        
        marks_obtained = 0
        eval_status = 'AUTO_SCORED'
        
        if q_type == 'MCQ':
            correct_ans = (q.get("correct_answer") or "").strip().upper()
            selected = selected.upper()
            marks_obtained = q_marks if selected == correct_ans and selected != "" else 0
        elif q_type in ['DESCRIPTIVE', 'SHORT_ANSWER']:
            eval_status = 'PENDING'
            selected = ""
            
        import json
        answer_json_str = json.dumps(answer_json) if answer_json else None

        cursor.execute("""
            INSERT INTO student_answers (student_id, exam_id, qid, selected_answer, answer_text, answer_json, evaluation_status, correct_answer, marks, marks_obtained)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                selected_answer = VALUES(selected_answer),
                answer_text = VALUES(answer_text),
                answer_json = VALUES(answer_json),
                evaluation_status = VALUES(evaluation_status),
                marks_obtained = VALUES(marks_obtained)
        """, (student_id, exam_id, qid, selected, answer_text, answer_json_str, eval_status, q.get("correct_answer"), q_marks, marks_obtained))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Answer autosaved."})

    except Exception as e:
        print(f"Autosave error: {e}")
        return jsonify({"success": False, "message": "Failed to autosave answer."}), 500

def _internal_submit_examination(student_id, exam_id, submission_type, answers, student_name_or_username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT exam_id, title, duration_minutes FROM examinations WHERE exam_id = %s", (exam_id,))
        exam = cursor.fetchone()
        if not exam:
            cursor.close(); conn.close()
            return {"success": False, "message": "Examination not found."}, 404

        cursor.execute("SELECT COUNT(*) AS cnt FROM student_results WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        row = cursor.fetchone()
        if row and row.get("cnt", 0) > 0:
            cursor.close(); conn.close()
            return {"success": False, "message": "You have already completed this examination."}, 400

        cursor.execute(
            "SELECT id, start_time, duration_seconds, status, TIMESTAMPDIFF(SECOND, start_time, NOW()) AS elapsed_seconds FROM student_exam_sessions WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        )
        sess = cursor.fetchone()
        if not sess:
            cursor.close(); conn.close()
            return {"success": False, "message": "No active exam session found."}, 400

        if sess.get("status") == "submitted":
            cursor.close(); conn.close()
            return {"success": False, "message": "You have already completed this examination."}, 400

        duration_seconds = int(sess.get("duration_seconds") or (exam["duration_minutes"] * 60))
        elapsed = int(sess.get("elapsed_seconds") or 0)

        if elapsed >= duration_seconds:
            submission_type = 'AUTO_TIMEOUT'

        cursor.execute("""
            SELECT q.qid, q.question, q.correct_answer, q.marks
            FROM exam_questions eq
            JOIN questions q ON eq.qid = q.qid
            WHERE eq.exam_id = %s
        """, (exam_id,))
        questions = cursor.fetchall()

        if not questions:
            cursor.execute("SELECT qid, question, correct_answer, marks FROM questions")
            questions = cursor.fetchall()

        total_marks = 0
        total_score = 0

        is_past_deadline = elapsed >= duration_seconds
        
        cursor.execute("SELECT qid, selected_answer, marks_obtained FROM student_answers WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        saved_answers = {row["qid"]: row for row in cursor.fetchall()}

        for q in questions:
            qid = q["qid"]
            q_marks = int(q.get("marks") or 1)
            total_marks += q_marks
            correct_ans = (q.get("correct_answer") or "").strip().upper()
            
            selected = ""
            if is_past_deadline:
                if qid in saved_answers:
                    selected = saved_answers[qid]["selected_answer"]
                    marks_obtained = saved_answers[qid]["marks_obtained"]
                else:
                    marks_obtained = 0
            else:
                payload_ans = (answers.get(str(qid)) or answers.get(qid) or "").strip().upper()
                if payload_ans:
                    selected = payload_ans
                    marks_obtained = q_marks if selected == correct_ans else 0
                    cursor.execute("""
                        INSERT INTO student_answers (student_id, exam_id, qid, selected_answer, correct_answer, marks, marks_obtained)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            selected_answer = VALUES(selected_answer),
                            marks_obtained = VALUES(marks_obtained)
                    """, (student_id, exam_id, qid, selected, correct_ans, q_marks, marks_obtained))
                else:
                    if qid in saved_answers:
                        selected = saved_answers[qid]["selected_answer"]
                        marks_obtained = saved_answers[qid]["marks_obtained"]
                    else:
                        marks_obtained = 0
                        cursor.execute("""
                            INSERT INTO student_answers (student_id, exam_id, qid, selected_answer, correct_answer, marks, marks_obtained)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                selected_answer = VALUES(selected_answer),
                                marks_obtained = VALUES(marks_obtained)
                        """, (student_id, exam_id, qid, "", correct_ans, q_marks, 0))

            total_score += marks_obtained

        percentage = round((total_score / total_marks * 100.0), 2) if total_marks > 0 else 0.0

        if percentage >= 90: grade = "A+"
        elif percentage >= 80: grade = "A"
        elif percentage >= 70: grade = "B"
        elif percentage >= 60: grade = "C"
        elif percentage >= 50: grade = "D"
        else: grade = "F"

        status_result = "PASSED" if percentage >= 50.0 else "FAILED"

        cursor.execute(
            "INSERT INTO student_results (student_id, exam_id, student_name, score, total_marks, percentage, grade, exam_date, submission_type) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)",
            (student_id, exam_id, student_name_or_username, total_score, total_marks, percentage, grade, submission_type)
        )

        cursor.execute(
            "UPDATE student_exam_sessions SET status = 'submitted', submitted_at = NOW(), submission_type = %s WHERE student_id = %s AND exam_id = %s",
            (submission_type, student_id, exam_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        create_notification(
            student_id,
            f"Examination Evaluated: {exam['title']}",
            f"Official Result: Score {total_score}/{total_marks} ({percentage}%), Grade {grade} ({status_result}).",
            "result"
        )

        return {
            "success": True,
            "message": "Exam submitted successfully!",
            "result": {
                "student_id": student_id,
                "exam_id": exam_id,
                "score": total_score,
                "total_marks": total_marks,
                "percentage": percentage,
                "grade": grade,
                "status": status_result,
                "submission_type": submission_type
            }
        }, 200

    except Exception as e:
        print(f"Submit error: {e}")
        return {"success": False, "message": "Failed to evaluate exam submission."}, 500

@app.route("/api/examinations/<int:exam_id>/submit", methods=["POST"])
def submit_examination(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    submission_type = data.get("submission_type", "MANUAL")
    answers = data.get("answers", {})
    student_id = student["student_id"]
    student_name_or_username = student.get("student_name") or student.get("username")

    result, status_code = _internal_submit_examination(student_id, exam_id, submission_type, answers, student_name_or_username)
    return jsonify(result), status_code



@app.route("/api/examinations/<int:exam_id>/result")
def get_examination_result(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT sr.result_id, sr.student_id, sr.exam_id, sr.student_name, sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date,
                   sr.submission_type, sr.status,
                   e.title as exam_title, e.exam_code, e.category
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            WHERE sr.student_id = %s AND sr.exam_id = %s
        """, (student_id, exam_id))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "No result found for this examination."}), 404

        # Fetch question details from student_answers
        cursor.execute("""
            SELECT sa.qid, q.category, q.question, sa.selected_answer, sa.correct_answer, sa.marks, sa.marks_obtained
            FROM student_answers sa
            JOIN questions q ON sa.qid = q.qid
            WHERE sa.student_id = %s AND sa.exam_id = %s
            ORDER BY sa.qid ASC
        """, (student_id, exam_id))
        answers = cursor.fetchall()

        cursor.close()
        conn.close()

        if result.get("exam_date"):
            result["exam_date"] = str(result["exam_date"])

        return jsonify({
            "success": True,
            "result": result,
            "answers": answers
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch examination result."}), 500


# ----------------------------------------------------
# BACKWARD COMPATIBLE LEGACY ROUTES
# ----------------------------------------------------

@app.route("/api/has-attempted")
def has_attempted():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS cnt FROM student_results WHERE student_id = %s", (student_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        attempted = bool(row and row.get("cnt", 0) > 0)
        return jsonify({"success": True, "attempted": attempted})
    except Exception:
        return jsonify({"success": False, "message": "Failed to check exam attempt status."}), 500


@app.route("/api/start-exam", methods=["POST"])
def start_exam_legacy():
    return start_examination(1)


@app.route("/api/session")
def get_session_legacy():
    return get_examination_session(1)


@app.route("/api/questions")
def get_questions_legacy():
    return get_examination_questions(1)


@app.route("/api/submit-exam", methods=["POST"])
def submit_exam_legacy():
    return submit_examination(1)


@app.route("/api/result")
def get_result_legacy():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check student_exam_sessions first to see if any are pending
        cursor.execute("""
            SELECT id, exam_id, status, submission_type, submitted_at
            FROM student_exam_sessions 
            WHERE student_id = %s AND status = 'submitted'
            ORDER BY submitted_at DESC LIMIT 1
        """, (student_id,))
        session = cursor.fetchone()
        
        cursor.execute(
            "SELECT student_id, student_name, score, total_marks, percentage, grade, exam_date FROM student_results WHERE student_id = %s ORDER BY exam_date DESC LIMIT 1",
            (student_id,)
        )
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if session and (not result or str(session['exam_id']) != str(result['exam_id'])):
            # Session submitted, but no result generated for it yet -> It's PENDING EVALUATION
            return jsonify({
                "success": True,
                "result": {
                    "status": "PENDING_EVALUATION",
                    "taken_at": str(session["submitted_at"]) if session.get("submitted_at") else None
                }
            })

        if not result:
            return jsonify({"success": False, "message": "No examination results found for this student."}), 404

        if result.get("exam_date"):
            result["exam_date"] = str(result["exam_date"])
            result["taken_at"] = str(result["exam_date"])
            
        result["status"] = "PASSED" if result.get("percentage", 0) >= 50 else "FAILED"

        return jsonify({
            "success": True,
            "result": result
        })
    except Exception as e:
        print(f"Result API Error: {e}")
        return jsonify({"success": False, "message": "Failed to fetch examination result."}), 500


@app.route("/api/categories")
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM questions WHERE category IS NOT NULL AND category != '' ORDER BY category ASC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        categories = [r[0] for r in rows]
        standard_categories = [
            "Computer Science & IT",
            "Mathematics",
            "Programming",
            "Database Management Systems",
            "Artificial Intelligence",
            "Computer Networks",
            "Operating Systems",
            "Electronics"
        ]
        for sc in standard_categories:
            if sc not in categories:
                categories.append(sc)

        return jsonify({
            "success": True,
            "categories": categories
        })
    except Exception:
        return jsonify({
            "success": True,
            "categories": ["Computer Science & IT", "Mathematics", "Programming", "Database Management Systems"]
        })


@app.route("/api/analytics")
def get_analytics():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT score, total_marks, percentage, grade, exam_date FROM student_results WHERE student_id = %s ORDER BY exam_date DESC LIMIT 1", (student["student_id"],))
        my_res = cursor.fetchone()
        if my_res and my_res.get("exam_date"):
            my_res["exam_date"] = str(my_res["exam_date"])

        cursor.execute("SELECT AVG(percentage) as avg_percentage, COUNT(*) as total_exams FROM student_results")
        row = cursor.fetchone()
        avg_percentage = float(row["avg_percentage"]) if row and row["avg_percentage"] is not None else 0.0
        total_exams = int(row["total_exams"]) if row and row["total_exams"] is not None else 0

        cursor.execute("SELECT grade, COUNT(*) as cnt FROM student_results GROUP BY grade")
        grade_rows = cursor.fetchall()
        grade_counts = {r["grade"]: r["cnt"] for r in grade_rows}

        cursor.execute("""
            SELECT q.qid, q.category, q.question, q.marks, 
                   COUNT(sa.student_id) as attempts, 
                   SUM(CASE WHEN sa.marks_obtained >= q.marks THEN 1 ELSE 0 END) as correct_count 
            FROM questions q 
            LEFT JOIN student_answers sa ON q.qid = sa.qid 
            GROUP BY q.qid
        """)
        qrows = cursor.fetchall()
        question_stats = []
        for qr in qrows:
            attempts = int(qr["attempts"]) if qr["attempts"] is not None else 0
            correct_count = int(qr["correct_count"]) if qr["correct_count"] is not None else 0
            pct = (correct_count / attempts * 100.0) if attempts > 0 else 0.0
            question_stats.append({
                "qid": qr["qid"],
                "category": qr.get("category") or "General",
                "question": qr["question"],
                "marks": qr["marks"],
                "attempts": attempts,
                "correct_count": correct_count,
                "percent_correct": round(pct, 2)
            })

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "avg_percentage": round(avg_percentage, 2),
            "total_exams": total_exams,
            "grade_counts": grade_counts,
            "question_stats": question_stats,
            "student_result": my_res
        })

    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch analytics."}), 500


@app.route("/api/analytics/score-distribution")
def get_score_distribution():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT percentage FROM student_results")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        buckets = [0] * 11
        labels = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-99", "100"]

        for r in rows:
            p = float(r.get("percentage") or 0)
            if p >= 100.0:
                idx = 10
            else:
                idx = int(p // 10)
            if 0 <= idx < len(buckets):
                buckets[idx] += 1

        return jsonify({
            "success": True,
            "labels": labels,
            "counts": buckets
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to compute score distribution."}), 500


# ----------------------------------------------------
# ADMIN EXAMINATION MANAGEMENT
# ----------------------------------------------------

@app.route("/api/admin/examinations", methods=["GET", "POST"])
def admin_examinations():
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    if request.method == "GET":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT e.exam_id, e.exam_code, e.title, e.category, e.description,
                       e.duration_minutes, e.total_marks, e.passing_percentage, e.attempt_limit,
                       e.status, e.start_date, e.end_date, e.created_at,
                       COUNT(DISTINCT eq.qid) AS question_count,
                       COUNT(DISTINCT sr.student_id) AS candidate_attempts
                FROM examinations e
                LEFT JOIN exam_questions eq ON e.exam_id = eq.exam_id
                LEFT JOIN student_results sr ON e.exam_id = sr.exam_id
                GROUP BY e.exam_id
                ORDER BY e.exam_id DESC
            """)
            exams = cursor.fetchall()
            cursor.close()
            conn.close()

            for ex in exams:
                if ex.get("created_at"):
                    ex["created_at"] = str(ex["created_at"])
                if ex.get("start_date"):
                    ex["start_date"] = str(ex["start_date"])
                if ex.get("end_date"):
                    ex["end_date"] = str(ex["end_date"])

            return jsonify({"success": True, "examinations": exams})
        except Exception:
            return jsonify({"success": False, "message": "Failed to fetch examinations list."}), 500

    # POST: Create new examination
    data = request.get_json(silent=True) or {}
    exam_code = (data.get("exam_code") or "").strip().upper()
    title = (data.get("title") or "").strip()
    category = (data.get("category") or "Computer Science & IT").strip()
    description = (data.get("description") or "").strip()
    duration_minutes = int(data.get("duration_minutes") or 60)
    total_marks = int(data.get("total_marks") or 10)
    passing_percentage = float(data.get("passing_percentage") or 50.0)
    attempt_limit = int(data.get("attempt_limit") or 1)
    status = (data.get("status") or "draft").strip().lower()

    if not exam_code or not title or not category:
        return jsonify({"success": False, "message": "Exam Code, Title, and Category are required."}), 400

    if duration_minutes <= 0 or total_marks <= 0:
        return jsonify({"success": False, "message": "Duration and Total Marks must be positive values."}), 400

    if status not in ["draft", "published", "active", "closed", "archived"]:
        status = "draft"

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT exam_id FROM examinations WHERE exam_code = %s", (exam_code,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "An examination with this code already exists."}), 409

        cursor.execute("""
            INSERT INTO examinations (
                exam_code, title, category, description, duration_minutes, total_marks, passing_percentage, attempt_limit, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (exam_code, title, category, description, duration_minutes, total_marks, passing_percentage, attempt_limit, status))
        new_exam_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        if status in ["published", "active"]:
            broadcast_notification_to_all_active_students(
                f"New Examination Available: {title}",
                f"Assessment {exam_code} is now available in your examination portal ({duration_minutes} Mins).",
                "exam"
            )

        return jsonify({
            "success": True,
            "message": "Examination created successfully.",
            "exam_id": new_exam_id
        }), 201

    except Exception:
        return jsonify({"success": False, "message": "Failed to create examination."}), 500


@app.route("/api/admin/examinations/<int:exam_id>", methods=["GET", "PUT", "DELETE"])
def admin_manage_examination(exam_id):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    if request.method == "GET":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT e.*, COUNT(DISTINCT eq.qid) as question_count, COUNT(DISTINCT sr.student_id) as candidate_attempts
                FROM examinations e
                LEFT JOIN exam_questions eq ON e.exam_id = eq.exam_id
                LEFT JOIN student_results sr ON e.exam_id = sr.exam_id
                WHERE e.exam_id = %s
                GROUP BY e.exam_id
            """, (exam_id,))
            exam = cursor.fetchone()
            cursor.close()
            conn.close()

            if not exam:
                return jsonify({"success": False, "message": "Examination not found."}), 404

            if exam.get("created_at"):
                exam["created_at"] = str(exam["created_at"])
            if exam.get("start_date"):
                exam["start_date"] = str(exam["start_date"])
            if exam.get("end_date"):
                exam["end_date"] = str(exam["end_date"])

            return jsonify({"success": True, "examination": exam})
        except Exception:
            return jsonify({"success": False, "message": "Failed to fetch examination."}), 500

    if request.method == "DELETE":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT exam_id, exam_code, title, status FROM examinations WHERE exam_id = %s", (exam_id,))
            exam = cursor.fetchone()
            if not exam:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "Examination not found."}), 404

            # Safety check: Protect historical student results
            cursor.execute("SELECT COUNT(*) AS cnt FROM student_results WHERE exam_id = %s", (exam_id,))
            res_cnt = cursor.fetchone()
            if res_cnt and res_cnt.get("cnt", 0) > 0:
                cursor.close()
                conn.close()
                return jsonify({
                    "success": False,
                    "has_results": True,
                    "message": "This examination has completed candidate results and cannot be permanently deleted. Change status to 'Archived' instead to preserve academic records."
                }), 409

            # Safe deletion in database transaction
            cursor.execute("DELETE FROM exam_questions WHERE exam_id = %s", (exam_id,))
            cursor.execute("DELETE FROM student_exam_sessions WHERE exam_id = %s", (exam_id,))
            cursor.execute(f"DELETE FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({"success": True, "message": "Examination deleted successfully."})
        except Exception:
            if 'conn' in locals() and conn.is_connected():
                conn.rollback()
                conn.close()
            return jsonify({"success": False, "message": "Failed to delete examination."}), 500

    # PUT: Update examination
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    exam_code = (data.get("exam_code") or "").strip().upper()
    category = (data.get("category") or "Computer Science & IT").strip()
    description = (data.get("description") or "").strip()
    duration_minutes = int(data.get("duration_minutes") or 60)
    total_marks = int(data.get("total_marks") or 10)
    passing_percentage = float(data.get("passing_percentage") or 50.0)
    attempt_limit = int(data.get("attempt_limit") or 1)
    status = (data.get("status") or "draft").strip().lower()

    if not title or not exam_code:
        return jsonify({"success": False, "message": "Title and Exam Code are required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT exam_id FROM examinations WHERE exam_code = %s AND exam_id != %s", (exam_code, exam_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Exam code is already in use by another examination."}), 409

        cursor.execute("""
            UPDATE examinations
            SET exam_code = %s, title = %s, category = %s, description = %s, duration_minutes = %s, total_marks = %s, passing_percentage = %s, attempt_limit = %s, status = %s
            WHERE exam_id = %s
        """, (exam_code, title, category, description, duration_minutes, total_marks, passing_percentage, attempt_limit, status, exam_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Examination updated successfully."})
    except Exception:
        return jsonify({"success": False, "message": "Failed to update examination."}), 500


@app.route("/api/admin/examinations/<int:exam_id>/status", methods=["PUT"])
def admin_update_exam_status(exam_id):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().lower()
    if new_status not in ["draft", "published", "active", "closed", "archived"]:
        return jsonify({"success": False, "message": "Invalid examination status."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT title, exam_code FROM examinations WHERE exam_id = %s", (exam_id,))
        exam = cursor.fetchone()
        if not exam:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Examination not found."}), 404

        cursor.execute(f"UPDATE examinations SET status = %s WHERE exam_id = %s {get_tenant_and(admin)}", (new_status, exam_id))
        conn.commit()
        cursor.close()
        conn.close()

        if new_status in ["published", "active"]:
            broadcast_notification_to_all_active_students(
                f"Examination Published: {exam['title']}",
                f"Assessment {exam['exam_code']} is now available for examination.",
                "exam"
            )

        return jsonify({"success": True, "message": f"Examination status updated to {new_status}."})
    except Exception:
        return jsonify({"success": False, "message": "Failed to update examination status."}), 500


@app.route("/api/admin/examinations/<int:exam_id>/questions", methods=["GET", "POST"])
def admin_exam_questions(exam_id):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    if request.method == "GET":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT q.qid, q.category, q.question, q.optionA, q.optionB, q.optionC, q.optionD, q.correct_answer, q.marks, eq.question_order
                FROM exam_questions eq
                JOIN questions q ON eq.qid = q.qid
                WHERE eq.exam_id = %s
                ORDER BY eq.question_order ASC, q.qid ASC
            """, (exam_id,))
            assigned = cursor.fetchall()
            assigned_qids = {r["qid"] for r in assigned}

            cursor.execute("SELECT qid, category, question, optionA, optionB, optionC, optionD, correct_answer, marks FROM questions ORDER BY qid ASC")
            all_questions = cursor.fetchall()
            for q in all_questions:
                q["is_assigned"] = bool(q["qid"] in assigned_qids)

            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "exam_id": exam_id,
                "assigned_questions": assigned,
                "all_questions": all_questions
            })
        except Exception:
            return jsonify({"success": False, "message": "Failed to fetch exam questions."}), 500

    # POST: Update assigned questions list
    data = request.get_json(silent=True) or {}
    question_ids = data.get("question_ids")
    if not isinstance(question_ids, list):
        return jsonify({"success": False, "message": "question_ids array is required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("DELETE FROM exam_questions WHERE exam_id = %s", (exam_id,))
        for order, qid in enumerate(question_ids, start=1):
            cursor.execute("INSERT INTO exam_questions (exam_id, qid, question_order) VALUES (%s, %s, %s)", (exam_id, int(qid), order))

        cursor.execute("""
            SELECT COALESCE(SUM(q.marks), 0) AS total_marks
            FROM exam_questions eq
            JOIN questions q ON eq.qid = q.qid
            WHERE eq.exam_id = %s
        """, (exam_id,))
        tm_row = cursor.fetchone()
        total_m = int(tm_row["total_marks"] or 0) if tm_row else 0
        if total_m > 0:
            cursor.execute("UPDATE examinations SET total_marks = %s WHERE exam_id = %s", (total_m, exam_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Assigned questions updated successfully.", "total_marks": total_m})
    except Exception:
        return jsonify({"success": False, "message": "Failed to update exam questions."}), 500


@app.route("/api/admin/examinations/<int:exam_id>/questions/<int:qid>", methods=["DELETE"])
def admin_remove_question_from_exam(exam_id, qid):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM exam_questions WHERE exam_id = %s AND qid = %s", (exam_id, qid))

        cursor.execute("""
            SELECT COALESCE(SUM(q.marks), 0) AS total_marks
            FROM exam_questions eq
            JOIN questions q ON eq.qid = q.qid
            WHERE eq.exam_id = %s
        """, (exam_id,))
        tm_row = cursor.fetchone()
        total_m = int(tm_row["total_marks"] or 0) if tm_row else 0
        if total_m > 0:
            cursor.execute("UPDATE examinations SET total_marks = %s WHERE exam_id = %s", (total_m, exam_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Question removed from examination.", "total_marks": total_m})
    except Exception:
        return jsonify({"success": False, "message": "Failed to remove question from exam."}), 500


# ----------------------------------------------------
# ADMIN STUDENT MANAGEMENT
# ----------------------------------------------------

@app.route("/api/admin/students", methods=["GET", "POST"])
def admin_students():
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    if request.method == "GET":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"""
                SELECT s.student_id, s.student_name, s.username, s.email, s.profile_picture, s.status, s.created_at,
                       sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date
                FROM students s
                LEFT JOIN student_results sr ON s.student_id = sr.student_id
                {get_tenant_where(admin, 's')}
                ORDER BY s.student_id DESC
            """)
            students = cursor.fetchall()
            cursor.close()
            conn.close()

            for s in students:
                if s.get("created_at"):
                    s["created_at"] = str(s["created_at"])
                if s.get("exam_date"):
                    s["exam_date"] = str(s["exam_date"])
                s["attempted"] = bool(s.get("score") is not None)

            return jsonify({"success": True, "students": students})
        except Exception:
            return jsonify({"success": False, "message": "Failed to fetch student roster."}), 500

    # POST: Admin creates student directly
    data = request.get_json(silent=True) or {}
    student_name = (data.get("student_name") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    status = data.get("status") or "active"

    if not student_name or not username or not email or not password:
        return jsonify({"success": False, "message": "All fields are required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT student_id FROM students WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Username already exists."}), 409

        cursor.execute("SELECT student_id FROM students WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already exists."}), 409

        institution_id = admin["institution_id"] if admin.get("role") != "SUPER_ADMIN" else (data.get("institution_id") or 1)
        pwd_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO students (institution_id, student_name, username, email, password_hash, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (institution_id, student_name, username, email, pwd_hash, status)
        )
        new_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        create_notification(
            new_id,
            "Account Created by Administrator",
            "An administrator has created your institutional examination account. You can now access your dashboard.",
            "account"
        )

        return jsonify({
            "success": True,
            "message": "Student created successfully.",
            "student_id": new_id
        }), 201

    except Exception:
        return jsonify({"success": False, "message": "Failed to create student."}), 500


@app.route("/api/admin/students/<int:student_id>/status", methods=["PUT"])
def admin_update_student_status(student_id):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ["active", "pending", "disabled"]:
        return jsonify({"success": False, "message": "Invalid status value."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"UPDATE students SET status = %s WHERE student_id = %s {get_tenant_and(admin)}", (new_status, student_id))
        conn.commit()
        cursor.close()
        conn.close()

        if new_status == "active":
            create_notification(
                student_id,
                "Account Approved & Activated",
                "Congratulations! Your student account has been approved by the institution administrator. You may now participate in examinations.",
                "account"
            )
        elif new_status == "disabled":
            create_notification(
                student_id,
                "Account Access Restricted",
                "Your student account has been temporarily disabled by an administrator. Please contact faculty support.",
                "account"
            )

        return jsonify({"success": True, "message": f"Student status updated to {new_status}."})
    except Exception:
        return jsonify({"success": False, "message": "Failed to update student status."}), 500


@app.route("/api/admin/students/<int:student_id>", methods=["DELETE"])
def admin_delete_student(student_id):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT student_id, student_name, username, profile_picture FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Student not found."}), 404

        # Safe cascade delete in transaction
        cursor.execute("DELETE FROM notifications WHERE student_id = %s", (student_id,))
        cursor.execute("DELETE FROM student_answers WHERE student_id = %s", (student_id,))
        cursor.execute("DELETE FROM student_results WHERE student_id = %s", (student_id,))
        cursor.execute("DELETE FROM student_exam_sessions WHERE student_id = %s", (student_id,))
        cursor.execute(f"DELETE FROM students WHERE student_id = %s {get_tenant_and(admin)}", (student_id,))
        conn.commit()

        # Clean up physical avatar file if present
        if student.get("profile_picture"):
            old_file = os.path.basename(student["profile_picture"])
            old_path = os.path.join(AVATARS_DIR, old_file)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Student and associated records removed successfully."})
    except Exception:
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": "Failed to delete student."}), 500


# ----------------------------------------------------
# ADMIN QUESTION BANK MANAGEMENT
# ----------------------------------------------------

@app.route("/api/admin/questions", methods=["GET", "POST"])
def admin_questions():
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    if request.method == "GET":
        category_filter = request.args.get("category", "").strip()
        search_query = request.args.get("search", "").strip()
        type_filter = request.args.get("type", "").strip()

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT qid, type, category, question, content, metadata, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_answer FROM questions"
            query += get_tenant_where(admin)
            params = []

            if category_filter and category_filter != "ALL":
                query += " AND category = %s"
                params.append(category_filter)

            if type_filter and type_filter != "ALL":
                query += " AND type = %s"
                params.append(type_filter)

            if search_query:
                query += " AND question LIKE %s"
                params.append(f"%{search_query}%")

            query += " ORDER BY qid ASC"

            cursor.execute(query, tuple(params))
            questions = cursor.fetchall()
            
            # parse JSON fields
            import json
            for q in questions:
                if q.get('content') and isinstance(q['content'], str):
                    try: q['content'] = json.loads(q['content'])
                    except: pass
                if q.get('metadata') and isinstance(q['metadata'], str):
                    try: q['metadata'] = json.loads(q['metadata'])
                    except: pass
                    
            cursor.close()
            conn.close()

            return jsonify({"success": True, "questions": questions})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # POST: Add new question
    data = request.get_json(silent=True) or {}
    q_type = (data.get("type") or "MCQ").strip().upper()
    category = (data.get("category") or "General").strip()
    question = (data.get("question") or "").strip()
    content = data.get("content")
    metadata = data.get("metadata")
    marks = int(data.get("marks") or 1)
    negative_marks = float(data.get("negative_marks") or 0.0)
    difficulty = data.get("difficulty", "medium")
    raw_tags = data.get("tags")
    import json
    tags = json.dumps(raw_tags) if isinstance(raw_tags, list) else (raw_tags if raw_tags else '[]')
    
    # Legacy fallbacks
    optionA = (data.get("optionA") or "").strip()
    optionB = (data.get("optionB") or "").strip()
    optionC = (data.get("optionC") or "").strip()
    optionD = (data.get("optionD") or "").strip()
    correct_ans = (data.get("correct_answer") or "").strip()

    if not question:
        return jsonify({"success": False, "message": "Question statement is required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        import json
        content_str = json.dumps(content) if content else None
        metadata_str = json.dumps(metadata) if metadata else None
        
        institution_id = admin["institution_id"] if admin.get("role") != "SUPER_ADMIN" else (data.get("institution_id") or 1)

        cursor.execute(
            """INSERT INTO questions (institution_id, type, category, question, content, metadata, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_answer) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (institution_id, q_type, category, question, content_str, metadata_str, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_ans)
        )
        new_qid = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Question added successfully.",
            "qid": new_qid
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin/questions/<int:qid>", methods=["PUT", "DELETE"])
def admin_manage_question(qid):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM questions WHERE qid = %s {get_tenant_and(admin)}", (qid,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Question not found or unauthorized."}), 404

        if request.method == "DELETE":
            cursor.execute("DELETE FROM questions WHERE qid = %s", (qid,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "Question deleted successfully."})

        # PUT (Update)
        data = request.get_json(silent=True) or {}
        q_type = (data.get("type") or "MCQ").strip().upper()
        category = (data.get("category") or "General").strip()
        question = (data.get("question") or "").strip()
        content = data.get("content")
        metadata = data.get("metadata")
        marks = int(data.get("marks") or 1)
        negative_marks = float(data.get("negative_marks") or 0.0)
        difficulty = data.get("difficulty", "medium")
        raw_tags = data.get("tags")
        import json
        tags = json.dumps(raw_tags) if isinstance(raw_tags, list) else (raw_tags if raw_tags else '[]')
        
        optionA = (data.get("optionA") or "").strip()
        optionB = (data.get("optionB") or "").strip()
        optionC = (data.get("optionC") or "").strip()
        optionD = (data.get("optionD") or "").strip()
        correct_ans = (data.get("correct_answer") or "").strip()

        if not question:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Question statement is required."}), 400

        import json
        content_str = json.dumps(content) if content else None
        metadata_str = json.dumps(metadata) if metadata else None

        cursor.execute("""
            UPDATE questions 
            SET type=%s, category=%s, question=%s, content=%s, metadata=%s, marks=%s, negative_marks=%s, difficulty=%s, tags=%s, optionA=%s, optionB=%s, optionC=%s, optionD=%s, correct_answer=%s
            WHERE qid = %s
        """, (q_type, category, question, content_str, metadata_str, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_ans, qid))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Question updated successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ----------------------------------------------------
# ADMIN RESULTS & ANALYTICS
# ----------------------------------------------------

@app.route("/api/admin/results")
def admin_results():
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    search = request.args.get("search", "").strip()
    grade = request.args.get("grade", "").strip()
    exam_id = request.args.get("exam_id", "").strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT sr.student_id, sr.exam_id, sr.student_name, sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date,
                   s.username, s.email, e.title as exam_title, e.exam_code
            FROM student_results sr
            JOIN students s ON sr.student_id = s.student_id
            LEFT JOIN examinations e ON sr.exam_id = e.exam_id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (s.student_name LIKE %s OR s.username LIKE %s OR s.email LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        if grade:
            query += " AND sr.grade = %s"
            params.append(grade)

        if exam_id:
            query += " AND sr.exam_id = %s"
            params.append(int(exam_id))

        query += " ORDER BY sr.exam_date DESC"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        for r in results:
            if r.get("exam_date"):
                r["exam_date"] = str(r["exam_date"])

        return jsonify({"success": True, "results": results})
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch student results."}), 500


@app.route("/api/admin/results/<int:student_id>")
def admin_student_result_detail(student_id):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Summary
        cursor.execute("""
            SELECT sr.student_id, sr.exam_id, sr.student_name, sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date,
                   s.username, s.email, e.title as exam_title, e.exam_code
            FROM student_results sr
            JOIN students s ON sr.student_id = s.student_id
            LEFT JOIN examinations e ON sr.exam_id = e.exam_id
            WHERE sr.student_id = %s
            ORDER BY sr.exam_date DESC
            LIMIT 1
        """, (student_id,))
        summary = cursor.fetchone()

        if not summary:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "No exam result found for this student."}), 404

        if summary.get("exam_date"):
            summary["exam_date"] = str(summary["exam_date"])

        # 2. Answers Breakdown
        exam_id = summary.get("exam_id") or 1
        cursor.execute("""
            SELECT sa.qid, q.category, q.question, q.optionA, q.optionB, q.optionC, q.optionD,
                   sa.selected_answer, sa.correct_answer, sa.marks, sa.marks_obtained
            FROM student_answers sa
            JOIN questions q ON sa.qid = q.qid
            WHERE sa.student_id = %s AND sa.exam_id = %s
            ORDER BY sa.qid ASC
        """, (student_id, exam_id))
        answers = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "summary": summary,
            "answers": answers
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to fetch student result details."}), 500


@app.route("/api/admin/analytics")
def admin_analytics():
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) as active,
                   SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status='disabled' THEN 1 ELSE 0 END) as disabled
            FROM students {get_tenant_where(admin)}
        """)
        student_counts = cursor.fetchone()

        cursor.execute(f"""
            SELECT COUNT(*) as total_exams, 
                   AVG(score) as avg_score, 
                   AVG(percentage) as avg_pct, 
                   SUM(CASE WHEN percentage >= 50 THEN 1 ELSE 0 END) as passed_count 
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            {get_tenant_where(admin, 'e')}
        """)
        result_stats = cursor.fetchone()

        cursor.execute(f"""
            SELECT sr.grade, COUNT(*) as count 
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            {get_tenant_where(admin, 'e')}
            GROUP BY sr.grade
        """)
        grade_rows = cursor.fetchall()
        grade_dist = {r["grade"]: r["count"] for r in grade_rows}

        cursor.execute(f"SELECT COUNT(*) as total_questions, COUNT(DISTINCT category) as total_categories FROM questions {get_tenant_where(admin)}")
        q_cnt = cursor.fetchone()

        cursor.execute(f"""
            SELECT COUNT(*) as total_examinations,
                   SUM(CASE WHEN status IN ('published', 'active') THEN 1 ELSE 0 END) as published_examinations
            FROM examinations {get_tenant_where(admin)}
        """)
        exam_cnt = cursor.fetchone()

        cursor.close()
        conn.close()

        total_exams = int(result_stats["total_exams"]) if result_stats and result_stats["total_exams"] else 0
        passed = int(result_stats["passed_count"]) if result_stats and result_stats["passed_count"] else 0
        pass_rate = round((passed / total_exams * 100.0), 1) if total_exams > 0 else 0.0

        return jsonify({
            "success": True,
            "analytics": {
                "total_students": int(student_counts["total"] or 0),
                "active_students": int(student_counts["active"] or 0),
                "pending_students": int(student_counts["pending"] or 0),
                "disabled_students": int(student_counts["disabled"] or 0),
                "total_exams_taken": total_exams,
                "total_questions": int(q_cnt["total_questions"] or 0),
                "total_categories": int(q_cnt["total_categories"] or 1),
                "total_examinations": int(exam_cnt["total_examinations"] or 0) if exam_cnt else 1,
                "published_examinations": int(exam_cnt["published_examinations"] or 0) if exam_cnt else 1,
                "avg_percentage": round(float(result_stats["avg_pct"] or 0), 1),
                "pass_rate": pass_rate,
                "grade_distribution": grade_dist
            }
        })
    except Exception:
        return jsonify({"success": False, "message": "Failed to compute administrative analytics."}), 500



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


# ----------------------------------------------------
# SERVER LAUNCH
# ----------------------------------------------------



# ----------------------------------------------------
# STUDENT RESULT & CERTIFICATE API
# ----------------------------------------------------

@app.route("/api/student/result/<int:result_id>")
def get_student_result_detail(result_id):
    """Return a single result with all data needed for the printable result sheet."""
    student, auth_error = require_student_auth()
    if auth_error: return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT sr.result_id, sr.student_id, sr.exam_id, sr.student_name,
                   sr.score, sr.total_marks, sr.percentage, sr.grade,
                   sr.exam_date, sr.submission_type, sr.status,
                   e.title AS exam_title, e.exam_code, e.category AS exam_category,
                   e.duration_minutes, e.passing_percentage,
                   s.email AS student_email, s.username,
                   i.institution_id, i.institution_name, i.logo AS institution_logo,
                   i.email AS institution_email, i.phone AS institution_phone,
                   i.website AS institution_website,
                   i.primary_color, i.secondary_color,
                   i.certificates_enabled
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            JOIN students s ON sr.student_id = s.student_id
            LEFT JOIN institutions i ON e.institution_id = i.institution_id
            WHERE sr.result_id = %s AND sr.student_id = %s
        """, (result_id, student["student_id"]))
        result = cursor.fetchone()

        if not result:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Result not found or access denied."}), 404

        # Check for pending descriptive answers
        cursor.execute("""
            SELECT COUNT(*) AS pending FROM student_answers
            WHERE student_id = %s AND exam_id = %s AND evaluation_status = 'PENDING'
        """, (student["student_id"], result["exam_id"]))
        pending = cursor.fetchone()["pending"]

        # Performance stats
        cursor.execute("""
            SELECT
                COUNT(*) AS total_questions,
                SUM(CASE WHEN selected_answer IS NOT NULL AND selected_answer != '' THEN 1
                         WHEN answer_text IS NOT NULL AND answer_text != '' THEN 1
                         ELSE 0 END) AS attempted,
                SUM(CASE WHEN marks_obtained > 0 THEN 1 ELSE 0 END) AS correct,
                SUM(CASE WHEN marks_obtained < 0 THEN 1 ELSE 0 END) AS negative_marked,
                SUM(CASE WHEN marks_obtained < 0 THEN ABS(marks_obtained) ELSE 0 END) AS negative_marks_total
            FROM student_answers
            WHERE student_id = %s AND exam_id = %s
        """, (student["student_id"], result["exam_id"]))
        perf = cursor.fetchone()

        # Certificate info
        cursor.execute("SELECT certificate_id, generated_at FROM certificates WHERE result_id = %s", (result_id,))
        cert = cursor.fetchone()

        cursor.close(); conn.close()

        if result.get("exam_date"):
            result["exam_date"] = str(result["exam_date"])

        is_passed = result["percentage"] >= result.get("passing_percentage", 50)
        evaluation_complete = pending == 0
        result_finalized = result["status"] == "FINAL" and evaluation_complete

        cert_available = (
            result_finalized and
            bool(result.get("certificates_enabled")) and
            is_passed
        )

        return jsonify({
            "success": True,
            "result": {
                "result_id": result["result_id"],
                "student_name": result["student_name"],
                "student_email": result["student_email"],
                "username": result["username"],
                "exam_title": result["exam_title"],
                "exam_code": result["exam_code"],
                "exam_category": result["exam_category"],
                "exam_date": result.get("exam_date"),
                "duration_minutes": result["duration_minutes"],
                "passing_percentage": result["passing_percentage"],
                "score": result["score"],
                "total_marks": result["total_marks"],
                "percentage": result["percentage"],
                "grade": result["grade"],
                "status": "PASSED" if is_passed else "FAILED",
                "submission_type": result["submission_type"],
                "evaluation_status": "FINALIZED" if evaluation_complete else "PENDING_EVALUATION",
                "result_status": result["status"],
                "institution_name": result["institution_name"],
                "institution_logo": result["institution_logo"],
                "institution_email": result["institution_email"],
                "institution_phone": result["institution_phone"],
                "institution_website": result["institution_website"],
                "primary_color": result["primary_color"],
                "secondary_color": result["secondary_color"],
            },
            "performance": {
                "total_questions": int(perf["total_questions"] or 0),
                "attempted": int(perf["attempted"] or 0),
                "correct": int(perf["correct"] or 0),
                "incorrect": int(perf["attempted"] or 0) - int(perf["correct"] or 0) - int(perf["negative_marked"] or 0),
                "unanswered": int(perf["total_questions"] or 0) - int(perf["attempted"] or 0),
                "negative_marks": float(perf["negative_marks_total"] or 0),
            },
            "certificate": {
                "available": cert_available,
                "generated": cert is not None,
                "certificate_id": cert["certificate_id"] if cert else None,
                "generated_at": str(cert["generated_at"]) if cert else None,
            }
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to fetch result details."}), 500


@app.route("/api/student/results/history")
def get_student_results_history():
    """Return all results for the authenticated student."""
    student, auth_error = require_student_auth()
    if auth_error: return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT sr.result_id, sr.exam_id, sr.score, sr.total_marks,
                   sr.percentage, sr.grade, sr.exam_date,
                   sr.submission_type, sr.status,
                   e.title AS exam_title, e.exam_code, e.passing_percentage,
                   c.certificate_id
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            LEFT JOIN certificates c ON sr.result_id = c.result_id
            WHERE sr.student_id = %s
            ORDER BY sr.exam_date DESC
        """, (student["student_id"],))
        results = cursor.fetchall()

        # Check pending descriptive evals per exam
        for r in results:
            cursor.execute("""
                SELECT COUNT(*) AS pending FROM student_answers
                WHERE student_id = %s AND exam_id = %s AND evaluation_status = 'PENDING'
            """, (student["student_id"], r["exam_id"]))
            pend = cursor.fetchone()["pending"]
            r["evaluation_status"] = "PENDING_EVALUATION" if pend > 0 else "FINALIZED"
            r["is_passed"] = r["percentage"] >= (r.get("passing_percentage") or 50)
            if r.get("exam_date"): r["exam_date"] = str(r["exam_date"])

        cursor.close(); conn.close()
        return jsonify({"success": True, "results": results})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to fetch result history."}), 500


@app.route("/api/student/result/<int:result_id>/certificate", methods=["POST"])
def generate_certificate(result_id):
    """Generate a certificate ID for a finalized, passing result."""
    student, auth_error = require_student_auth()
    if auth_error: return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify ownership and finalization
        cursor.execute("""
            SELECT sr.result_id, sr.student_id, sr.exam_id, sr.percentage, sr.status,
                   e.institution_id, e.passing_percentage, i.certificates_enabled
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            JOIN institutions i ON e.institution_id = i.institution_id
            WHERE sr.result_id = %s AND sr.student_id = %s
        """, (result_id, student["student_id"]))
        result = cursor.fetchone()

        if not result:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Result not found or access denied."}), 404

        if not result.get("certificates_enabled"):
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Certificates are not enabled for your institution."}), 403

        if result["status"] != "FINAL":
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Result is not yet finalized."}), 400

        # Check pending evals
        cursor.execute("""
            SELECT COUNT(*) AS pending FROM student_answers
            WHERE student_id = %s AND exam_id = %s AND evaluation_status = 'PENDING'
        """, (student["student_id"], result["exam_id"]))
        if cursor.fetchone()["pending"] > 0:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Evaluation is still pending."}), 400

        passing = result.get("passing_percentage") or 50
        if result["percentage"] < passing:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Certificate requires a passing grade."}), 400

        # Check if cert already exists (idempotent)
        cursor.execute("SELECT certificate_id, generated_at FROM certificates WHERE result_id = %s", (result_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.close(); conn.close()
            return jsonify({
                "success": True,
                "certificate_id": existing["certificate_id"],
                "generated_at": str(existing["generated_at"]),
                "message": "Certificate already exists."
            })

        # Generate unique certificate ID: EXM-YYYY-XXXXXX
        import random
        from datetime import datetime
        year = datetime.now().strftime("%Y")
        for attempt in range(10):
            rand_part = str(random.randint(100000, 999999))
            cert_id = f"EXM-{year}-{rand_part}"
            cursor.execute("SELECT certificate_id FROM certificates WHERE certificate_id = %s", (cert_id,))
            if not cursor.fetchone():
                break
        else:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Failed to generate unique certificate ID."}), 500

        cursor.execute("""
            INSERT INTO certificates (certificate_id, result_id, student_id, exam_id, institution_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (cert_id, result_id, student["student_id"], result["exam_id"], result["institution_id"]))
        conn.commit()

        log_audit(student["student_id"], "STUDENT", result["institution_id"],
                  "GENERATE_CERTIFICATE", cert_id,
                  {"result_id": result_id, "exam_id": result["exam_id"]})

        cursor.close(); conn.close()
        return jsonify({
            "success": True,
            "certificate_id": cert_id,
            "generated_at": str(datetime.now()),
            "message": "Certificate generated successfully."
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to generate certificate."}), 500


@app.route("/api/public/verify-certificate")
def verify_certificate():
    """Public endpoint: verify a certificate ID. No authentication required."""
    cid = request.args.get("cid", "").strip()
    if not cid:
        return jsonify({"success": False, "valid": False, "message": "Certificate ID is required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.certificate_id, c.generated_at,
                   sr.student_name, sr.percentage, sr.grade, sr.exam_date,
                   e.title AS exam_title,
                   i.institution_name
            FROM certificates c
            JOIN student_results sr ON c.result_id = sr.result_id
            JOIN examinations e ON c.exam_id = e.exam_id
            JOIN institutions i ON c.institution_id = i.institution_id
            WHERE c.certificate_id = %s
        """, (cid,))
        cert = cursor.fetchone()

        cursor.close(); conn.close()

        if not cert:
            return jsonify({"success": True, "valid": False, "message": "Certificate not found."})

        is_passed = cert["percentage"] >= 50

        return jsonify({
            "success": True,
            "valid": True,
            "certificate": {
                "certificate_id": cert["certificate_id"],
                "student_name": cert["student_name"],
                "institution_name": cert["institution_name"],
                "exam_title": cert["exam_title"],
                "exam_date": str(cert["exam_date"]) if cert["exam_date"] else None,
                "percentage": cert["percentage"],
                "grade": cert["grade"],
                "status": "PASSED" if is_passed else "FAILED",
                "generated_at": str(cert["generated_at"]),
            }
        })
    except Exception:
        return jsonify({"success": False, "message": "Verification failed."}), 500


# ----------------------------------------------------
# ADMIN RESULT REPORTING & EXPORT API
# ----------------------------------------------------

@app.route("/api/admin/results/history")
def admin_results_history():
    """Paginated, filtered result listing for admin reporting dashboard."""
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    search = request.args.get("search", "").strip()
    grade_filter = request.args.get("grade", "").strip()
    exam_id = request.args.get("exam_id", "").strip()
    status_filter = request.args.get("status", "").strip()
    timeout_only = request.args.get("timeout", "").strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        tenant_cond = get_tenant_and(admin, "e")

        query = """
            SELECT sr.result_id, sr.student_id, sr.exam_id, sr.student_name,
                   sr.score, sr.total_marks, sr.percentage, sr.grade,
                   sr.exam_date, sr.submission_type, sr.status,
                   s.email, s.username,
                   e.title AS exam_title, e.exam_code, e.passing_percentage,
                   c.certificate_id,
                   i.institution_name
            FROM student_results sr
            JOIN students s ON sr.student_id = s.student_id
            JOIN examinations e ON sr.exam_id = e.exam_id
            LEFT JOIN institutions i ON e.institution_id = i.institution_id
            LEFT JOIN certificates c ON sr.result_id = c.result_id
            WHERE 1=1 {tenant}
        """.format(tenant=tenant_cond)
        params = []

        if search:
            query += " AND (sr.student_name LIKE %s OR s.email LIKE %s OR e.title LIKE %s)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp])

        if grade_filter:
            query += " AND sr.grade = %s"
            params.append(grade_filter)

        if exam_id:
            query += " AND sr.exam_id = %s"
            params.append(int(exam_id))

        if status_filter == "PASSED":
            query += " AND sr.percentage >= COALESCE(e.passing_percentage, 50)"
        elif status_filter == "FAILED":
            query += " AND sr.percentage < COALESCE(e.passing_percentage, 50)"

        if timeout_only == "1":
            query += " AND sr.submission_type = 'AUTO_TIMEOUT'"

        # Count
        count_query = f"SELECT COUNT(*) AS total FROM ({query}) AS sub"
        cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()["total"]

        query += " ORDER BY sr.exam_date DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        for r in results:
            if r.get("exam_date"): r["exam_date"] = str(r["exam_date"])
            r["is_passed"] = r["percentage"] >= (r.get("passing_percentage") or 50)

        cursor.close(); conn.close()

        return jsonify({
            "success": True,
            "results": results,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to fetch results."}), 500


@app.route("/api/admin/results/export")
def admin_results_export():
    """Stream CSV export of results filtered by tenant."""
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error

    import csv, io

    search = request.args.get("search", "").strip()
    grade_filter = request.args.get("grade", "").strip()
    exam_id = request.args.get("exam_id", "").strip()
    status_filter = request.args.get("status", "").strip()
    timeout_only = request.args.get("timeout", "").strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        tenant_cond = get_tenant_and(admin, "e")

        query = """
            SELECT i.institution_name, e.title AS exam_title, e.exam_code,
                   sr.student_name, s.email, sr.exam_date,
                   sr.score, sr.total_marks, sr.percentage, sr.grade,
                   sr.submission_type, sr.status AS evaluation_status,
                   c.certificate_id
            FROM student_results sr
            JOIN students s ON sr.student_id = s.student_id
            JOIN examinations e ON sr.exam_id = e.exam_id
            LEFT JOIN institutions i ON e.institution_id = i.institution_id
            LEFT JOIN certificates c ON sr.result_id = c.result_id
            WHERE 1=1 {tenant}
        """.format(tenant=tenant_cond)
        params = []

        if search:
            query += " AND (sr.student_name LIKE %s OR s.email LIKE %s OR e.title LIKE %s)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp])
        if grade_filter:
            query += " AND sr.grade = %s"
            params.append(grade_filter)
        if exam_id:
            query += " AND sr.exam_id = %s"
            params.append(int(exam_id))
        if status_filter == "PASSED":
            query += " AND sr.percentage >= COALESCE(e.passing_percentage, 50)"
        elif status_filter == "FAILED":
            query += " AND sr.percentage < COALESCE(e.passing_percentage, 50)"
        if timeout_only == "1":
            query += " AND sr.submission_type = 'AUTO_TIMEOUT'"

        query += " ORDER BY sr.exam_date DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close(); conn.close()

        log_audit(admin["admin_id"], admin.get("role"), admin.get("institution_id"),
                  "EXPORT_RESULTS", f"{len(rows)} rows", {"filters": {"search": search, "grade": grade_filter}})

        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Institution", "Exam", "Exam Code", "Student", "Email",
                             "Date", "Score", "Total Marks", "Percentage", "Grade",
                             "Status", "Submission Type", "Evaluation Status", "Certificate ID"])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            for row in rows:
                pct = row.get("percentage") or 0
                is_pass = "PASSED" if pct >= 50 else "FAILED"
                writer.writerow([
                    row.get("institution_name", ""),
                    row.get("exam_title", ""),
                    row.get("exam_code", ""),
                    row.get("student_name", ""),
                    row.get("email", ""),
                    str(row.get("exam_date", "")),
                    row.get("score", 0),
                    row.get("total_marks", 0),
                    round(pct, 2),
                    row.get("grade", ""),
                    is_pass,
                    row.get("submission_type", ""),
                    row.get("evaluation_status", ""),
                    row.get("certificate_id", ""),
                ])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        from flask import Response
        return Response(
            generate(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=examora_results_export.csv"}
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Export failed."}), 500



@app.route("/api/admin/examinations/<int:exam_id>/builder", methods=["GET", "POST"])
def admin_exam_builder(exam_id):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    if request.method == "GET":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM examinations WHERE exam_id = %s", (exam_id,))
            exam = cursor.fetchone()
            
            cursor.execute("""
                SELECT q.qid, q.category, q.question, q.marks, eq.question_order, q.type, q.optionA, q.optionB, q.optionC, q.optionD, q.correct_answer, q.content
                FROM exam_questions eq
                JOIN questions q ON eq.qid = q.qid
                WHERE eq.exam_id = %s
                ORDER BY eq.question_order ASC, q.qid ASC
            """, (exam_id,))
            unsectioned = cursor.fetchall()
            
            for row in unsectioned:
                if row.get("content") and isinstance(row["content"], str):
                    try:
                        row["content"] = json.loads(row["content"])
                    except:
                        pass
            
            cursor.close()
            conn.close()
            
            if not exam:
                return jsonify({"success": False, "message": "Exam not found"}), 404
                
            return jsonify({
                "success": True, 
                "exam": exam,
                "sections": [],
                "unsectioned_questions": unsectioned
            })
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    # POST: Save builder data
    data = request.get_json(silent=True) or {}
    sections = data.get("sections", [])
    
    question_ids = []
    for sec in sections:
        for qid in sec.get("questions", []):
            question_ids.append(qid)
            
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("DELETE FROM exam_questions WHERE exam_id = %s", (exam_id,))
        for order, qid in enumerate(question_ids, start=1):
            cursor.execute("INSERT INTO exam_questions (exam_id, qid, question_order) VALUES (%s, %s, %s)", (exam_id, int(qid), order))

        cursor.execute("""
            SELECT COALESCE(SUM(q.marks), 0) AS total_marks
            FROM exam_questions eq
            JOIN questions q ON eq.qid = q.qid
            WHERE eq.exam_id = %s
        """, (exam_id,))
        tm_row = cursor.fetchone()
        total_m = int(tm_row["total_marks"] or 0) if tm_row else 0
        if total_m > 0:
            cursor.execute("UPDATE examinations SET total_marks = %s WHERE exam_id = %s", (total_m, exam_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Exam builder saved successfully.", "total_marks": total_m})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to save builder data: " + str(e)}), 500

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )