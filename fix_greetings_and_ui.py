import re

# 1. Update app.py greetings
with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

new_greetings = """def get_greeting(state, lang):
    greetings = {
        "Rajasthan": "Khamma Ghani",
        "Punjab": "Sat Sri Akal",
        "Haryana": "Ram Ram",
        "Uttar Pradesh": "Ram Ram",
        "Maharashtra": "Namaskar",
        "Tamil Nadu": "Vanakkam",
        "Gujarat": "Jai Shri Krishna",
        "West Bengal": "Nomoshkar",
        "Kerala": "Namaskaram",
        "Karnataka": "Namaskara",
        "Andhra Pradesh": "Namaskaram",
        "Telangana": "Namaskaram",
        "Odisha": "Jai Jagannath",
        "Assam": "Nomoskar",
        "Jharkhand": "Johar",
        "Chhattisgarh": "Johar",
        "Sikkim": "Tashi Delek",
        "Ladakh": "Julley",
        "Manipur": "Khurumjari",
        "Mizoram": "Chibai"
    }
    
    if lang == "hi":
        return "नमस्ते किसान भाई!"
    
    return f"{greetings.get(state, 'Namaste')}!"
"""

app_py = re.sub(r'def get_greeting\(state, lang\):.*?return f"\{greetings\.get\(state, \'Namaste\'\)\}!"', new_greetings, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

# 2. Fix index.html
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the absolute positioned div with lang buttons
html = re.sub(r'<div style="position: absolute; top: 1rem; left: 50%;.*?</button>\s*</div>', '', html, flags=re.DOTALL)

# Add Google Translate div in the top header if it's not already in a good place
if 'id="google_translate_element"' not in html:
    html = html.replace('<header class="top-header">', '<header class="top-header">\n<div id="google_translate_element" style="position: absolute; top: 1rem; right: 1rem; z-index: 1000;"></div>')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated greetings and removed old buttons.")
