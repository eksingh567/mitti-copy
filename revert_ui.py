import re

with open('old_dashboard.html', 'r', encoding='utf-8') as f:
    old_html = f.read()

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Replace LAYOUT_HTML and DASHBOARD_CONTENT with DASHBOARD_HTML
# First, remove DASHBOARD_CONTENT block
app_py = re.sub(r'DASHBOARD_CONTENT\s*=\s*\"\"\"(.*?)\"\"\"', '', app_py, flags=re.DOTALL)
# Replace LAYOUT_HTML block with DASHBOARD_HTML
app_py = re.sub(r'LAYOUT_HTML\s*=\s*\"\"\"(.*?)\"\"\"', 'DASHBOARD_HTML = """\\n' + old_html.replace('"', '\\"') + '\\n"""', app_py, flags=re.DOTALL)

# In dashboard(), change the return statement
# From: return render_template_string(LAYOUT_HTML, content=content_html, active_page='dashboard', data=latest)
# To: return render_template_string(DASHBOARD_HTML, data=latest, advisories=english_list, english=english_text, wisdom=wisdom, timestamp=latest.get("timestamp", "Not yet received"), soil_profile=soil_profile)

# Find the lines:
old_return = """    content_html = render_template_string(
        DASHBOARD_CONTENT,
        data=latest,
        advisories=english_list,
        english=english_text,
        wisdom=wisdom,
        greeting=greeting,
        timestamp=latest.get("timestamp", "Not yet received"),
        state=session.get("state", "Rajasthan"),
        city=session.get("city", "Jaipur"),
        soil_profile=soil_profile
    )
    # Wrap it in layout
    return render_template_string(LAYOUT_HTML, content=content_html, active_page='dashboard', data=latest)"""

new_return = """    return render_template_string(
        DASHBOARD_HTML,
        data=latest,
        advisories=english_list,
        english=english_text,
        wisdom=wisdom,
        greeting=greeting,
        timestamp=latest.get("timestamp", "Not yet received"),
        state=session.get("state", "Rajasthan"),
        city=session.get("city", "Jaipur"),
        soil_profile=soil_profile
    )"""

app_py = app_py.replace(old_return, new_return)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Reverted to old UI")
