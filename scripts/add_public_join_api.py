import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

public_join_endpoints = '''
# ----------------------------------------------------
# PUBLIC JOIN FLOW
# ----------------------------------------------------

@app.route("/api/students/public_join", methods=["POST"])
def public_join_exam():
    data = request.get_json(silent=True) or {}
    exam_code = data.get("exam_code", "").strip()
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    if not exam_code or not full_name or not email or not password:
        return jsonify({"success": False, "message": "All fields are required."}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Check if exam exists and is published
        cursor.execute("SELECT exam_id, institution_id, status FROM examinations WHERE exam_code = %s", (exam_code,))
        exam = cursor.fetchone()
        
        if not exam:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Invalid exam code."}), 404
            
        if exam['status'] != 'published':
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "This examination is not currently open."}), 403
            
        institution_id = exam['institution_id']
        
        # 2. Check if student already exists by email
        cursor.execute("SELECT student_id, password_hash, institution_id FROM students WHERE email = %s", (email,))
        student = cursor.fetchone()
        
        student_id = None
        
        if student:
            # Verify password
            if not check_password_hash(student['password_hash'], password):
                cursor.close(); conn.close()
                return jsonify({"success": False, "message": "Email already registered. Incorrect password."}), 401
            student_id = student['student_id']
            # Optionally update institution_id to match the exam if it's different? No, keep it as is.
        else:
            # 3. Create new student account
            # Generate username from email
            base_username = email.split('@')[0]
            username = base_username
            # ensure unique
            counter = 1
            while True:
                cursor.execute("SELECT 1 FROM students WHERE username = %s", (username,))
                if not cursor.fetchone():
                    break
                username = f"{base_username}{counter}"
                counter += 1
                
            pwd_hash = generate_password_hash(password)
            
            cursor.execute("""
                INSERT INTO students (institution_id, student_name, username, email, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, (institution_id, full_name, username, email, pwd_hash))
            
            student_id = cursor.lastrowid
            conn.commit()
            
        # 4. Create session and log them in
        session["student_id"] = student_id
        session.permanent = True
        
        # 5. Automatically assign the exam if not already assigned
        cursor.execute("SELECT 1 FROM exam_assignments WHERE student_id = %s AND exam_id = %s", (student_id, exam['exam_id']))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO exam_assignments (student_id, exam_id) VALUES (%s, %s)", (student_id, exam['exam_id']))
            conn.commit()
            
        cursor.close(); conn.close()
        
        return jsonify({
            "success": True,
            "message": "Successfully joined! Redirecting to exam instructions...",
            "exam_id": exam['exam_id']
        }), 200

    except Exception as e:
        print(f"Public join error: {e}")
        return jsonify({"success": False, "message": "Server error."}), 500
'''

code = code.replace("if __name__ == '__main__':", public_join_endpoints + "\n\nif __name__ == '__main__':")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Public join API updated.")
