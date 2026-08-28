import re
import os

PROCTORING_JS = """
/**
 * EXAMORA PROCTORING SYSTEM
 * Real Client-Side AI Proctoring using face-api.js
 */

class ExamoraProctoring {
    constructor(examId) {
        this.examId = examId;
        this.isActive = false;
        
        // Modules
        this.cameraStream = null;
        this.videoElement = null;
        
        // Face AI State
        this.modelsLoaded = false;
        this.referenceDescriptor = null;
        
        // Anti-spam states
        this.lastFaceMissingTime = 0;
        this.faceMissingReported = false;
        
        this.lastAttentionDevTime = 0;
        this.attentionDevReported = false;
        
        this.lastMismatchTime = 0;
        
        this.detectionInterval = null;
        
        // Configurable Thresholds
        this.MISSING_FACE_TOLERANCE_MS = 3000;
        this.ATTENTION_TOLERANCE_MS = 3000;
        this.IDENTITY_THRESHOLD = 0.55; // Euclidean distance threshold
        
        this.bindEvents();
    }
    
    bindEvents() {
        document.addEventListener('visibilitychange', () => {
            if (!this.isActive) return;
            if (document.visibilityState === 'hidden') {
                this.recordEvent('TAB_SWITCH', 'MEDIUM', { detail: 'Student switched away from exam tab.' });
            } else if (document.visibilityState === 'visible') {
                this.recordEvent('TAB_RETURN', 'LOW', { detail: 'Student returned to exam tab.' });
            }
        });
        
        window.addEventListener('blur', () => {
            if (!this.isActive) return;
            this.recordEvent('WINDOW_BLUR', 'MEDIUM', { detail: 'Exam window lost focus.' });
        });
        
        document.addEventListener('fullscreenchange', () => {
            if (!this.isActive) return;
            if (!document.fullscreenElement) {
                this.recordEvent('FULLSCREEN_EXIT', 'HIGH', { detail: 'Student exited fullscreen mode.' });
            }
        });
    }
    
    async loadModels() {
        try {
            const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1/model/';
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
                faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
                faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
            ]);
            this.modelsLoaded = true;
            return true;
        } catch (e) {
            console.error('Failed to load Face AI models:', e);
            return false;
        }
    }
    
    async captureReferenceFace() {
        if (!this.modelsLoaded || !this.videoElement) return false;
        
        // Try multiple times to get a valid face
        for (let i = 0; i < 5; i++) {
            const detection = await faceapi.detectSingleFace(this.videoElement, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor();
                
            if (detection) {
                this.referenceDescriptor = detection.descriptor;
                return true;
            }
            await new Promise(r => setTimeout(r, 500));
        }
        return false;
    }
    
    async initialize(videoElementId) {
        this.videoElement = document.getElementById(videoElementId);
        
        try {
            // 1. Request Camera
            this.cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            if (this.videoElement) {
                this.videoElement.srcObject = this.cameraStream;
                // Wait for video to actually start playing before taking reference
                await new Promise((resolve) => {
                    this.videoElement.onloadedmetadata = () => {
                        this.videoElement.play();
                        resolve();
                    };
                });
            }
            
            // 2. Request Fullscreen
            try {
                await document.documentElement.requestFullscreen();
            } catch (e) {
                console.warn('Fullscreen request denied or not supported by browser.');
            }
            
            // 3. Load Models & Enroll Identity
            if (typeof faceapi !== 'undefined') {
                const loaded = await this.loadModels();
                if (loaded) {
                    const enrolled = await this.captureReferenceFace();
                    if (!enrolled) {
                        alert("Could not detect a clear face for identity verification. Make sure your face is clearly visible.");
                        // We will allow them to continue but log it.
                        this.recordEvent('IDENTITY_ENROLLMENT_FAILED', 'MEDIUM', { detail: 'Failed to capture reference face.' });
                    }
                }
            }
            
            this.isActive = true;
            this.startFaceMonitoring();
            return true;
        } catch (e) {
            console.error('Proctoring Initialization Failed:', e);
            if (e.name === 'NotAllowedError' || e.name === 'NotFoundError') {
                alert("Camera access is required for this examination. Please allow camera permissions and try again.");
            }
            return false;
        }
    }
    
    startFaceMonitoring() {
        if (!this.modelsLoaded) return;
        
        this.detectionInterval = setInterval(async () => {
            if (!this.isActive || !this.videoElement || this.videoElement.paused) return;
            
            const detections = await faceapi.detectAllFaces(this.videoElement, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptors();
                
            const now = Date.now();
            
            // 1. Check Face Presence
            if (detections.length === 0) {
                if (this.lastFaceMissingTime === 0) this.lastFaceMissingTime = now;
                
                if (now - this.lastFaceMissingTime >= this.MISSING_FACE_TOLERANCE_MS) {
                    if (!this.faceMissingReported) {
                        this.recordEvent('FACE_NOT_DETECTED', 'MEDIUM', { detail: 'Face not visible for sustained period.' });
                        this.faceMissingReported = true;
                    }
                }
                // Reset others
                this.lastAttentionDevTime = 0;
                this.attentionDevReported = false;
                return; 
            } else {
                if (this.faceMissingReported) {
                    this.recordEvent('FACE_DETECTED', 'LOW', { detail: 'Face returned to view.' });
                }
                this.lastFaceMissingTime = 0;
                this.faceMissingReported = false;
            }
            
            // 2. Check Multiple Faces
            if (detections.length > 1) {
                this.recordEvent('MULTIPLE_FACES', 'HIGH', { count: detections.length });
                // Reset others to avoid spam
                this.lastAttentionDevTime = 0;
                return;
            }
            
            const face = detections[0];
            
            // 3. Identity Verification
            if (this.referenceDescriptor) {
                const distance = faceapi.euclideanDistance(this.referenceDescriptor, face.descriptor);
                if (distance > this.IDENTITY_THRESHOLD) {
                    if (now - this.lastMismatchTime > 5000) { // Cooldown 5s
                        this.recordEvent('IDENTITY_MISMATCH', 'CRITICAL', { distance: distance.toFixed(2) });
                        this.lastMismatchTime = now;
                    }
                }
            }
            
            // 4. Attention/Gaze Monitoring (Simple Heuristic via Landmarks)
            // Nose vs jaw bounding to detect significant head turn
            const nose = face.landmarks.getNose();
            const jaw = face.landmarks.getJawOutline();
            
            if (nose.length > 0 && jaw.length > 0) {
                const nosePoint = nose[0]; // Top of nose
                const leftJaw = jaw[0];
                const rightJaw = jaw[jaw.length - 1];
                
                const distLeft = Math.abs(nosePoint.x - leftJaw.x);
                const distRight = Math.abs(nosePoint.x - rightJaw.x);
                
                const ratio = distLeft / (distRight + 0.001);
                
                // If ratio is extremely skewed, head is turned
                if (ratio > 3.0 || ratio < 0.33) {
                    if (this.lastAttentionDevTime === 0) this.lastAttentionDevTime = now;
                    if (now - this.lastAttentionDevTime >= this.ATTENTION_TOLERANCE_MS) {
                        if (!this.attentionDevReported) {
                            this.recordEvent('ATTENTION_DEVIATION', 'MEDIUM', { detail: 'Looking away from screen.' });
                            this.attentionDevReported = true;
                        }
                    }
                } else {
                    this.lastAttentionDevTime = 0;
                    this.attentionDevReported = false;
                }
            }
            
        }, 1000); // 1 FPS for performance
    }
    
    stop() {
        this.isActive = false;
        if (this.detectionInterval) clearInterval(this.detectionInterval);
        if (this.cameraStream) {
            this.cameraStream.getTracks().forEach(track => track.stop());
            this.cameraStream = null;
        }
        if (document.fullscreenElement) {
            document.exitFullscreen().catch(e => console.log(e));
        }
    }
    
    async recordEvent(eventType, severity = 'LOW', metadata = {}) {
        console.log(`[PROCTORING EVENT] ${eventType} (${severity})`, metadata);
        
        // Update live minimal indicator if present
        const statusEl = document.getElementById('live-proctor-status-text');
        if (statusEl) {
            if (eventType === 'FACE_NOT_DETECTED') statusEl.textContent = 'Face Missing';
            else if (eventType === 'MULTIPLE_FACES') statusEl.textContent = 'Multiple Faces';
            else if (eventType === 'IDENTITY_MISMATCH') statusEl.textContent = 'Identity Warning';
            else if (eventType === 'ATTENTION_DEVIATION') statusEl.textContent = 'Attention Warn';
            else if (eventType === 'FACE_DETECTED' || eventType === 'TAB_RETURN') statusEl.textContent = 'Monitoring Active';
        }
        
        try {
            await fetchApi('/api/proctoring/event', {
                method: 'POST',
                body: JSON.stringify({
                    exam_id: this.examId,
                    event_type: eventType,
                    severity: severity,
                    metadata: metadata
                })
            });
        } catch (e) {
            console.error('Failed to record proctoring event', e);
        }
    }
}

window.proctoringSystem = null;
"""

