import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Update require_student_auth to fetch branding
student_auth = '''def require_student_auth():
    if "student_id" not in session:
        return None, (jsonify({"success": False, "message": "Not authenticated"}), 401)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.student_id, s.student_name, s.username, s.institution_id, 
                   i.institution_name, i.primary_color, i.secondary_color, i.logo
            FROM students s 
            LEFT JOIN institutions i ON s.institution_id = i.institution_id
            WHERE s.student_id = %s
        """, (session["student_id"],))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        if student:
            return student, None
        return None, (jsonify({"success": False, "message": "Student not found"}), 404)
    except Exception as e:
        return None, (jsonify({"success": False, "message": "Server error"}), 500)'''
        
pattern = re.compile(r'def require_student_auth\(\):.*?return None, \(jsonify\(\{"success": False, "message": "Server error"\}\), 500\)', re.DOTALL)
code = pattern.sub(student_auth, code)

# Update require_admin_auth
admin_auth = '''def require_admin_auth():
    if "admin_id" not in session:
        return None, (jsonify({"success": False, "message": "Not authenticated"}), 401)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.admin_id, a.username, a.full_name, a.institution_id, a.role,
                   i.institution_name, i.primary_color, i.secondary_color, i.logo
            FROM admins a
            LEFT JOIN institutions i ON a.institution_id = i.institution_id
            WHERE a.admin_id = %s
        """, (session["admin_id"],))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        if admin:
            return admin, None
        return None, (jsonify({"success": False, "message": "Admin not found"}), 404)
    except Exception as e:
        return None, (jsonify({"success": False, "message": "Server error"}), 500)'''
pattern2 = re.compile(r'def require_admin_auth\(\):.*?return None, \(jsonify\(\{"success": False, "message": "Server error"\}\), 500\)', re.DOTALL)
code = pattern2.sub(admin_auth, code)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

# Update auth.js
with open('frontend/shared/auth.js', 'r', encoding='utf-8') as f:
    auth_js = f.read()

branding_func = '''
function applyBranding(user) {
    if (!user) return;
    
    // Update institution name text
    document.querySelectorAll('.institution-name-display').forEach(el => {
        el.textContent = user.institution_name || 'EXAMORA';
    });
    
    // Update CSS variables for white-label colors
    const root = document.documentElement;
    if (user.primary_color) {
        // Convert hex to rgb format for tailwind opacity support
        const hex = user.primary_color.replace('#', '');
        if (hex.length === 6) {
            const r = parseInt(hex.substring(0, 2), 16);
            const g = parseInt(hex.substring(2, 4), 16);
            const b = parseInt(hex.substring(4, 6), 16);
            root.style.setProperty('--color-primary', `${r} ${g} ${b}`);
        }
    }
    if (user.secondary_color) {
        const hex = user.secondary_color.replace('#', '');
        if (hex.length === 6) {
            const r = parseInt(hex.substring(0, 2), 16);
            const g = parseInt(hex.substring(2, 4), 16);
            const b = parseInt(hex.substring(4, 6), 16);
            root.style.setProperty('--color-secondary', `${r} ${g} ${b}`);
        }
    }
}
'''
auth_js = auth_js.replace('function updateStudentUI(student) {', branding_func + '\nfunction updateStudentUI(student) {\n    applyBranding(student);')
auth_js = auth_js.replace('function updateAdminUI(admin) {', 'function updateAdminUI(admin) {\n    applyBranding(admin);')

with open('frontend/shared/auth.js', 'w', encoding='utf-8') as f:
    f.write(auth_js)

print("Added white-label branding.")
