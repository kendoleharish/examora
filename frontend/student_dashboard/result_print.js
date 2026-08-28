/**
 * EXAMORA — Result Print Sheet & Certificate Logic
 * Fetches result data from /api/student/result/<result_id> and populates the professional A4 sheet.
 */

let currentResult = null;
let currentCertificate = null;

document.addEventListener('DOMContentLoaded', async () => {
    const student = await requireStudentAuth({ redirectOnFail: true, updateUI: false });
    if (!student) return;

    const params = new URLSearchParams(window.location.search);
    const resultId = params.get('result_id');

    if (!resultId) {
        document.getElementById('result-sheet').innerHTML =
            '<div class="p-12 text-center text-on-surface-variant"><p class="text-lg font-bold">No result ID specified.</p><p class="text-sm mt-2">Please access this page from your Results dashboard.</p></div>';
        return;
    }

    try {
        const resp = await fetchApi(`/api/student/result/${resultId}`);
        const data = await resp.json();

        if (!resp.ok || !data.success) {
            document.getElementById('result-sheet').innerHTML =
                `<div class="p-12 text-center text-on-surface-variant"><p class="text-lg font-bold">Result not found</p><p class="text-sm mt-2">${data.message || 'Unable to load this result.'}</p></div>`;
            return;
        }

        currentResult = data.result;
        currentCertificate = data.certificate;
        renderResultSheet(data.result, data.performance, data.certificate);
    } catch (e) {
        console.error('Failed to load result:', e);
    }
});

function renderResultSheet(result, performance, certificate) {
    // ── Institution branding ──
    const instName = document.getElementById('inst-name');
    instName.textContent = result.institution_name || 'EXAMORA';

    if (result.institution_logo) {
        const logoContainer = document.getElementById('inst-logo-container');
        const logoImg = document.getElementById('inst-logo');
        logoImg.src = result.institution_logo.startsWith('/') ? `${API_BASE}${result.institution_logo}` : result.institution_logo;
        logoContainer.classList.remove('hidden');
        logoContainer.classList.add('flex');
    }

    const instContact = document.getElementById('inst-contact');
    const contactParts = [];
    if (result.institution_email) contactParts.push(result.institution_email);
    if (result.institution_website) contactParts.push(result.institution_website);
    if (contactParts.length > 0) {
        instContact.textContent = contactParts.join(' | ');
        instContact.classList.remove('hidden');
    }

    // ── Document metadata ──
    document.getElementById('doc-id').textContent = `RES-${result.result_id || '000'}`;
    document.getElementById('doc-date').textContent = new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' });
    document.getElementById('gen-date').textContent = new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' });

    // ── Student details ──
    document.getElementById('s-name').textContent = result.student_name || '—';
    document.getElementById('s-email').textContent = result.student_email || '—';
    document.getElementById('s-inst').textContent = result.institution_name || '—';

    // ── Exam details ──
    document.getElementById('e-title').textContent = result.exam_title || '—';
    document.getElementById('e-category').textContent = result.exam_category || '—';
    document.getElementById('e-date').textContent = result.exam_date ? new Date(result.exam_date).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }) : '—';
    document.getElementById('e-duration').textContent = result.duration_minutes ? `${result.duration_minutes} min` : '—';

    // ── Result summary ──
    document.getElementById('r-score').textContent = result.score ?? '—';
    document.getElementById('r-total').textContent = result.total_marks ?? '—';
    document.getElementById('r-pct').textContent = result.percentage != null ? `${parseFloat(result.percentage).toFixed(1)}%` : '—%';
    document.getElementById('r-grade').textContent = result.grade || '—';

    const statusEl = document.getElementById('r-status');
    const isPassed = result.status === 'PASSED';
    statusEl.textContent = result.status || '—';
    statusEl.className = `inline-block px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-wider ${isPassed ? 'bg-success-container text-success' : 'bg-error-container text-error'}`;

    // ── Performance ──
    if (performance) {
        document.getElementById('p-total').textContent = performance.total_questions ?? '—';
        document.getElementById('p-attempted').textContent = performance.attempted ?? '—';
        document.getElementById('p-correct').textContent = performance.correct ?? '—';
        document.getElementById('p-incorrect').textContent = performance.incorrect ?? '—';
        document.getElementById('p-unanswered').textContent = performance.unanswered ?? '—';

        if (performance.negative_marks > 0) {
            document.getElementById('neg-marks-section').classList.remove('hidden');
            document.getElementById('neg-marks-val').textContent = performance.negative_marks;
        }
    }

    // ── Submission type ──
    const subEl = document.getElementById('r-submission');
    if (result.submission_type === 'AUTO_TIMEOUT') {
        subEl.textContent = 'Automatically Submitted — Time Expired';
    } else {
        subEl.textContent = 'Submitted by Student';
    }

    // ── Evaluation status ──
    const evalEl = document.getElementById('r-eval');
    if (result.evaluation_status === 'PENDING_EVALUATION') {
        evalEl.textContent = 'Pending Teacher Evaluation';
        document.getElementById('pending-warning').classList.remove('hidden');
    } else {
        evalEl.textContent = 'Complete';
    }

    // ── Certificate section ──
    if (certificate && certificate.available) {
        document.getElementById('cert-section').classList.remove('hidden');
        if (certificate.generated && certificate.certificate_id) {
            showCertificateGenerated(certificate.certificate_id, certificate.generated_at);
        }
    }

    // ── Apply institution branding colors ──
    if (result.primary_color) {
        applyBranding(result);
    }
}

