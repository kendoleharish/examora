import re

with open('frontend/admin_dashboard/super_admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace title and script
html = html.replace('EXAMORA | Admin Dashboard', 'EXAMORA | Super Admin Dashboard')
html = html.replace('<script src="code.js"></script>', '<script src="super_admin.js"></script>')

# Update Navigation to indicate Super Admin
nav_regex = re.compile(r'<nav class="space-y-2 mb-8">.*?</nav>', re.DOTALL)
new_nav = '''<nav class="space-y-2 mb-8">
            <a href="super_admin.html" class="flex items-center gap-3 px-4 py-3 rounded-xl bg-primary/10 text-primary font-bold transition-colors">
                <span class="material-symbols-outlined">corporate_fare</span> Institutions
            </a>
            <a href="code.html" class="flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface transition-colors font-medium">
                <span class="material-symbols-outlined">dashboard</span> Tenant View
            </a>
        </nav>'''
html = nav_regex.sub(new_nav, html)

main_content = '''
                <div class="mb-8 flex justify-between items-end">
                    <div>
                        <h2 class="text-3xl font-black text-on-surface tracking-tight mb-2">Super Admin Console</h2>
                        <p class="text-on-surface-variant font-medium">Manage multi-tenant institutions and platform-wide settings.</p>
                    </div>
                </div>

                <!-- Stats Row -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div class="p-6 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex items-center gap-4">
                        <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-primary text-2xl">corporate_fare</span>
                        </div>
                        <div>
                            <p class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-1">Total Tenants</p>
                            <h3 class="text-2xl font-black text-on-surface" id="stat-tenants">0</h3>
                        </div>
                    </div>
                    <div class="p-6 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex items-center gap-4">
                        <div class="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-secondary text-2xl">group</span>
                        </div>
                        <div>
                            <p class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-1">Total Students</p>
                            <h3 class="text-2xl font-black text-on-surface" id="stat-students">0</h3>
                        </div>
                    </div>
                    <div class="p-6 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex items-center gap-4">
                        <div class="w-12 h-12 rounded-xl bg-tertiary/10 flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-tertiary text-2xl">quiz</span>
                        </div>
                        <div>
                            <p class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-1">Total Exams</p>
                            <h3 class="text-2xl font-black text-on-surface" id="stat-exams">0</h3>
                        </div>
                    </div>
                </div>

                <!-- Institutions Table -->
                <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-2xl shadow-sm overflow-hidden mb-8">
                    <div class="p-6 border-b border-outline-variant/30 flex justify-between items-center bg-surface-container">
                        <h3 class="text-lg font-bold text-on-surface">Registered Institutions</h3>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="bg-surface-container-low border-b border-outline-variant/30">
                                    <th class="p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">ID</th>
                                    <th class="p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Institution Name</th>
                                    <th class="p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Status</th>
                                    <th class="p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Students</th>
                                    <th class="p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Exams</th>
                                    <th class="p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Registered</th>
                                    <th class="p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="institutions-table-body" class="divide-y divide-outline-variant/20">
                                <!-- JS Injected -->
                            </tbody>
                        </table>
                    </div>
                </div>
'''
pattern = re.compile(r'<div class="mb-8 flex justify-between items-end">.*?</main>', re.DOTALL)
html = pattern.sub(main_content + '\n            </div>\n        </main>', html)

with open('frontend/admin_dashboard/super_admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
