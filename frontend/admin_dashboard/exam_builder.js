// exam_builder.js
let currentExamId = null;
let examData = null;
let allQuestions = [];
let builderSections = [];

// State for picker
let activeSectionIndex = null;
let selectedQuestionIds = new Set();

document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;

    const urlParams = new URLSearchParams(window.location.search);
    currentExamId = urlParams.get('exam_id');
    
    if (!currentExamId) {
        alert("No exam ID provided.");
        window.location.href = '../admin_examinations/code.html';
        return;
    }

    await loadExamData();
    await loadQuestionBank();
});

async function loadExamData() {
    try {
        const res = await fetchApi(`/api/admin/examinations/${currentExamId}/builder`);
        if (res.ok) {
            const data = await res.json();
            examData = data.exam;
            builderSections = data.sections || [];
            
            // Map legacy questions if any
            if (data.unsectioned_questions && data.unsectioned_questions.length > 0) {
                if (builderSections.length === 0) {
                    builderSections.push({
                        title: "Main Section",
                        description: "Default section for legacy questions",
                        time_limit_minutes: null,
                        marks_per_question: 1,
                        negative_marks_per_question: 0,
                        randomize_order: false,
                        questions: data.unsectioned_questions
                    });
                } else {
                    builderSections[0].questions.push(...data.unsectioned_questions);
                }
            }

            document.getElementById('headerTitle').textContent = `Builder: ${examData.title}`;
            document.getElementById('headerSubtitle').textContent = examData.exam_code;
            
            renderSections();
        } else {
            showToast('Failed to load exam data.', 'error');
        }
    } catch (e) {
        showToast('Server error.', 'error');
    }
}

async function loadQuestionBank() {
    try {
        const res = await fetchApi('/api/admin/questions');
        if (res.ok) {
            const data = await res.json();
            allQuestions = data.questions || [];
        }
    } catch (e) {
        console.error(e);
    }
}

