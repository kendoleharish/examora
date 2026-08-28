let pendingEvaluations = [];
let activeStudentId = null;
let activeExamId = null;
let studentAnswers = [];

document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;
    
    await loadPendingEvaluations();
});

async function loadPendingEvaluations() {
    try {
        const res = await fetchApi('/api/admin/evaluations/pending');
        if (res.ok) {
            const data = await res.json();
            pendingEvaluations = data.pending || [];
            document.getElementById('pendingCount').textContent = `${pendingEvaluations.length} Pending`;
            renderEvalList();
        } else {
            showToast('Failed to load pending evaluations', 'error');
        }
    } catch (e) {
        showToast('Network error loading evaluations', 'error');
    }
}

function renderEvalList() {
    const container = document.getElementById('evalListContainer');
    const search = document.getElementById('evalSearch').value.toLowerCase().trim();
    
    const filtered = pendingEvaluations.filter(p => 
        !search || 
        p.student_name.toLowerCase().includes(search) || 
        p.username.toLowerCase().includes(search) || 
        p.exam_code.toLowerCase().includes(search) || 
        p.exam_title.toLowerCase().includes(search)
    );
    
    container.innerHTML = '';
    if (filtered.length === 0) {
        container.innerHTML = `<p class="text-xs text-on-surface-variant text-center p-8">No pending evaluations found.</p>`;
        return;
    }
    
    filtered.forEach(p => {
        const isActive = activeStudentId === p.student_id && activeExamId === p.exam_id;
        
        const div = document.createElement('div');
        div.className = `p-4 border-b border-outline-variant/10 cursor-pointer transition-colors ${isActive ? 'bg-primary/10 border-l-4 border-l-primary' : 'hover:bg-surface-container-low border-l-4 border-l-transparent'}`;
        div.onclick = () => selectEvaluation(p.exam_id, p.student_id, p);
        
        div.innerHTML = `
            <div class="flex justify-between items-start mb-1">
                <span class="font-bold text-sm text-on-surface">${p.student_name}</span>
                <span class="text-[10px] font-bold bg-warning-container text-warning px-2 py-0.5 rounded-full">${p.pending_count} Q's</span>
            </div>
            <div class="text-[11px] text-on-surface-variant font-medium flex items-center gap-1.5">
                <span class="text-primary font-mono bg-primary/5 px-1 rounded">${p.exam_code}</span>
                <span class="truncate">${p.exam_title}</span>
            </div>
        `;
        container.appendChild(div);
    });
}

async function selectEvaluation(examId, studentId, pData) {
    activeExamId = examId;
    activeStudentId = studentId;
    renderEvalList(); // Update selected styling
    
    document.getElementById('evalWorkspaceEmpty').classList.add('hidden');
    document.getElementById('evalWorkspaceActive').classList.remove('hidden');
    
    document.getElementById('activeStudentName').textContent = pData.student_name;
    document.getElementById('activeExamCode').textContent = pData.exam_code;
    document.getElementById('activeExamTitle').textContent = pData.exam_title;
    document.getElementById('evalQuestionsContainer').innerHTML = `<p class="text-center text-sm text-on-surface-variant py-12">Loading answers...</p>`;
    document.getElementById('finalizeBtn').classList.add('hidden');
    
    try {
        const res = await fetchApi(`/api/admin/evaluations/student/${examId}/${studentId}`);
        if (res.ok) {
            const data = await res.json();
            studentAnswers = data.answers || [];
            renderEvalQuestions();
            checkFinalizeStatus();
        } else {
            document.getElementById('evalQuestionsContainer').innerHTML = `<p class="text-center text-sm text-error py-12">Failed to load student answers.</p>`;
        }
    } catch (e) {
        document.getElementById('evalQuestionsContainer').innerHTML = `<p class="text-center text-sm text-error py-12">Network error.</p>`;
    }
}

