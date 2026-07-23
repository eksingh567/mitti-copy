import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove Google Translate widget completely
html = re.sub(r'<div id="google_translate_element".*?</script>', '', html, flags=re.DOTALL)

# 2. Fix Layout by extracting view-encyclopedia and view-history, and placing them at the end.
encyc_match = re.search(r'(<!-- Encyclopedia View -->.*?</div>\s*</div>)', html, flags=re.DOTALL)
if not encyc_match:
    # Try another regex
    encyc_match = re.search(r'(<!-- Encyclopedia View -->.*?</div>\s*<!-- History View -->)', html, flags=re.DOTALL)
    
history_match = re.search(r'(<!-- History View -->.*?</div>\s*</div>)', html, flags=re.DOTALL)
if not history_match:
    history_match = re.search(r'(<!-- History View -->.*?</form>\s*</section>.*?</section>\s*</div>\s*</div>)', html, flags=re.DOTALL)

if encyc_match and history_match:
    encyc_html = encyc_match.group(1)
    history_html = history_match.group(1)
    
    # Remove them from current position
    html = html.replace(encyc_html, '')
    html = html.replace(history_html, '')
    
    # Also remove the early closing of view-dashboard
    html = html.replace('</div> <!-- End view-dashboard -->', '')
    
    # Place them at the end of main
    html = html.replace('</main>', f'</div> <!-- End view-dashboard -->\n{encyc_html}\n{history_html}\n</main>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Fixed layout and removed google translate widget")
