import re

with open('frontend/admin_dashboard/institution_settings.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace title and script
html = html.replace('EXAMORA | Admin Dashboard', 'EXAMORA | Institution Settings')
html = html.replace('<script src="code.js"></script>', '<script src="institution_settings.js"></script>')

# Update Navigation to show settings active
nav_regex = re.compile(r'<nav class="space-y-2 mb-8">.*?</nav>', re.DOTALL)
new_nav = '''<nav class="space-y-2 mb-8">
            <a href="code.html" class="flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface transition-colors font-medium">
                <span class="material-symbols-outlined">dashboard</span> Dashboard
            </a>
            <a href="institution_settings.html" class="flex items-center gap-3 px-4 py-3 rounded-xl bg-primary/10 text-primary font-bold transition-colors">
                <span class="material-symbols-outlined">settings</span> Institution Settings
            </a>
        </nav>'''
html = nav_regex.sub(new_nav, html)

main_content = '''
                <div class="mb-8 flex justify-between items-end">
                    <div>
                        <h2 class="text-3xl font-black text-on-surface tracking-tight mb-2">Institution Settings</h2>
                        <p class="text-on-surface-variant font-medium">Manage your institution profile and branding colors.</p>
                    </div>
                    <button onclick="saveSettings()" id="saveBtn" class="px-6 py-2.5 bg-primary text-on-primary rounded-xl font-bold shadow-md hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">save</span> Save Changes
                    </button>
                </div>

                <div id="error-message" class="hidden p-4 rounded-xl bg-error-container text-on-error-container text-sm font-semibold mb-6"></div>
                <div id="success-message" class="hidden p-4 rounded-xl bg-primary-container text-primary text-sm font-semibold mb-6">Settings saved successfully.</div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <!-- Profile Information -->
                    <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-3xl p-8 shadow-sm">
                        <h3 class="text-lg font-bold text-on-surface mb-6 flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">domain</span> Profile Information
                        </h3>
                        
                        <div class="space-y-5">
                            <div>
                                <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-2 ml-1">Institution Name</label>
                                <input type="text" id="instName" class="w-full bg-surface-container-low border border-outline-variant/40 rounded-xl px-4 py-3 text-sm text-on-surface focus:border-primary outline-none">
                            </div>
                            <div>
                                <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-2 ml-1">Support Email</label>
                                <input type="email" id="instEmail" class="w-full bg-surface-container-low border border-outline-variant/40 rounded-xl px-4 py-3 text-sm text-on-surface focus:border-primary outline-none">
                            </div>
                            <div>
                                <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-2 ml-1">Contact Phone</label>
                                <input type="text" id="instPhone" class="w-full bg-surface-container-low border border-outline-variant/40 rounded-xl px-4 py-3 text-sm text-on-surface focus:border-primary outline-none">
                            </div>
                            <div>
                                <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-2 ml-1">Website URL</label>
                                <input type="url" id="instWebsite" class="w-full bg-surface-container-low border border-outline-variant/40 rounded-xl px-4 py-3 text-sm text-on-surface focus:border-primary outline-none">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Branding & White-Label -->
                    <div class="bg-surface-container-lowest border border-outline-variant/30 rounded-3xl p-8 shadow-sm">
                        <h3 class="text-lg font-bold text-on-surface mb-6 flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">palette</span> White-Label Branding
                        </h3>
                        
                        <div class="space-y-6">
                            <p class="text-sm text-on-surface-variant mb-4">Customize the primary and secondary colors used throughout the examination interface for your students.</p>
                            
                            <div>
                                <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-2 ml-1">Primary Color</label>
                                <div class="flex items-center gap-4">
                                    <input type="color" id="primaryColor" class="w-12 h-12 rounded cursor-pointer bg-transparent border-0 p-0">
                                    <input type="text" id="primaryHex" class="flex-1 bg-surface-container-low border border-outline-variant/40 rounded-xl px-4 py-3 text-sm font-mono text-on-surface focus:border-primary outline-none" placeholder="#000000">
                                </div>
                            </div>
                            
                            <div>
                                <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-2 ml-1">Secondary Color</label>
                                <div class="flex items-center gap-4">
                                    <input type="color" id="secondaryColor" class="w-12 h-12 rounded cursor-pointer bg-transparent border-0 p-0">
                                    <input type="text" id="secondaryHex" class="flex-1 bg-surface-container-low border border-outline-variant/40 rounded-xl px-4 py-3 text-sm font-mono text-on-surface focus:border-primary outline-none" placeholder="#000000">
                                </div>
                            </div>
                            
                            <div class="mt-8 p-6 rounded-2xl border border-outline-variant/30 bg-surface-container">
                                <h4 class="text-sm font-bold text-on-surface mb-3">Live Preview</h4>
                                <div class="space-y-3">
                                    <button class="w-full py-2 text-white rounded-lg font-bold text-sm shadow-md" id="previewBtn">Primary Button</button>
                                    <div class="w-full py-2 text-center rounded-lg font-bold text-sm border-2" id="previewOutline">Secondary Accent</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
'''
pattern = re.compile(r'<div class="mb-8 flex justify-between items-end">.*?</main>', re.DOTALL)
html = pattern.sub(main_content + '\n            </div>\n        </main>', html)

with open('frontend/admin_dashboard/institution_settings.html', 'w', encoding='utf-8') as f:
    f.write(html)
