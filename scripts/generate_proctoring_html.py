import re

with open('frontend/admin_examinations/code.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace title and headers
html = html.replace('EXAMORA | Admin Examinations', 'EXAMORA | Proctoring Dashboard')
html = html.replace('>Examinations Management<', '>Proctoring Dashboard<')
html = html.replace('>Create, manage, and monitor active examination instances.<', '>Monitor examination integrity events and review student compliance.<')
html = html.replace('<script src="code.js"></script>', '<script src="proctoring.js"></script>')

# Replace main content area
main_content = '''
                <!-- Stats Row -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="p-6 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm">
                        <p class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">High Severity Events</p>
                        <h3 class="text-3xl font-black text-error" id="metric-high">0</h3>
                    </div>
                    <div class="p-6 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm">
                        <p class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Total Monitored Students</p>
                        <h3 class="text-3xl font-black text-on-surface" id="metric-students">0</h3>
                    </div>
                    <div class="p-6 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm">
                        <p class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Total Events Logged</p>
                        <h3 class="text-3xl font-black text-primary" id="metric-events">0</h3>
                    </div>
                </div>
                
                <!-- Exam Selector -->
                <div class="mb-6 flex items-center justify-between">
                    <div>
                        <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-2">Select Examination</label>
                        <select id="examSelector" class="w-64 bg-surface-container-lowest border border-outline-variant/40 rounded-xl px-4 py-2 text-sm focus:border-primary outline-none">
                            <option value="">Select an exam...</option>
                        </select>
                    </div>
                    <button onclick="loadProctoringData()" class="px-4 py-2 bg-primary/10 text-primary rounded-xl font-bold text-sm hover:bg-primary/20 flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">refresh</span> Refresh
                    </button>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Left: Student List -->
                    <div class="col-span-1 border border-outline-variant/30 rounded-2xl overflow-hidden bg-surface-container-lowest shadow-sm flex flex-col min-h-[500px]">
                        <div class="bg-surface-container p-4 border-b border-outline-variant/30 flex justify-between items-center">
                            <h3 class="font-bold text-sm text-on-surface">Monitored Students</h3>
                            <span class="text-[10px] font-bold bg-primary/20 text-primary px-2 py-0.5 rounded-full" id="studentCountBadge">0</span>
                        </div>
                        <div class="flex-1 overflow-y-auto" id="studentListContainer">
                            <p class="text-xs text-on-surface-variant text-center p-8">Select an examination first.</p>
                        </div>
                    </div>
                    
                    <!-- Right: Event Timeline -->
                    <div class="col-span-1 lg:col-span-2 border border-outline-variant/30 rounded-2xl overflow-hidden bg-surface-container-lowest shadow-sm flex flex-col">
                        <div class="bg-surface-container p-4 border-b border-outline-variant/30 flex justify-between items-center">
                            <h3 class="font-bold text-sm text-on-surface" id="activeStudentName">Event Timeline</h3>
                            <div class="flex items-center gap-2" id="eventFilters">
                                <span class="text-[10px] font-bold text-on-surface-variant uppercase">Filter:</span>
                                <select id="severityFilter" onchange="renderEventTimeline()" class="bg-surface-container-lowest border border-outline-variant/40 rounded-lg px-2 py-1 text-[11px] font-bold outline-none">
                                    <option value="ALL">All Severities</option>
                                    <option value="HIGH">High Only</option>
                                </select>
                            </div>
                        </div>
                        <div class="flex-1 overflow-y-auto p-6" id="eventTimelineContainer">
                            <div class="h-full flex flex-col items-center justify-center text-center">
                                <span class="material-symbols-outlined text-4xl text-outline mb-3">timeline</span>
                                <h3 class="text-sm font-bold text-on-surface mb-1">No student selected</h3>
                                <p class="text-xs text-on-surface-variant">Select a student from the list to view their proctoring timeline.</p>
                            </div>
                        </div>
                    </div>
                </div>
'''

pattern = re.compile(r'<!-- Stats Row -->.*?</div>\s*</div>\s*</div>\s*</main>', re.DOTALL)
html = pattern.sub(main_content + '\n            </div>\n        </main>', html)

with open('frontend/admin_dashboard/proctoring.html', 'w', encoding='utf-8') as f:
    f.write(html)
