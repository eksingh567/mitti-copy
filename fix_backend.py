import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Fix NameError by ensuring lang is defined in dashboard()
def replace_dashboard(match):
    return 'def dashboard():\n    state = request.args.get("state", "Rajasthan")\n    lang = request.args.get("lang", "en")'

app_py = re.sub(r'def dashboard\(\):\n\s*state = request\.args\.get\("state", "Rajasthan"\)', replace_dashboard, app_py)

# Add personalized greeting based on state
greeting_logic = '''def get_greeting(state, lang):
    greetings = {
        "Punjab": "Sat Sri Akal",
        "Maharashtra": "Namaskar",
        "Tamil Nadu": "Vanakkam",
        "Gujarat": "Kem Cho",
        "West Bengal": "Nomoshkar",
        "Kerala": "Namaskaram",
        "Karnataka": "Namaskara",
        "Andhra Pradesh": "Namaskaram",
        "Telangana": "Namaskaram",
        "Odisha": "Namaskar"
    }
    
    if lang == "hi":
        return "नमस्ते किसान भाई!"
    
    return f"{greetings.get(state, 'Namaste')}!"
'''

app_py = app_py.replace('def dashboard():', greeting_logic + '\n@app.route("/")\ndef dashboard():')
# Wait, I just replaced def dashboard():, but it's part of @app.route("/")\ndef dashboard():
# Actually, I'll just use regex.

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)