function renderSections() {
    const container = document.getElementById('sectionsContainer');
    if (builderSections.length === 0) {
        container.innerHTML = `
            <div class="text-center py-16 bg-surface-container-lowest border border-outline-variant/30 border-dashed rounded-2xl">
                <span class="material-symbols-outlined text-4xl text-on-surface-variant/50 mb-3 block">view_agenda</span>
                <p class="text-sm font-semibold text-on-surface">No Sections Yet</p>
                <p class="text-xs text-on-surface-variant mt-1">Create a section to start adding questions.</p>
                <button onclick="addSection()" class="mt-4 px-4 py-2 bg-primary/10 text-primary rounded-xl text-xs font-bold hover:bg-primary/20">Add First Section</button>
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    builderSections.forEach((sec, idx) => {
        const secDiv = document.createElement('div');
        secDiv.className = 'bg-surface-container-lowest rounded-2xl border border-outline-variant/30 shadow-sm overflow-hidden';
        
        let questionsHtml = '';
        if (!sec.questions || sec.questions.length === 0) {
            questionsHtml = `<p class="text-xs text-on-surface-variant italic p-4 text-center">No questions added yet.</p>`;
        } else {
            questionsHtml = `<div class="divide-y divide-outline-variant/10">` + sec.questions.map((q, qIdx) => {
                return `
                    <div class="p-3 flex items-center justify-between hover:bg-surface-container-low transition-colors group">
                        <div class="flex items-center gap-3 overflow-hidden">
                            <span class="text-[10px] font-bold text-on-surface-variant bg-surface-container-high w-6 h-6 rounded flex items-center justify-center flex-shrink-0">${qIdx + 1}</span>
                            <div class="truncate">
                                <span class="text-xs font-bold text-primary mr-2">[Q${q.qid}]</span>
                                <span class="text-xs text-on-surface truncate">${q.question}</span>
                            </div>
                        </div>
                        <button onclick="removeQuestion(${idx}, ${qIdx})" class="p-1 text-on-surface-variant hover:text-error opacity-0 group-hover:opacity-100 transition-opacity">
                            <span class="material-symbols-outlined text-sm">close</span>
                        </button>
                    </div>
                `;
            }).join('') + `</div>`;
        }

        secDiv.innerHTML = `
            <div class="p-4 border-b border-outline-variant/20 bg-surface-container-low flex justify-between items-start">
                <div class="flex-1 mr-4 space-y-2">
                    <input type="text" value="${sec.title || ''}" onchange="updateSection(${idx}, 'title', this.value)" placeholder="Section Title" class="w-full bg-transparent font-bold text-sm text-on-surface border-b border-transparent focus:border-primary outline-none transition-colors px-1 py-0.5"/>
                    <input type="text" value="${sec.description || ''}" onchange="updateSection(${idx}, 'description', this.value)" placeholder="Optional instructions for this section..." class="w-full bg-transparent text-xs text-on-surface-variant border-b border-transparent focus:border-primary outline-none transition-colors px-1"/>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="openQuestionPicker(${idx})" class="px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-[11px] font-bold hover:bg-primary/20 flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">add_circle</span> Add Q's
                    </button>
                    <button onclick="deleteSection(${idx})" class="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/30 rounded-lg">
                        <span class="material-symbols-outlined text-base">delete</span>
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 border-b border-outline-variant/10 bg-surface-container-lowest">
                <div>
                    <label class="block text-[10px] uppercase font-bold text-on-surface-variant mb-1">Time Limit (Mins)</label>
                    <input type="number" value="${sec.time_limit_minutes || ''}" onchange="updateSection(${idx}, 'time_limit_minutes', this.value)" placeholder="None" class="w-full bg-surface-container-low text-xs rounded-lg py-1.5 px-2 border border-outline-variant/30 outline-none"/>
                </div>
                <div>
                    <label class="block text-[10px] uppercase font-bold text-on-surface-variant mb-1">Marks/Question</label>
                    <input type="number" value="${sec.marks_per_question || 1}" onchange="updateSection(${idx}, 'marks_per_question', this.value)" class="w-full bg-surface-container-low text-xs rounded-lg py-1.5 px-2 border border-outline-variant/30 outline-none"/>
                </div>
                <div>
                    <label class="block text-[10px] uppercase font-bold text-on-surface-variant mb-1">Negative Marks</label>
                    <input type="number" step="any" value="${sec.negative_marks_per_question || 0}" onchange="updateSection(${idx}, 'negative_marks_per_question', this.value)" class="w-full bg-surface-container-low text-xs rounded-lg py-1.5 px-2 border border-outline-variant/30 outline-none"/>
                </div>
                <div class="flex items-center gap-2 mt-4">
                    <input type="checkbox" id="rand_${idx}" ${sec.randomize_order ? 'checked' : ''} onchange="updateSection(${idx}, 'randomize_order', this.checked)" class="rounded text-primary"/>
                    <label for="rand_${idx}" class="text-[10px] font-bold text-on-surface-variant">Randomize Order</label>
                </div>
            </div>

            <div class="bg-surface">
                ${questionsHtml}
            </div>
        `;
        container.appendChild(secDiv);
    });
}

function addSection() {
    builderSections.push({
        title: `Section ${builderSections.length + 1}`,
        description: "",
        time_limit_minutes: null,
        marks_per_question: 1,
        negative_marks_per_question: 0,
        randomize_order: false,
        questions: []
    });
    renderSections();
}

function updateSection(idx, field, val) {
    if (field === 'time_limit_minutes' || field === 'marks_per_question' || field === 'negative_marks_per_question') {
        val = val === '' ? null : Number(val);
    }
    builderSections[idx][field] = val;
}

function deleteSection(idx) {
    if(confirm('Delete this section and remove its questions from the exam?')) {
        builderSections.splice(idx, 1);
        renderSections();
    }
}

function removeQuestion(secIdx, qIdx) {
    builderSections[secIdx].questions.splice(qIdx, 1);
    renderSections();
}

// ----------------------------------------------------
// QUESTION PICKER
// ----------------------------------------------------

function openQuestionPicker(secIdx) {
    activeSectionIndex = secIdx;
    selectedQuestionIds.clear();
    document.getElementById('pickerSectionName').textContent = builderSections[secIdx].title || `Section ${secIdx + 1}`;
    document.getElementById('questionPickerModal').classList.remove('hidden');
    renderPickerQuestions();
}

function closeQuestionPicker() {
    document.getElementById('questionPickerModal').classList.add('hidden');
    activeSectionIndex = null;
}

function renderPickerQuestions() {
    const container = document.getElementById('pickerQuestionsContainer');
    const search = document.getElementById('pickerSearch').value.toLowerCase().trim();
    const catFilter = document.getElementById('pickerCategory').value;
    const typeFilter = document.getElementById('pickerType').value;
    
    // Existing QIDs in current section to not show again or show as disabled
    const currentQids = new Set(builderSections[activeSectionIndex].questions.map(q => q.qid));

    const filtered = allQuestions.filter(q => {
        const matchSearch = !search || q.question.toLowerCase().includes(search);
        const matchCat = catFilter === 'ALL' || q.category === catFilter;
        const matchType = typeFilter === 'ALL' || q.type === typeFilter;
        return matchSearch && matchCat && matchType;
    });

    container.innerHTML = '';
    
    if (filtered.length === 0) {
        container.innerHTML = `<p class="text-center text-xs text-on-surface-variant p-4">No questions found.</p>`;
        return;
    }

    filtered.forEach(q => {
        const isAlreadyAdded = currentQids.has(q.qid);
        const isSelected = selectedQuestionIds.has(q.qid);
        
        const div = document.createElement('div');
        div.className = `flex items-start gap-3 p-3 rounded-xl border ${isSelected ? 'bg-primary/5 border-primary/40' : 'bg-surface border-outline-variant/20 hover:border-outline-variant/60'} cursor-pointer transition-colors ${isAlreadyAdded ? 'opacity-50 pointer-events-none' : ''}`;
        
        if(!isAlreadyAdded) {
            div.onclick = () => toggleQuestionSelection(q.qid);
        }

        div.innerHTML = `
            <div class="pt-1">
                ${isAlreadyAdded ? 
                    `<span class="material-symbols-outlined text-success text-lg">check_circle</span>` : 
                    `<input type="checkbox" ${isSelected ? 'checked' : ''} class="w-4 h-4 text-primary pointer-events-none"/>`
                }
            </div>
            <div class="flex-1 overflow-hidden">
                <div class="flex gap-2 items-center mb-1">
                    <span class="text-[10px] font-bold text-on-surface-variant bg-surface-container px-2 py-0.5 rounded-md">Q${q.qid}</span>
                    <span class="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-md uppercase tracking-wider">${q.type || 'MCQ'}</span>
                    <span class="text-[10px] font-semibold text-on-surface-variant truncate">${q.category || ''}</span>
                    ${isAlreadyAdded ? `<span class="ml-auto text-[10px] text-success font-bold">Already Added</span>` : ''}
                </div>
                <p class="text-xs text-on-surface line-clamp-2">${q.question}</p>
            </div>
        `;
        container.appendChild(div);
    });
    
    document.getElementById('pickerSelectedCount').textContent = selectedQuestionIds.size;
}

function toggleQuestionSelection(qid) {
    if (selectedQuestionIds.has(qid)) {
        selectedQuestionIds.delete(qid);
    } else {
        selectedQuestionIds.add(qid);
    }
    renderPickerQuestions();
}

function confirmQuestionSelection() {
    if (activeSectionIndex === null) return;
    
    // Add selected questions to section
    selectedQuestionIds.forEach(qid => {
        const qObj = allQuestions.find(q => q.qid === qid);
        if(qObj) {
            builderSections[activeSectionIndex].questions.push(qObj);
        }
    });
    
    closeQuestionPicker();
    renderSections();
}

// ----------------------------------------------------
// SAVE BUILDER
// ----------------------------------------------------

async function saveExamBuilder() {
    document.getElementById('saveStatus').textContent = 'Saving...';
    
    const payload = {
        sections: builderSections.map(sec => ({
            title: sec.title,
            description: sec.description,
            time_limit_minutes: sec.time_limit_minutes,
            marks_per_question: sec.marks_per_question,
            negative_marks_per_question: sec.negative_marks_per_question,
            randomize_order: sec.randomize_order,
            questions: sec.questions.map(q => q.qid)
        }))
    };

    try {
        const res = await fetchApi(`/api/admin/examinations/${currentExamId}/builder`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            document.getElementById('saveStatus').textContent = 'Saved successfully';
            setTimeout(() => document.getElementById('saveStatus').textContent = '', 3000);
            showToast('Exam structure saved.', 'success');
        } else {
            const data = await res.json();
            document.getElementById('saveStatus').textContent = 'Save failed';
            showToast(data.message || 'Failed to save', 'error');
        }
    } catch (e) {
        document.getElementById('saveStatus').textContent = 'Network error';
        showToast('Error saving.', 'error');
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

// --- Injected Builder Question Creator Logic ---
window.openBuilderQuestionCreator = function() {
    document.getElementById('questionPickerModal').classList.add('hidden');
    document.getElementById('questionModal').classList.remove('hidden');
    document.getElementById('questionForm').reset();
    document.getElementById('edit_qid').value = '';
    document.getElementById('questionModalTitle').textContent = 'Add New Question (To Bank)';
    if (typeof renderDynamicQuestionFields === 'function') {
        renderDynamicQuestionFields();
    }
};

window.closeQuestionModal = function() {
    document.getElementById('questionModal').classList.add('hidden');
    document.getElementById('questionPickerModal').classList.remove('hidden');
};

window.fetchQuestions = async function() {
    await loadQuestionBank();
    if (typeof renderPickerQuestions === 'function') {
        renderPickerQuestions();
    }
};
