import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update get_examination_session
old_get_session = '''
        if not sess:
            return jsonify({"success": False, "message": "No active session for this examination."}), 404

        start_time = sess.get("start_time")
        duration_seconds = int(sess.get("duration_seconds") or 0)
        status = sess.get("status") or "active"
        elapsed = int(sess.get("elapsed_seconds") or 0)
        remaining = max(0, duration_seconds - elapsed)

        return jsonify({
            "success": True,
            "session": {
                "exam_id": exam_id,
                "status": status,
                "remaining_seconds": remaining,
                "start_time": str(start_time),
                "duration_seconds": duration_seconds,
                "submitted_at": str(sess.get("submitted_at")) if sess.get("submitted_at") else None
            }
        })
'''

new_get_session = '''
        if not sess:
            return jsonify({"success": False, "message": "No active session for this examination."}), 404

        start_time = sess.get("start_time")
        duration_seconds = int(sess.get("duration_seconds") or 0)
        status = sess.get("status") or "active"
        elapsed = int(sess.get("elapsed_seconds") or 0)
        remaining = max(0, duration_seconds - elapsed)

        # Auto-finalize if expired and not yet submitted
        if remaining <= 0 and status != "submitted":
            student_name_or_username = student.get("student_name") or student.get("username")
            _internal_submit_examination(student_id, exam_id, "AUTO_TIMEOUT", {}, student_name_or_username)
            status = "submitted"
            remaining = 0

        return jsonify({
            "success": True,
            "session": {
                "exam_id": exam_id,
                "status": status,
                "remaining_seconds": remaining,
                "start_time": str(start_time),
                "duration_seconds": duration_seconds,
                "submitted_at": str(sess.get("submitted_at")) if sess.get("submitted_at") else None
            }
        })
'''

content = content.replace(old_get_session.strip(), new_get_session.strip())


# Update start_examination
old_start_exam = '''
            if status == "expired" or remaining <= 0:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "This exam session has expired."}), 400
'''

new_start_exam = '''
            if status == "expired" or remaining <= 0:
                if status != "submitted":
                    student_name_or_username = student.get("student_name") or student.get("username")
                    _internal_submit_examination(student_id, exam_id, "AUTO_TIMEOUT", {}, student_name_or_username)
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "This exam session has expired."}), 400
'''

content = content.replace(old_start_exam.strip(), new_start_exam.strip())

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated get_examination_session and start_examination")
