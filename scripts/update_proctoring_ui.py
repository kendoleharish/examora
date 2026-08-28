import re

with open('frontend/live_examination/code.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add proctoring script tag
if 'proctoring.js' not in html:
    html = html.replace('<script src="../shared/auth.js"></script>', '<script src="../shared/auth.js"></script>\n<script src="proctoring.js"></script>')

# Add camera preview UI to the top nav
camera_html = '''
        <div class="flex items-center gap-3">
            <div id="proctoring-status" class="hidden items-center gap-1.5 px-3 py-1 bg-surface-container rounded-lg border border-outline-variant/30">
                <div class="w-2 h-2 rounded-full bg-error animate-pulse"></div>
                <span class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Recording</span>
            </div>
            <div class="w-12 h-12 rounded-lg bg-surface-container-highest overflow-hidden border-2 border-outline-variant/30 relative">
                <video id="proctor-video" class="w-full h-full object-cover" muted playsinline></video>
                <div class="absolute inset-0 flex items-center justify-center bg-surface-container-highest/80 backdrop-blur-sm" id="proctor-overlay">
                    <span class="material-symbols-outlined text-on-surface-variant text-sm">videocam_off</span>
                </div>
            </div>
'''
html = re.sub(r'<div class="flex items-center gap-3">\s*<div class="text-right hidden sm:block">', camera_html + '\n            <div class="text-right hidden sm:block">', html)

# Add security check overlay at the end of body
overlay_html = '''
<div id="security-check-overlay" class="fixed inset-0 z-50 bg-background flex flex-col items-center justify-center p-6">
    <div class="max-w-md w-full bg-surface-container-low p-8 rounded-3xl shadow-xl border border-outline-variant/30 text-center">
        <span class="material-symbols-outlined text-4xl text-primary mb-4">security</span>
        <h2 class="text-2xl font-bold text-on-surface mb-2">Security Check</h2>
        <p class="text-sm text-on-surface-variant mb-6">This examination is proctored. You must grant camera access and enter fullscreen mode to continue.</p>
        
        <div class="space-y-3 text-left mb-8">
            <div class="flex items-center gap-3 text-sm font-semibold text-on-surface">
                <span class="material-symbols-outlined text-primary">videocam</span> Camera Access Required
            </div>
            <div class="flex items-center gap-3 text-sm font-semibold text-on-surface">
                <span class="material-symbols-outlined text-primary">fullscreen</span> Fullscreen Mode Required
            </div>
            <div class="flex items-center gap-3 text-sm font-semibold text-error">
                <span class="material-symbols-outlined">warning</span> Face Verification: NOT CONFIGURED
            </div>
            <div class="flex items-center gap-3 text-sm font-semibold text-error">
                <span class="material-symbols-outlined">warning</span> Gaze Tracking: NOT CONFIGURED
            </div>
        </div>

        <button id="start-proctoring-btn" class="w-full py-3 bg-primary text-on-primary rounded-xl font-bold hover:bg-primary/90 transition-colors">
            Grant Permissions & Start
        </button>
        <p id="proctoring-error" class="text-error text-xs font-bold mt-3 hidden"></p>
    </div>
</div>
'''
html = html.replace('</body>', overlay_html + '\n</body>')

# Update initialization logic in script to wait for proctoring
init_logic = '''
    const urlParams = new URLSearchParams(window.location.search);
    const examId = urlParams.get('exam_id') || '1';

    // Set up proctoring check
    const securityOverlay = document.getElementById('security-check-overlay');
    const startProctoringBtn = document.getElementById('start-proctoring-btn');
    
    startProctoringBtn.addEventListener('click', async () => {
        window.proctoringSystem = new ExamoraProctoring(examId);
        const success = await window.proctoringSystem.initialize('proctor-video');
        if (success) {
            document.getElementById('proctor-overlay').classList.add('hidden');
            document.getElementById('proctoring-status').classList.remove('hidden');
            document.getElementById('proctoring-status').classList.add('flex');
            securityOverlay.classList.add('hidden');
            
            // Now start exam loading
            await loadExamData();
        } else {
            document.getElementById('proctoring-error').textContent = "Failed to access camera. Please check permissions.";
            document.getElementById('proctoring-error').classList.remove('hidden');
        }
    });

    // We defer the loading until after security check
    async function loadExamData() {
'''

# Find the start of exam loading logic and wrap it in loadExamData
pattern = re.compile(r"const urlParams = new URLSearchParams.*?let timerInterval = null;\s+try \{", re.DOTALL)
html = pattern.sub(init_logic + '\n    let questions = [];\n    let currentIndex = 0;\n    let answers = {};\n    let markedQuestions = new Set();\n    let remainingSeconds = 3600;\n    let timerInterval = null;\n\n        try {', html)

# Add closing brace for loadExamData() before autoSubmitExam function
html = html.replace('function autoSubmitExam() {', '}\n\n    function autoSubmitExam() {')

# Stop proctoring on submit
submit_logic = '''
            if (window.proctoringSystem) window.proctoringSystem.stop();
            window.location.href = '../student_dashboard/code.html';
'''
html = html.replace("window.location.href = '../student_dashboard/code.html';", submit_logic)

with open('frontend/live_examination/code.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated live examination with proctoring integration.")
