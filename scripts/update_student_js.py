import re

with open('frontend/student_dashboard/code.html', 'r', encoding='utf-8') as f:
    html = f.read()

replacement = '''
                    const statusEl = document.getElementById('metric-status');
                    const certBtn = document.getElementById('viewCertificateBtn');
                    
                    if (result.status === 'PENDING_EVALUATION') {
                        if (avgEl) avgEl.innerHTML = '<span class="material-symbols-outlined text-[20px] animate-pulse">pending</span>';
                        if (recentScore) recentScore.textContent = 'PENDING';
                        if (recentGrade) {
                            recentGrade.textContent = '-';
                            recentGrade.className = 'text-2xl font-black text-warning';
                        }
                        if (recentStatus) {
                            recentStatus.textContent = 'EVALUATING';
                            recentStatus.className = 'text-2xl font-black text-warning';
                        }
                        if (recentBadge) recentBadge.textContent = 'Pending';
                        if (statusEl) statusEl.textContent = 'In Review';
                        if (certBtn) certBtn.classList.add('opacity-50', 'pointer-events-none');
                    } else {
                        if (avgEl) avgEl.textContent = String(pct);
                        if (recentScore) recentScore.textContent = `${pct}%`;
                        if (recentGrade) {
                            recentGrade.textContent = result.grade || 'A+';
                            recentGrade.className = 'text-2xl font-black text-primary';
                        }
                        if (recentStatus) {
                            recentStatus.textContent = result.status || 'PASSED';
                            recentStatus.className = `text-2xl font-black ${result.status === 'PASSED' ? 'text-emerald-600' : 'text-error'}`;
                        }
                        if (recentBadge) recentBadge.textContent = result.grade || 'A+';
                        if (statusEl) statusEl.textContent = 'Completed';
                        if (certBtn) certBtn.classList.remove('opacity-50', 'pointer-events-none');
                    }
'''

pattern = re.compile(r'const avgEl = document\.getElementById\(\'metric-avg-score\'\);.*?certBtn\.classList\.remove\(\'opacity-50\', \'pointer-events-none\'\);\s+\}', re.DOTALL)

html = pattern.sub(replacement.strip() + '\n                }', html)

with open('frontend/student_dashboard/code.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated student dashboard JS for PENDING_EVALUATION.")
