import re

with open('backend/services/metricas_factuais.py', 'r') as f:
    content = f.read()

content = content.replace("func.case(", "case(")
if "from sqlalchemy import" in content:
    content = re.sub(r'(from sqlalchemy import [^\n]+)', r'\1, case', content, count=1)
else:
    content = "from sqlalchemy import case\n" + content

with open('backend/services/metricas_factuais.py', 'w') as f:
    f.write(content)
