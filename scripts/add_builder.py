import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

builder_endpoints = '''
# ----------------------------------------------------
# EXAM BUILDER ENDPOINTS
# ----------------------------------------------------
@app.route("/api/admin/examinations/<int:exam_id>/builder", methods=["GET", "POST"])
def admin_exam_builder(exam_id):
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error
    
    if request.method == "GET":
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Fetch Exam
            cursor.execute(f"SELECT * FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))
            exam = cursor.fetchone()
            if not exam:
                cursor.close(); conn.close()
                return jsonify({"success": False, "message": "Exam not found."}), 404
                
            # Fetch Sections
            cursor.execute("SELECT * FROM exam_sections WHERE exam_id = %s ORDER BY order_index ASC", (exam_id,))
            sections = cursor.fetchall()
            
            # Fetch Questions for sections
            for section in sections:
                cursor.execute("""
                    SELECT eq.order_index, q.* 
                    FROM exam_questions eq
                    JOIN questions q ON eq.qid = q.qid
                    WHERE eq.exam_id = %s AND eq.section_id = %s
                    ORDER BY eq.order_index ASC
                """, (exam_id, section["section_id"]))
                section["questions"] = cursor.fetchall()
                
            # Fetch Unsectioned Questions
            cursor.execute("""
                SELECT eq.order_index, q.* 
                FROM exam_questions eq
                JOIN questions q ON eq.qid = q.qid
                WHERE eq.exam_id = %s AND eq.section_id IS NULL
                ORDER BY eq.order_index ASC
            """, (exam_id,))
            unsectioned = cursor.fetchall()
            
            cursor.close(); conn.close()
            
            return jsonify({
                "success": True,
                "exam": exam,
                "sections": sections,
                "unsectioned_questions": unsectioned
            })
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        sections_data = data.get("sections", [])
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Verify exam ownership
            cursor.execute(f"SELECT exam_id FROM examinations WHERE exam_id = %s {get_tenant_and(admin)}", (exam_id,))
            if not cursor.fetchone():
                cursor.close(); conn.close()
                return jsonify({"success": False, "message": "Exam not found."}), 404
                
            # Delete existing sections (cascade will remove exam_questions linked to section)
            cursor.execute("DELETE FROM exam_sections WHERE exam_id = %s", (exam_id,))
            
            for s_idx, sec in enumerate(sections_data):
                cursor.execute("""
                    INSERT INTO exam_sections (exam_id, title, description, time_limit_minutes, marks_per_question, negative_marks_per_question, randomize_order, order_index)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (exam_id, sec.get("title", f"Section {s_idx+1}"), sec.get("description", ""), sec.get("time_limit_minutes"), sec.get("marks_per_question"), sec.get("negative_marks_per_question"), sec.get("randomize_order", False), s_idx))
                
                section_id = cursor.lastrowid
                questions = sec.get("questions", [])
                for q_idx, qid in enumerate(questions):
                    cursor.execute("""
                        INSERT INTO exam_questions (exam_id, qid, section_id, order_index)
                        VALUES (%s, %s, %s, %s)
                    """, (exam_id, qid, section_id, q_idx))
                    
            conn.commit()
            cursor.close(); conn.close()
            
            return jsonify({"success": True, "message": "Exam builder saved."})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

'''

# Append to file before the if __name__ == '__main__' block
code = code.replace("if __name__ == '__main__':", builder_endpoints + "\n\nif __name__ == '__main__':")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Exam Builder endpoints added.")
