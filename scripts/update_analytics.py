import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

analytics_new = '''
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
'''

pattern = re.compile(r'try:\s+conn = get_db_connection\(\).*?cursor\.close\(\)\s+conn\.close\(\)', re.DOTALL)
code = pattern.sub(analytics_new.strip(), code, count=1)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Analytics updated.")
