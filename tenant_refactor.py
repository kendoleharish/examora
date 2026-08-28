import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. admin_examinations
code = code.replace(
    '''cursor.execute("SELECT * FROM examinations ORDER BY created_at DESC")''',
    '''cursor.execute(f"SELECT * FROM examinations {get_tenant_where(admin)} ORDER BY created_at DESC")'''
)

code = code.replace(
    '''cursor.execute("""
                    INSERT INTO examinations 
                    (title, category, description, duration_minutes, total_marks, passing_percentage, attempt_limit, status, exam_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (title, category, desc, dur, tm, pp, al, status, exam_code))''',
    '''cursor.execute(f"""
                    INSERT INTO examinations 
                    (institution_id, title, category, description, duration_minutes, total_marks, passing_percentage, attempt_limit, status, exam_code)
                    VALUES ({{int(admin['institution_id']) if admin.get('role') != 'SUPER_ADMIN' else 1}}, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (title, category, desc, dur, tm, pp, al, status, exam_code))'''
)

# 2. admin_manage_examination
code = code.replace(
    '''cursor.execute("SELECT * FROM examinations WHERE exam_id = %s", (exam_id,))''',
    '''cursor.execute(f"SELECT * FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))'''
)

code = code.replace(
    '''cursor.execute("""
                    UPDATE examinations 
                    SET title=%s, category=%s, description=%s, duration_minutes=%s, 
                        total_marks=%s, passing_percentage=%s, attempt_limit=%s, status=%s, exam_code=%s
                    WHERE exam_id=%s
                """, (title, category, desc, dur, tm, pp, al, status, exam_code, exam_id))''',
    '''cursor.execute(f"""
                    UPDATE examinations 
                    SET title=%s, category=%s, description=%s, duration_minutes=%s, 
                        total_marks=%s, passing_percentage=%s, attempt_limit=%s, status=%s, exam_code=%s
                    WHERE exam_id=%s {get_tenant_and(admin)}
                """, (title, category, desc, dur, tm, pp, al, status, exam_code, exam_id))'''
)

code = code.replace(
    '''cursor.execute("DELETE FROM examinations WHERE exam_id = %s", (exam_id,))''',
    '''cursor.execute(f"DELETE FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))'''
)

# 3. admin_update_exam_status
code = code.replace(
    '''cursor.execute("UPDATE examinations SET status = %s WHERE exam_id = %s", (new_status, exam_id))''',
    '''cursor.execute(f"UPDATE examinations SET status = %s WHERE exam_id = %s {get_tenant_and(admin)}", (new_status, exam_id))'''
)

# 4. admin_students
code = code.replace(
    '''SELECT s.student_id, s.student_name, s.username, s.email, s.profile_picture, s.status, s.created_at,
                       sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date
                FROM students s
                LEFT JOIN student_results sr ON s.student_id = sr.student_id
                ORDER BY s.student_id DESC''',
    '''SELECT s.student_id, s.student_name, s.username, s.email, s.profile_picture, s.status, s.created_at,
                       sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date
                FROM students s
                LEFT JOIN student_results sr ON s.student_id = sr.student_id
                {get_tenant_where(admin, 's')}
                ORDER BY s.student_id DESC'''
)

# 5. admin_update_student_status
code = code.replace(
    '''cursor.execute("UPDATE students SET status = %s WHERE student_id = %s", (new_status, student_id))''',
    '''cursor.execute(f"UPDATE students SET status = %s WHERE student_id = %s {get_tenant_and(admin)}", (new_status, student_id))'''
)

# 6. admin_delete_student
code = code.replace(
    '''cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))''',
    '''cursor.execute(f"DELETE FROM students WHERE student_id = %s {get_tenant_and(admin)}", (student_id,))'''
)

# 7. admin_questions
code = code.replace(
    '''cursor.execute("SELECT * FROM questions ORDER BY qid DESC")''',
    '''cursor.execute(f"SELECT * FROM questions {get_tenant_where(admin)} ORDER BY qid DESC")'''
)
code = code.replace(
    '''cursor.execute("""
                    INSERT INTO questions (question, optionA, optionB, optionC, optionD, correct_answer, marks, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (q, oA, oB, oC, oD, ca, m, cat))''',
    '''cursor.execute(f"""
                    INSERT INTO questions (institution_id, question, optionA, optionB, optionC, optionD, correct_answer, marks, category)
                    VALUES ({{int(admin['institution_id']) if admin.get('role') != 'SUPER_ADMIN' else 1}}, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (q, oA, oB, oC, oD, ca, m, cat))'''
)

# 8. admin_manage_question
code = code.replace(
    '''cursor.execute("SELECT * FROM questions WHERE qid = %s", (qid,))''',
    '''cursor.execute(f"SELECT * FROM questions WHERE qid = %s {get_tenant_and(admin)}", (qid,))'''
)
code = code.replace(
    '''cursor.execute("""
                    UPDATE questions
                    SET question=%s, optionA=%s, optionB=%s, optionC=%s, optionD=%s, correct_answer=%s, marks=%s, category=%s
                    WHERE qid=%s
                """, (q, oA, oB, oC, oD, ca, m, cat, qid))''',
    '''cursor.execute(f"""
                    UPDATE questions
                    SET question=%s, optionA=%s, optionB=%s, optionC=%s, optionD=%s, correct_answer=%s, marks=%s, category=%s
                    WHERE qid=%s {get_tenant_and(admin)}
                """, (q, oA, oB, oC, oD, ca, m, cat, qid))'''
)
code = code.replace(
    '''cursor.execute("DELETE FROM questions WHERE qid = %s", (qid,))''',
    '''cursor.execute(f"DELETE FROM questions WHERE qid = %s {get_tenant_and(admin)}", (qid,))'''
)

# 9. admin_results
code = code.replace(
    '''SELECT sr.student_id, sr.exam_id, sr.student_name, sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date, sr.submission_type, e.title as exam_title
                FROM student_results sr
                JOIN examinations e ON sr.exam_id = e.exam_id
                ORDER BY sr.exam_date DESC''',
    '''SELECT sr.student_id, sr.exam_id, sr.student_name, sr.score, sr.total_marks, sr.percentage, sr.grade, sr.exam_date, sr.submission_type, e.title as exam_title
                FROM student_results sr
                JOIN examinations e ON sr.exam_id = e.exam_id
                {get_tenant_where(admin, 'e')}
                ORDER BY sr.exam_date DESC'''
)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Tenant refactor completed successfully.")
