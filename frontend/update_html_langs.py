import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Translate Widget to only include Indian languages
old_trans = "new google.translate.TranslateElement({pageLanguage: 'en', layout: google.translate.TranslateElement.InlineLayout.SIMPLE}, 'google_translate_element');"
new_trans = "new google.translate.TranslateElement({pageLanguage: 'en', includedLanguages: 'hi,mr,ta,te,gu,pa,bn,kn,ml,or', layout: google.translate.TranslateElement.InlineLayout.SIMPLE}, 'google_translate_element');"
html = html.replace(old_trans, new_trans)

# 2. Add Native Language Toggles
toggles = '''    <div style="position: absolute; top: 1rem; left: 50%; transform: translateX(-50%); display: flex; gap: 0.5rem; z-index: 1000; background: rgba(0,0,0,0.5); padding: 0.5rem; border-radius: 20px; border: 1px solid var(--border);">
        <button onclick="setNativeLanguage('en')" style="background: none; border: none; color: white; cursor: pointer; padding: 0.2rem 0.5rem; border-radius: 10px;" id="lang-btn-en">English</button>
        <button onclick="setNativeLanguage('hinglish')" style="background: none; border: none; color: white; cursor: pointer; padding: 0.2rem 0.5rem; border-radius: 10px;" id="lang-btn-hinglish">Hinglish</button>
        <button onclick="setNativeLanguage('hi')" style="background: none; border: none; color: white; cursor: pointer; padding: 0.2rem 0.5rem; border-radius: 10px;" id="lang-btn-hi">हिन्दी</button>
    </div>'''
html = html.replace('<div class="app-container">', toggles + '\n    <div class="app-container">')

# 3. Change "Call Expert" to "Call The Farmer"
html = html.replace('<i data-lucide="phone-call"></i> Call Expert', '<i data-lucide="phone-call"></i> Call The Farmer')

# 4. Add data-i18n attributes to hardcoded HTML text for easy replacement
html = html.replace('<h2>Mitti</h2>', '<h2 data-i18n="mitti_title">Mitti</h2>')
html = html.replace('Dashboard</li>', 'Dashboard <span data-i18n="nav_dash" style="display:none"></span></li>')
# Actually, a simple script to replace innerText is easier than adding data tags to everything. We will write a dictionary mapping English strings to Hindi/Hinglish strings in app.js and just text-replace.

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated index.html with language toggles and translation limits")
