import re

with open('frontend/admin_examinations/code.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace(
    '''<button onclick="openAssignModal(${ex.exam_id}, '${ex.exam_code}')" class="p-1.5 rounded-lg text-primary hover:bg-primary/10 transition-colors" title="Assign Questions">
                            <span class="material-symbols-outlined text-base">format_list_bulleted</span>
                        </button>''',
    '''<button onclick="window.location.href='../admin_dashboard/exam_builder.html?exam_id=${ex.exam_id}'" class="p-1.5 rounded-lg text-primary hover:bg-primary/10 transition-colors" title="Build Examination (Sections & Questions)">
                            <span class="material-symbols-outlined text-base">handyman</span>
                        </button>'''
)

with open('frontend/admin_examinations/code.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Linked exam builder to examinations list.")
