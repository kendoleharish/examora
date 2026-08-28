// question_creator.js - Handles polymorphic question UI logic

function renderDynamicQuestionFields() {
    const qType = document.getElementById('q_type').value;
    const container = document.getElementById('dynamicQuestionFields');
    let html = '';

    if (qType === 'MCQ') {
        html = `
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option A</label><input type="text" id="q_optA" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/></div>
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option B</label><input type="text" id="q_optB" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/></div>
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option C</label><input type="text" id="q_optC" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/></div>
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option D</label><input type="text" id="q_optD" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/></div>
            </div>
            <div class="mt-4">
                <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Correct Answer</label>
                <select id="q_correct" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary">
                    <option value="A">Option A</option>
                    <option value="B">Option B</option>
                    <option value="C">Option C</option>
                    <option value="D">Option D</option>
                </select>
            </div>
        `;
    } else if (qType === 'MULTIPLE_SELECT') {
        html = `
            <div id="ms_options_container" class="space-y-3">
                <!-- Dynamically add more options if needed, sticking to 4 for simplicity right now -->
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option 1</label><input type="text" id="ms_opt1" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40"/></div>
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option 2</label><input type="text" id="ms_opt2" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40"/></div>
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option 3</label><input type="text" id="ms_opt3" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40"/></div>
                <div><label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Option 4</label><input type="text" id="ms_opt4" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40"/></div>
            </div>
            <div class="mt-4">
                <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Correct Answers (Check all that apply)</label>
                <div class="flex gap-4 items-center">
                    <label class="flex items-center gap-2"><input type="checkbox" id="ms_chk1" value="1" class="w-4 h-4 text-primary bg-surface-container-low border-outline-variant/40 rounded focus:ring-primary"/> Option 1</label>
                    <label class="flex items-center gap-2"><input type="checkbox" id="ms_chk2" value="2" class="w-4 h-4 text-primary bg-surface-container-low border-outline-variant/40 rounded focus:ring-primary"/> Option 2</label>
                    <label class="flex items-center gap-2"><input type="checkbox" id="ms_chk3" value="3" class="w-4 h-4 text-primary bg-surface-container-low border-outline-variant/40 rounded focus:ring-primary"/> Option 3</label>
                    <label class="flex items-center gap-2"><input type="checkbox" id="ms_chk4" value="4" class="w-4 h-4 text-primary bg-surface-container-low border-outline-variant/40 rounded focus:ring-primary"/> Option 4</label>
                </div>
            </div>
        `;
    } else if (qType === 'TRUE_FALSE') {
        html = `
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Correct Answer</label>
                <select id="tf_correct" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary">
                    <option value="TRUE">True</option>
                    <option value="FALSE">False</option>
                </select>
            </div>
        `;
    } else if (qType === 'FILL_BLANK') {
        html = `
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Expected Exact Answer</label>
                <input type="text" id="fb_correct" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary" placeholder="e.g. Paris"/>
                <p class="text-[10px] text-on-surface-variant mt-1">Students must type this exactly (case-insensitive).</p>
            </div>
        `;
    } else if (qType === 'SHORT_ANSWER') {
        html = `
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Grading Rubric / Expected Answer</label>
                <textarea id="sa_rubric" rows="2" class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary" placeholder="Keywords or concepts expected"></textarea>
                <p class="text-[10px] text-warning font-semibold mt-1">Short answers require manual evaluation by a teacher.</p>
            </div>
        `;
    } else if (qType === 'DESCRIPTIVE') {
        html = `
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Grading Rubric</label>
                <textarea id="desc_rubric" rows="3" class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary" placeholder="Extensive rubric for manual evaluation"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4 mt-3">
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Word Limit</label>
                    <input type="number" id="desc_word_limit" min="10" value="500" class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Evaluation Method</label>
                    <select id="desc_eval_method" class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary">
                        <option value="MANUAL">Manual Evaluation Only</option>
                        <option value="AI_ASSISTED" disabled>AI Assisted (Pending Provider)</option>
                    </select>
                </div>
            </div>
            <p class="text-[10px] text-warning font-semibold mt-1">Descriptive answers require manual evaluation by a teacher.</p>
        `;
    } else if (qType === 'NUMERICAL') {
        html = `
            <div class="grid grid-cols-3 gap-4">
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Correct Value</label>
                    <input type="number" step="any" id="num_correct" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Tolerance (±)</label>
                    <input type="number" step="any" id="num_tolerance" value="0" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider tracking-wider text-on-surface-variant mb-1">Unit (Optional)</label>
                    <input type="text" id="num_unit" placeholder="e.g. kg, m/s" class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Ensure these functions override any existing ones in code.html/code.js
window.openQuestionModal = function() {
    document.getElementById('edit_qid').value = '';
    document.getElementById('questionModalTitle').textContent = 'Add New Question';
    document.getElementById('questionForm').reset();
    document.getElementById('q_type').value = 'MCQ';
    document.getElementById('q_category').value = 'Computer Science & IT';
    renderDynamicQuestionFields();
    document.getElementById('questionModal').classList.remove('hidden');
}

window.editQuestion = function(qid) {
    const q = globalQuestions.find(item => item.qid === qid);
    if (!q) return;

    document.getElementById('edit_qid').value = q.qid;
    document.getElementById('questionModalTitle').textContent = `Edit Question #${q.qid}`;
    document.getElementById('q_category').value = q.category || 'General';
    document.getElementById('q_text').value = q.question;
    document.getElementById('q_type').value = q.type || 'MCQ';
    document.getElementById('q_marks').value = q.marks || 1;
    document.getElementById('q_negative_marks').value = q.negative_marks || 0;
    document.getElementById('q_difficulty').value = q.difficulty || 'medium';
    
    renderDynamicQuestionFields();
    
    setTimeout(() => {
        const type = q.type || 'MCQ';
        const content = q.content || {};
        
        if (type === 'MCQ') {
            document.getElementById('q_optA').value = q.optionA || '';
            document.getElementById('q_optB').value = q.optionB || '';
            document.getElementById('q_optC').value = q.optionC || '';
            document.getElementById('q_optD').value = q.optionD || '';
            document.getElementById('q_correct').value = q.correct_answer || 'A';
        } else if (type === 'MULTIPLE_SELECT') {
            document.getElementById('ms_opt1').value = content.options?.[0] || '';
            document.getElementById('ms_opt2').value = content.options?.[1] || '';
            document.getElementById('ms_opt3').value = content.options?.[2] || '';
            document.getElementById('ms_opt4').value = content.options?.[3] || '';
            const correct = content.correct_answers || [];
            document.getElementById('ms_chk1').checked = correct.includes("1");
            document.getElementById('ms_chk2').checked = correct.includes("2");
            document.getElementById('ms_chk3').checked = correct.includes("3");
            document.getElementById('ms_chk4').checked = correct.includes("4");
        } else if (type === 'TRUE_FALSE') {
            document.getElementById('tf_correct').value = q.correct_answer || 'TRUE';
        } else if (type === 'FILL_BLANK') {
            document.getElementById('fb_correct').value = q.correct_answer || '';
        } else if (type === 'SHORT_ANSWER') {
            document.getElementById('sa_rubric').value = content.rubric || '';
        } else if (type === 'DESCRIPTIVE') {
            document.getElementById('desc_rubric').value = content.rubric || '';
            document.getElementById('desc_word_limit').value = content.word_limit || 500;
        } else if (type === 'NUMERICAL') {
            document.getElementById('num_correct').value = content.correct_value || '';
            document.getElementById('num_tolerance').value = content.tolerance || 0;
            document.getElementById('num_unit').value = content.unit || '';
        }
    }, 50);

    document.getElementById('questionModal').classList.remove('hidden');
}

window.handleSaveQuestion = async function(e) {
    e.preventDefault();
    const qid = document.getElementById('edit_qid').value;
    const qType = document.getElementById('q_type').value;
    
    let payload = {
        type: qType,
        category: document.getElementById('q_category').value.trim() || 'General',
        question: document.getElementById('q_text').value.trim(),
        marks: parseInt(document.getElementById('q_marks').value) || 1,
        negative_marks: parseFloat(document.getElementById('q_negative_marks').value) || 0,
        difficulty: document.getElementById('q_difficulty').value || 'medium',
        content: {},
        correct_answer: ''
    };

    if (qType === 'MCQ') {
        payload.optionA = document.getElementById('q_optA').value.trim();
        payload.optionB = document.getElementById('q_optB').value.trim();
        payload.optionC = document.getElementById('q_optC').value.trim();
        payload.optionD = document.getElementById('q_optD').value.trim();
        payload.correct_answer = document.getElementById('q_correct').value;
    } else if (qType === 'MULTIPLE_SELECT') {
        payload.content.options = [
            document.getElementById('ms_opt1').value.trim(),
            document.getElementById('ms_opt2').value.trim(),
            document.getElementById('ms_opt3').value.trim(),
            document.getElementById('ms_opt4').value.trim()
        ];
        let correct = [];
        if (document.getElementById('ms_chk1').checked) correct.push("1");
        if (document.getElementById('ms_chk2').checked) correct.push("2");
        if (document.getElementById('ms_chk3').checked) correct.push("3");
        if (document.getElementById('ms_chk4').checked) correct.push("4");
        payload.content.correct_answers = correct;
        
        if (correct.length === 0) {
            showToast('Please select at least one correct answer.', 'error');
            return;
        }
    } else if (qType === 'TRUE_FALSE') {
        payload.correct_answer = document.getElementById('tf_correct').value;
    } else if (qType === 'FILL_BLANK') {
        payload.correct_answer = document.getElementById('fb_correct').value.trim();
    } else if (qType === 'SHORT_ANSWER') {
        payload.content.rubric = document.getElementById('sa_rubric').value.trim();
    } else if (qType === 'DESCRIPTIVE') {
        payload.content.rubric = document.getElementById('desc_rubric').value.trim();
        payload.content.word_limit = parseInt(document.getElementById('desc_word_limit').value) || 500;
        payload.content.eval_method = document.getElementById('desc_eval_method').value;
    } else if (qType === 'NUMERICAL') {
        payload.content.correct_value = parseFloat(document.getElementById('num_correct').value);
        payload.content.tolerance = parseFloat(document.getElementById('num_tolerance').value) || 0;
        payload.content.unit = document.getElementById('num_unit').value.trim();
    }

    try {
        const url = qid ? `/api/admin/questions/${qid}` : '/api/admin/questions';
        const method = qid ? 'PUT' : 'POST';
        const res = await fetchApi(url, { method, body: JSON.stringify(payload) });

        if (res.ok) {
            closeQuestionModal();
            showToast(qid ? 'Question updated successfully.' : 'Question added successfully.', 'success');
            await fetchQuestions();
            if (typeof fetchAnalytics === 'function') await fetchAnalytics();
        } else {
            const data = await res.json();
            showToast(data.message || 'Failed to save question.', 'error');
        }
    } catch (err) {
        showToast('Server error saving question.', 'error');
    }
}

// Rewrite renderQuestions to handle polymorphic types beautifully
window.renderQuestions = function() {
    const container = document.getElementById('questionsContainer');
    if (!container) return;
    
    const catFilter = document.getElementById('questionCategoryFilter') ? document.getElementById('questionCategoryFilter').value : 'ALL';
    const search = document.getElementById('questionSearchInput') ? document.getElementById('questionSearchInput').value.toLowerCase().trim() : '';
    // Optional type filter if we add one later
    const typeFilter = document.getElementById('questionTypeFilter') ? document.getElementById('questionTypeFilter').value : 'ALL';

    const filtered = globalQuestions.filter(q => {
        const matchCat = catFilter === 'ALL' || (q.category && q.category === catFilter);
        const matchSearch = !search || (q.question && q.question.toLowerCase().includes(search));
        const matchType = typeFilter === 'ALL' || (q.type && q.type === typeFilter);
        return matchCat && matchSearch && matchType;
    });

    if (filtered.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-on-surface-variant text-xs bg-surface-container-low rounded-2xl border border-outline-variant/20">No questions found matching criteria. Click "New Question" to add one.</div>`;
        return;
    }

    container.innerHTML = '';
    filtered.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'bg-surface-container-low rounded-2xl p-6 shadow-sm border border-outline-variant/20 space-y-4';
        
        const qType = q.type || 'MCQ';
        
        let typeBadgeClass = 'bg-primary-container text-on-primary-container';
        if (qType === 'DESCRIPTIVE' || qType === 'SHORT_ANSWER') typeBadgeClass = 'bg-tertiary-container text-on-tertiary-container';
        if (qType === 'MULTIPLE_SELECT') typeBadgeClass = 'bg-secondary-container text-on-secondary-container';
        if (qType === 'NUMERICAL') typeBadgeClass = 'bg-warning-container text-warning';

        let bottomHtml = '';
        if (qType === 'MCQ') {
            const opts = [
                { key: 'A', text: q.optionA }, { key: 'B', text: q.optionB },
                { key: 'C', text: q.optionC }, { key: 'D', text: q.optionD }
            ];
            bottomHtml = `<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">` + opts.map(o => {
                const isCorrect = o.key === q.correct_answer;
                const pillClass = isCorrect ? 'bg-success-container text-success font-bold border border-success/30' : 'bg-surface-container-low text-on-surface border border-outline-variant/20';
                return `<div class="flex items-center gap-2 p-2.5 rounded-xl ${pillClass} text-xs">
                    <span class="font-bold w-5 h-5 rounded-full bg-surface-container-low flex items-center justify-center text-[10px]">${o.key}</span>
                    <span class="truncate">${o.text || '-'}</span>
                    ${isCorrect ? '<span class="material-symbols-outlined text-xs ml-auto">check_circle</span>' : ''}
                </div>`;
            }).join('') + `</div>`;
        } else if (qType === 'MULTIPLE_SELECT') {
            const content = q.content || {};
            const options = content.options || [];
            const correct = content.correct_answers || [];
            bottomHtml = `<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">` + options.map((opt, i) => {
                const isCorrect = correct.includes(String(i+1));
                const pillClass = isCorrect ? 'bg-success-container text-success font-bold border border-success/30' : 'bg-surface-container-low text-on-surface border border-outline-variant/20';
                return `<div class="flex items-center gap-2 p-2.5 rounded-xl ${pillClass} text-xs">
                    <span class="font-bold w-5 h-5 rounded-md bg-surface-container-low flex items-center justify-center text-[10px]">${i+1}</span>
                    <span class="truncate">${opt || '-'}</span>
                    ${isCorrect ? '<span class="material-symbols-outlined text-xs ml-auto">check_box</span>' : ''}
                </div>`;
            }).join('') + `</div>`;
        } else if (qType === 'TRUE_FALSE') {
            bottomHtml = `<div class="p-3 bg-success-container/30 text-success rounded-xl text-xs font-bold border border-success/20 inline-block mt-2">Correct Answer: ${q.correct_answer || 'TRUE'}</div>`;
        } else if (qType === 'FILL_BLANK') {
            bottomHtml = `<div class="p-3 bg-surface-container-low text-on-surface rounded-xl text-xs font-semibold border border-outline-variant/20 inline-block mt-2">Expected: ${q.correct_answer || ''}</div>`;
        } else if (qType === 'SHORT_ANSWER' || qType === 'DESCRIPTIVE') {
            const content = q.content || {};
            bottomHtml = `<div class="p-3 bg-surface-container-low text-on-surface-variant rounded-xl text-xs border border-outline-variant/20 mt-2 italic">
                <span class="font-bold not-italic mb-1 block">Grading Rubric:</span>
                ${content.rubric || 'No rubric provided.'}
                ${qType === 'DESCRIPTIVE' ? `<br><span class="font-bold not-italic block mt-2">Word Limit: ${content.word_limit || 500}</span>` : ''}
            </div>`;
        } else if (qType === 'NUMERICAL') {
            const content = q.content || {};
            bottomHtml = `<div class="flex gap-4 mt-2">
                <div class="p-3 bg-surface-container-low rounded-xl text-xs font-bold border border-outline-variant/20">Value: ${content.correct_value}</div>
                <div class="p-3 bg-surface-container-low rounded-xl text-xs border border-outline-variant/20">Tolerance: ±${content.tolerance || 0}</div>
                ${content.unit ? `<div class="p-3 bg-surface-container-low rounded-xl text-xs border border-outline-variant/20">Unit: ${content.unit}</div>` : ''}
            </div>`;
        }

        card.innerHTML = `
            <div class="flex justify-between items-start gap-4">
                <div class="flex items-start gap-3">
                    <span class="w-7 h-7 rounded-lg bg-primary/10 text-primary font-bold text-xs flex items-center justify-center flex-shrink-0">Q${q.qid}</span>
                    <div>
                        <div class="flex flex-wrap items-center gap-2 mb-1">
                            <span class="px-2.5 py-0.5 rounded-full ${typeBadgeClass} text-[10px] font-bold uppercase tracking-wider">${qType.replace('_', ' ')}</span>
                            <span class="px-2.5 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant text-[10px] font-bold uppercase tracking-wider">${q.category || 'General'}</span>
                            <span class="text-[11px] text-on-surface-variant font-semibold">Marks: ${q.marks}</span>
                        </div>
                        <h3 class="text-sm font-bold text-on-surface mt-2">${q.question}</h3>
                    </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                    <button onclick="editQuestion(${q.qid})" class="p-1.5 text-on-surface-variant hover:text-primary rounded-lg hover:bg-surface-container cursor-pointer" title="Edit Question">
                        <span class="material-symbols-outlined text-lg">edit</span>
                    </button>
                    <button onclick="deleteQuestion(${q.qid})" class="p-1.5 text-on-surface-variant hover:text-error rounded-lg hover:bg-error-container/40 cursor-pointer" title="Delete Question">
                        <span class="material-symbols-outlined text-lg">delete</span>
                    </button>
                </div>
            </div>
            ${bottomHtml}
        `;
        container.appendChild(card);
    });
}
