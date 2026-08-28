import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

autosave_new = '''
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
'''

pattern_autosave = re.compile(r'@app\.route\("/api/examinations/<int:exam_id>/autosave", methods=\["POST"\]\).*?def _internal_submit_examination', re.DOTALL)
code = pattern_autosave.sub(autosave_new.strip() + '\n\ndef _internal_submit_examination', code)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Autosave updated.")
