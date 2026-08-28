import re
with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_apis = '''

# ----------------------------------------------------
# STUDENT RESULT & CERTIFICATE API
# ----------------------------------------------------

@app.route("/api/student/result/<int:result_id>")
def get_student_result_detail(result_id):
    """Return a single result with all data needed for the printable result sheet."""
    student, auth_error = require_student_auth()
    if auth_error: return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT sr.result_id, sr.student_id, sr.exam_id, sr.student_name,
                   sr.score, sr.total_marks, sr.percentage, sr.grade,
                   sr.exam_date, sr.submission_type, sr.status,
                   e.title AS exam_title, e.exam_code, e.category AS exam_category,
                   e.duration_minutes, e.passing_percentage,
                   s.email AS student_email, s.username,
                   i.institution_id, i.institution_name, i.logo AS institution_logo,
                   i.email AS institution_email, i.phone AS institution_phone,
                   i.website AS institution_website,
                   i.primary_color, i.secondary_color,
                   i.certificates_enabled
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            JOIN students s ON sr.student_id = s.student_id
            LEFT JOIN institutions i ON e.institution_id = i.institution_id
            WHERE sr.result_id = %s AND sr.student_id = %s
        """, (result_id, student["student_id"]))
        result = cursor.fetchone()

        if not result:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Result not found or access denied."}), 404

        # Check for pending descriptive answers
        cursor.execute("""
            SELECT COUNT(*) AS pending FROM student_answers
            WHERE student_id = %s AND exam_id = %s AND evaluation_status = 'PENDING'
        """, (student["student_id"], result["exam_id"]))
        pending = cursor.fetchone()["pending"]

        # Performance stats
        cursor.execute("""
            SELECT
                COUNT(*) AS total_questions,
                SUM(CASE WHEN selected_answer IS NOT NULL AND selected_answer != '' THEN 1
                         WHEN answer_text IS NOT NULL AND answer_text != '' THEN 1
                         ELSE 0 END) AS attempted,
                SUM(CASE WHEN marks_obtained > 0 THEN 1 ELSE 0 END) AS correct,
                SUM(CASE WHEN marks_obtained < 0 THEN 1 ELSE 0 END) AS negative_marked,
                SUM(CASE WHEN marks_obtained < 0 THEN ABS(marks_obtained) ELSE 0 END) AS negative_marks_total
            FROM student_answers
            WHERE student_id = %s AND exam_id = %s
        """, (student["student_id"], result["exam_id"]))
        perf = cursor.fetchone()

        # Certificate info
        cursor.execute("SELECT certificate_id, generated_at FROM certificates WHERE result_id = %s", (result_id,))
        cert = cursor.fetchone()

        cursor.close(); conn.close()

        if result.get("exam_date"):
            result["exam_date"] = str(result["exam_date"])

        is_passed = result["percentage"] >= result.get("passing_percentage", 50)
        evaluation_complete = pending == 0
        result_finalized = result["status"] == "FINAL" and evaluation_complete

        cert_available = (
            result_finalized and
            bool(result.get("certificates_enabled")) and
            is_passed
        )

        return jsonify({
            "success": True,
            "result": {
                "result_id": result["result_id"],
                "student_name": result["student_name"],
                "student_email": result["student_email"],
                "username": result["username"],
                "exam_title": result["exam_title"],
                "exam_code": result["exam_code"],
                "exam_category": result["exam_category"],
                "exam_date": result.get("exam_date"),
                "duration_minutes": result["duration_minutes"],
                "passing_percentage": result["passing_percentage"],
                "score": result["score"],
                "total_marks": result["total_marks"],
                "percentage": result["percentage"],
                "grade": result["grade"],
                "status": "PASSED" if is_passed else "FAILED",
                "submission_type": result["submission_type"],
                "evaluation_status": "FINALIZED" if evaluation_complete else "PENDING_EVALUATION",
                "result_status": result["status"],
                "institution_name": result["institution_name"],
                "institution_logo": result["institution_logo"],
                "institution_email": result["institution_email"],
                "institution_phone": result["institution_phone"],
                "institution_website": result["institution_website"],
                "primary_color": result["primary_color"],
                "secondary_color": result["secondary_color"],
            },
            "performance": {
                "total_questions": int(perf["total_questions"] or 0),
                "attempted": int(perf["attempted"] or 0),
                "correct": int(perf["correct"] or 0),
                "incorrect": int(perf["attempted"] or 0) - int(perf["correct"] or 0) - int(perf["negative_marked"] or 0),
                "unanswered": int(perf["total_questions"] or 0) - int(perf["attempted"] or 0),
                "negative_marks": float(perf["negative_marks_total"] or 0),
            },
            "certificate": {
                "available": cert_available,
                "generated": cert is not None,
                "certificate_id": cert["certificate_id"] if cert else None,
                "generated_at": str(cert["generated_at"]) if cert else None,
            }
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to fetch result details."}), 500


@app.route("/api/student/results/history")
def get_student_results_history():
    """Return all results for the authenticated student."""
    student, auth_error = require_student_auth()
    if auth_error: return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT sr.result_id, sr.exam_id, sr.score, sr.total_marks,
                   sr.percentage, sr.grade, sr.exam_date,
                   sr.submission_type, sr.status,
                   e.title AS exam_title, e.exam_code, e.passing_percentage,
                   c.certificate_id
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            LEFT JOIN certificates c ON sr.result_id = c.result_id
            WHERE sr.student_id = %s
            ORDER BY sr.exam_date DESC
        """, (student["student_id"],))
        results = cursor.fetchall()

        # Check pending descriptive evals per exam
        for r in results:
            cursor.execute("""
                SELECT COUNT(*) AS pending FROM student_answers
                WHERE student_id = %s AND exam_id = %s AND evaluation_status = 'PENDING'
            """, (student["student_id"], r["exam_id"]))
            pend = cursor.fetchone()["pending"]
            r["evaluation_status"] = "PENDING_EVALUATION" if pend > 0 else "FINALIZED"
            r["is_passed"] = r["percentage"] >= (r.get("passing_percentage") or 50)
            if r.get("exam_date"): r["exam_date"] = str(r["exam_date"])

        cursor.close(); conn.close()
        return jsonify({"success": True, "results": results})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to fetch result history."}), 500


@app.route("/api/student/result/<int:result_id>/certificate", methods=["POST"])
def generate_certificate(result_id):
    """Generate a certificate ID for a finalized, passing result."""
    student, auth_error = require_student_auth()
    if auth_error: return auth_error

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify ownership and finalization
        cursor.execute("""
            SELECT sr.result_id, sr.student_id, sr.exam_id, sr.percentage, sr.status,
                   e.institution_id, e.passing_percentage, i.certificates_enabled
            FROM student_results sr
            JOIN examinations e ON sr.exam_id = e.exam_id
            JOIN institutions i ON e.institution_id = i.institution_id
            WHERE sr.result_id = %s AND sr.student_id = %s
        """, (result_id, student["student_id"]))
        result = cursor.fetchone()

        if not result:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Result not found or access denied."}), 404

        if not result.get("certificates_enabled"):
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Certificates are not enabled for your institution."}), 403

        if result["status"] != "FINAL":
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Result is not yet finalized."}), 400

        # Check pending evals
        cursor.execute("""
            SELECT COUNT(*) AS pending FROM student_answers
            WHERE student_id = %s AND exam_id = %s AND evaluation_status = 'PENDING'
        """, (student["student_id"], result["exam_id"]))
        if cursor.fetchone()["pending"] > 0:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Evaluation is still pending."}), 400

        passing = result.get("passing_percentage") or 50
        if result["percentage"] < passing:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Certificate requires a passing grade."}), 400

        # Check if cert already exists (idempotent)
        cursor.execute("SELECT certificate_id, generated_at FROM certificates WHERE result_id = %s", (result_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.close(); conn.close()
            return jsonify({
                "success": True,
                "certificate_id": existing["certificate_id"],
                "generated_at": str(existing["generated_at"]),
                "message": "Certificate already exists."
            })

        # Generate unique certificate ID: EXM-YYYY-XXXXXX
        import random
        from datetime import datetime
        year = datetime.now().strftime("%Y")
        for attempt in range(10):
            rand_part = str(random.randint(100000, 999999))
            cert_id = f"EXM-{year}-{rand_part}"
            cursor.execute("SELECT certificate_id FROM certificates WHERE certificate_id = %s", (cert_id,))
            if not cursor.fetchone():
                break
        else:
            cursor.close(); conn.close()
            return jsonify({"success": False, "message": "Failed to generate unique certificate ID."}), 500

        cursor.execute("""
            INSERT INTO certificates (certificate_id, result_id, student_id, exam_id, institution_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (cert_id, result_id, student["student_id"], result["exam_id"], result["institution_id"]))
        conn.commit()

        log_audit(student["student_id"], "STUDENT", result["institution_id"],
                  "GENERATE_CERTIFICATE", cert_id,
                  {"result_id": result_id, "exam_id": result["exam_id"]})

        cursor.close(); conn.close()
        return jsonify({
            "success": True,
            "certificate_id": cert_id,
            "generated_at": str(datetime.now()),
            "message": "Certificate generated successfully."
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to generate certificate."}), 500


@app.route("/api/public/verify-certificate")
def verify_certificate():
    """Public endpoint: verify a certificate ID. No authentication required."""
    cid = request.args.get("cid", "").strip()
    if not cid:
        return jsonify({"success": False, "valid": False, "message": "Certificate ID is required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.certificate_id, c.generated_at,
                   sr.student_name, sr.percentage, sr.grade, sr.exam_date,
                   e.title AS exam_title,
                   i.institution_name
            FROM certificates c
            JOIN student_results sr ON c.result_id = sr.result_id
            JOIN examinations e ON c.exam_id = e.exam_id
            JOIN institutions i ON c.institution_id = i.institution_id
            WHERE c.certificate_id = %s
        """, (cid,))
        cert = cursor.fetchone()

        cursor.close(); conn.close()

        if not cert:
            return jsonify({"success": True, "valid": False, "message": "Certificate not found."})

        is_passed = cert["percentage"] >= 50

        return jsonify({
            "success": True,
            "valid": True,
            "certificate": {
                "certificate_id": cert["certificate_id"],
                "student_name": cert["student_name"],
                "institution_name": cert["institution_name"],
                "exam_title": cert["exam_title"],
                "exam_date": str(cert["exam_date"]) if cert["exam_date"] else None,
                "percentage": cert["percentage"],
                "grade": cert["grade"],
                "status": "PASSED" if is_passed else "FAILED",
                "generated_at": str(cert["generated_at"]),
            }
        })
    except Exception:
        return jsonify({"success": False, "message": "Verification failed."}), 500


# ----------------------------------------------------
# ADMIN RESULT REPORTING & EXPORT API
# ----------------------------------------------------

@app.route("/api/admin/results/history")
def admin_results_history():
    """Paginated, filtered result listing for admin reporting dashboard."""
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    search = request.args.get("search", "").strip()
    grade_filter = request.args.get("grade", "").strip()
    exam_id = request.args.get("exam_id", "").strip()
    status_filter = request.args.get("status", "").strip()
    timeout_only = request.args.get("timeout", "").strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        tenant_cond = get_tenant_and(admin, "e")

        query = """
            SELECT sr.result_id, sr.student_id, sr.exam_id, sr.student_name,
                   sr.score, sr.total_marks, sr.percentage, sr.grade,
                   sr.exam_date, sr.submission_type, sr.status,
                   s.email, s.username,
                   e.title AS exam_title, e.exam_code, e.passing_percentage,
                   c.certificate_id,
                   i.institution_name
            FROM student_results sr
            JOIN students s ON sr.student_id = s.student_id
            JOIN examinations e ON sr.exam_id = e.exam_id
            LEFT JOIN institutions i ON e.institution_id = i.institution_id
            LEFT JOIN certificates c ON sr.result_id = c.result_id
            WHERE 1=1 {tenant}
        """.format(tenant=tenant_cond)
        params = []

        if search:
            query += " AND (sr.student_name LIKE %s OR s.email LIKE %s OR e.title LIKE %s)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp])

        if grade_filter:
            query += " AND sr.grade = %s"
            params.append(grade_filter)

        if exam_id:
            query += " AND sr.exam_id = %s"
            params.append(int(exam_id))

        if status_filter == "PASSED":
            query += " AND sr.percentage >= COALESCE(e.passing_percentage, 50)"
        elif status_filter == "FAILED":
            query += " AND sr.percentage < COALESCE(e.passing_percentage, 50)"

        if timeout_only == "1":
            query += " AND sr.submission_type = 'AUTO_TIMEOUT'"

        # Count
        count_query = f"SELECT COUNT(*) AS total FROM ({query}) AS sub"
        cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()["total"]

        query += " ORDER BY sr.exam_date DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        for r in results:
            if r.get("exam_date"): r["exam_date"] = str(r["exam_date"])
            r["is_passed"] = r["percentage"] >= (r.get("passing_percentage") or 50)

        cursor.close(); conn.close()

        return jsonify({
            "success": True,
            "results": results,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to fetch results."}), 500


@app.route("/api/admin/results/export")
def admin_results_export():
    """Stream CSV export of results filtered by tenant."""
    admin, auth_error = require_admin_auth()
    if auth_error: return auth_error

    import csv, io

    search = request.args.get("search", "").strip()
    grade_filter = request.args.get("grade", "").strip()
    exam_id = request.args.get("exam_id", "").strip()
    status_filter = request.args.get("status", "").strip()
    timeout_only = request.args.get("timeout", "").strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        tenant_cond = get_tenant_and(admin, "e")

        query = """
            SELECT i.institution_name, e.title AS exam_title, e.exam_code,
                   sr.student_name, s.email, sr.exam_date,
                   sr.score, sr.total_marks, sr.percentage, sr.grade,
                   sr.submission_type, sr.status AS evaluation_status,
                   c.certificate_id
            FROM student_results sr
            JOIN students s ON sr.student_id = s.student_id
            JOIN examinations e ON sr.exam_id = e.exam_id
            LEFT JOIN institutions i ON e.institution_id = i.institution_id
            LEFT JOIN certificates c ON sr.result_id = c.result_id
            WHERE 1=1 {tenant}
        """.format(tenant=tenant_cond)
        params = []

        if search:
            query += " AND (sr.student_name LIKE %s OR s.email LIKE %s OR e.title LIKE %s)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp])
        if grade_filter:
            query += " AND sr.grade = %s"
            params.append(grade_filter)
        if exam_id:
            query += " AND sr.exam_id = %s"
            params.append(int(exam_id))
        if status_filter == "PASSED":
            query += " AND sr.percentage >= COALESCE(e.passing_percentage, 50)"
        elif status_filter == "FAILED":
            query += " AND sr.percentage < COALESCE(e.passing_percentage, 50)"
        if timeout_only == "1":
            query += " AND sr.submission_type = 'AUTO_TIMEOUT'"

        query += " ORDER BY sr.exam_date DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close(); conn.close()

        log_audit(admin["admin_id"], admin.get("role"), admin.get("institution_id"),
                  "EXPORT_RESULTS", f"{len(rows)} rows", {"filters": {"search": search, "grade": grade_filter}})

        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Institution", "Exam", "Exam Code", "Student", "Email",
                             "Date", "Score", "Total Marks", "Percentage", "Grade",
                             "Status", "Submission Type", "Evaluation Status", "Certificate ID"])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            for row in rows:
                pct = row.get("percentage") or 0
                is_pass = "PASSED" if pct >= 50 else "FAILED"
                writer.writerow([
                    row.get("institution_name", ""),
                    row.get("exam_title", ""),
                    row.get("exam_code", ""),
                    row.get("student_name", ""),
                    row.get("email", ""),
                    str(row.get("exam_date", "")),
                    row.get("score", 0),
                    row.get("total_marks", 0),
                    round(pct, 2),
                    row.get("grade", ""),
                    is_pass,
                    row.get("submission_type", ""),
                    row.get("evaluation_status", ""),
                    row.get("certificate_id", ""),
                ])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        from flask import Response
        return Response(
            generate(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=examora_results_export.csv"}
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": "Export failed."}), 500

'''

if 'def get_student_result_detail' not in code:
    code = code.replace('if __name__ == "__main__":', new_apis + '\nif __name__ == "__main__":')
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Code successfully replaced!")
else:
    print("APIs already exist.")
