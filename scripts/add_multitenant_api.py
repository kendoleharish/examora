import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add audit logging function
audit_func = '''
import json
def log_audit(actor_id, actor_role, institution_id, action, target_id, metadata=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        meta_str = json.dumps(metadata) if metadata else None
        cursor.execute("""
            INSERT INTO audit_logs (actor_id, actor_role, institution_id, action, target_id, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (actor_id, actor_role, institution_id, action, str(target_id), meta_str))
        conn.commit()
        cursor.close(); conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")
'''
if 'def log_audit' not in code:
    code = code.replace('def get_db_connection():', audit_func + '\n\ndef get_db_connection():')

# Multitenant & Super Admin endpoints
api_endpoints = '''
# ----------------------------------------------------
# SUPER ADMIN / INSTITUTION API
# ----------------------------------------------------

@app.route("/api/admin/institutions", methods=["GET"])
def get_institutions():
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    if admin.get("role") != "SUPER_ADMIN":
        return jsonify({"success": False, "message": "Unauthorized. Super Admin only."}), 403
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT i.*, 
                (SELECT COUNT(*) FROM students WHERE institution_id = i.institution_id) as student_count,
                (SELECT COUNT(*) FROM admins WHERE institution_id = i.institution_id) as admin_count,
                (SELECT COUNT(*) FROM examinations WHERE institution_id = i.institution_id) as exam_count
            FROM institutions i
            ORDER BY i.created_at DESC
        """)
        insts = cursor.fetchall()
        for i in insts: i["created_at"] = str(i["created_at"])
        cursor.close(); conn.close()
        return jsonify({"success": True, "institutions": insts})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/institutions/<int:inst_id>", methods=["PUT"])
def update_institution(inst_id):
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    # Super admins can edit any, regular admins can edit their own
    if admin.get("role") != "SUPER_ADMIN" and str(admin.get("institution_id")) != str(inst_id):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # update fields
        updates = []
        vals = []
        allowed = ["institution_name", "email", "phone", "website", "primary_color", "secondary_color", "status"]
        for k in allowed:
            if k in data:
                updates.append(f"{k} = %s")
                vals.append(data[k])
                
        if updates:
            vals.append(inst_id)
            cursor.execute(f"UPDATE institutions SET {', '.join(updates)} WHERE institution_id = %s", tuple(vals))
            conn.commit()
            
            log_audit(admin["admin_id"], admin.get("role"), inst_id, "UPDATE_INSTITUTION", inst_id, data)
            
        cursor.close(); conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/auth/theme", methods=["GET"])
def get_auth_theme():
    """Return branding info for the public login/join pages based on origin or a generic default"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # For simplicity, returning the default institution branding unless specified.
        # In a real multi-tenant app, we'd check subdomain. 
        # Here we just return the first active one, or maybe we shouldn't brand login unless we know the tenant.
        # Let's just return nothing or a placeholder. 
        # Actually, let's allow fetching by exam_code for the join page.
        code = request.args.get("exam_code")
        if code:
            cursor.execute("""
                SELECT i.institution_name, i.logo, i.primary_color, i.secondary_color
                FROM institutions i
                JOIN examinations e ON e.institution_id = i.institution_id
                WHERE e.exam_code = %s
            """, (code,))
            inst = cursor.fetchone()
            cursor.close(); conn.close()
            if inst:
                return jsonify({"success": True, "branding": inst})
        
        cursor.close(); conn.close()
        return jsonify({"success": True, "branding": None})
    except:
        return jsonify({"success": False})

'''
if 'def get_institutions' not in code:
    code = code.replace("if __name__ == '__main__':", api_endpoints + "\nif __name__ == '__main__':")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Added Multitenant API.")
