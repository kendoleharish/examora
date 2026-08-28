import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

result_logic = '''
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
'''

pattern = re.compile(r'@app\.route\("/api/result"\).*?return jsonify\(\{"success": False, "message": "Failed to fetch examination result\."\}\), 500', re.DOTALL)
code = pattern.sub(result_logic.strip(), code)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Result API updated.")
