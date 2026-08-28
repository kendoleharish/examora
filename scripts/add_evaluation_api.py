import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

evaluate_endpoints = '''
# ----------------------------------------------------
# EVALUATION DASHBOARD ENDPOINTS
# ----------------------------------------------------

@app.route("/api/admin/evaluations/pending", methods=["GET"])
def admin_evaluations_pending():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Find exams that have pending descriptive questions
        query = """
            SELECT sa.exam_id, sa.student_id, e.title as exam_title, e.exam_code, s.student_name, s.username, COUNT(sa.qid) as pending_count
            FROM student_answers sa
            JOIN examinations e ON sa.exam_id = e.exam_id
            JOIN students s ON sa.student_id = s.student_id
            WHERE sa.evaluation_status = 'PENDING'
        """
        query += get_tenant_and(admin, prefix="AND e.")
        query += " GROUP BY sa.exam_id, sa.student_id, e.title, e.exam_code, s.student_name, s.username"
        
        cursor.execute(query)
        pending = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "pending": pending})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/evaluations/student/<int:exam_id>/<int:student_id>", methods=["GET"])
def admin_evaluations_student_answers(exam_id, student_id):
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Check tenant isolation
        cursor.execute(f"SELECT exam_id FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Unauthorized"}), 403
            
        cursor.execute("""
            SELECT sa.*, q.question, q.content, q.type as question_type, q.marks as max_marks, q.negative_marks
            FROM student_answers sa
            JOIN questions q ON sa.qid = q.qid
            WHERE sa.exam_id = %s AND sa.student_id = %s AND sa.evaluation_status != 'AUTO_SCORED'
        """, (exam_id, student_id))
        answers = cursor.fetchall()
        
        # parse json
        import json
        for a in answers:
            if a.get('answer_json') and isinstance(a['answer_json'], str):
                try: a['answer_json'] = json.loads(a['answer_json'])
                except: pass
            if a.get('content') and isinstance(a['content'], str):
                try: a['content'] = json.loads(a['content'])
                except: pass

        cursor.close(); conn.close()
        return jsonify({"success": True, "answers": answers})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/evaluations/score", methods=["POST"])
def admin_evaluations_score():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    data = request.get_json() or {}
    student_id = data.get("student_id")
    exam_id = data.get("exam_id")
    qid = data.get("qid")
    marks_awarded = data.get("marks_awarded")
    feedback = data.get("feedback")
    
    if student_id is None or exam_id is None or qid is None or marks_awarded is None:
        return jsonify({"success": False, "message": "Missing fields"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT exam_id FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Unauthorized"}), 403
            
        cursor.execute("""
            UPDATE student_answers
            SET marks_obtained = %s, feedback = %s, evaluation_status = 'EVALUATED', evaluator_id = %s
            WHERE student_id = %s AND exam_id = %s AND qid = %s
        """, (marks_awarded, feedback, admin["admin_id"], student_id, exam_id, qid))
        conn.commit()
        cursor.close(); conn.close()
        return jsonify({"success": True, "message": "Score saved"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/evaluations/finalize", methods=["POST"])
def admin_evaluations_finalize():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    data = request.get_json() or {}
    student_id = data.get("student_id")
    exam_id = data.get("exam_id")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if any are still pending
        cursor.execute("SELECT COUNT(*) as pending FROM student_answers WHERE student_id=%s AND exam_id=%s AND evaluation_status='PENDING'", (student_id, exam_id))
        if cursor.fetchone()["pending"] > 0:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Cannot finalize while some answers are still pending evaluation."}), 400
            
        # Sum total marks obtained
        cursor.execute("SELECT SUM(marks_obtained) as total_obtained, SUM(marks) as max_marks FROM student_answers WHERE student_id=%s AND exam_id=%s", (student_id, exam_id))
        totals = cursor.fetchone()
        
        score = totals["total_obtained"] or 0
        total_max = totals["max_marks"] or 1
        percentage = (score / total_max) * 100
        
        # Simple grading logic
        if percentage >= 90: grade = 'A+'
        elif percentage >= 80: grade = 'A'
        elif percentage >= 70: grade = 'B'
        elif percentage >= 60: grade = 'C'
        elif percentage >= 50: grade = 'D'
        else: grade = 'F'
        
        cursor.execute("""
            UPDATE student_results
            SET score = %s, percentage = %s, grade = %s
            WHERE student_id = %s AND exam_id = %s
        """, (score, percentage, grade, student_id, exam_id))
        
        conn.commit()
        cursor.close(); conn.close()
        return jsonify({"success": True, "message": "Evaluation finalized and grades published."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
'''

code = code.replace("if __name__ == '__main__':", evaluate_endpoints + "\n\nif __name__ == '__main__':")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Evaluation API updated.")
