import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Replace all occurrences of ampersands in state names in app.py to match index.html
replacements = {
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Andaman & Nicobar Islands": "Andaman and Nicobar Islands",
    "Dadra & Nagar Haveli and Daman & Diu": "Dadra and Nagar Haveli and Daman and Diu"
}

for old, new in replacements.items():
    app_py = app_py.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Fixed state names in app.py!")
