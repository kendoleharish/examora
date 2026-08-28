import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

endpoint_code = '''
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

'''

# Insert right before start_examination
code = code.replace('@app.route("/api/examinations/<int:exam_id>/start"', endpoint_code + '\n@app.route("/api/examinations/<int:exam_id>/start"')

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Endpoint added.")
