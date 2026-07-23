import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Increase the penalty for soil mismatch from 15 to 40
old_penalty = """
        if active_profile not in profile.get("soils", []):
            penalty += 15
"""
new_penalty = """
        if active_profile not in profile.get("soils", []):
            penalty += 40
"""

app_py = app_py.replace(old_penalty, new_penalty)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Increased soil mismatch penalty to 40 points!")
