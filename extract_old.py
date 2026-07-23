import re

with open('app_old.py', 'r', encoding='utf-8') as f:
    old_py = f.read()

match = re.search(r'DASHBOARD_HTML\s*=\s*\"\"\"(.*?)\"\"\"', old_py, re.DOTALL)
if match:
    dashboard_html = match.group(1)
    with open('old_dashboard.html', 'w', encoding='utf-8') as out:
        out.write(dashboard_html)
    print("Extracted DASHBOARD_HTML to old_dashboard.html")
else:
    print("Could not find DASHBOARD_HTML in app_old.py")
