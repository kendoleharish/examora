import re
code = open('backend/app.py','r',encoding='utf-8').read()
routes = re.findall(r'@app\.route\("([^"]+)"', code)
for r in routes: print(r)
