document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;
    
    if (admin.role !== 'SUPER_ADMIN') {
        alert("Unauthorized. Super Admin access only.");
        window.location.href = 'code.html';
        return;
    }
    
    loadInstitutions();
});

async function loadInstitutions() {
    try {
        const res = await fetchApi('/api/admin/institutions');
        if (res.ok) {
            const data = await res.json();
            renderInstitutions(data.institutions || []);
        }
    } catch (e) {
        console.error(e);
    }
}

function renderInstitutions(insts) {
    let totalStudents = 0;
    let totalExams = 0;
    
    const tbody = document.getElementById('institutions-table-body');
    tbody.innerHTML = '';
    
    insts.forEach(i => {
        totalStudents += i.student_count || 0;
        totalExams += i.exam_count || 0;
        
        const statusBadge = i.status === 'active' 
            ? `<span class="px-2 py-1 bg-primary/20 text-primary rounded-lg text-[10px] font-bold uppercase tracking-wider">Active</span>`
            : `<span class="px-2 py-1 bg-error-container text-on-error-container rounded-lg text-[10px] font-bold uppercase tracking-wider">Inactive</span>`;
            
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-surface-container-lowest transition-colors';
        tr.innerHTML = `
            <td class="p-4 text-sm font-mono text-on-surface-variant">#${i.institution_id}</td>
            <td class="p-4">
                <div class="font-bold text-sm text-on-surface">${i.institution_name}</div>
                <div class="text-[11px] text-on-surface-variant">${i.email || 'No email provided'}</div>
            </td>
            <td class="p-4">${statusBadge}</td>
            <td class="p-4 text-sm font-medium text-on-surface">${i.student_count || 0}</td>
            <td class="p-4 text-sm font-medium text-on-surface">${i.exam_count || 0}</td>
            <td class="p-4 text-xs text-on-surface-variant">${new Date(i.created_at).toLocaleDateString()}</td>
            <td class="p-4 text-right">
                <button onclick="toggleStatus(${i.institution_id}, '${i.status}')" class="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-lg hover:bg-surface-container" title="${i.status === 'active' ? 'Deactivate' : 'Activate'}">
                    <span class="material-symbols-outlined text-[18px]">${i.status === 'active' ? 'block' : 'check_circle'}</span>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    document.getElementById('stat-tenants').textContent = insts.length;
    document.getElementById('stat-students').textContent = totalStudents;
    document.getElementById('stat-exams').textContent = totalExams;
}

async function toggleStatus(id, currentStatus) {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    if (!confirm(`Are you sure you want to ${newStatus === 'active' ? 'activate' : 'deactivate'} this institution?`)) return;
    
    try {
        const res = await fetchApi(`/api/admin/institutions/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            loadInstitutions();
        } else {
            alert('Failed to update institution status.');
        }
    } catch(e) {
        console.error(e);
    }
}
