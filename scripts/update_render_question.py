import re

with open('frontend/live_examination/code.html', 'r', encoding='utf-8') as f:
    html = f.read()

render_question_replacement = r'''
    function renderQuestion(index) {
        if (index < 0 || index >= questions.length) return;
        currentIndex = index;
        const q = questions[index];
        const qid = q.qid;
        const qType = q.type || 'MCQ';

        document.getElementById('q-category-badge').textContent = q.category || 'General';
        document.getElementById('q-number-badge').textContent = `Question ${index + 1}`;
        document.getElementById('q-marks-badge').textContent = `${q.marks || 1} Mark${q.marks > 1 ? 's' : ''}`;
        
        let typeBadge = document.getElementById('q-type-badge');
        if (!typeBadge) {
            typeBadge = document.createElement('span');
            typeBadge.id = 'q-type-badge';
            typeBadge.className = 'px-2.5 py-0.5 rounded-full bg-tertiary-container text-on-tertiary-container text-[11px] font-bold uppercase tracking-wider ml-2';
            document.getElementById('q-category-badge').after(typeBadge);
        }
        typeBadge.textContent = qType.replace('_', ' ');

        document.getElementById('question-text').textContent = q.question;

        const isMarked = markedQuestions.has(qid);
        const mrIcon = document.getElementById('mark-review-icon');
        const mrText = document.getElementById('mark-review-text');
        
        if (isMarked) {
            mrIcon.textContent = 'bookmark';
            mrIcon.classList.add('text-primary');
            mrText.textContent = 'Marked';
            mrText.classList.add('text-primary', 'font-bold');
        } else {
            mrIcon.textContent = 'bookmark_border';
            mrIcon.classList.remove('text-primary');
            mrText.textContent = 'Mark for Review';
            mrText.classList.remove('text-primary', 'font-bold');
        }

        const optionsContainer = document.getElementById('options-container');
        optionsContainer.innerHTML = '';
        
        const saveAnswer = (val) => {
            answers[qid] = val;
            try { localStorage.setItem('exam_answers', JSON.stringify(answers)); } catch (e) {}
            renderPalette();
            updateProgress();
            
            fetchApi(`/api/examinations/${examId}/autosave`, {
                method: 'POST',
                body: JSON.stringify({ qid: qid, selected_answer: val })
            }).then(r => r.json()).then(res => {
                if (res && res.message === 'EXAM_EXPIRED') {
                    clearInterval(timerInterval);
                    autoSubmitExam();
                }
            }).catch(console.error);
        };

        if (qType === 'MCQ') {
            const optionKeys = ['A', 'B', 'C', 'D'];
            optionKeys.forEach((key) => {
                const optVal = q[`option${key}`];
                if (optVal === undefined || optVal === null || optVal === '') return;
                const isSelected = answers[qid] === key;
                
                const label = document.createElement('label');
                label.className = `group relative flex items-center p-5 rounded-2xl border transition-all duration-200 cursor-pointer ${isSelected ? 'bg-primary/5 border-primary shadow-sm' : 'bg-surface-container-lowest border-outline-variant/40 hover:bg-surface-container-low hover:border-primary/40'}`;
                
                const input = document.createElement('input');
                input.type = 'radio'; input.name = `question_${qid}`; input.value = key; input.checked = isSelected; input.className = 'sr-only';
                input.addEventListener('change', () => {
                    saveAnswer(key);
                    renderQuestion(currentIndex);
                });
                
                const letterCircle = document.createElement('div');
                letterCircle.className = `w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm mr-5 shrink-0 transition-colors ${isSelected ? 'bg-primary text-on-primary shadow-sm' : 'bg-surface-container-high text-on-surface-variant group-hover:bg-primary/10 group-hover:text-primary'}`;
                letterCircle.textContent = key;
                
                const textSpan = document.createElement('div');
                textSpan.className = `text-base flex-1 font-medium ${isSelected ? 'text-primary font-semibold' : 'text-on-surface'}`;
                textSpan.textContent = optVal;
                
                const checkIcon = document.createElement('span');
                checkIcon.className = `material-symbols-outlined text-primary text-2xl ml-3 transition-opacity ${isSelected ? 'opacity-100' : 'opacity-0'}`;
                checkIcon.textContent = 'check_circle';
                
                label.append(input, letterCircle, textSpan, checkIcon);
                optionsContainer.appendChild(label);
            });
        } else if (qType === 'TRUE_FALSE') {
            ['TRUE', 'FALSE'].forEach((key) => {
                const isSelected = answers[qid] === key;
                const label = document.createElement('label');
                label.className = `group relative flex items-center p-5 rounded-2xl border transition-all duration-200 cursor-pointer ${isSelected ? 'bg-primary/5 border-primary shadow-sm' : 'bg-surface-container-lowest border-outline-variant/40 hover:bg-surface-container-low hover:border-primary/40'}`;
                
                const input = document.createElement('input');
                input.type = 'radio'; input.name = `question_${qid}`; input.value = key; input.checked = isSelected; input.className = 'sr-only';
                input.addEventListener('change', () => {
                    saveAnswer(key);
                    renderQuestion(currentIndex);
                });
                
                const textSpan = document.createElement('div');
                textSpan.className = `text-base flex-1 font-medium ${isSelected ? 'text-primary font-semibold' : 'text-on-surface'}`;
                textSpan.textContent = key === 'TRUE' ? 'True' : 'False';
                
                const checkIcon = document.createElement('span');
                checkIcon.className = `material-symbols-outlined text-primary text-2xl ml-3 transition-opacity ${isSelected ? 'opacity-100' : 'opacity-0'}`;
                checkIcon.textContent = 'check_circle';
                
                label.append(input, textSpan, checkIcon);
                optionsContainer.appendChild(label);
            });
        } else if (qType === 'MULTIPLE_SELECT') {
            const content = q.content || {};
            const options = content.options || [];
            const selectedArr = Array.isArray(answers[qid]) ? answers[qid] : [];
            
            options.forEach((optVal, idx) => {
                const valStr = String(idx + 1);
                const isSelected = selectedArr.includes(valStr);
                
                const label = document.createElement('label');
                label.className = `group relative flex items-center p-5 rounded-2xl border transition-all duration-200 cursor-pointer ${isSelected ? 'bg-primary/5 border-primary shadow-sm' : 'bg-surface-container-lowest border-outline-variant/40 hover:bg-surface-container-low hover:border-primary/40'}`;
                
                const input = document.createElement('input');
                input.type = 'checkbox'; input.name = `question_${qid}`; input.value = valStr; input.checked = isSelected; input.className = 'w-5 h-5 mr-5 rounded border-outline-variant/40 text-primary focus:ring-primary';
                
                input.addEventListener('change', (e) => {
                    let arr = Array.isArray(answers[qid]) ? [...answers[qid]] : [];
                    if (e.target.checked) arr.push(valStr);
                    else arr = arr.filter(v => v !== valStr);
                    saveAnswer(arr);
                    renderQuestion(currentIndex);
                });
                
                const textSpan = document.createElement('div');
                textSpan.className = `text-base flex-1 font-medium ${isSelected ? 'text-primary font-semibold' : 'text-on-surface'}`;
                textSpan.textContent = optVal;
                
                label.append(input, textSpan);
                optionsContainer.appendChild(label);
            });
            
            const hint = document.createElement('p');
            hint.className = 'text-xs text-on-surface-variant mt-2';
            hint.textContent = 'Select all that apply.';
            optionsContainer.appendChild(hint);
        } else if (qType === 'FILL_BLANK' || qType === 'SHORT_ANSWER' || qType === 'NUMERICAL') {
            const input = document.createElement('input');
            input.type = qType === 'NUMERICAL' ? 'number' : 'text';
            if(qType === 'NUMERICAL') input.step = 'any';
            input.className = 'w-full bg-surface-container-lowest text-on-surface rounded-xl py-4 px-5 border border-outline-variant/40 outline-none focus:border-primary text-lg transition-colors';
            input.placeholder = qType === 'NUMERICAL' ? 'Enter numerical value' : 'Type your answer here...';
            input.value = answers[qid] || '';
            
            let debounceTimeout;
            input.addEventListener('input', (e) => {
                const val = e.target.value;
                answers[qid] = val;
                clearTimeout(debounceTimeout);
                debounceTimeout = setTimeout(() => saveAnswer(val), 1000);
            });
            input.addEventListener('blur', (e) => saveAnswer(e.target.value));
            
            optionsContainer.appendChild(input);
            
            if (qType === 'NUMERICAL' && q.content && q.content.unit) {
                const unitSpan = document.createElement('span');
                unitSpan.className = 'absolute right-6 top-1/2 -translate-y-1/2 text-on-surface-variant font-bold';
                unitSpan.textContent = q.content.unit;
                
                const wrapper = document.createElement('div');
                wrapper.className = 'relative mt-2';
                wrapper.append(input, unitSpan);
                optionsContainer.innerHTML = '';
                optionsContainer.appendChild(wrapper);
            }
        } else if (qType === 'DESCRIPTIVE') {
            const textarea = document.createElement('textarea');
            textarea.rows = 8;
            textarea.className = 'w-full bg-surface-container-lowest text-on-surface rounded-xl py-4 px-5 border border-outline-variant/40 outline-none focus:border-primary text-base transition-colors leading-relaxed font-serif resize-y min-h-[150px]';
            textarea.placeholder = 'Type your descriptive answer here...';
            textarea.value = answers[qid] || '';
            
            const wordCount = document.createElement('div');
            wordCount.className = 'text-xs font-bold text-on-surface-variant text-right mt-2';
            const wordLimit = q.content ? (q.content.word_limit || 500) : 500;
            
            const updateCount = () => {
                const text = textarea.value.trim();
                const count = text ? text.split(/\\s+/).length : 0;
                wordCount.textContent = `${count} / ${wordLimit} words`;
                if (count > wordLimit) wordCount.classList.add('text-error');
                else wordCount.classList.remove('text-error');
            };
            updateCount();
            
            let debounceTimeout;
            textarea.addEventListener('input', (e) => {
                updateCount();
                const val = e.target.value;
                answers[qid] = val;
                clearTimeout(debounceTimeout);
                debounceTimeout = setTimeout(() => saveAnswer(val), 1500);
            });
            textarea.addEventListener('blur', (e) => saveAnswer(e.target.value));
            
            optionsContainer.append(textarea, wordCount);
        }

        prevBtn.disabled = index === 0;
        if (index === questions.length - 1) {
            nextBtn.innerHTML = `<span>Review & Submit</span><span class="material-symbols-outlined text-sm">send</span>`;
            nextBtn.classList.remove('bg-primary');
            nextBtn.classList.add('bg-error', 'hover:bg-error/90');
        } else {
            nextBtn.innerHTML = `<span>Next Question</span><span class="material-symbols-outlined text-sm">arrow_forward</span>`;
            nextBtn.classList.add('bg-primary');
            nextBtn.classList.remove('bg-error', 'hover:bg-error/90');
        }

        renderPalette();
    }
'''

pattern = re.compile(r'function renderQuestion\(index\) \{.*?renderPalette\(\);\n\s+\}', re.DOTALL)
html = pattern.sub(lambda match: render_question_replacement.strip(), html)

with open('frontend/live_examination/code.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated renderQuestion in live examination")
