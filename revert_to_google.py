import re

# 1. Fix app.py region bug
with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

app_py = app_py.replace('region = request.args.get("region", "West")', 'region = STATE_TO_REGION.get(state, "North")')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

# 2. Revert index.html
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    index_html = f.read()

lang_controls = r'''<div class="lang-controls">.*?</div>'''
google_div = r'''<div id="google_translate_element" style="margin-right: 20px;"></div>'''

index_html = re.sub(lang_controls, google_div, index_html, flags=re.DOTALL)

if 'googleTranslateElementInit' not in index_html:
    google_scripts = r'''
    <!-- Google Translate -->
    <script type="text/javascript">
      function googleTranslateElementInit() {
        new google.translate.TranslateElement({
          pageLanguage: 'en',
          includedLanguages: 'en,hi,pa,mr,ta,gu,bn,te,kn,ml,or,as,ur',
          layout: google.translate.TranslateElement.InlineLayout.SIMPLE
        }, 'google_translate_element');
      }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    '''
    index_html = index_html.replace('</body>', google_scripts + '\n</body>')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)

# 3. Clean up app.js (remove translation logic from UI elements)
with open('frontend/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

app_js = re.sub(r'\$\{currentLang === \'hi\' \? \(details\.name_hi \|\| details\.name_en\) : \(details\.name_en \|\| cropKey\)\}', '${details.name_en || cropKey}', app_js)

# Also force currentLang to be en so the backend returns English, letting Google Translate do its job
app_js = re.sub(r'let currentLang = \'.*?\';', "let currentLang = 'en';", app_js)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(app_js)

print("Reverted to Google Translate and fixed region bug!")
