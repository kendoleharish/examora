async function handleJoinExam(e) {
    e.preventDefault();
    
    const examCode = document.getElementById('examCode').value.trim();
    const fullName = document.getElementById('fullName').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const btn = document.getElementById('submitBtn');
    const errDiv = document.getElementById('error-message');
    
    errDiv.classList.add('hidden');
    
    if(!examCode || !fullName || !email || !password) {
        errDiv.textContent = 'All fields are required.';
        errDiv.classList.remove('hidden');
        return;
    }
    
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">refresh</span> <span>Joining...</span>`;
    
    try {
        const res = await fetchApi('/api/students/public_join', {
            method: 'POST',
            body: JSON.stringify({
                exam_code: examCode,
                full_name: fullName,
                email: email,
                password: password
            })
        });
        
        const data = await res.json();
        
        if (res.ok && data.success) {
            // Joined successfully, redirect to instructions
            window.location.href = `../exam_instructions/code.html?exam_id=${data.exam_id}`;
        } else {
            errDiv.textContent = data.message || 'Failed to join examination.';
            errDiv.classList.remove('hidden');
            btn.disabled = false;
            btn.innerHTML = origText;
        }
    } catch(err) {
        errDiv.textContent = 'Network error. Please try again.';
        errDiv.classList.remove('hidden');
        btn.disabled = false;
        btn.innerHTML = origText;
    }
}