function showCertificateGenerated(certId, generatedAt) {
    document.getElementById('cert-id-display').textContent = certId;
    const btn = document.getElementById('gen-cert-btn');
    btn.textContent = 'View Certificate';
    btn.onclick = openCertificate;

    document.getElementById('cert-btn').classList.remove('hidden');
    document.getElementById('cert-btn').classList.add('flex');

    // Footer verify info
    const footerVerify = document.getElementById('footer-verify');
    footerVerify.classList.remove('hidden');
    footerVerify.querySelector('strong').textContent = certId;
}

async function generateCertificate() {
    if (!currentResult) return;

    const btn = document.getElementById('gen-cert-btn');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const resp = await fetchApi(`/api/student/result/${currentResult.result_id}/certificate`, {
            method: 'POST'
        });
        const data = await resp.json();

        if (data.success) {
            currentCertificate = {
                available: true,
                generated: true,
                certificate_id: data.certificate_id,
                generated_at: data.generated_at
            };
            showCertificateGenerated(data.certificate_id, data.generated_at);
            showToast('Certificate generated successfully!', 'success');
        } else {
            showToast(data.message || 'Failed to generate certificate.', 'error');
            btn.disabled = false;
            btn.textContent = 'Generate Certificate';
        }
    } catch (e) {
        showToast('Network error generating certificate.', 'error');
        btn.disabled = false;
        btn.textContent = 'Generate Certificate';
    }
}

function openCertificate() {
    if (!currentResult || !currentCertificate || !currentCertificate.certificate_id) {
        showToast('No certificate available.', 'warning');
        return;
    }

    // Populate certificate overlay
    const r = currentResult;
    const c = currentCertificate;

    if (r.institution_logo) {
        document.getElementById('cert-inst-logo').src = r.institution_logo.startsWith('/') ? `${API_BASE}${r.institution_logo}` : r.institution_logo;
        document.getElementById('cert-inst-logo-container').classList.remove('hidden');
    }
    document.getElementById('cert-inst-name').textContent = r.institution_name || 'EXAMORA';
    document.getElementById('cert-student-name').textContent = r.student_name || '—';
    document.getElementById('cert-exam-title').textContent = r.exam_title || '—';
    document.getElementById('cert-grade').textContent = r.grade || '—';
    document.getElementById('cert-pct').textContent = r.percentage != null ? `${parseFloat(r.percentage).toFixed(1)}%` : '—%';
    document.getElementById('cert-status').textContent = r.status || '—';
    document.getElementById('cert-exam-date').textContent = r.exam_date ? new Date(r.exam_date).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }) : '—';
    document.getElementById('cert-cert-id').textContent = c.certificate_id;
    document.getElementById('cert-gen-date').textContent = c.generated_at ? new Date(c.generated_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }) : '—';

    document.getElementById('certificate-overlay').classList.remove('hidden');
}

function closeCertificate() {
    document.getElementById('certificate-overlay').classList.add('hidden');
}

function printResult() {
    // Hide certificate overlay if open
    document.getElementById('certificate-overlay').classList.add('hidden');
    window.print();
}

function printCertificate() {
    // For certificate printing, we open a new window with just the certificate content
    const certDoc = document.getElementById('certificate-doc');
    const printWin = window.open('', '_blank', 'width=800,height=1000');
    printWin.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>EXAMORA Certificate - ${currentCertificate?.certificate_id || ''}</title>
            <script src="https://cdn.tailwindcss.com"><\/script>
            <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet"/>
            <style>
                body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; }
                @media print {
                    @page { size: A4 landscape; margin: 15mm; }
                    body { padding: 0; }
                    .no-print { display: none !important; }
                }
            </style>
        </head>
        <body>
            ${certDoc.querySelector('.p-10').outerHTML}
            <div class="no-print" style="text-align:center; margin-top:20px;">
                <button onclick="window.print()" style="padding:10px 30px; background:#0050cb; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Print / Save as PDF</button>
            </div>
        </body>
        </html>
    `);
    printWin.document.close();
}
