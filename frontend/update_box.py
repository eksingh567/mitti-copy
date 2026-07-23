import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_feedback = '<div style="margin-top: 1.5rem; line-height: 1.6; color: var(--text-muted);" id="detailFeedback">'
new_feedback = '''<div style="margin-top: 1.5rem; line-height: 1.6; color: var(--text-muted); background: rgba(250, 204, 21, 0.05); border: 1px solid rgba(250, 204, 21, 0.3); border-left: 4px solid #facc15; padding: 1.5rem; border-radius: 8px;" id="detailFeedback">'''

html = html.replace(old_feedback, new_feedback)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Added distinct suggestion box")
