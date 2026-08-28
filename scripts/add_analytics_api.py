import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

analytics = '''
@app.route("/api/admin/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_cond = get_tenant_and(admin)
        
        cursor.execute(f"SELECT COUNT(*) as c FROM students WHERE 1=1 {tenant_cond}")
        students = cursor.fetchone()["c"]
        
        cursor.execute(f"SELECT COUNT(*) as c FROM examinations WHERE status = 'published' {tenant_cond}")
        active_exams = cursor.fetchone()["c"]
        
        cursor.execute(f"SELECT COUNT(*) as c FROM results r JOIN examinations e ON r.exam_id = e.exam_id WHERE 1=1 {get_tenant_and(admin, 'e')}")
        completed_exams = cursor.fetchone()["c"]
        
        cursor.execute(f"SELECT COUNT(*) as c FROM student_answers a JOIN examinations e ON a.exam_id = e.exam_id WHERE a.evaluation_status = 'PENDING' {get_tenant_and(admin, 'e')}")
        pending_evals = cursor.fetchone()["c"]
        
        cursor.execute(f"SELECT AVG(r.percentage) as a FROM results r JOIN examinations e ON r.exam_id = e.exam_id WHERE 1=1 {get_tenant_and(admin, 'e')}")
        avg_score = cursor.fetchone()["a"]
        
        cursor.execute(f"SELECT COUNT(*) as c FROM student_exam_sessions s JOIN examinations e ON s.exam_id = e.exam_id WHERE s.status = 'submitted' AND s.submission_type = 'AUTO_TIMEOUT' {get_tenant_and(admin, 'e')}")
        timeouts = cursor.fetchone()["c"]
        
        cursor.close(); conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_students": students,
                "active_exams": active_exams,
                "completed_exams": completed_exams,
                "pending_evaluations": pending_evals,
                "average_score": round(avg_score, 1) if avg_score else 0,
                "auto_timeouts": timeouts
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
'''
if 'def get_dashboard_stats()' not in code:
    code = code.replace("if __name__ == '__main__':", analytics + "\nif __name__ == '__main__':")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Added Analytics Endpoint.")
