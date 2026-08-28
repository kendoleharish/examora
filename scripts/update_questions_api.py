import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

questions_api = '''
@app.route("/api/admin/questions", methods=["GET", "POST"])
def admin_questions():
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    if request.method == "GET":
        category_filter = request.args.get("category", "").strip()
        search_query = request.args.get("search", "").strip()
        type_filter = request.args.get("type", "").strip()

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT qid, type, category, question, content, metadata, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_answer FROM questions"
            query += get_tenant_where(admin)
            params = []

            if category_filter and category_filter != "ALL":
                query += " AND category = %s"
                params.append(category_filter)

            if type_filter and type_filter != "ALL":
                query += " AND type = %s"
                params.append(type_filter)

            if search_query:
                query += " AND question LIKE %s"
                params.append(f"%{search_query}%")

            query += " ORDER BY qid ASC"

            cursor.execute(query, tuple(params))
            questions = cursor.fetchall()
            
            # parse JSON fields
            import json
            for q in questions:
                if q.get('content') and isinstance(q['content'], str):
                    try: q['content'] = json.loads(q['content'])
                    except: pass
                if q.get('metadata') and isinstance(q['metadata'], str):
                    try: q['metadata'] = json.loads(q['metadata'])
                    except: pass
                    
            cursor.close()
            conn.close()

            return jsonify({"success": True, "questions": questions})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # POST: Add new question
    data = request.get_json(silent=True) or {}
    q_type = (data.get("type") or "MCQ").strip().upper()
    category = (data.get("category") or "General").strip()
    question = (data.get("question") or "").strip()
    content = data.get("content")
    metadata = data.get("metadata")
    marks = int(data.get("marks") or 1)
    negative_marks = float(data.get("negative_marks") or 0.0)
    difficulty = data.get("difficulty", "medium")
    tags = data.get("tags", "")
    
    # Legacy fallbacks
    optionA = (data.get("optionA") or "").strip()
    optionB = (data.get("optionB") or "").strip()
    optionC = (data.get("optionC") or "").strip()
    optionD = (data.get("optionD") or "").strip()
    correct_ans = (data.get("correct_answer") or "").strip()

    if not question:
        return jsonify({"success": False, "message": "Question statement is required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        import json
        content_str = json.dumps(content) if content else None
        metadata_str = json.dumps(metadata) if metadata else None
        
        institution_id = admin["institution_id"] if admin.get("role") != "SUPER_ADMIN" else (data.get("institution_id") or 1)

        cursor.execute(
            """INSERT INTO questions (institution_id, type, category, question, content, metadata, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_answer) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (institution_id, q_type, category, question, content_str, metadata_str, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_ans)
        )
        new_qid = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Question added successfully.",
            "qid": new_qid
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin/questions/<int:qid>", methods=["PUT", "DELETE"])
def admin_manage_question(qid):
    admin, auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM questions WHERE qid = %s {get_tenant_and(admin)}", (qid,))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Question not found or unauthorized."}), 404

        if request.method == "DELETE":
            cursor.execute("DELETE FROM questions WHERE qid = %s", (qid,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "Question deleted successfully."})

        # PUT (Update)
        data = request.get_json(silent=True) or {}
        q_type = (data.get("type") or "MCQ").strip().upper()
        category = (data.get("category") or "General").strip()
        question = (data.get("question") or "").strip()
        content = data.get("content")
        metadata = data.get("metadata")
        marks = int(data.get("marks") or 1)
        negative_marks = float(data.get("negative_marks") or 0.0)
        difficulty = data.get("difficulty", "medium")
        tags = data.get("tags", "")
        
        optionA = (data.get("optionA") or "").strip()
        optionB = (data.get("optionB") or "").strip()
        optionC = (data.get("optionC") or "").strip()
        optionD = (data.get("optionD") or "").strip()
        correct_ans = (data.get("correct_answer") or "").strip()

        if not question:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Question statement is required."}), 400

        import json
        content_str = json.dumps(content) if content else None
        metadata_str = json.dumps(metadata) if metadata else None

        cursor.execute("""
            UPDATE questions 
            SET type=%s, category=%s, question=%s, content=%s, metadata=%s, marks=%s, negative_marks=%s, difficulty=%s, tags=%s, optionA=%s, optionB=%s, optionC=%s, optionD=%s, correct_answer=%s
            WHERE qid = %s
        """, (q_type, category, question, content_str, metadata_str, marks, negative_marks, difficulty, tags, optionA, optionB, optionC, optionD, correct_ans, qid))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Question updated successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
'''

pattern = re.compile(r'@app\.route\("/api/admin/questions", methods=\["GET", "POST"\]\).*?return jsonify\(\{"success": False, "message": "Failed to update question\."\}\), 500', re.DOTALL)
code = pattern.sub(questions_api.strip(), code)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Questions API updated.")
