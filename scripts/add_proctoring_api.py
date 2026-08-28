import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

proctoring_endpoints = '''
# ----------------------------------------------------
# PROCTORING API
# ----------------------------------------------------

@app.route("/api/proctoring/event", methods=["POST"])
def record_proctoring_event():
    student, auth_error = require_student_auth()
    if auth_error:
        return auth_error
        
    data = request.get_json(silent=True) or {}
    exam_id = data.get("exam_id")
    event_type = data.get("event_type")
    severity = data.get("severity", "LOW")
    metadata = data.get("metadata", {})
    
    if not exam_id or not event_type:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get active session
        cursor.execute("SELECT id FROM student_exam_sessions WHERE student_id = %s AND exam_id = %s AND status = 'active'", (student["student_id"], exam_id))
        sess = cursor.fetchone()
        if not sess:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "No active session"}), 400
            
        import json
        meta_str = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO proctoring_events (session_id, student_id, exam_id, event_type, severity, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (sess["id"], student["student_id"], exam_id, event_type, severity, meta_str))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Proctoring event error: {e}")
        return jsonify({"success": False}), 500

@app.route("/api/admin/proctoring/events/<int:exam_id>", methods=["GET"])
def get_proctoring_events(exam_id):
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # verify tenant
        cursor.execute(f"SELECT 1 FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Unauthorized"}), 403
            
        cursor.execute("""
            SELECT p.*, s.student_name, s.username, s.email 
            FROM proctoring_events p
            JOIN students s ON p.student_id = s.student_id
            WHERE p.exam_id = %s
            ORDER BY p.timestamp DESC
        """, (exam_id,))
        events = cursor.fetchall()
        
        import json
        for e in events:
            e["timestamp"] = str(e["timestamp"])
            if e.get("metadata") and isinstance(e["metadata"], str):
                try: e["metadata"] = json.loads(e["metadata"])
                except: pass
                
        cursor.close(); conn.close()
        return jsonify({"success": True, "events": events})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/proctoring/summary/<int:exam_id>", methods=["GET"])
def get_proctoring_summary(exam_id):
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"SELECT 1 FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Unauthorized"}), 403
            
        cursor.execute("""
            SELECT p.student_id, s.student_name, s.username, 
                   COUNT(*) as total_events,
                   SUM(CASE WHEN p.severity = 'HIGH' THEN 1 ELSE 0 END) as high_severity,
                   SUM(CASE WHEN p.severity = 'MEDIUM' THEN 1 ELSE 0 END) as medium_severity
            FROM proctoring_events p
            JOIN students s ON p.student_id = s.student_id
            WHERE p.exam_id = %s
            GROUP BY p.student_id, s.student_name, s.username
            ORDER BY high_severity DESC, medium_severity DESC, total_events DESC
        """, (exam_id,))
        summary = cursor.fetchall()
        
        cursor.close(); conn.close()
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
'''

code = code.replace("if __name__ == '__main__':", proctoring_endpoints + "\n\nif __name__ == '__main__':")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Proctoring API added.")
