import re
with open('frontend/landing page/code.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all href="../ and src="../ with href="./ and src="./
content = re.sub(r'(href|src)="\.\./', r'\1="./', content)
content = re.sub(r'url\([\'"]?\.\./', r'url("./', content)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Index generated successfully.")
