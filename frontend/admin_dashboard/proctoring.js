let exams = [];
let selectedExamId = null;
let proctoringSummary = [];
let allEvents = [];
let activeStudentId = null;

document.addEventListener('DOMContentLoaded', async () => {
    const admin = await requireAdminAuth({ redirectOnFail: true, updateUI: true });
    if (!admin) return;
    
    await loadExams();
    
    document.getElementById('examSelector').addEventListener('change', (e) => {
        selectedExamId = e.target.value;
        if (selectedExamId) {
            loadProctoringData();
        } else {
            resetView();
        }
    });
});

async function loadExams() {
    try {
        const res = await fetchApi('/api/admin/examinations');
        if (res.ok) {
            const data = await res.json();
            exams = data.examinations || [];
            const select = document.getElementById('examSelector');
            exams.forEach(ex => {
                const opt = document.createElement('option');
                opt.value = ex.exam_id;
                opt.textContent = `${ex.exam_code} - ${ex.title}`;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Failed to load exams", e);
    }
}

function resetView() {
    proctoringSummary = [];
    allEvents = [];
    activeStudentId = null;
    
    document.getElementById('metric-high').textContent = '0';
    document.getElementById('metric-students').textContent = '0';
    document.getElementById('metric-events').textContent = '0';
    document.getElementById('studentCountBadge').textContent = '0';
    
    document.getElementById('studentListContainer').innerHTML = `<p class="text-xs text-on-surface-variant text-center p-8">Select an examination first.</p>`;
    document.getElementById('eventTimelineContainer').innerHTML = `
        <div class="h-full flex flex-col items-center justify-center text-center">
            <span class="material-symbols-outlined text-4xl text-outline mb-3">timeline</span>
            <h3 class="text-sm font-bold text-on-surface mb-1">No student selected</h3>
            <p class="text-xs text-on-surface-variant">Select a student from the list to view their proctoring timeline.</p>
        </div>
    `;
    document.getElementById('activeStudentName').textContent = 'Event Timeline';
}

async function loadProctoringData() {
    if (!selectedExamId) return;
    
    try {
        const [summaryRes, eventsRes] = await Promise.all([
            fetchApi(`/api/admin/proctoring/summary/${selectedExamId}`),
            fetchApi(`/api/admin/proctoring/events/${selectedExamId}`)
        ]);
        
        if (summaryRes.ok && eventsRes.ok) {
            const sData = await summaryRes.json();
            const eData = await eventsRes.json();
            
            proctoringSummary = sData.summary || [];
            allEvents = eData.events || [];
            
            updateMetrics();
            renderStudentList();
            
            if (activeStudentId) {
                renderEventTimeline();
            } else {
                document.getElementById('eventTimelineContainer').innerHTML = `
                    <div class="h-full flex flex-col items-center justify-center text-center">
                        <span class="material-symbols-outlined text-4xl text-outline mb-3">timeline</span>
                        <h3 class="text-sm font-bold text-on-surface mb-1">Select a student</h3>
                        <p class="text-xs text-on-surface-variant">Click on a student to review their events.</p>
                    </div>
                `;
            }
        }
    } catch (e) {
        console.error("Failed to load proctoring data", e);
    }
}

function updateMetrics() {
    const totalStudents = proctoringSummary.length;
    let highEvents = 0;
    let totalEvents = allEvents.length;
    
    proctoringSummary.forEach(s => {
        highEvents += Number(s.high_severity || 0);
    });
    
    document.getElementById('metric-high').textContent = highEvents;
    document.getElementById('metric-students').textContent = totalStudents;
    document.getElementById('metric-events').textContent = totalEvents;
    document.getElementById('studentCountBadge').textContent = totalStudents;
}

function renderStudentList() {
    const container = document.getElementById('studentListContainer');
    container.innerHTML = '';
    
    if (proctoringSummary.length === 0) {
        container.innerHTML = `<p class="text-xs text-on-surface-variant text-center p-8">No proctoring events recorded for this exam yet.</p>`;
        return;
    }
    
    proctoringSummary.forEach(s => {
        const isActive = s.student_id === activeStudentId;
        const div = document.createElement('div');
        div.className = `p-4 border-b border-outline-variant/10 cursor-pointer transition-colors ${isActive ? 'bg-primary/10 border-l-4 border-l-primary' : 'hover:bg-surface-container-low border-l-4 border-l-transparent'}`;
        div.onclick = () => selectStudent(s.student_id, s.student_name);
        
        let severityBadge = '';
        if (s.high_severity > 0) {
            severityBadge = `<span class="text-[10px] font-bold bg-error text-on-error px-2 py-0.5 rounded-full">${s.high_severity} HIGH</span>`;
        } else if (s.medium_severity > 0) {
            severityBadge = `<span class="text-[10px] font-bold bg-warning-container text-warning px-2 py-0.5 rounded-full">${s.medium_severity} MED</span>`;
        }
        
        div.innerHTML = `
            <div class="flex justify-between items-start mb-1">
                <span class="font-bold text-sm text-on-surface">${s.student_name}</span>
                ${severityBadge}
            </div>
            <div class="text-[11px] text-on-surface-variant font-medium flex items-center justify-between">
                <span>@${s.username}</span>
                <span>${s.total_events} events</span>
            </div>
        `;
        container.appendChild(div);
    });
}

function selectStudent(studentId, name) {
    activeStudentId = studentId;
    document.getElementById('activeStudentName').textContent = `${name}'s Timeline`;
    renderStudentList();
    renderEventTimeline();
}

function renderEventTimeline() {
    const container = document.getElementById('eventTimelineContainer');
    if (!activeStudentId) return;
    
    const severityFilter = document.getElementById('severityFilter').value;
    
    let studentEvents = allEvents.filter(e => e.student_id === activeStudentId);
    if (severityFilter === 'HIGH') {
        studentEvents = studentEvents.filter(e => e.severity === 'HIGH');
    }
    
    container.innerHTML = '';
    
    if (studentEvents.length === 0) {
        container.innerHTML = `<p class="text-xs text-on-surface-variant text-center p-8">No matching events found.</p>`;
        return;
    }
    
    const timelineDiv = document.createElement('div');
    timelineDiv.className = 'relative border-l border-outline-variant/30 ml-4 py-2 space-y-6';
    
    studentEvents.forEach(e => {
        let icon = 'info';
        let colorClass = 'text-primary bg-primary-container';
        
        if (e.severity === 'HIGH') {
            icon = 'warning';
            colorClass = 'text-on-error bg-error';
        } else if (e.severity === 'MEDIUM') {
            icon = 'visibility';
            colorClass = 'text-warning bg-warning-container';
        }
        
        const timeStr = new Date(e.timestamp).toLocaleTimeString();
        
        const detailHtml = e.metadata && e.metadata.detail ? `<p class="text-xs text-on-surface-variant mt-1">${e.metadata.detail}</p>` : '';
        
        const item = document.createElement('div');
        item.className = 'relative pl-6';
        item.innerHTML = `
            <div class="absolute -left-3.5 top-0 w-7 h-7 rounded-full flex items-center justify-center ${colorClass} border-4 border-surface-container-lowest shadow-sm z-10">
                <span class="material-symbols-outlined text-[14px]">${icon}</span>
            </div>
            <div class="bg-surface-container-low p-3 rounded-xl border border-outline-variant/20 shadow-sm">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-xs font-bold uppercase tracking-wider text-on-surface">${e.event_type.replace(/_/g, ' ')}</span>
                    <span class="text-[10px] font-mono text-on-surface-variant bg-surface-container px-1.5 py-0.5 rounded">${timeStr}</span>
                </div>
                ${detailHtml}
            </div>
        `;
        timelineDiv.appendChild(item);
    });
    
    container.appendChild(timelineDiv);
}