with open('frontend/live_examination/proctoring.js', 'w', encoding='utf-8') as f:
    f.write(PROCTORING_JS)
    
# Update code.html to include face-api.js script tag
with open('frontend/live_examination/code.html', 'r', encoding='utf-8') as f:
    html = f.read()
    
if 'face-api.js' not in html:
    html = html.replace('<script src="proctoring.js"></script>', '<script defer src="https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1/dist/face-api.js"></script>\n<script src="proctoring.js"></script>')

# Update the security check overlay text to show it IS configured
html = html.replace('<span class="material-symbols-outlined">warning</span> Face Verification: NOT CONFIGURED', '<span class="material-symbols-outlined text-primary">face</span> Face Verification: Active')
html = html.replace('<span class="material-symbols-outlined">warning</span> Gaze Tracking: NOT CONFIGURED', '<span class="material-symbols-outlined text-primary">visibility</span> Attention Monitoring: Active')

# Add minimal indicator next to Recording
indicator_html = '''
            <div id="proctoring-status" class="hidden items-center gap-1.5 px-3 py-1 bg-surface-container rounded-lg border border-outline-variant/30">
                <div class="w-2 h-2 rounded-full bg-error animate-pulse"></div>
                <span id="live-proctor-status-text" class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Monitoring Active</span>
            </div>
'''
html = re.sub(r'<div id="proctoring-status".*?</div>', indicator_html.strip(), html, flags=re.DOTALL)

with open('frontend/live_examination/code.html', 'w', encoding='utf-8') as f:
    f.write(html)
    
print("Updated proctoring UI to use face-api.js")
