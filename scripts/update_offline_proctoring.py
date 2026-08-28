import re

with open('frontend/live_examination/proctoring.js', 'r', encoding='utf-8') as f:
    js = f.read()

offline_logic = '''
        this.eventQueue = [];
        
        window.addEventListener('online', () => {
            this.flushEventQueue();
        });
'''
js = js.replace('this.bindEvents();', offline_logic + '\n        this.bindEvents();')

flush_logic = '''
    async flushEventQueue() {
        if (this.eventQueue.length === 0) return;
        
        console.log(`[PROCTORING] Flushing ${this.eventQueue.length} queued events...`);
        const queueCopy = [...this.eventQueue];
        this.eventQueue = [];
        
        for (const ev of queueCopy) {
            try {
                await fetchApi('/api/proctoring/event', {
                    method: 'POST',
                    body: JSON.stringify(ev)
                });
            } catch (e) {
                // If it fails again, push back
                this.eventQueue.push(ev);
            }
        }
    }
'''
js = js.replace('async recordEvent(eventType, severity', flush_logic + '\n    async recordEvent(eventType, severity')

record_logic = '''
        const payload = {
            exam_id: this.examId,
            event_type: eventType,
            severity: severity,
            metadata: metadata,
            timestamp: new Date().toISOString()
        };
        
        if (!navigator.onLine) {
            console.warn('[PROCTORING EVENT QUEUED - OFFLINE]');
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
'''
js = re.sub(r'try \{\s*await fetchApi.*?\}\s*catch\s*\(e\)\s*\{\s*console\.error.*?\}', record_logic.strip(), js, flags=re.DOTALL)

with open('frontend/live_examination/proctoring.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Added offline event queueing.")
