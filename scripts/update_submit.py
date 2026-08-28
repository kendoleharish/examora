import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

submit_logic = '''
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
            SELECT q.qid, q.question, q.correct_answer, q.marks, q.negative_marks, q.type, q.content
            FROM exam_questions eq
            JOIN questions q ON eq.qid = q.qid
            WHERE eq.exam_id = %s
        """, (exam_id,))
        questions = cursor.fetchall()

        if not questions:
            cursor.execute("SELECT qid, question, correct_answer, marks, negative_marks, type, content FROM questions")
            questions = cursor.fetchall()

        import json
        for q in questions:
            if q.get('content') and isinstance(q['content'], str):
                try: q['content'] = json.loads(q['content'])
                except: pass

        total_marks = 0
        total_score = 0
        has_pending_eval = False
        is_past_deadline = elapsed >= duration_seconds
        
        cursor.execute("SELECT qid, selected_answer, answer_text, answer_json, marks_obtained FROM student_answers WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
        saved_answers = {row["qid"]: row for row in cursor.fetchall()}

        for q in questions:
            qid = q["qid"]
            q_marks = int(q.get("marks") or 1)
            q_type = q.get("type", "MCQ")
            total_marks += q_marks
            
            needs_manual_eval = q_type in ["DESCRIPTIVE", "SHORT_ANSWER"]
            
            selected = ""
            answer_text = None
            answer_json = None
            marks_obtained = 0
            eval_status = "PENDING" if needs_manual_eval else "AUTO_SCORED"
            
            if is_past_deadline:
                if qid in saved_answers:
                    selected = saved_answers[qid]["selected_answer"]
                    answer_text = saved_answers[qid]["answer_text"]
                    answer_json = saved_answers[qid]["answer_json"]
                    if not needs_manual_eval:
                        marks_obtained = saved_answers[qid]["marks_obtained"]
            else:
                payload_ans = answers.get(str(qid)) or answers.get(qid)
                
                if q_type == "MCQ" or q_type == "TRUE_FALSE":
                    selected = (str(payload_ans) if payload_ans else "").strip().upper()
                    correct_ans = (q.get("correct_answer") or "").strip().upper()
                    if selected and selected == correct_ans: marks_obtained = q_marks
                    elif selected: marks_obtained = -(q.get("negative_marks") or 0)
                elif q_type == "FILL_BLANK":
                    answer_text = (str(payload_ans) if payload_ans else "").strip()
                    correct_ans = (q.get("correct_answer") or "").strip()
                    if answer_text.lower() == correct_ans.lower(): marks_obtained = q_marks
                elif q_type == "MULTIPLE_SELECT":
                    if payload_ans and isinstance(payload_ans, list):
                        answer_json = json.dumps(payload_ans)
                        correct_answers = q.get('content', {}).get('correct_answers', [])
                        # Exact match
                        if set(map(str, payload_ans)) == set(map(str, correct_answers)):
                            marks_obtained = q_marks
                elif q_type == "NUMERICAL":
                    answer_text = str(payload_ans) if payload_ans else ""
                    if answer_text:
                        try:
                            val = float(answer_text)
                            correct_val = float(q.get('content', {}).get('correct_value', 0))
                            tol = float(q.get('content', {}).get('tolerance', 0))
                            if correct_val - tol <= val <= correct_val + tol:
                                marks_obtained = q_marks
                        except: pass
                elif needs_manual_eval:
                    answer_text = str(payload_ans) if payload_ans else ""
                    marks_obtained = 0
                    has_pending_eval = True

                cursor.execute("""
                    INSERT INTO student_answers (student_id, exam_id, qid, selected_answer, answer_text, answer_json, correct_answer, marks, marks_obtained, evaluation_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        selected_answer = VALUES(selected_answer),
                        answer_text = VALUES(answer_text),
                        answer_json = VALUES(answer_json),
                        marks_obtained = VALUES(marks_obtained),
                        evaluation_status = VALUES(evaluation_status)
                """, (student_id, exam_id, qid, selected, answer_text, answer_json, q.get("correct_answer"), q_marks, marks_obtained, eval_status))

            total_score += marks_obtained
            if needs_manual_eval: has_pending_eval = True

        cursor.execute(
            "UPDATE student_exam_sessions SET status = 'submitted', submitted_at = NOW(), submission_type = %s WHERE student_id = %s AND exam_id = %s",
            (submission_type, student_id, exam_id)
        )

        if not has_pending_eval:
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
            conn.commit()
            
            create_notification(
                student_id,
                f"Examination Evaluated: {exam['title']}",
                f"Official Result: Score {total_score}/{total_marks} ({percentage}%), Grade {grade} ({status_result}).",
                "result"
            )
            cursor.close(); conn.close()
            return {
                "success": True,
                "message": "Exam submitted successfully!",
                "result": {
                    "student_id": student_id, "exam_id": exam_id, "score": total_score, "total_marks": total_marks,
                    "percentage": percentage, "grade": grade, "status": status_result, "submission_type": submission_type
                }
            }, 200
        else:
            conn.commit()
            create_notification(
                student_id,
                f"Examination Submitted: {exam['title']}",
                "Your examination has been submitted successfully and is pending manual evaluation by your teacher.",
                "info"
            )
            cursor.close(); conn.close()
            return {
                "success": True,
                "message": "Exam submitted successfully! Pending manual evaluation.",
                "result": {
                    "student_id": student_id, "exam_id": exam_id, "status": "PENDING_EVALUATION"
                }
            }, 200

    except Exception as e:
        print(f"Submit exam error: {e}")
        return {"success": False, "message": "Internal server error."}, 500
'''

pattern = re.compile(r'def _internal_submit_examination\(student_id, exam_id, submission_type, answers, student_name_or_username\):.*?return \{"success": False, "message": "Internal server error\."\}, 500', re.DOTALL)
code = pattern.sub(submit_logic.strip(), code)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated _internal_submit_examination")
