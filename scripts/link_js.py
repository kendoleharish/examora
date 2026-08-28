import re

with open('frontend/admin_dashboard/code.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add script tag right after `<script src="../shared/auth.js"></script>`
if '<script src="question_creator.js"></script>' not in html:
    html = html.replace('<script src="../shared/auth.js"></script>', '<script src="../shared/auth.js"></script>\n<script src="question_creator.js"></script>')

with open('frontend/admin_dashboard/code.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Linked question_creator.js")
