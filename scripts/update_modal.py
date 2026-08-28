import re

with open('frontend/admin_dashboard/code.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_modal = '''
<!-- Question Add/Edit Modal -->
<div id="questionModal" class="hidden fixed inset-0 z-[60] flex items-center justify-center bg-on-surface/40 backdrop-blur-sm p-4">
    <div class="bg-surface-container-lowest w-full max-w-2xl rounded-2xl p-6 shadow-2xl border border-outline-variant/30 max-h-[90vh] overflow-y-auto flex flex-col">
        <div class="flex justify-between items-center mb-6 pb-4 border-b border-outline-variant/20">
            <div>
                <h3 class="text-lg font-bold text-on-surface" id="questionModalTitle">Add New Question</h3>
                <p class="text-xs text-on-surface-variant">Polymorphic question engine</p>
            </div>
            <button onclick="closeQuestionModal()" class="p-1 rounded-lg text-on-surface-variant hover:bg-surface-container cursor-pointer">
                <span class="material-symbols-outlined">close</span>
            </button>
        </div>
        <form id="questionForm" onsubmit="handleSaveQuestion(event)" class="space-y-4 flex-1">
            <input type="hidden" id="edit_qid" value=""/>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1" for="q_type">Question Type</label>
                    <select id="q_type" onchange="renderDynamicQuestionFields()" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary">
                        <option value="MCQ">Multiple Choice (Single Correct)</option>
                        <option value="MULTIPLE_SELECT">Multiple Select (Multiple Correct)</option>
                        <option value="TRUE_FALSE">True / False</option>
                        <option value="FILL_BLANK">Fill in the Blanks</option>
                        <option value="SHORT_ANSWER">Short Answer</option>
                        <option value="DESCRIPTIVE">Descriptive / Essay</option>
                        <option value="NUMERICAL">Numerical Value</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1" for="q_category">Subject / Category</label>
                    <input type="text" id="q_category" list="categoryOptions" placeholder="e.g. Science" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/>
                    <datalist id="categoryOptions">
                        <option value="Computer Science & IT">
                        <option value="Mathematics">
                        <option value="Programming">
                    </datalist>
                </div>
            </div>

            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1" for="q_text">Question Statement</label>
                <textarea id="q_text" rows="3" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3.5 border border-outline-variant/40 outline-none focus:border-primary"></textarea>
            </div>
            
            <div id="dynamicQuestionFields" class="bg-surface-container p-4 rounded-xl space-y-4 border border-outline-variant/20">
                <!-- Injected via question_creator.js -->
            </div>

            <div class="grid grid-cols-3 gap-4">
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1" for="q_marks">Marks</label>
                    <input type="number" id="q_marks" min="1" max="100" value="1" required class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1" for="q_negative_marks">Negative Marks</label>
                    <input type="number" id="q_negative_marks" step="0.1" min="0" max="100" value="0" class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary"/>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1" for="q_difficulty">Difficulty</label>
                    <select id="q_difficulty" class="w-full bg-surface-container-low text-sm rounded-xl py-2.5 px-3 border border-outline-variant/40 outline-none focus:border-primary">
                        <option value="easy">Easy</option>
                        <option value="medium" selected>Medium</option>
                        <option value="hard">Hard</option>
                    </select>
                </div>
            </div>
            
            <div class="flex justify-end gap-3 pt-4 border-t border-outline-variant/20 mt-6">
                <button type="button" onclick="closeQuestionModal()" class="px-4 py-2 text-xs font-bold text-on-surface-variant hover:bg-surface-container rounded-xl">Cancel</button>
                <button type="submit" class="px-5 py-2 text-xs font-bold bg-primary text-on-primary rounded-xl hover:bg-primary-container cursor-pointer">Save Question</button>
            </div>
        </form>
    </div>
</div>
'''

pattern_modal = re.compile(r'<!-- Question Add/Edit Modal -->.*?<!-- Student Answer Sheet Modal -->', re.DOTALL)
html = pattern_modal.sub(new_modal.strip() + '\n\n<!-- Student Answer Sheet Modal -->', html)

with open('frontend/admin_dashboard/code.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated Question Modal in code.html")
