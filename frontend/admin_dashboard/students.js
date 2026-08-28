document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;
    
    // In a full implementation, this would load /api/admin/students
    document.getElementById('stat-tenants').textContent = '0';
    document.getElementById('stat-students').textContent = '0';
    document.getElementById('stat-exams').textContent = '0';
    
    document.getElementById('institutions-table-body').innerHTML = '<tr><td colspan="7" class="p-8 text-center text-on-surface-variant text-sm">Student management module active. API connection pending.</td></tr>';
});