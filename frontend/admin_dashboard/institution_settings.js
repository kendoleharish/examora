let currentInstId = null;

document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;
    
    currentInstId = admin.institution_id;
    await loadSettings();
    
    // Bind color inputs
    const pColor = document.getElementById('primaryColor');
    const pHex = document.getElementById('primaryHex');
    pColor.addEventListener('input', e => { pHex.value = e.target.value; updatePreview(); });
    pHex.addEventListener('input', e => { pColor.value = e.target.value; updatePreview(); });
    
    const sColor = document.getElementById('secondaryColor');
    const sHex = document.getElementById('secondaryHex');
    sColor.addEventListener('input', e => { sHex.value = e.target.value; updatePreview(); });
    sHex.addEventListener('input', e => { sColor.value = e.target.value; updatePreview(); });
});

async function loadSettings() {
    try {
        const res = await fetchApi('/api/admin/institutions');
        if (res.ok) {
            const data = await res.json();
            // find current institution
            const inst = data.institutions.find(i => String(i.institution_id) === String(currentInstId));
            if (inst) {
                document.getElementById('instName').value = inst.institution_name || '';
                document.getElementById('instEmail').value = inst.email || '';
                document.getElementById('instPhone').value = inst.phone || '';
                document.getElementById('instWebsite').value = inst.website || '';
                
                document.getElementById('primaryColor').value = inst.primary_color || '#0061A4';
                document.getElementById('primaryHex').value = inst.primary_color || '#0061A4';
                document.getElementById('secondaryColor').value = inst.secondary_color || '#535F70';
                document.getElementById('secondaryHex').value = inst.secondary_color || '#535F70';
                
                updatePreview();
            }
        }
    } catch(e) {
        console.error("Failed to load settings", e);
    }
}

function updatePreview() {
    const p = document.getElementById('primaryHex').value;
    const s = document.getElementById('secondaryHex').value;
    
    const btn = document.getElementById('previewBtn');
    btn.style.backgroundColor = p;
    
    const outline = document.getElementById('previewOutline');
    outline.style.borderColor = s;
    outline.style.color = s;
}

async function saveSettings() {
    const btn = document.getElementById('saveBtn');
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">refresh</span> Saving...`;
    
    const errDiv = document.getElementById('error-message');
    const succDiv = document.getElementById('success-message');
    errDiv.classList.add('hidden');
    succDiv.classList.add('hidden');
    
    const payload = {
        institution_name: document.getElementById('instName').value,
        email: document.getElementById('instEmail').value,
        phone: document.getElementById('instPhone').value,
        website: document.getElementById('instWebsite').value,
        primary_color: document.getElementById('primaryHex').value,
        secondary_color: document.getElementById('secondaryHex').value
    };
    
    try {
        const res = await fetchApi(`/api/admin/institutions/${currentInstId}`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        if (res.ok && data.success) {
            succDiv.classList.remove('hidden');
            // update local storage branding if needed, or theme injection
        } else {
            errDiv.textContent = data.message || 'Failed to save settings.';
            errDiv.classList.remove('hidden');
        }
    } catch(e) {
        errDiv.textContent = 'Network error.';
        errDiv.classList.remove('hidden');
    }
    
    btn.disabled = false;
    btn.innerHTML = `<span class="material-symbols-outlined text-[18px]">save</span> Save Changes`;
}
