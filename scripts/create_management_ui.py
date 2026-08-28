import shutil
import re

# 1. Teachers
shutil.copy('frontend/admin_dashboard/super_admin.html', 'frontend/admin_dashboard/teachers.html')
with open('frontend/admin_dashboard/teachers.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('Super Admin Dashboard', 'Teacher Management')
html = html.replace('Super Admin Console', 'Teacher Directory')
html = html.replace('Manage multi-tenant institutions and platform-wide settings.', 'Manage instructors and their access permissions.')
html = html.replace('<script src="super_admin.js"></script>', '<script src="teachers.js"></script>')
html = html.replace('Total Tenants', 'Total Teachers')
html = html.replace('Registered Institutions', 'Instructor Directory')

with open('frontend/admin_dashboard/teachers.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('frontend/admin_dashboard/teachers.js', 'w', encoding='utf-8') as f:
    f.write('''document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;
    
    // In a full implementation, this would load /api/admin/teachers
    document.getElementById('stat-tenants').textContent = '0';
    document.getElementById('stat-students').textContent = '0';
    document.getElementById('stat-exams').textContent = '0';
    
    document.getElementById('institutions-table-body').innerHTML = '<tr><td colspan="7" class="p-8 text-center text-on-surface-variant text-sm">Teacher management module active. API connection pending.</td></tr>';
});''')

# 2. Students
shutil.copy('frontend/admin_dashboard/super_admin.html', 'frontend/admin_dashboard/students.html')
with open('frontend/admin_dashboard/students.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('Super Admin Dashboard', 'Student Management')
html = html.replace('Super Admin Console', 'Student Directory')
html = html.replace('Manage multi-tenant institutions and platform-wide settings.', 'Manage student accounts, approve registrations, and view profiles.')
html = html.replace('<script src="super_admin.js"></script>', '<script src="students.js"></script>')
html = html.replace('Total Tenants', 'Pending Approvals')
html = html.replace('Registered Institutions', 'Student Roster')

with open('frontend/admin_dashboard/students.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('frontend/admin_dashboard/students.js', 'w', encoding='utf-8') as f:
    f.write('''document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;
    
    // In a full implementation, this would load /api/admin/students
    document.getElementById('stat-tenants').textContent = '0';
    document.getElementById('stat-students').textContent = '0';
    document.getElementById('stat-exams').textContent = '0';
    
    document.getElementById('institutions-table-body').innerHTML = '<tr><td colspan="7" class="p-8 text-center text-on-surface-variant text-sm">Student management module active. API connection pending.</td></tr>';
});''')

print("Created Teacher and Student Management UIs.")
