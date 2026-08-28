import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

autosave_func = """
@app.route("/api/examinations/<int:exam_id>/autosave", methods=["POST"])
def autosave_examination(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    qid = data.get("qid")
    selected = data.get("selected_answer", "").strip().upper()

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

        if elapsed > duration_seconds + 5:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "EXAM_EXPIRED"}), 400

        cursor.execute("SELECT marks, correct_answer FROM questions WHERE qid = %s", (qid,))
        q = cursor.fetchone()
        if not q:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Question not found."}), 404
        
        q_marks = int(q.get("marks") or 1)
        correct_ans = (q.get("correct_answer") or "").strip().upper()
        marks_obtained = q_marks if selected == correct_ans and selected != "" else 0

        cursor.execute(\"\"\"
            INSERT INTO student_answers (student_id, exam_id, qid, selected_answer, correct_answer, marks, marks_obtained)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                selected_answer = VALUES(selected_answer),
                marks_obtained = VALUES(marks_obtained)
        \"\"\", (student_id, exam_id, qid, selected, correct_ans, q_marks, marks_obtained))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Answer autosaved."})

    except Exception as e:
        print(f"Autosave error: {e}")
        return jsonify({"success": False, "message": "Failed to autosave answer."}), 500

@app.route("/api/examinations/<int:exam_id>/submit", methods=["POST"])
def submit_examination(exam_id):
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    submission_type = data.get("submission_type", "MANUAL")
    # We no longer strictly rely on answers payload for scoring due to autosave,
    # but we can fallback to it if they didn't autosave (or if we want to sync remaining).
    answers = data.get("answers", {})

    student_id = student["student_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT exam_id, title, duration_minutes FROM examinations WHERE exam_id = %s", (exam_id,))
        exam = cursor.fetchone()
        if not exam:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Examination not found."}), 404

        cursor.execute("SELECT COUNT(*) AS cnt FROM student_results WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        row = cursor.fetchone()
        if row and row.get("cnt", 0) > 0:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "You have already completed this examination."}), 400

        cursor.execute(
            "SELECT id, start_time, duration_seconds, status, TIMESTAMPDIFF(SECOND, start_time, NOW()) AS elapsed_seconds FROM student_exam_sessions WHERE student_id = %s AND exam_id = %s",
            (student_id, exam_id)
        )
        sess = cursor.fetchone()
        if not sess:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "No active exam session found."}), 400

        if sess.get("status") == "submitted":
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "You have already completed this examination."}), 400

        duration_seconds = int(sess.get("duration_seconds") or (exam["duration_minutes"] * 60))
        elapsed = int(sess.get("elapsed_seconds") or 0)

        if elapsed >= duration_seconds:
            submission_type = 'AUTO_TIMEOUT'

        cursor.execute(\"\"\"
            SELECT q.qid, q.question, q.correct_answer, q.marks
            FROM exam_questions eq
            JOIN questions q ON eq.qid = q.qid
            WHERE eq.exam_id = %s
        \"\"\", (exam_id,))
        questions = cursor.fetchall()

        if not questions:
            cursor.execute("SELECT qid, question, correct_answer, marks FROM questions")
            questions = cursor.fetchall()

        total_marks = 0
        total_score = 0

        # We need to process whatever wasn't autosaved, but only if it's NOT an AUTO_TIMEOUT that's past deadline.
        # If it's an AUTO_TIMEOUT past deadline, we ONLY trust the database state.
        is_past_deadline = elapsed > duration_seconds + 5
        
        # Get already saved answers
        cursor.execute("SELECT qid, selected_answer, marks_obtained FROM student_answers WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        saved_answers = {row["qid"]: row for row in cursor.fetchall()}

        for q in questions:
            qid = q["qid"]
            q_marks = int(q.get("marks") or 1)
            total_marks += q_marks
            correct_ans = (q.get("correct_answer") or "").strip().upper()
            
            # If past deadline, ONLY use saved answers. Otherwise, we can accept the payload as a final sync.
            selected = ""
            if is_past_deadline:
                if qid in saved_answers:
                    selected = saved_answers[qid]["selected_answer"]
                    marks_obtained = saved_answers[qid]["marks_obtained"]
                else:
                    marks_obtained = 0
            else:
                # Use payload if present, else fallback to saved answer
                payload_ans = (answers.get(str(qid)) or answers.get(qid) or "").strip().upper()
                if payload_ans:
                    selected = payload_ans
                    marks_obtained = q_marks if selected == correct_ans else 0
                    # Insert/Update it since it was provided in payload
                    cursor.execute(\"\"\"
                        INSERT INTO student_answers (student_id, exam_id, qid, selected_answer, correct_answer, marks, marks_obtained)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            selected_answer = VALUES(selected_answer),
                            marks_obtained = VALUES(marks_obtained)
                    \"\"\", (student_id, exam_id, qid, selected, correct_ans, q_marks, marks_obtained))
                else:
                    if qid in saved_answers:
                        selected = saved_answers[qid]["selected_answer"]
                        marks_obtained = saved_answers[qid]["marks_obtained"]
                    else:
                        marks_obtained = 0
                        cursor.execute(\"\"\"
                            INSERT INTO student_answers (student_id, exam_id, qid, selected_answer, correct_answer, marks, marks_obtained)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                selected_answer = VALUES(selected_answer),
                                marks_obtained = VALUES(marks_obtained)
                        \"\"\", (student_id, exam_id, qid, "", correct_ans, q_marks, 0))

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
            (student_id, exam_id, student.get("student_name") or student.get("username"), total_score, total_marks, percentage, grade, submission_type)
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

        return jsonify({
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
        })

    except Exception as e:
        print(f"Submit error: {e}")
        return jsonify({"success": False, "message": "Failed to evaluate exam submission."}), 500
"""

# Replace the original submit_examination function
old_submit_start = content.find('@app.route("/api/examinations/<int:exam_id>/submit", methods=["POST"])')
old_submit_end = content.find('@app.route("/api/examinations/<int:exam_id>/result")')

if old_submit_start != -1 and old_submit_end != -1:
    new_content = content[:old_submit_start] + autosave_func + "\n\n" + content[old_submit_end:]
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("app.py updated successfully.")
else:
    print("Could not find the submit_examination boundaries.")
