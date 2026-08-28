import re

with open('frontend/live_examination/code.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update session initialization (lines 310-313 approx)
old_session_code = """
            remainingSeconds = Math.max(0, parseInt(sess.remaining_seconds) || 0);
            localStorage.setItem(`exam_time_left_${examId}`, String(remainingSeconds));
            localStorage.setItem('exam_time_left', String(remainingSeconds));
"""

new_session_code = """
            const duration = parseInt(sess.duration_seconds) || 3600;
            const elapsed = parseInt(sess.elapsed_seconds) || 0;
            remainingSeconds = Math.max(0, duration - elapsed);
            
            if (elapsed >= duration) {
                showToast('Exam time has expired. Submitting automatically...', 'info');
                autoSubmitExam();
                return;
            }
            
            localStorage.setItem(`exam_time_left_${examId}`, String(remainingSeconds));
            localStorage.setItem('exam_time_left', String(remainingSeconds));
"""

content = content.replace(old_session_code.strip(), new_session_code.strip())

# 2. Update radio button change listener (lines 396-404 approx)
old_radio_code = """
            input.addEventListener('change', () => {
                answers[qid] = key;
                try {
                    localStorage.setItem('exam_answers', JSON.stringify(answers));
                } catch (e) {}
                renderQuestion(currentIndex);
                renderPalette();
                updateProgress();
            });
"""

new_radio_code = """
            input.addEventListener('change', () => {
                answers[qid] = key;
                try {
                    localStorage.setItem('exam_answers', JSON.stringify(answers));
                } catch (e) {}
                renderQuestion(currentIndex);
                renderPalette();
                updateProgress();
                
                // Server-authoritative autosave
                fetchApi(`/api/examinations/${examId}/autosave`, {
                    method: 'POST',
                    body: JSON.stringify({ qid: qid, selected_answer: key })
                }).then(r => r.json()).then(res => {
                    if (res && res.message === 'EXAM_EXPIRED') {
                        clearInterval(timerInterval);
                        autoSubmitExam();
                    }
                }).catch(console.error);
            });
"""
content = content.replace(old_radio_code.strip(), new_radio_code.strip())

# 3. Update autoSubmitExam to send AUTO_TIMEOUT
old_payload_code = """
    // Auto-submit when time reaches zero
    async function autoSubmitExam() {
        const payload = {
            student_id: student.student_id,
            exam_id: parseInt(examId),
            answers: {}
        };
"""

new_payload_code = """
    // Auto-submit when time reaches zero
    async function autoSubmitExam() {
        const payload = {
            student_id: student.student_id,
            exam_id: parseInt(examId),
            submission_type: 'AUTO_TIMEOUT',
            answers: {}
        };
"""
content = content.replace(old_payload_code.strip(), new_payload_code.strip())

# Also disable inputs when autoSubmitExam is called
old_autosubmit_start = """
    async function autoSubmitExam() {
"""
new_autosubmit_start = """
    async function autoSubmitExam() {
        document.querySelectorAll('input, button').forEach(el => el.disabled = true);
        if (timerInterval) clearInterval(timerInterval);
"""
content = content.replace(old_autosubmit_start.strip(), new_autosubmit_start.strip())


with open('frontend/live_examination/code.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated live_examination/code.html")
