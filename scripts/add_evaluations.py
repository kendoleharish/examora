import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

evaluations_endpoints = '''
# ----------------------------------------------------
# MANUAL EVALUATION ENDPOINTS
# ----------------------------------------------------
@app.route("/api/admin/evaluations/pending", methods=["GET"])
def admin_pending_evaluations():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"""
            SELECT sr.student_id, sr.exam_id, sr.student_name, sr.exam_date, e.title as exam_title
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            WHERE sr.status = 'PENDING_EVALUATION' {get_tenant_and(admin, 'e')}
            ORDER BY sr.exam_date ASC
        """)
        results = cursor.fetchall()
        cursor.close(); conn.close()
        
        for r in results:
            r["exam_date"] = str(r["exam_date"])
            
        return jsonify({"success": True, "pending_evaluations": results})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/evaluations/score", methods=["POST"])
def admin_score_answer():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    exam_id = data.get("exam_id")
    qid = data.get("qid")
    marks_awarded = data.get("marks_awarded", 0)
    feedback = data.get("feedback", "")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE student_answers 
            SET marks_obtained = %s, feedback = %s, evaluation_status = 'EVALUATED', evaluator_id = %s
            WHERE student_id = %s AND exam_id = %s AND qid = %s
        """, (marks_awarded, feedback, admin["admin_id"], student_id, exam_id, qid))
        
        conn.commit()
        cursor.close(); conn.close()
        
        return jsonify({"success": True, "message": "Score saved successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/evaluations/finalize", methods=["POST"])
def admin_finalize_evaluation():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    exam_id = data.get("exam_id")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if any answers are still pending
        cursor.execute("""
            SELECT COUNT(*) as pending_count 
            FROM student_answers 
            WHERE student_id = %s AND exam_id = %s AND evaluation_status = 'PENDING'
        """, (student_id, exam_id))
        row = cursor.fetchone()
        
        if row and row["pending_count"] > 0:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": f"{row['pending_count']} answers are still pending evaluation."}), 400
            
        # Recalculate total score
        cursor.execute("SELECT SUM(marks_obtained) as total_score FROM student_answers WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        score_row = cursor.fetchone()
        total_score = int(score_row["total_score"]) if score_row and score_row["total_score"] else 0
        
        cursor.execute("SELECT total_marks FROM student_results WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        res = cursor.fetchone()
        if not res:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Result record not found."}), 404
            
        total_marks = int(res["total_marks"])
        percentage = round((total_score / total_marks * 100.0), 2) if total_marks > 0 else 0.0
        
        if percentage >= 90: grade = "A+"
        elif percentage >= 80: grade = "A"
        elif percentage >= 70: grade = "B"
        elif percentage >= 60: grade = "C"
        elif percentage >= 50: grade = "D"
        else: grade = "F"
        
        cursor.execute("""
            UPDATE student_results 
            SET score = %s, percentage = %s, grade = %s, status = 'FINAL'
            WHERE student_id = %s AND exam_id = %s
        """, (total_score, percentage, grade, student_id, exam_id))
        
        conn.commit()
        cursor.close(); conn.close()
        
        create_notification(
            student_id,
            f"Examination Fully Evaluated",
            f"Your descriptive answers have been evaluated. Final Score: {total_score}/{total_marks} ({percentage}%).",
            "result"
        )
        
        return jsonify({"success": True, "message": "Evaluation finalized."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

'''

# Append to file before the if __name__ == '__main__' block
code = code.replace("if __name__ == '__main__':", evaluations_endpoints + "\n\nif __name__ == '__main__':")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Evaluation endpoints added.")
