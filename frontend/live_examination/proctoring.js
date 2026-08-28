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
        this.IDENTITY_THRESHOLD = 0.55; 
        
        this.eventQueue = [];
        
        window.addEventListener('online', () => {
            this.flushEventQueue();
        });

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

    async initCamera(videoElementId) {
        this.videoElement = document.getElementById(videoElementId);
        try {
            this.cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            if (this.videoElement) {
                this.videoElement.srcObject = this.cameraStream;
                await new Promise((resolve) => {
                    this.videoElement.onloadedmetadata = () => {
                        this.videoElement.play();
                        resolve();
                    };
                });
            }
            return true;
        } catch (e) {
            console.error('Camera Init Failed:', e);
            throw new Error("Camera access is required. Please allow camera permissions and try again.");
        }
    }

    async initFullscreen() {
        try {
            await document.documentElement.requestFullscreen();
            // Verify fullscreen is active
            if (!document.fullscreenElement) {
                throw new Error("Fullscreen mode was not engaged.");
            }
            return true;
        } catch (e) {
            console.error('Fullscreen Init Failed:', e);
            throw new Error("Fullscreen request was denied. Please allow it.");
        }
    }

    async initFaceModels() {
        try {
            if (typeof faceapi === 'undefined') {
                throw new Error("Face API is not available.");
            }
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
            throw new Error("Failed to load Face Verification models.");
        }
    }
    
    async captureReferenceFace() {
        if (!this.modelsLoaded || !this.videoElement) {
            throw new Error("Models or video not loaded.");
        }
        
        // Try multiple times to get a valid face
        for (let i = 0; i < 5; i++) {
            const detection = await faceapi.detectSingleFace(this.videoElement, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor();
                
            if (detection) {
                this.referenceDescriptor = detection.descriptor;
                return true;
            }
            await new Promise(r => setTimeout(r, 1000));
        }
        throw new Error("Could not detect a clear face for identity verification. Please ensure you are visible and well-lit.");
    }

    startFaceMonitoring() {
        if (!this.modelsLoaded) throw new Error("Models not loaded.");
        
        this.isActive = true;
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
            
            // 4. Attention/Gaze Monitoring
            const nose = face.landmarks.getNose();
            const jaw = face.landmarks.getJawOutline();
            
            if (nose.length > 0 && jaw.length > 0) {
                const nosePoint = nose[0];
                const leftJaw = jaw[0];
                const rightJaw = jaw[jaw.length - 1];
                
                const distLeft = Math.abs(nosePoint.x - leftJaw.x);
                const distRight = Math.abs(nosePoint.x - rightJaw.x);
                
                const ratio = distLeft / (distRight + 0.001);
                
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
        }, 1000);
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
    
    async recordEvent(eventType, severity, metadata = {}) {
        const payload = {
            exam_id: this.examId,
            event_type: eventType,
            severity: severity,
            metadata: metadata,
            timestamp: new Date().toISOString()
        };
        
        if (!navigator.onLine) {
            this.eventQueue.push(payload);
            return;
        }

        try {
            await fetchApi('/api/proctoring/event', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        } catch (e) {
            console.error('Failed to record proctoring event, queueing...', e);
            this.eventQueue.push(payload);
        }
    }

    async flushEventQueue() {
        if (this.eventQueue.length === 0) return;
        
        console.log(`[PROCTORING] Flushing ${this.eventQueue.length} queued events...`);
        const queueCopy = [...this.eventQueue];
        this.eventQueue = [];
        
        for (const payload of queueCopy) {
            if (!navigator.onLine) {
                this.eventQueue.push(payload);
                continue;
            }
            try {
                await fetchApi('/api/proctoring/event', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
            } catch (e) {
                this.eventQueue.push(payload);
            }
        }
    }
}

window.proctoringSystem = null;