function renderEvalQuestions() {
    const container = document.getElementById('evalQuestionsContainer');
    container.innerHTML = '';
    
    if (studentAnswers.length === 0) {
        container.innerHTML = `<p class="text-center text-sm text-on-surface-variant py-12">No questions require manual evaluation.</p>`;
        return;
    }
    
    studentAnswers.forEach((ans, idx) => {
        const div = document.createElement('div');
        div.className = 'bg-surface-container-lowest border border-outline-variant/30 rounded-2xl shadow-sm overflow-hidden mb-6';
        
        const isPending = ans.evaluation_status === 'PENDING';
        
        let answerTextHtml = '';
        if (ans.question_type === 'DESCRIPTIVE' || ans.question_type === 'SHORT_ANSWER') {
            answerTextHtml = `
                <div class="p-4 bg-surface-container-low/50 rounded-xl border border-outline-variant/20 mb-4 whitespace-pre-wrap font-serif text-on-surface leading-relaxed text-sm">${ans.answer_text || '<span class="italic text-on-surface-variant">No answer provided.</span>'}</div>
            `;
        } else {
            answerTextHtml = `<div class="p-4 bg-surface-container-low rounded-xl text-sm">${ans.answer_text || '-'}</div>`;
        }

        let rubricHtml = '';
        const content = ans.content || {};
        if (content.rubric) {
            rubricHtml = `
                <div class="mb-4">
                    <span class="block text-[11px] font-bold uppercase tracking-wider text-on-surface-variant mb-1">Grading Rubric</span>
                    <div class="text-xs text-on-surface-variant bg-tertiary-container/20 p-3 rounded-lg border border-tertiary-container/30">${content.rubric}</div>
                </div>
            `;
        }

        div.innerHTML = `
            <div class="p-4 border-b border-outline-variant/20 bg-surface-container-low flex justify-between items-start">
                <div class="flex items-center gap-3">
                    <span class="bg-primary/10 text-primary font-bold text-xs w-7 h-7 flex items-center justify-center rounded-lg">Q${ans.qid}</span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-surface-container-highest text-on-surface">${ans.question_type.replace('_', ' ')}</span>
                </div>
                <div class="flex items-center gap-2">
                    ${isPending ? `<span class="text-[10px] font-bold bg-warning-container text-warning px-2 py-1 rounded-full border border-warning/30 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">pending_actions</span> Needs Grading</span>` : `<span class="text-[10px] font-bold bg-success-container text-success px-2 py-1 rounded-full border border-success/30 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">check_circle</span> Evaluated</span>`}
                    <span class="text-xs font-bold text-on-surface-variant">Max Marks: ${ans.max_marks}</span>
                </div>
            </div>
            
            <div class="p-5">
                <h3 class="text-sm font-bold text-on-surface mb-3">${ans.question}</h3>
                
                ${rubricHtml}
                
                <span class="block text-[11px] font-bold uppercase tracking-wider text-on-surface-variant mb-1">Student's Response</span>
                ${answerTextHtml}
                
                <div class="mt-6 pt-5 border-t border-outline-variant/20">
                    <span class="block text-[11px] font-bold uppercase tracking-wider text-primary mb-3">Teacher Evaluation</span>
                    <div class="flex gap-4 items-start">
                        <div class="w-32">
                            <label class="block text-[10px] font-bold uppercase text-on-surface-variant mb-1">Marks Awarded</label>
                            <input type="number" id="marks_${ans.qid}" value="${ans.marks_obtained !== null ? ans.marks_obtained : ''}" min="0" max="${ans.max_marks}" step="any" class="w-full bg-surface-container-lowest text-sm rounded-lg py-2 px-3 border border-outline-variant/40 outline-none focus:border-primary font-bold text-primary text-center"/>
                        </div>
                        <div class="flex-1">
                            <label class="block text-[10px] font-bold uppercase text-on-surface-variant mb-1">Feedback / Remarks (Optional)</label>
                            <textarea id="feedback_${ans.qid}" rows="1" class="w-full bg-surface-container-lowest text-sm rounded-lg py-2 px-3 border border-outline-variant/40 outline-none focus:border-primary" placeholder="Provide constructive feedback...">${ans.feedback || ''}</textarea>
                        </div>
                        <div class="pt-5">
                            <button onclick="saveScore(${ans.qid}, ${ans.max_marks})" class="px-4 py-2 bg-primary text-on-primary rounded-lg text-xs font-bold hover:bg-primary/90 flex items-center gap-1 shadow-sm">
                                <span class="material-symbols-outlined text-[16px]">save</span> Save
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(div);
    });
}

async function saveScore(qid, maxMarks) {
    const marksInput = document.getElementById(`marks_${qid}`).value;
    const feedback = document.getElementById(`feedback_${qid}`).value.trim();
    
    if (marksInput === '') {
        showToast('Please enter marks before saving.', 'error');
        return;
    }
    
    let marks = parseFloat(marksInput);
    if (isNaN(marks) || marks < 0 || marks > maxMarks) {
        showToast(`Marks must be between 0 and ${maxMarks}.`, 'error');
        return;
    }
    
    const payload = {
        student_id: activeStudentId,
        exam_id: activeExamId,
        qid: qid,
        marks_awarded: marks,
        feedback: feedback
    };
    
    try {
        const res = await fetchApi('/api/admin/evaluations/score', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            showToast('Score saved!', 'success');
            // Update local state
            const ans = studentAnswers.find(a => a.qid === qid);
            if (ans) {
                ans.marks_obtained = marks;
                ans.feedback = feedback;
                ans.evaluation_status = 'EVALUATED';
            }
            renderEvalQuestions();
            checkFinalizeStatus();
        } else {
            const data = await res.json();
            showToast(data.message || 'Failed to save score', 'error');
        }
    } catch(e) {
        showToast('Network error saving score', 'error');
    }
}

function checkFinalizeStatus() {
    const hasPending = studentAnswers.some(ans => ans.evaluation_status === 'PENDING');
    const finalizeBtn = document.getElementById('finalizeBtn');
    if (!hasPending && studentAnswers.length > 0) {
        finalizeBtn.classList.remove('hidden');
    } else {
        finalizeBtn.classList.add('hidden');
    }
}

async function finalizeEvaluation() {
    if (!confirm("Are you sure you want to finalize this evaluation? The final grade will be calculated and published to the student.")) {
        return;
    }
    
    const finalizeBtn = document.getElementById('finalizeBtn');
    finalizeBtn.disabled = true;
    finalizeBtn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">refresh</span> Finalizing...`;
    
    try {
        const res = await fetchApi('/api/admin/evaluations/finalize', {
            method: 'POST',
            body: JSON.stringify({
                student_id: activeStudentId,
                exam_id: activeExamId
            })
        });
        
        if (res.ok) {
            showToast('Evaluation finalized and grade published!', 'success');
            // Remove from list and reload
            activeStudentId = null;
            activeExamId = null;
            document.getElementById('evalWorkspaceEmpty').classList.remove('hidden');
            document.getElementById('evalWorkspaceActive').classList.add('hidden');
            await loadPendingEvaluations();
        } else {
            const data = await res.json();
            showToast(data.message || 'Failed to finalize', 'error');
        }
    } catch(e) {
        showToast('Network error', 'error');
    } finally {
        finalizeBtn.disabled = false;
        finalizeBtn.innerHTML = `<span class="material-symbols-outlined text-[18px]">done_all</span> Finalize & Publish Grade`;
    }
}

function showToast(msg, type='info') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-full text-sm font-semibold shadow-xl transition-all duration-300 transform translate-y-0 opacity-100 ${type==='error'?'bg-error text-white':(type==='success'?'bg-success text-white':'bg-surface-container-highest text-on-surface')}`;
    setTimeout(() => {
        t.classList.remove('translate-y-0', 'opacity-100');
        t.classList.add('translate-y-4', 'opacity-0');
    }, 3000);
}
